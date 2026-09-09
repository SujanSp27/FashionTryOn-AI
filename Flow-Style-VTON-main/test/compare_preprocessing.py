"""
Comparison of Current Preprocessing vs. Previous (Old) Preprocessing
Measures actual collar Y coordinate, bounding box, and canvas placement across real test garments.
"""

import os
import sys
from pathlib import Path
from PIL import Image
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from garment_preprocessor import GarmentPreprocessor


def old_garment_placement(garment_rgb: Image.Image, garment_mask: Image.Image, target_w: int = 192, target_h: int = 256):
    """Previous implementation: blind vertical centering."""
    mask_np = np.array(garment_mask)
    ys, xs = np.where(mask_np > 30)
    if len(ys) == 0 or len(xs) == 0:
        return garment_rgb.resize((target_w, target_h), Image.Resampling.BICUBIC), garment_mask.resize((target_w, target_h), Image.Resampling.NEAREST), (0, 0, target_w, target_h)

    ymin, ymax = int(ys.min()), int(ys.max())
    xmin, xmax = int(xs.min()), int(xs.max())

    crop_rgb = garment_rgb.crop((xmin, ymin, xmax + 1, ymax + 1))
    crop_mask = garment_mask.crop((xmin, ymin, xmax + 1, ymax + 1))

    w_c, h_c = crop_rgb.size
    avail_w = int(target_w * 0.90)  # 172
    avail_h = int(target_h * 0.90)  # 230
    scale = min(avail_w / max(1, w_c), avail_h / max(1, h_c))
    new_w = max(1, int(round(w_c * scale)))
    new_h = max(1, int(round(h_c * scale)))

    resized_rgb = crop_rgb.resize((new_w, new_h), Image.Resampling.BICUBIC)
    resized_mask = crop_mask.resize((new_w, new_h), Image.Resampling.NEAREST)

    canvas_rgb = Image.new("RGB", (target_w, target_h), (0, 0, 0))
    canvas_mask = Image.new("L", (target_w, target_h), 0)

    # OLD: Centered vertically
    offset_x = (target_w - new_w) // 2
    offset_y = (target_h - new_h) // 2

    canvas_rgb.paste(resized_rgb, (offset_x, offset_y))
    canvas_mask.paste(resized_mask, (offset_x, offset_y))

    c_rgb_np = np.array(canvas_rgb)
    c_mask_np = np.array(canvas_mask)
    c_rgb_np[c_mask_np == 0] = 0

    return Image.fromarray(c_rgb_np, "RGB"), Image.fromarray(c_mask_np, "L"), (offset_x, offset_y, new_w, new_h)


def find_garment_dir():
    """Locates available garment images directory."""
    candidates = [
        SCRIPT_DIR / "garment_tests",
        SCRIPT_DIR / "mini_dataset" / "test_clothes",
        SCRIPT_DIR / "data_viton" / "VITON_test" / "test_clothes"
    ]
    for c in candidates:
        if c.exists() and any(c.glob("*.jpg")):
            return c
    return None


def main():
    prep = GarmentPreprocessor(mode="simple", debug=False)
    garment_dir = find_garment_dir()

    print("=" * 80)
    print("PREPROCESSING COMPARISON: PREVIOUS (CENTERED) vs CURRENT (CANONICAL)")
    print("=" * 80)
    print("Ground Truth VITON Reference:")
    print("  Collar Y in [8, 16] px (~3% to 6% of height)")
    print("  Width in [175, 191] px (~91% to 100% of width)")
    print("-" * 80)

    if garment_dir is None:
        print("[-] Error: No garment test directory found.")
        return

    # Select representative test garments
    available = list(garment_dir.glob("*.jpg"))
    test_names = ["03_dark_bg.jpg", "04_colored_bg.jpg", "10_patterned.jpg"]
    targets = [garment_dir / n for n in test_names if (garment_dir / n).exists()]
    if not targets:
        targets = available[:3]

    comparison_strips = []

    for p in targets:
        orig_pil = prep._load_pil(p, "Garment")
        orig_rgb = orig_pil.convert("RGB")
        rgba = prep.remove_background(orig_pil)
        clean_mask = prep.create_mask(rgba)

        # 1. Old (centered)
        old_g, old_m, (old_ox, old_oy, old_w, old_h) = old_garment_placement(orig_rgb, clean_mask)
        old_m_np = np.array(old_m)
        old_ys, old_xs = np.where(old_m_np > 30)

        # 2. Current (canonical)
        curr_g, curr_m = prep.preserve_aspect_ratio_and_center(orig_rgb, clean_mask)
        curr_m_np = np.array(curr_m)
        curr_ys, curr_xs = np.where(curr_m_np > 30)

        shift = int(old_ys.min()) - int(curr_ys.min())

        print(f"Garment: {p.name}")
        print(f"  [PREVIOUS/OLD] Collar Top Y: {old_ys.min():3d} | Bottom Y: {old_ys.max():3d} | Width: {old_xs.max()-old_xs.min():3d} | Height: {old_ys.max()-old_ys.min():3d}")
        print(f"  [CURRENT]      Collar Top Y: {curr_ys.min():3d} | Bottom Y: {curr_ys.max():3d} | Width: {curr_xs.max()-curr_xs.min():3d} | Height: {curr_ys.max()-curr_ys.min():3d}")
        print(f"  -> Alignment Shift: Collar placed {shift:+d}px higher (anchored to y={curr_ys.min()} matching VITON standard)")
        print("-" * 80)

        # Strip: Original | Old Preprocessed | Current Preprocessed | Current Mask
        w, h = 192, 256
        strip = Image.new("RGB", (w * 4, h), (25, 25, 25))
        strip.paste(orig_pil.resize((w, h)), (0, 0))
        strip.paste(old_g, (w, 0))
        strip.paste(curr_g, (w * 2, 0))
        strip.paste(curr_m.convert("RGB"), (w * 3, 0))
        comparison_strips.append(strip)

    if comparison_strips:
        total_h = h * len(comparison_strips)
        combined = Image.new("RGB", (w * 4, total_h), (0, 0, 0))
        for i, s in enumerate(comparison_strips):
            combined.paste(s, (0, i * h))
        out_path = SCRIPT_DIR / "preprocessing_comparison.jpg"
        combined.save(out_path, quality=92)
        print(f"[+] Saved visual comparison to: {out_path.resolve()}")


if __name__ == "__main__":
    main()
