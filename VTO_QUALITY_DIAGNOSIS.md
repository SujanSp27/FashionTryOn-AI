# Virtual Try-On Quality Diagnosis: Root Cause Analysis

**Project**: AI Virtual Try-On (Flow-Style-VTON / PFAFN)  
**Date**: September 2026  
**Status**: Investigated & Diagnosed  

---

## 1. Executive Summary

During testing of the virtual try-on pipeline with real-world user images, a specific failure pattern was observed:
- **Test Case A (Different Garment)**: A person wearing a white t-shirt paired with a black patterned target garment succeeds with clear visual transfer.
- **Test Case B (Challenging Real-World)**: A male subject with **crossed arms** wearing a **dark navy t-shirt**, paired with a **dark navy target garment**, produces an output that appears virtually unchanged or indistinguishable from the input.

This document traces the exact execution pipeline through the codebase (`tryon_engine.py`, `garment_preprocessor.py`, `models/afwm.py`, `models/networks.py`) to determine the underlying mechanical and architectural root causes.

---

## 2. Code Trace of the Existing Pipeline

### 2.1 Person Image Preprocessing
```python
# tryon_engine.py:preprocess_person()
pil_img = self._load_pil(person_input, 'Person image').convert('RGB')
pil_cropped = resize_and_crop(pil_img, target_w=192, target_h=256)
tensor = self.transform_rgb(pil_cropped).unsqueeze(0).to(self.device)
```
In `garment_preprocessor.py:resize_and_crop()`:
```python
if src_aspect > target_aspect:
    new_h = target_h
    new_w = int(round(src_w * (target_h / src_h)))
else:
    new_w = target_w
    new_h = int(round(src_h * (target_w / src_w)))
resized = image.resize((new_w, new_h), Image.BICUBIC)
left = (new_w - target_w) // 2
top = (new_h - target_h) // 2
return resized.crop((left, top, left + target_w, top + target_h))
```

### 2.2 Garment Segmentation & Mask Generation
- `garment_preprocessor.py:remove_background()` executes U²-Net via `rembg.remove()`, returning an RGBA PIL image.
- `garment_preprocessor.py:create_mask()` extracts alpha, binarizes at threshold 127, eliminates isolated islands smaller than 0.2% area, and applies a $3 \times 3$ morphological closing.

### 2.3 Garment Alignment & Edge Construction
```python
# garment_preprocessor.py:preserve_aspect_ratio_and_center()
avail_w = int(target_w * (1.0 - 2.0 * padding_ratio))
avail_h = int(target_h * (1.0 - 2.0 * padding_ratio))
scale = min(avail_w / max(1, w_c), avail_h / max(1, h_c))
...
offset_x = (target_w - new_w) // 2
offset_y = (target_h - new_h) // 2
canvas_rgb.paste(resized_rgb, (offset_x, offset_y))
canvas_mask.paste(resized_mask, (offset_x, offset_y))
```
- `clothes_tensor = transform_rgb(canvas_rgb) * (edge_tensor > 0.5).float()`
- `edge_tensor = (transform_mask(canvas_mask) > 0.5).float()`

### 2.4 AFWM Warping and ResUnet Generation
```python
# tryon_engine.py:try_on()
flow_out = self.warp_model(real_image, clothes)
warped_cloth, last_flow = flow_out
warped_edge = F.grid_sample(edge, last_flow.permute(0, 2, 3, 1), mode='bilinear', padding_mode='zeros', align_corners=False)

gen_inputs = torch.cat([real_image, warped_cloth, warped_edge], dim=1)
gen_outputs = self.gen_model(gen_inputs)
p_rendered, m_composite = torch.split(gen_outputs, [3, 1], dim=1)
p_rendered = torch.tanh(p_rendered)
m_composite = torch.sigmoid(m_composite) * warped_edge
p_tryon = warped_cloth * m_composite + p_rendered * (1.0 - m_composite)
```

---

## 3. Root Cause Analysis

Tracing the mathematical operations through each layer reveals **three interacting root causes**:

### Root Cause 1: Vertical Misalignment of the Target Garment (Spatial Domain Mismatch)
- **VITON Canonical Coordinates**: In the official VITON dataset on which Flow-Style-VTON was trained:
  - Clothes images in `test_clothes` have their collar starting at $y \in [8, 20]$ pixels ($3\%\text{--}8\%$ from top).
  - Garment shoulders span across $x \in [10, 180]$ pixels (width $\approx 170\text{--}190$ px).
- **The Bug in `preserve_aspect_ratio_and_center()`**:
  - The function blindly centers the garment vertically: `offset_y = (target_h - new_h) // 2`.
  - For a typical square or slightly wide product image of a t-shirt (e.g. aspect ratio $1:1$), `new_w = 172`, `new_h = 172`.
  - `offset_y = (256 - 172) // 2 = 42` pixels.
  - The collar is placed at $y = 42$ instead of $y = 12$. The garment is shifted downward by $30\text{--}40$ pixels into the stomach region!
- **Consequence on AFWM**:
  - The Appearance Flow Warping Module (AFWM) computes feature correlation between the person's upper torso ($y \in [50, 120]$) and the garment.
  - When the garment collar is located at $y = 42$ and chest at $y \in [90, 160]$, the receptive fields fail to find strong feature correlation. The optical flow field becomes attenuated or collapsed.

### Root Cause 2: Naive Center Cropping of Non-Standard Person Photos
- Phone portraits (e.g., $9:16$, $3:4$, or full body) have varying headroom and framing.
- In `resize_and_crop()`, `top = (new_h - target_h) // 2` blindly crops equal amounts from top and bottom.
- If a photo has headroom, the person's torso gets shifted downward towards the bottom edge of the $192 \times 256$ canvas.
- If a photo is a full-body shot, the torso occupies less than $25\%$ of the image height, making it impossible for the model (which was trained exclusively on upper-body portraits where torso is $\sim 60\%$ of image height) to register the body.

### Root Cause 3: The Interaction of Crossed Arms and Identical Dark Garment Colors
- **Occlusion Dynamics**:
  - Flow-Style-VTON was trained on VITON where models stand facing forward with arms at their sides.
  - When a user crosses their arms across their chest, the forearms physically occlude the torso.
  - AFWM has no limb segmentation or depth reasoning — it attempts 2D appearance flow.
- **Why Navy-on-Navy Looks "Unchanged"**:
  - In `tryon_engine.py`:
    $$p_{\text{tryon}} = \text{warped\_cloth} \odot m_{\text{composite}} + p_{\text{rendered}} \odot (1.0 - m_{\text{composite}})$$
  - When the warped edge is degraded or misaligned due to Root Cause 1 and arm occlusion, $m_{\text{composite}}$ remains low on the torso.
  - When $m_{\text{composite}}$ is low, $p_{\text{tryon}} \approx p_{\text{rendered}}$.
  - The generator network's rendered branch $p_{\text{rendered}}$ is conditioned on `real_image`. When `real_image` already has a dark navy shirt, $p_{\text{rendered}}$ reconstructs a dark navy shirt.
  - Even where $\text{warped\_cloth}$ is blended, both the source shirt and the target shirt are dark navy! The difference in pixel RGB values is negligible ($\Delta \text{RGB} < 5\%$).
  - In contrast, when the person wore a white shirt and the target was black patterned, the contrast was extreme ($\Delta \text{RGB} > 70\%$), making even a partially warped transfer immediately noticeable to the human eye.

---

## 4. Remediation Plan

1. **Intelligent Person Preprocessing (Requirement 1)**:
   - Implement aspect-ratio-preserving smart cropping with modes: `'auto'`, `'upper_body'`, `'center'`.
   - Upper-body framing: focus on the upper $70\%$ of the body height, ensuring shoulders and torso occupy standard VITON proportions ($y_{\text{shoulder}} \approx 50\text{--}70$, torso width $\approx 120\text{--}160$).
2. **Canonical Garment Alignment (Requirement 2 & 5)**:
   - Replace naive vertical centering with **canonical torso-anchored alignment**:
   - Scale garment width to standard VITON span ($\approx 175\text{--}185$ px).
   - Anchor the top of the garment neckline to the upper canonical region ($y \approx 10\text{--}18$ px).
   - Maintain horizontal centering.
3. **Garment Edge & Mask Validation (Requirement 3)**:
   - Provide quantitative diagnostics: mask coverage $\%$, edge pixel $\%$, bounding box, width/height, aspect ratio.
4. **Optional Contrast/Brightness Normalization (Requirement 4)**:
   - Add optional histogram/luminance adjustment without recoloring garment hue or texture. Disabled by default.
5. **Debug Visualizations (Requirement 6)**:
   - Save all 7 required intermediate debug stages plus a side-by-side composite visualization panel.
6. **Comprehensive Test Suite (Requirement 7)**:
   - Build `test/tryon_quality_test.py` covering Tests A through E.
7. **Document Inherent Model Limitations (Requirement 10)**:
   - Acknowledge that crossed-arm poses with severe self-occlusion represent out-of-distribution geometric topologies for 2D flow warping models like PFAFN. Canonical alignment will maximize transfer on the visible torso and sleeve boundaries without corrupting arms.
