"""
Flow-Style-VTON Garment Preprocessor with AI Background Removal
Paper: Style-Based Global Appearance Flow for Virtual Try-On (CVPR 2022)

This module provides robust garment preprocessing for real-world product photos,
in-the-wild images, and e-commerce catalog garments.

Key Capabilities:
1. Pretrained AI background removal via rembg (U²-Net) - loaded once and cached.
2. Binary garment silhouette and edge mask generation.
3. Morphological cleanup (island removal, small hole filling) without destroying
   delicate sleeves, collars, buttons, or thin straps.
4. Bounding-box detection, aspect-ratio preservation, and centered canvas fitting (256x192).
5. Modular fallback modes: 'ai' (default), 'simple' (thresholding), 'provided_mask'.
6. Optional debug outputs (01 to 05 images) for inspection and diagnosis.
"""

import os
import sys
import time
from pathlib import Path
from typing import Union, Tuple, Optional

import cv2
import numpy as np
import torch
import torchvision.transforms as transforms
from PIL import Image

try:
    import rembg
    REMBG_AVAILABLE = True
except ImportError:
    REMBG_AVAILABLE = False


class GarmentPreprocessor:
    """
    Dedicated Garment Preprocessing & Background Removal Module.

    Initializes the AI segmentation model (U²-Net session) ONCE during startup
    and processes arbitrary garment images into aligned tensors for Flow-Style-VTON.
    """

    def __init__(
        self,
        mode: str = "ai",
        model_name: str = "u2net",
        device: Optional[Union[str, torch.device]] = None,
        debug: bool = False,
        output_debug_dir: Optional[Union[str, Path]] = None
    ):
        """
        Args:
            mode: 'ai' (U²-Net background removal), 'simple' (thresholding), or 'provided_mask'.
            model_name: rembg model name ('u2net', 'u2netp', 'u2net_cloth_seg'). Default: 'u2net'.
            device: torch device ('cuda' or 'cpu').
            debug: If True, saves intermediate debug images (01_original to 05_final).
            output_debug_dir: Directory to save debug artifacts.
        """
        self.mode = mode.lower()
        self.model_name = model_name
        self.debug = debug
        self.output_debug_dir = Path(output_debug_dir) if output_debug_dir else None

        if device is None:
            self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        else:
            self.device = torch.device(device)

        # Transforms
        self.transform_rgb = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        ])
        self.transform_mask = transforms.Compose([
            transforms.ToTensor()
        ])

        # Initialize AI session ONCE
        self.session = None
        if self.mode == "ai":
            if not REMBG_AVAILABLE:
                print("[GarmentPreprocessor] Warning: rembg not installed. Falling back to mode='simple'.")
                self.mode = "simple"
            else:
                t0 = time.time()
                print(f"[GarmentPreprocessor] Initializing AI background remover ({self.model_name})...")
                self.session = rembg.new_session(self.model_name)
                print(f"[GarmentPreprocessor] AI session ready in {time.time() - t0:.2f}s!")

    def _load_pil(self, img_input: Union[str, Path, Image.Image], input_name: str = "Garment") -> Image.Image:
        """Helper to ensure image is a valid PIL Image."""
        if isinstance(img_input, Image.Image):
            return img_input
        path = Path(img_input)
        if not path.exists():
            raise FileNotFoundError(f"{input_name} not found at: {path}")
        valid_exts = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
        if path.suffix.lower() not in valid_exts:
            raise ValueError(f"{input_name} extension '{path.suffix}' not supported. Valid: {valid_exts}")
        try:
            return Image.open(path)
        except Exception as e:
            raise ValueError(f"Could not decode {input_name} from {path}: {str(e)}")

    def remove_background(self, garment_image: Image.Image) -> Image.Image:
        """
        Removes background from garment image and returns RGBA PIL Image.
        """
        # If in AI mode and session is available:
        if self.mode == "ai" and self.session is not None:
            rgba = rembg.remove(garment_image, session=self.session)
            return rgba

        # Simple mode fallback (heuristic thresholding):
        return self._simple_background_removal(garment_image)

    def _simple_background_removal(self, garment_image: Image.Image) -> Image.Image:
        """Fallback thresholding background removal for catalog/flat-lay images."""
        cloth_np = np.array(garment_image)
        if len(cloth_np.shape) == 3 and cloth_np.shape[2] == 4:
            return garment_image  # Already RGBA

        rgb = cloth_np[:, :, :3] if cloth_np.ndim == 3 else np.stack([cloth_np]*3, axis=-1)
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)

        h, w = gray.shape[:2]
        c_size = max(5, min(h, w) // 20)
        corners = np.concatenate([
            gray[:c_size, :c_size].flatten(),
            gray[:c_size, -c_size:].flatten(),
            gray[-c_size:, :c_size].flatten(),
            gray[-c_size:, -c_size:].flatten()
        ])
        bg_val = float(np.median(corners))

        if bg_val > 180:
            thresh = max(180, int(bg_val - 15))
            _, mask = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY_INV)
        else:
            thresh = min(80, int(bg_val + 20))
            _, mask = cv2.threshold(gray, thresh, 255, cv2.THRESH_BINARY)

        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Composite into RGBA
        rgba = np.dstack([rgb, mask])
        return Image.fromarray(rgba, mode="RGBA")

    def create_mask(self, rgba_image: Image.Image) -> Image.Image:
        """
        Extracts alpha channel from RGBA image and performs morphological cleanup:
        - Removes small disconnected noise blobs
        - Fills small interior voids without eroding garment edges or sleeve details
        Returns grayscale PIL Image ('L') with values in [0, 255].
        """
        alpha = np.array(rgba_image)[:, :, 3]

        # Step 1: Binarize alpha channel at threshold 127
        _, bin_mask = cv2.threshold(alpha, 127, 255, cv2.THRESH_BINARY)

        # Step 2: Remove small isolated components (noise / speckles)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(bin_mask, connectivity=8)
        if num_labels > 1:
            total_fg = np.sum(bin_mask > 0)
            # Filter threshold proportional to garment size
            min_area = max(50, int(total_fg * 0.002))
            clean_mask = np.zeros_like(bin_mask)
            for i in range(1, num_labels):
                if stats[i, cv2.CC_STAT_AREA] >= min_area:
                    clean_mask[labels == i] = 255
        else:
            clean_mask = bin_mask

        # Step 3: Gentle closing to seal tiny pinholes (small 3x3 ellipse to preserve sleeves/straps)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        clean_mask = cv2.morphologyEx(clean_mask, cv2.MORPH_CLOSE, kernel)

        return Image.fromarray(clean_mask, mode="L")

    def create_edge(self, mask: Image.Image) -> Image.Image:
        """
        Formats mask to the Flow-Style-VTON edge representation.
        (Flow-Style-VTON uses the binary/anti-aliased silhouette where garment=1, background=0).
        """
        return mask.copy()

    def preserve_aspect_ratio_and_center(
        self,
        garment_rgb: Image.Image,
        garment_mask: Image.Image,
        target_w: int = 192,
        target_h: int = 256,
        padding_ratio: float = 0.05
    ) -> Tuple[Image.Image, Image.Image]:
        """
        Detects garment bounding box from mask, crops both RGB and mask with the exact same box,
        preserves original aspect ratio, and places onto the 192x256 canvas according to canonical
        VITON training distribution:
        - Scaled to span ~94% of canvas width (180px) and ~92% of height (235px)
        - Horizontally centered
        - Collar/neckline anchored at canonical top margin (y ~ 12-14px), matching VITON reference
        - Computes and logs quantitative diagnostics
        Zero pixel shift between garment RGB and mask.
        """
        mask_np = np.array(garment_mask)
        ys, xs = np.where(mask_np > 30)

        if len(ys) == 0 or len(xs) == 0:
            # Empty mask fallback: resize directly
            r_rgb = garment_rgb.resize((target_w, target_h), Image.Resampling.BICUBIC)
            r_mask = garment_mask.resize((target_w, target_h), Image.Resampling.NEAREST)
            self.last_diagnostics = {
                "mask_coverage_pct": 0.0,
                "edge_pixel_pct": 0.0,
                "garment_bbox": (0, 0, 0, 0),
                "garment_width": 0,
                "garment_height": 0,
                "garment_aspect_ratio": 0.0,
                "collar_y": 0,
                "hem_y": 0
            }
            return r_rgb, r_mask

        # Bounding box
        ymin, ymax = int(ys.min()), int(ys.max())
        xmin, xmax = int(xs.min()), int(xs.max())

        crop_rgb = garment_rgb.crop((xmin, ymin, xmax + 1, ymax + 1))
        crop_mask = garment_mask.crop((xmin, ymin, xmax + 1, ymax + 1))

        w_c, h_c = crop_rgb.size

        # In VITON, garments span ~175-184px wide and ~215-235px high
        max_w = int(round(target_w * 0.94))  # ~180 px
        max_h = int(round(target_h * 0.92))  # ~235 px

        scale = min(max_w / max(1, w_c), max_h / max(1, h_c))
        new_w = max(1, int(round(w_c * scale)))
        new_h = max(1, int(round(h_c * scale)))

        # Resize both identically
        resized_rgb = crop_rgb.resize((new_w, new_h), Image.Resampling.BICUBIC)
        resized_mask = crop_mask.resize((new_w, new_h), Image.Resampling.NEAREST)

        # Create target canvas (black background for RGB, 0 for mask)
        canvas_rgb = Image.new("RGB", (target_w, target_h), (0, 0, 0))
        canvas_mask = Image.new("L", (target_w, target_h), 0)

        # Horizontal alignment: center
        offset_x = (target_w - new_w) // 2

        # Vertical alignment: Anchor to canonical VITON collar position (y ~ 12-14px)
        # Prevents garments from sitting down on the stomach/waist
        canonical_top = int(round(target_h * 0.05))  # ~13 px
        if canonical_top + new_h > target_h - 4:
            offset_y = max(4, target_h - new_h - 4)
        else:
            offset_y = canonical_top

        canvas_rgb.paste(resized_rgb, (offset_x, offset_y))
        canvas_mask.paste(resized_mask, (offset_x, offset_y))

        # Ensure background pixels outside mask are strictly black (0, 0, 0)
        c_rgb_np = np.array(canvas_rgb)
        c_mask_np = np.array(canvas_mask)
        c_rgb_np[c_mask_np == 0] = 0

        # Calculate diagnostics
        total_pixels = target_w * target_h
        mask_fg_pixels = int(np.sum(c_mask_np > 30))
        coverage_pct = round((mask_fg_pixels / total_pixels) * 100, 2)
        aspect_ratio = round(w_c / max(1, h_c), 3)

        self.last_diagnostics = {
            "mask_coverage_pct": coverage_pct,
            "edge_pixel_pct": coverage_pct,
            "garment_bbox": (xmin, ymin, xmax, ymax),
            "garment_width": w_c,
            "garment_height": h_c,
            "garment_aspect_ratio": aspect_ratio,
            "collar_y": offset_y,
            "hem_y": offset_y + new_h,
            "canvas_width": new_w,
            "canvas_height": new_h
        }

        if self.debug:
            print(f"[GarmentPreprocessor Diagnostics]")
            print(f"  Bbox: ({xmin}, {ymin}, {xmax}, {ymax}) | Size: {w_c}x{h_c} (aspect: {aspect_ratio})")
            print(f"  Canvas placement: offset=({offset_x}, {offset_y}), size={new_w}x{new_h}")
            print(f"  Collar Y: {offset_y} | Hem Y: {offset_y + new_h} | Mask coverage: {coverage_pct}%")

        return Image.fromarray(c_rgb_np, mode="RGB"), Image.fromarray(c_mask_np, mode="L")

    def prepare_garment_pil(
        self,
        garment_input: Union[str, Path, Image.Image],
        edge_input: Optional[Union[str, Path, Image.Image]] = None,
        debug_prefix: Optional[str] = None
    ) -> Tuple[Image.Image, Image.Image]:
        """
        Executes full preprocessing pipeline and returns aligned (garment_rgb, garment_mask) PIL images.
        """
        orig_pil = self._load_pil(garment_input, "Garment image")
        orig_rgb = orig_pil.convert("RGB")

        # Step 1: Background removal
        if edge_input is not None or self.mode == "provided_mask":
            # Use explicit mask provided
            if edge_input is None:
                raise ValueError("mode='provided_mask' requires edge_input to be provided.")
            raw_mask = self._load_pil(edge_input, "Edge mask").convert("L")
            rgba_image = Image.merge("RGBA", (*orig_rgb.split(), raw_mask))
        else:
            rgba_image = self.remove_background(orig_pil)

        # Step 2: Extract & clean mask
        clean_mask = self.create_mask(rgba_image)

        # Step 3: Edge representation
        edge_image = self.create_edge(clean_mask)

        # Step 4: Aspect-ratio preservation & centered canvas alignment (192x256)
        final_garment, final_mask = self.preserve_aspect_ratio_and_center(
            garment_rgb=orig_rgb,
            garment_mask=clean_mask,
            target_w=192,
            target_h=256
        )

        # Step 5: Optional debug output saving
        if self.debug and self.output_debug_dir is not None:
            self._save_debug_artifacts(
                debug_prefix or "sample",
                orig_rgb,
                rgba_image,
                clean_mask,
                edge_image,
                final_garment,
                final_mask
            )

        return final_garment, final_mask

    def prepare_garment(
        self,
        garment_input: Union[str, Path, Image.Image],
        edge_input: Optional[Union[str, Path, Image.Image]] = None,
        debug_prefix: Optional[str] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Executes full preprocessing and returns normalized PyTorch tensors:
            clothes_tensor: [1, 3, 256, 192] in range [-1, 1]
            edge_tensor:    [1, 1, 256, 192] in range [0.0, 1.0]
        """
        final_garment, final_mask = self.prepare_garment_pil(
            garment_input=garment_input,
            edge_input=edge_input,
            debug_prefix=debug_prefix
        )

        clothes_tensor = self.transform_rgb(final_garment).unsqueeze(0).to(self.device)
        edge_tensor = self.transform_mask(final_mask).unsqueeze(0).to(self.device)
        edge_tensor = (edge_tensor > 0.5).float()
        clothes_tensor = clothes_tensor * edge_tensor

        # Verify dimensions strictly
        assert clothes_tensor.shape == (1, 3, 256, 192), f"Invalid clothes tensor shape: {clothes_tensor.shape}"
        assert edge_tensor.shape == (1, 1, 256, 192), f"Invalid edge tensor shape: {edge_tensor.shape}"

        return clothes_tensor, edge_tensor

    def _save_debug_artifacts(
        self,
        prefix: str,
        orig_rgb: Image.Image,
        rgba: Image.Image,
        mask: Image.Image,
        edge: Image.Image,
        final_garment: Image.Image,
        final_mask: Image.Image
    ):
        """Saves 01 to 05 debug inspection images."""
        d_dir = self.output_debug_dir / prefix
        d_dir.mkdir(parents=True, exist_ok=True)

        orig_rgb.save(d_dir / "01_original_garment.jpg")
        rgba.save(d_dir / "02_removed_background.png")
        mask.save(d_dir / "03_garment_mask.png")
        edge.save(d_dir / "04_garment_edge.png")
        final_garment.save(d_dir / "05_final_garment.png")
        final_mask.save(d_dir / "06_final_canvas_mask.png")


def crop_person_image(
    image: Image.Image,
    mode: str = "auto",
    target_w: int = 192,
    target_h: int = 256
) -> Image.Image:
    """
    Intelligently crops and resizes a person image to (target_w, target_h) preserving aspect ratio.
    
    Modes:
      - 'auto' (default): For smartphone portraits / full-body photos (aspect < 0.70), anchors crop to the
                upper body to prevent slicing off the head or burying torso/arms at the bottom.
                For wide/square photos, center-crops horizontally.
                For near-target aspect (0.70 to 0.80), resizes directly.
      - 'upper_body': Explicitly crops the upper body of the image (head, shoulders, chest, arms).
      - 'center': Classic center crop.
    """
    src_w, src_h = image.size
    target_aspect = target_w / target_h  # 0.75
    src_aspect = src_w / src_h

    mode = mode.lower()

    if mode == "upper_body" or (mode == "auto" and src_aspect < 0.65):
        # Tall image (e.g. 9:16 or full-body): focus on upper body
        crop_w = src_w
        crop_h = int(round(src_w / target_aspect))
        if crop_h > src_h:
            crop_h = src_h
            crop_w = int(round(src_h * target_aspect))
            x0 = (src_w - crop_w) // 2
            y0 = 0
        else:
            x0 = 0
            # Leave small headroom (~2% of image height) to avoid chopping hair
            y0 = max(0, int(round(src_h * 0.02)))
            if y0 + crop_h > src_h:
                y0 = src_h - crop_h
        cropped = image.crop((x0, y0, x0 + crop_w, y0 + crop_h))

    elif mode == "auto" and src_aspect < target_aspect:
        # Slightly tall portrait (0.65 <= aspect < 0.75)
        crop_w = src_w
        crop_h = int(round(src_w / target_aspect))
        x0 = 0
        # Gentle top anchor: 15% of vertical slack rather than 50% (center)
        y0 = max(0, int(round((src_h - crop_h) * 0.15)))
        if y0 + crop_h > src_h:
            y0 = src_h - crop_h
        cropped = image.crop((x0, y0, x0 + crop_w, y0 + crop_h))

    elif src_aspect > target_aspect:
        # Wide image (landscape or square): center horizontally
        crop_h = src_h
        crop_w = int(round(src_h * target_aspect))
        x0 = (src_w - crop_w) // 2
        y0 = 0
        cropped = image.crop((x0, y0, x0 + crop_w, y0 + crop_h))

    else:
        # Classic center crop fallback
        if src_aspect > target_aspect:
            new_h = target_h
            new_w = int(round(src_w * (target_h / src_h)))
        else:
            new_w = target_w
            new_h = int(round(src_h * (target_w / src_w)))
        resized = image.resize((new_w, new_h), Image.Resampling.BICUBIC)
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        return resized.crop((left, top, left + target_w, top + target_h))

    return cropped.resize((target_w, target_h), Image.Resampling.BICUBIC)


def resize_and_crop(image: Image.Image, target_w: int = 192, target_h: int = 256) -> Image.Image:
    """Backward-compatible wrapper delegating to crop_person_image in 'auto' mode."""
    return crop_person_image(image, mode="auto", target_w=target_w, target_h=target_h)


def normalize_contrast_brightness(
    garment_rgb: Image.Image,
    person_rgb: Optional[Image.Image] = None,
    enabled: bool = False
) -> Image.Image:
    """
    Optional harmonization of extreme brightness/contrast differences.
    Preserves exact garment hue, pattern, and color identity.
    Disabled by default.
    """
    if not enabled or person_rgb is None:
        return garment_rgb

    garment_np = np.array(garment_rgb)
    person_np = np.array(person_rgb)

    g_lab = cv2.cvtColor(garment_np, cv2.COLOR_RGB2LAB).astype(np.float32)
    p_lab = cv2.cvtColor(person_np, cv2.COLOR_RGB2LAB).astype(np.float32)

    # Focus on torso region of person (y: 60-180, x: 40-150)
    p_torso = p_lab[60:180, 40:150, 0]
    p_mean_l = float(np.mean(p_torso))
    p_std_l = float(np.std(p_torso)) + 1e-5

    # Garment non-black pixels
    g_mask = g_lab[:, :, 0] > 10
    if np.sum(g_mask) > 100:
        g_l = g_lab[:, :, 0]
        g_mean_l = float(np.mean(g_l[g_mask]))
        g_std_l = float(np.std(g_l[g_mask])) + 1e-5

        # Gentle contrast scaling (max 15% adjustment to avoid altering garment identity)
        gain = np.clip(p_std_l / g_std_l, 0.85, 1.15)
        bias = np.clip((p_mean_l - g_mean_l) * 0.15, -20.0, 20.0)

        g_l_adj = (g_l - g_mean_l) * gain + g_mean_l + bias
        g_lab[:, :, 0] = np.where(g_mask, np.clip(g_l_adj, 0, 255), 0)

        norm_rgb = cv2.cvtColor(g_lab.astype(np.uint8), cv2.COLOR_LAB2RGB)
        return Image.fromarray(norm_rgb, mode="RGB")

    return garment_rgb


