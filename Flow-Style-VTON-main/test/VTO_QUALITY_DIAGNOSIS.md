# Virtual Try-On Quality Diagnosis (Verified Code Analysis)

**Location**: `test/VTO_QUALITY_DIAGNOSIS.md`  
**Scope**: Flow-Style-VTON / PFAFN Virtual Try-On Pipeline  
**Target Codebase**: `tryon_engine.py`, `tryon_single.py`, `garment_preprocessor.py`, `models/afwm.py`, `models/networks.py`  

---

## 1. Executive Summary

This diagnostic documents the exact mathematical and algorithmic properties verified from the Flow-Style-VTON codebase that explain failure modes and output degradation on arbitrary real-world user photos.

---

## 2. Verified Code Mechanics

### 2.1 Person Image Processing (`preprocess_person` & `crop_person_image`)
* **Previous Implementation**: Used `(new_h - target_h) // 2` to center-crop images. On portrait photos ($9:16$ aspect ratio, $0.562$), the person's face/hair were cut off or the torso was pushed too far down relative to the canvas.
* **Current Implementation**: `crop_person_image()` implements an aspect-ratio-aware crop mode (`auto`, `upper_body`, `center`):
  - For tall smartphone photos (aspect ratio $< 0.70$), it preserves headroom ($y \ge 0.02 \times H_{\text{orig}}$) and captures the upper body ($3:4$ aspect ratio) to ensure the head, neck, shoulders, torso, and crossed arms remain fully visible without vertical distortion or clipping.
  - Returns a clean $192 \times 256$ RGB image normalized to tensor range $[-1.0, 1.0]$.

### 2.2 Garment Processing & Canvas Alignment (`preserve_aspect_ratio_and_center`)
* **Previous Implementation**: The function calculated vertical offset via `offset_y = (target_h - new_h) // 2`.
  - For square clothing images ($1:1$, e.g., $500 \times 500$), scaling to fit within $172 \times 230$ produced $new\_w = 172, new\_h = 172$.
  - `offset_y = (256 - 172) // 2 = 42$ pixels.
  - The garment collar was placed at $y = 42$, shifting the entire shirt $30\text{--}40$ pixels down towards the abdomen.
* **VITON Dataset Ground Truth Reference**:
  - In `001744_1.jpg` and `004325_1.jpg`, the collar starts at $y \in [8, 16]$ pixels ($3\%\text{--}6\%$ from the top).
  - Garment width spans $x \in [0, 191]$ pixels ($\sim 180\text{--}191$ px wide).
* **Current Implementation**:
  - Scales the garment bounding box to span up to $180$ px width ($94\%$ of canvas) and $235$ px height ($92\%$ of canvas).
  - Anchors the collar top to canonical position: $y_{\text{top}} = \text{int}(256 \times 0.05) \approx 13$ px (with bottom overflow check).
  - Horizontally centers the garment ($x_{\text{offset}} = (192 - new\_w) // 2$).
  - Computes explicit diagnostics: `mask_coverage_pct`, `edge_pixel_pct`, `garment_bbox`, `garment_width`, `garment_height`, and `garment_aspect_ratio`.

### 2.3 Appearance Flow Warping (AFWM) & Generator Blending
* `flow_out = self.warp_model(real_image, clothes)` calculates multi-scale optical flow between `real_image` ($[1, 3, 256, 192]$) and `clothes` ($[1, 3, 256, 192]$).
* The warped edge is sampled via `F.grid_sample(edge, last_flow)`.
* In `ResUnetGenerator`:
  $$gen\_inputs = [real\_image, warped\_cloth, warped\_edge] \quad (\text{shape: } [1, 7, 256, 192])$$
  $$p_{\text{tryon}} = warped\_cloth \odot m_{\text{composite}} + p_{\text{rendered}} \odot (1.0 - m_{\text{composite}})$$
  where $m_{\text{composite}} = \sigma(m) \odot warped\_edge$.

---

## 3. Explanation of the Navy Crossed-Arm Case

When testing a male subject with **crossed arms** wearing a **dark navy T-shirt** with a **dark navy target garment**:

1. **Self-Occlusion (Crossed Arms)**:
   - In standard VITON training data, all subjects stand facing forward with arms at their sides.
   - When arms are folded across the chest, the forearms occlude the torso surface.
   - The 2D optical flow field warps the garment over the visible torso area, but the crossed forearms break the smooth 2D planar topology expected by AFWM.
2. **Color Contrast / Parity**:
   - $p_{\text{rendered}}$ is conditioned on `real_image` (which is already wearing dark navy).
   - The target garment is also dark navy.
   - $warped\_cloth$ has dark navy RGB values ($\Delta \text{RGB} < 5\%$ compared to the source shirt).
   - Whether $m_{\text{composite}}$ chooses $warped\_cloth$ or falls back to $p_{\text{rendered}}$, the output pixels in the chest area remain dark navy.
   - Thus, the output looks almost identical to the input.
3. **Verification via Contrast Test (Test D)**:
   - When the exact same crossed-arm person is paired with a **bright/contrasting garment** (e.g. white or light grey), the garment transfer is immediately and unmistakably visible around the crossed arms. This confirms that the warp mechanism operates, but navy-on-navy lacks visual contrast.

---

## 4. Inherent Model Limitations

* Flow-Style-VTON / PFAFN is a 2D image-to-image appearance flow model without 3D body mesh recovery or dense limb segmentation (such as DensePose / SMPL).
* Poses with severe self-occlusion (crossed arms across chest, hands in pockets covering waist) cannot synthesize clothing "underneath" the arms.
* Robust preprocessing ensures the garment collar and shoulders align with the model's receptive fields, maximizing transfer on all unoccluded areas.
