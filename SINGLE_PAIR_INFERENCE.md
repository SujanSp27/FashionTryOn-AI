# Flow-Style-VTON: Single-Pair Virtual Try-On Engine & CLI

This document describes the single-pair virtual try-on engine and CLI interface, updated with integrated **AI Garment Background Removal (Prompt 3)**.

---

## 1. Overview

The single-pair virtual try-on system takes any person photograph and any garment image, automatically strips the garment's background, generates the required edge silhouette, aligns the images to $192 \times 256$, and synthesizes the try-on output.

```
person.jpg + garment.jpg (any background)
                   ↓
        GarmentPreprocessor (U²-Net)
                   ↓
   aligned [1,3,256,192] + edge [1,1,256,192]
                   ↓
       TryOnEngine (AFWM + ResUnet)
                   ↓
              tryon.jpg
```

---

## 2. CLI Usage (`tryon_single.py`)

### Basic Command (AI Background Removal by default)
```bash
python tryon_single.py \
    --person path/to/person.jpg \
    --garment path/to/garment.jpg \
    --output result.jpg
```

### Advanced Options
```bash
python tryon_single.py \
    --person path/to/person.jpg \
    --garment path/to/garment.jpg \
    --output result.jpg \
    --bg_mode ai \
    --use_aug \
    --debug \
    --debug_dir debug_artifacts
```

### CLI Arguments Reference

| Argument | Shorthand | Default | Description |
| :--- | :--- | :--- | :--- |
| `--person` | `-p` | *Required* | Path to person photograph (JPG, PNG, WEBP). |
| `--garment` | `-g` | *Required* | Path to garment photograph (any background). |
| `--output` | `-o` | `tryon_result.jpg` | Destination filepath for the synthesized try-on image. |
| `--bg_mode` | | `ai` | Background removal mode: `'ai'` (U²-Net), `'simple'` (thresholding), or `'provided_mask'`. |
| `--edge` | `-e` | `None` | Optional manual edge mask path (used when `--bg_mode provided_mask`). |
| `--use_aug` | | `False` | Use checkpoint trained with affine data augmentation. |
| `--warp_checkpoint`| | Auto-resolved | Custom path to `PFAFN_warp_epoch_101.pth`. |
| `--gen_checkpoint` | | Auto-resolved | Custom path to `PFAFN_gen_epoch_101.pth`. |
| `--gpu` | | `0` | GPU device index (`-1` for CPU, auto-falls back if no CUDA). |
| `--debug` | | `False` | Save intermediate preprocessing images (01 to 06). |
| `--debug_dir` | | `debug_outputs` | Directory to save debug artifacts. |

---

## 3. Python API Integration (`TryOnEngine`)

```python
from tryon_engine import TryOnEngine

# Initialize engine ONCE (caches U²-Net and Flow-Style-VTON models in memory)
engine = TryOnEngine(
    background_removal_mode="ai",
    use_aug=False,
    debug=False
)

# Run inference repeatedly on multiple pairs with zero model reloading
result_pil = engine.try_on(
    person_image="person.jpg",
    garment_image="shirt_on_table.jpg",
    save_path="output_tryon.jpg"
)

# Access precise timings breakdown
print(engine.last_timing)
# {'person_time': 0.027, 'garment_time': 0.78, 'vton_time': 0.92, 'total_time': 1.73}
```
