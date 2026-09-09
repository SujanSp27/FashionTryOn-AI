"""
Flow-Style-VTON / PFAFN Single-Pair Inference Engine with Integrated AI Garment Preprocessor
Paper: Style-Based Global Appearance Flow for Virtual Try-On (CVPR 2022)
Official Repo: https://github.com/SenHe/Flow-Style-VTON

This module provides a production-ready, reusable engine (TryOnEngine)
that initializes the Flow-Style-VTON warping (AFWM), generator (ResUnetGenerator),
and AI background-removal (U²-Net) models ONCE into memory and performs fast
single-pair virtual try-on inference.
"""

import os
import sys
import time
from pathlib import Path
from typing import Union, Tuple, Optional, Dict

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision.transforms as transforms
from PIL import Image

# Ensure models and options packages can be imported
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from models.afwm import AFWM
from models.networks import ResUnetGenerator, load_checkpoint
from garment_preprocessor import (
    GarmentPreprocessor,
    resize_and_crop,
    crop_person_image,
    normalize_contrast_brightness
)


class EngineOpt:
    """Mock options container to satisfy AFWM constructor signature without CLI parsing."""
    def __init__(self, gpu_ids=None):
        self.name = 'tryon_engine'
        self.gpu_ids = gpu_ids if gpu_ids is not None else ([0] if torch.cuda.is_available() else [])
        self.norm = 'instance'
        self.use_dropout = False
        self.data_type = 32
        self.verbose = False
        self.batchSize = 1
        self.loadSize = 512
        self.fineSize = 512
        self.input_nc = 3
        self.output_nc = 3
        self.dataroot = ''
        self.resize_or_crop = 'None'
        self.serial_batches = True
        self.no_flip = True
        self.nThreads = 1
        self.max_dataset_size = float('inf')
        self.display_winsize = 512
        self.tf_log = False
        self.isTrain = False


class TryOnEngine:
    """
    Reusable Single-Pair Virtual Try-On Engine for Flow-Style-VTON (PFAFN).

    Initializes AFWM warp model, ResUnetGenerator, and GarmentPreprocessor ONCE
    and retains them in evaluation mode for fast repeated inference requests.
    """

    def __init__(
        self,
        warp_checkpoint: Optional[Union[str, Path]] = None,
        gen_checkpoint: Optional[Union[str, Path]] = None,
        device: Optional[Union[str, torch.device]] = None,
        use_aug: bool = False,
        background_removal_mode: str = "ai",
        bg_mode: Optional[str] = None,
        model_name: str = "u2net",
        debug: bool = False,
        output_debug_dir: Optional[Union[str, Path]] = None
    ):

        """
        Initialize the TryOnEngine with pretrained checkpoints and target device.

        Args:
            warp_checkpoint: Path to PFAFN_warp_epoch_101.pth. If None, resolves default.
            gen_checkpoint: Path to PFAFN_gen_epoch_101.pth. If None, resolves default.
            device: 'cuda', 'cuda:0', 'cpu', or torch.device. If None, auto-detected.
            use_aug: If True, selects checkpoints trained with augmentation.
            background_removal_mode: 'ai' (U²-Net), 'simple' (thresholding), or 'provided_mask'.
            bg_mode: Alias for background_removal_mode.
            model_name: Model name for background remover ('u2net').
            debug: Whether to save intermediate debug steps (01 to 05 images).
            output_debug_dir: Directory where debug images will be stored.
        """
        if bg_mode is not None:
            background_removal_mode = bg_mode

        # 1. Device Resolution
        if device is None:
            self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        else:
            resolved = torch.device(device)
            if resolved.type == 'cuda' and not torch.cuda.is_available():
                print(f"[TryOnEngine] WARNING: CUDA requested ('{device}') but not available on this system. Falling back to CPU.")
                self.device = torch.device('cpu')
            else:
                self.device = resolved

        print(f"[TryOnEngine] Initializing engine on device: {self.device}")
        if self.device.type == 'cuda' and torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(self.device)
            vram_gb = torch.cuda.get_device_properties(self.device).total_mem / (1024**3)
            print(f"[TryOnEngine] Active GPU: {gpu_name} ({vram_gb:.2f} GB VRAM)")


        # 2. Checkpoint Path Resolution
        sub = 'aug' if use_aug else ''
        default_ckp_dir = SCRIPT_DIR / 'checkpoints'

        if warp_checkpoint is None:
            cand1 = default_ckp_dir / sub / 'PFAFN_warp_epoch_101.pth'
            cand2 = default_ckp_dir / 'PFAFN_warp_epoch_101.pth'
            self.warp_checkpoint = cand1 if cand1.exists() else cand2
        else:
            self.warp_checkpoint = Path(warp_checkpoint)

        if gen_checkpoint is None:
            cand1 = default_ckp_dir / sub / 'PFAFN_gen_epoch_101.pth'
            cand2 = default_ckp_dir / 'PFAFN_gen_epoch_101.pth'
            self.gen_checkpoint = cand1 if cand1.exists() else cand2
        else:
            self.gen_checkpoint = Path(gen_checkpoint)

        # 3. Validation
        if not self.warp_checkpoint.exists():
            raise FileNotFoundError(
                f"[TryOnEngine] Warp checkpoint not found at: {self.warp_checkpoint}. "
                "Ensure PFAFN_warp_epoch_101.pth is downloaded into test/checkpoints/."
            )
        if not self.gen_checkpoint.exists():
            raise FileNotFoundError(
                f"[TryOnEngine] Generator checkpoint not found at: {self.gen_checkpoint}. "
                "Ensure PFAFN_gen_epoch_101.pth is downloaded into test/checkpoints/."
            )

        warp_size = self.warp_checkpoint.stat().st_size
        gen_size = self.gen_checkpoint.stat().st_size
        if warp_size == 0 or gen_size == 0:
            raise ValueError("[TryOnEngine] Checkpoint file is empty (0 bytes)!")

        print(f"[TryOnEngine] Loading Warp Checkpoint:      {self.warp_checkpoint.name} ({warp_size/(1024*1024):.2f} MB)")
        print(f"[TryOnEngine] Loading Generator Checkpoint: {self.gen_checkpoint.name} ({gen_size/(1024*1024):.2f} MB)")

        # 4. Initialize Flow-Style-VTON Models ONCE
        gpu_ids = [self.device.index] if self.device.type == 'cuda' and self.device.index is not None else ([0] if self.device.type == 'cuda' else [])
        opt = EngineOpt(gpu_ids=gpu_ids)

        t0 = time.time()
        self.warp_model = AFWM(opt, 3).to(self.device).eval()
        load_checkpoint(self.warp_model, str(self.warp_checkpoint))

        self.gen_model = ResUnetGenerator(7, 4, 5, ngf=64, norm_layer=nn.BatchNorm2d).to(self.device).eval()
        load_checkpoint(self.gen_model, str(self.gen_checkpoint))

        for p in self.warp_model.parameters():
            p.requires_grad = False
        for p in self.gen_model.parameters():
            p.requires_grad = False

        # Image transforms
        self.transform_rgb = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))
        ])

        # 5. Initialize GarmentPreprocessor ONCE
        self.garment_preprocessor = GarmentPreprocessor(
            mode=background_removal_mode,
            model_name=model_name,
            device=self.device,
            debug=debug,
            output_debug_dir=output_debug_dir
        )

        self.last_timing: Dict[str, float] = {}
        print(f"[TryOnEngine] Models and preprocessor cached successfully in {time.time() - t0:.2f}s!")

    def _load_pil(self, img_input: Union[str, Path, Image.Image], input_name: str = 'Image') -> Image.Image:
        """Validates and loads a PIL Image."""
        if isinstance(img_input, Image.Image):
            return img_input
        path = Path(img_input)
        if not path.exists():
            raise FileNotFoundError(f"{input_name} not found at path: {path}")
        valid_exts = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}
        if path.suffix.lower() not in valid_exts:
            raise ValueError(f"{input_name} file extension '{path.suffix}' not supported. Supported: {valid_exts}")
        try:
            return Image.open(path)
        except Exception as e:
            raise ValueError(f"Could not decode {input_name} from {path}: {str(e)}")

    def preprocess_person(
        self,
        person_input: Union[str, Path, Image.Image],
        crop_mode: str = "auto"
    ) -> Tuple[torch.Tensor, Image.Image]:
        """
        Preprocesses a person image:
        1. Decodes and converts to RGB
        2. Crops/resizes to 192x256 using intelligent crop_mode ('auto', 'upper_body', 'center')
        3. Normalizes to [-1, 1] tensor of shape [1, 3, 256, 192]
        Returns (tensor, pil_image).
        """
        pil_img = self._load_pil(person_input, 'Person image').convert('RGB')
        pil_cropped = crop_person_image(pil_img, mode=crop_mode, target_w=192, target_h=256)
        tensor = self.transform_rgb(pil_cropped).unsqueeze(0).to(self.device)

        expected_shape = (1, 3, 256, 192)
        if tensor.shape != expected_shape:
            raise ValueError(f"Person tensor shape mismatch: expected {expected_shape}, got {tensor.shape}")
        return tensor, pil_cropped

    def preprocess_garment(
        self,
        garment_input: Union[str, Path, Image.Image],
        edge_input: Optional[Union[str, Path, Image.Image]] = None,
        debug_prefix: Optional[str] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Delegates to self.garment_preprocessor."""
        return self.garment_preprocessor.prepare_garment(
            garment_input=garment_input,
            edge_input=edge_input,
            debug_prefix=debug_prefix
        )

    @torch.no_grad()
    def try_on(
        self,
        person_image: Union[str, Path, Image.Image],
        garment_image: Union[str, Path, Image.Image],
        edge_image: Optional[Union[str, Path, Image.Image]] = None,
        save_path: Optional[Union[str, Path]] = None,
        debug_prefix: Optional[str] = None,
        crop_mode: str = "auto",
        normalize_color: bool = False,
        debug: Optional[bool] = None,
        debug_dir: Optional[Union[str, Path]] = None
    ) -> Image.Image:
        """
        Executes single-pair virtual try-on inference.

        Args:
            person_image: Path to person photo or PIL Image.
            garment_image: Path to garment photo or PIL Image.
            edge_image: Optional explicit garment mask path or PIL Image.
            save_path: Optional file path to save the generated image.
            debug_prefix: Optional prefix for debug output subdirectories.
            crop_mode: Person cropping mode ('auto', 'upper_body', 'center').
            normalize_color: Optional gentle brightness/contrast harmonization.
            debug: Whether to save intermediate debug images (Requirement 6).
            debug_dir: Directory to store debug images.

        Returns:
            PIL.Image.Image: The generated virtual try-on result (192x256 RGB).
        """
        t_start = time.time()
        is_debug = debug if debug is not None else self.garment_preprocessor.debug
        effective_debug_dir = Path(debug_dir) if debug_dir else (self.garment_preprocessor.output_debug_dir or SCRIPT_DIR / "debug_outputs")

        # Step 1: Preprocess Person
        t_p0 = time.time()
        real_image, pil_person_preprocessed = self.preprocess_person(person_image, crop_mode=crop_mode)
        time_person = time.time() - t_p0

        # Step 2: Preprocess Garment via GarmentPreprocessor
        t_g0 = time.time()
        orig_garment_pil = self._load_pil(garment_image, "Garment image")
        orig_garment_rgb = orig_garment_pil.convert("RGB")

        # Optional color normalization
        if normalize_color:
            orig_garment_rgb = normalize_contrast_brightness(
                orig_garment_rgb,
                person_rgb=pil_person_preprocessed,
                enabled=True
            )

        final_garment_pil, final_mask_pil = self.garment_preprocessor.prepare_garment_pil(
            garment_input=orig_garment_rgb,
            edge_input=edge_image,
            debug_prefix=debug_prefix
        )

        # Convert to model tensors
        clothes = self.transform_rgb(final_garment_pil).unsqueeze(0).to(self.device)
        edge = self.garment_preprocessor.transform_mask(final_mask_pil).unsqueeze(0).to(self.device)
        edge = (edge > 0.5).float()
        clothes = clothes * edge

        time_garment = time.time() - t_g0

        # Step 3: Appearance Flow Warping (AFWM)
        t_vton0 = time.time()
        flow_out = self.warp_model(real_image, clothes)
        warped_cloth, last_flow = flow_out

        warped_edge = F.grid_sample(
            edge,
            last_flow.permute(0, 2, 3, 1),
            mode='bilinear',
            padding_mode='zeros',
            align_corners=False
        )

        # Step 4: ResUnet Generator Synthesis
        gen_inputs = torch.cat([real_image, warped_cloth, warped_edge], dim=1)
        gen_outputs = self.gen_model(gen_inputs)
        p_rendered, m_composite = torch.split(gen_outputs, [3, 1], dim=1)
        p_rendered = torch.tanh(p_rendered)
        m_composite = torch.sigmoid(m_composite) * warped_edge
        p_tryon = warped_cloth * m_composite + p_rendered * (1.0 - m_composite)

        # Step 5: Convert tensor to PIL Image (denormalize from [-1, 1] to [0, 255])
        result_tensor = (p_tryon[0] * 0.5 + 0.5).clamp(0, 1)
        result_np = (result_tensor.permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
        result_pil = Image.fromarray(result_np, mode='RGB')

        time_vton = time.time() - t_vton0
        total_time = time.time() - t_start

        # Record benchmark metrics
        self.last_timing = {
            'person_time': time_person,
            'garment_time': time_garment,
            'vton_time': time_vton,
            'total_time': total_time
        }

        # Step 6: Requirement 6 - Save All Debug Outputs if Debug Active
        if is_debug:
            sub = debug_prefix or f"debug_{int(time.time())}"
            d_dir = effective_debug_dir / sub
            d_dir.mkdir(parents=True, exist_ok=True)

            # 1. debug_person_preprocessed.jpg
            pil_person_preprocessed.save(d_dir / "debug_person_preprocessed.jpg")
            # 2. debug_garment_original.jpg
            orig_garment_pil.convert("RGB").save(d_dir / "debug_garment_original.jpg")
            # 3. debug_garment_mask.png
            final_mask_pil.save(d_dir / "debug_garment_mask.png")
            # 4. debug_garment_cutout.png (RGBA cutout)
            cutout_rgba = Image.merge("RGBA", (*final_garment_pil.split(), final_mask_pil))
            cutout_rgba.save(d_dir / "debug_garment_cutout.png")
            # 5. debug_garment_edge.png
            final_mask_pil.save(d_dir / "debug_garment_edge.png")
            # 6. debug_person_tensor.jpg (denormalized tensor visualization)
            p_tensor_denorm = (real_image[0] * 0.5 + 0.5).clamp(0, 1)
            p_tensor_np = (p_tensor_denorm.permute(1, 2, 0).cpu().numpy() * 255).astype(np.uint8)
            Image.fromarray(p_tensor_np, mode='RGB').save(d_dir / "debug_person_tensor.jpg")
            # 7. debug_final_result.jpg
            result_pil.save(d_dir / "debug_final_result.jpg")

            # Composite visual summary: Person | Garment Original | Garment Mask | Garment Preprocessed | Final Try-On
            w, h = 192, 256
            summary_strip = Image.new("RGB", (w * 5, h), (20, 20, 20))
            summary_strip.paste(pil_person_preprocessed.resize((w, h)), (0, 0))
            summary_strip.paste(orig_garment_pil.convert("RGB").resize((w, h)), (w, 0))
            summary_strip.paste(final_mask_pil.convert("RGB"), (w * 2, 0))
            summary_strip.paste(final_garment_pil, (w * 3, 0))
            summary_strip.paste(result_pil, (w * 4, 0))
            summary_strip.save(d_dir / "debug_visual_summary.jpg")
            print(f"[TryOnEngine] Saved complete debug inspection suite to: {d_dir}")

        # Step 7: Save final output if requested
        if save_path is not None:
            save_file = Path(save_path)
            save_file.parent.mkdir(parents=True, exist_ok=True)
            result_pil.save(str(save_file))
            print(f"[TryOnEngine] Saved try-on result to: {save_file}")
            print(f"             Timings: Total={total_time:.3f}s | Garment Prep={time_garment:.3f}s | VTON={time_vton:.3f}s")

        return result_pil
