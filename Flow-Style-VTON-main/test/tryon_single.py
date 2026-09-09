"""
Flow-Style-VTON Single-Pair CLI Tool with AI Background Removal
Usage:
    python tryon_single.py \
        --person person.jpg \
        --garment shirt.jpg \
        --output tryon_result.jpg \
        [--bg_mode ai|simple|provided_mask] \
        [--debug]
"""

import argparse
import sys
import time
from pathlib import Path
import torch


# Add current directory to path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from tryon_engine import TryOnEngine


def main():
    parser = argparse.ArgumentParser(
        description="Flow-Style-VTON Single-Pair Virtual Try-On CLI",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "--person", "-p",
        type=str,
        required=True,
        help="Path to person image (JPG, PNG, JPEG)"
    )
    parser.add_argument(
        "--garment", "-g",
        type=str,
        required=True,
        help="Path to target garment image (JPG, PNG, JPEG)"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="tryon_result.jpg",
        help="Path to save the generated try-on result"
    )
    parser.add_argument(
        "--edge", "-e",
        type=str,
        default=None,
        help="Optional path to explicit garment edge/silhouette mask"
    )
    parser.add_argument(
        "--bg_mode",
        type=str,
        choices=["ai", "simple", "provided_mask"],
        default="ai",
        help="Garment background removal mode: 'ai' (U²-Net), 'simple' (thresholding), 'provided_mask'"
    )
    parser.add_argument(
        "--warp_checkpoint",
        type=str,
        default=None,
        help="Custom path to PFAFN_warp_epoch_101.pth"
    )
    parser.add_argument(
        "--gen_checkpoint",
        type=str,
        default=None,
        help="Custom path to PFAFN_gen_epoch_101.pth"
    )
    parser.add_argument(
        "--use_aug",
        action="store_true",
        help="Use checkpoints trained with augmentation"
    )
    parser.add_argument(
        "--gpu",
        type=int,
        default=0,
        help="GPU device index (-1 for CPU)"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Save intermediate debug artifacts (01 to 05 images)"
    )
    parser.add_argument(
        "--crop_mode",
        type=str,
        choices=["auto", "upper_body", "center"],
        default="auto",
        help="Person aspect ratio cropping mode ('auto', 'upper_body', 'center')"
    )
    parser.add_argument(
        "--normalize_color",
        action="store_true",
        help="Optional gentle brightness/contrast harmonization (disabled by default)"
    )
    parser.add_argument(
        "--debug_dir",
        type=str,
        default="debug_outputs",
        help="Directory to save debug images when --debug is set"
    )

    args = parser.parse_args()

    # Validate inputs exist
    if not Path(args.person).exists():
        print(f"[-] ERROR: Person image not found at: {args.person}", file=sys.stderr)
        sys.exit(1)
    if not Path(args.garment).exists():
        print(f"[-] ERROR: Garment image not found at: {args.garment}", file=sys.stderr)
        sys.exit(1)
    if args.edge is not None and not Path(args.edge).exists():
        print(f"[-] ERROR: Edge mask image not found at: {args.edge}", file=sys.stderr)
        sys.exit(1)

    device = f"cuda:{args.gpu}" if (args.gpu >= 0 and torch.cuda.is_available()) else "cpu"

    print("=" * 60)
    print("FLOW-STYLE-VTON: SINGLE-PAIR VIRTUAL TRY-ON")
    print("=" * 60)
    print(f"Person input:    {args.person}")
    print(f"Garment input:   {args.garment}")
    print(f"BG Removal Mode: {args.bg_mode}")
    if args.edge:
        print(f"Edge mask input: {args.edge}")
    print(f"Output target:   {args.output}")
    print(f"Augmented ckp:   {args.use_aug}")
    print(f"Debug artifacts: {args.debug}")
    print("-" * 60)

    # Initialize engine ONCE
    t_init_start = time.time()
    engine = TryOnEngine(
        warp_checkpoint=args.warp_checkpoint,
        gen_checkpoint=args.gen_checkpoint,
        device=device,
        use_aug=args.use_aug,
        background_removal_mode=args.bg_mode,
        debug=args.debug,
        output_debug_dir=args.debug_dir if args.debug else None
    )
    init_time = time.time() - t_init_start
    print(f"[+] Engine ready in {init_time:.2f}s")
    print("-" * 60)

    # Execute try-on
    print("[*] Running single-pair virtual try-on inference...")
    result = engine.try_on(
        person_image=args.person,
        garment_image=args.garment,
        edge_image=args.edge,
        save_path=args.output,
        debug_prefix=Path(args.output).stem,
        crop_mode=args.crop_mode,
        normalize_color=args.normalize_color,
        debug=args.debug,
        debug_dir=args.debug_dir
    )

    timings = engine.last_timing
    print("=" * 60)
    print(f"[+] SUCCESS! Virtual Try-On image generated:")
    print(f"    File: {Path(args.output).resolve()}")
    print(f"    Resolution: {result.size[0]}x{result.size[1]} (Width x Height)")
    print(f"    Timings breakdown:")
    print(f"      - Person prep:      {timings['person_time']:.3f}s")
    print(f"      - Garment prep (BG):{timings['garment_time']:.3f}s")
    print(f"      - VTON forward:     {timings['vton_time']:.3f}s")
    print(f"      - Total try-on:     {timings['total_time']:.3f}s")
    print("=" * 60)


if __name__ == "__main__":
    main()
