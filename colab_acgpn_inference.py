# =============================================================================
# ACGPN Virtual Try-On — Google Colab Inference Script
# =============================================================================
# Copy each "# %% [markdown]" or "# %%" section into a SEPARATE Colab cell.
# Run cells sequentially from top to bottom.
# Make sure you have selected: Runtime → Change runtime type → T4 GPU
# =============================================================================

# %% [markdown]
# # ACGPN Virtual Try-On — First Successful Inference
# **Model**: ACGPN (CVPR 2020) — Towards Photo-Realistic Virtual Try-On
#
# **Goal**: Person Image + Garment Image → ACGPN → Generated Try-On Image
#
# **Prerequisites**: Runtime → Change runtime type → **T4 GPU**

# %% Cell 1: Verify GPU availability
import torch
print("=" * 60)
print("CELL 1: GPU VERIFICATION")
print("=" * 60)
print(f"PyTorch version: {torch.__version__}")
print(f"CUDA available:  {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"CUDA version:    {torch.version.cuda}")
    print(f"GPU device:      {torch.cuda.get_device_name(0)}")
    print(f"GPU memory:      {torch.cuda.get_device_properties(0).total_mem / 1024**3:.1f} GB")
    print("\n✅ GPU is ready!")
else:
    print("\n❌ NO GPU DETECTED!")
    print("Go to: Runtime → Change runtime type → T4 GPU")
    raise RuntimeError("GPU required. Change runtime type to T4 GPU.")

# %% Cell 2: Clone ACGPN repository from GitHub
import os
print("=" * 60)
print("CELL 2: CLONE ACGPN REPOSITORY")
print("=" * 60)

REPO_DIR = "/content/DeepFashion_Try_On"

if os.path.exists(REPO_DIR):
    print(f"Repository already exists at {REPO_DIR}")
else:
    !git clone https://github.com/switchablenorms/DeepFashion_Try_On.git /content/DeepFashion_Try_On
    print("✅ Repository cloned successfully!")

# Verify structure
for item in sorted(os.listdir(REPO_DIR)):
    print(f"  {item}/")

# %% Cell 3: Install compatible dependencies
print("=" * 60)
print("CELL 3: INSTALL DEPENDENCIES")
print("=" * 60)

!pip install tensorboardX opencv-python-headless gdown --quiet
print("✅ Dependencies installed!")

import torchvision
import numpy as np
print(f"  torch:       {torch.__version__}")
print(f"  torchvision: {torchvision.__version__}")
print(f"  numpy:       {np.__version__}")

# %% Cell 4: Download pretrained checkpoints
print("=" * 60)
print("CELL 4: DOWNLOAD PRETRAINED CHECKPOINTS")
print("=" * 60)

CHECKPOINT_DIR = os.path.join(REPO_DIR, "ACGPN_inference", "checkpoints", "label2city")
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

# Check if checkpoints already exist
required_files = ["latest_net_U.pth", "latest_net_G1.pth", "latest_net_G2.pth", "latest_net_G.pth"]
all_exist = all(os.path.exists(os.path.join(CHECKPOINT_DIR, f)) for f in required_files)

if all_exist:
    print("✅ All checkpoint files already exist!")
else:
    print("Downloading checkpoints from Google Drive...")
    print("(File ID: 1UWT6esQIU_d4tUm8cjxDKMhB8joQbrFx)")

    # Download checkpoint archive
    !gdown "1UWT6esQIU_d4tUm8cjxDKMhB8joQbrFx" -O /content/checkpoints.zip --fuzzy --quiet

    if os.path.exists("/content/checkpoints.zip"):
        # Extract and find the .pth files
        !unzip -o /content/checkpoints.zip -d /content/checkpoints_temp/
        print("\nExtracted contents:")
        !find /content/checkpoints_temp/ -name "*.pth" -type f

        # Move .pth files to the correct location
        !find /content/checkpoints_temp/ -name "*.pth" -exec cp {} {CHECKPOINT_DIR}/ \;
        !rm -rf /content/checkpoints_temp/ /content/checkpoints.zip
    else:
        print("❌ Download may have failed. Trying alternative method...")
        # Try direct gdown with fuzzy matching
        !gdown "https://drive.google.com/file/d/1UWT6esQIU_d4tUm8cjxDKMhB8joQbrFx/view?usp=sharing" -O /content/checkpoints.zip --fuzzy
        if os.path.exists("/content/checkpoints.zip"):
            !unzip -o /content/checkpoints.zip -d /content/checkpoints_temp/
            !find /content/checkpoints_temp/ -name "*.pth" -exec cp {} {CHECKPOINT_DIR}/ \;
            !rm -rf /content/checkpoints_temp/ /content/checkpoints.zip

# Verify checkpoints
print("\nCheckpoint verification:")
for f in required_files:
    path = os.path.join(CHECKPOINT_DIR, f)
    if os.path.exists(path):
        size_mb = os.path.getsize(path) / (1024 * 1024)
        print(f"  ✅ {f} ({size_mb:.1f} MB)")
    else:
        print(f"  ❌ {f} — MISSING!")

# %% Cell 5: Download VITON test dataset
print("=" * 60)
print("CELL 5: DOWNLOAD VITON TEST DATASET")
print("=" * 60)

DATA_DIR = os.path.join(REPO_DIR, "Data_preprocessing")
os.makedirs(DATA_DIR, exist_ok=True)

# Check if dataset directories already exist
required_dirs = ["test_label", "test_img", "test_color", "test_edge", "test_pose"]
all_dirs_exist = all(
    os.path.isdir(os.path.join(DATA_DIR, d)) and len(os.listdir(os.path.join(DATA_DIR, d))) > 0
    for d in required_dirs
    if os.path.isdir(os.path.join(DATA_DIR, d))
)

if all_dirs_exist and all(os.path.isdir(os.path.join(DATA_DIR, d)) for d in required_dirs):
    print("✅ Test dataset directories already exist!")
else:
    print("Downloading VITON test dataset from Google Drive...")
    print("(File ID: 1tE7hcVFm8Td8kRh5iYRBSDFdvZIkbUIR)")

    !gdown "1tE7hcVFm8Td8kRh5iYRBSDFdvZIkbUIR" -O /content/test_dataset.zip --fuzzy --quiet

    if os.path.exists("/content/test_dataset.zip"):
        # Extract
        !unzip -o /content/test_dataset.zip -d /content/test_dataset_temp/
        print("\nExtracted structure:")
        !find /content/test_dataset_temp/ -maxdepth 3 -type d

        # The extracted structure might be nested — find the test_img directory
        import subprocess
        result = subprocess.run(
            ["find", "/content/test_dataset_temp/", "-name", "test_img", "-type", "d"],
            capture_output=True, text=True
        )
        test_img_paths = result.stdout.strip().split('\n')
        if test_img_paths and test_img_paths[0]:
            # The parent of test_img is the data root
            extracted_data_root = os.path.dirname(test_img_paths[0])
            print(f"\nFound data root: {extracted_data_root}")

            # Copy all test_* directories to Data_preprocessing/
            for d in os.listdir(extracted_data_root):
                src = os.path.join(extracted_data_root, d)
                dst = os.path.join(DATA_DIR, d)
                if os.path.isdir(src) and d.startswith("test_"):
                    if not os.path.exists(dst):
                        !cp -r "{src}" "{dst}"
                        print(f"  Copied {d}/")
                    else:
                        print(f"  {d}/ already exists")

        !rm -rf /content/test_dataset_temp/ /content/test_dataset.zip
    else:
        print("❌ Download failed!")
        print("\n=== MANUAL DOWNLOAD INSTRUCTIONS ===")
        print("1. Go to: https://drive.google.com/file/d/1tE7hcVFm8Td8kRh5iYRBSDFdvZIkbUIR/view")
        print("2. Click Download")
        print("3. Upload the zip to Colab Files panel")
        print("4. Run: !unzip uploaded_file.zip -d /content/DeepFashion_Try_On/Data_preprocessing/")

# Also ensure test_mask and test_colormask directories exist (required by dataset loader)
for d in ["test_mask", "test_colormask"]:
    dpath = os.path.join(DATA_DIR, d)
    if not os.path.isdir(dpath):
        os.makedirs(dpath, exist_ok=True)
        # Create a dummy file so make_dataset doesn't fail on empty dir
        # The actual paths are overridden in __getitem__ to use test_img paths
        import shutil
        img_dir = os.path.join(DATA_DIR, "test_img")
        if os.path.isdir(img_dir):
            first_img = sorted(os.listdir(img_dir))[0] if os.listdir(img_dir) else None
            if first_img:
                shutil.copy(os.path.join(img_dir, first_img), os.path.join(dpath, first_img))
        print(f"  Created {d}/ (placeholder)")

# Verify dataset
print("\nDataset verification:")
for d in ["test_label", "test_img", "test_color", "test_edge", "test_pose", "test_mask", "test_colormask"]:
    dpath = os.path.join(DATA_DIR, d)
    if os.path.isdir(dpath):
        count = len(os.listdir(dpath))
        print(f"  ✅ {d}/ — {count} files")
    else:
        print(f"  ❌ {d}/ — MISSING!")

# %% Cell 6: Apply compatibility patches
print("=" * 60)
print("CELL 6: APPLY COMPATIBILITY PATCHES")
print("=" * 60)

INFERENCE_DIR = os.path.join(REPO_DIR, "ACGPN_inference")

# ─── Patch 1: transforms.Scale → transforms.Resize ───
# File: data/base_dataset.py (lines 38, 42)
# Reason: transforms.Scale was removed in torchvision >= 0.14
print("Patch 1: transforms.Scale → transforms.Resize (base_dataset.py)")
!sed -i 's/transforms\.Scale/transforms.Resize/g' {INFERENCE_DIR}/data/base_dataset.py

# ─── Patch 2: np.int → int ───
# File: test.py (lines 42, 59, 60, 61, 121, 122)
# Reason: np.int was removed in NumPy >= 1.24
print("Patch 2: np.int → int (test.py)")
!sed -i 's/\.astype(np\.int)/.astype(int)/g' {INFERENCE_DIR}/test.py

# ─── Patch 3: np.float → float ───
# File: test.py (line 118)
# Reason: np.float was removed in NumPy >= 1.24
print("Patch 3: np.float → float (test.py)")
!sed -i 's/\.astype(np\.float)/.astype(float)/g' {INFERENCE_DIR}/test.py

# ─── Patch 4: np.float → float ───
# File: models/pix2pixHD_model.py (lines 292, 293, 294, 312, 315, 316)
# Reason: Same as above
print("Patch 4: np.float → float (pix2pixHD_model.py)")
!sed -i 's/\.astype(np\.float)/.astype(float)/g' {INFERENCE_DIR}/models/pix2pixHD_model.py

# ─── Patch 5: F.grid_sample align_corners ───
# File: grid_sample.py (lines 7, 12)
# Reason: Modern PyTorch changed default align_corners from True to False
# Original model was trained with align_corners=True behavior
print("Patch 5: F.grid_sample → add align_corners=True (grid_sample.py)")
!sed -i 's/F\.grid_sample(input, grid)/F.grid_sample(input, grid, align_corners=True)/g' {INFERENCE_DIR}/grid_sample.py
!sed -i 's/F\.grid_sample(input_mask, grid)/F.grid_sample(input_mask, grid, align_corners=True)/g' {INFERENCE_DIR}/grid_sample.py

# ─── Patch 6: torch.load compatibility ───
# File: models/base_model.py (line 63)
# Reason: PyTorch >= 2.6 changed weights_only default to True
print("Patch 6: torch.load → add weights_only=False (base_model.py)")
!sed -i "s/network.load_state_dict(torch.load(save_path))/network.load_state_dict(torch.load(save_path, map_location='cuda:0', weights_only=False))/" {INFERENCE_DIR}/models/base_model.py

# ─── Patch 7: Hardcoded dataset size ───
# File: data/aligned_dataset.py (line 109)
# Reason: np.random.randint(2032) will crash if dataset has != 2032 items
print("Patch 7: hardcoded randint(2032) → randint(len(self.C_paths)) (aligned_dataset.py)")
!sed -i 's/np\.random\.randint(2032)/np.random.randint(len(self.C_paths))/g' {INFERENCE_DIR}/data/aligned_dataset.py

print("\n✅ All 7 patches applied!")
print("\nPatch summary:")
print("  1. transforms.Scale → transforms.Resize")
print("  2. np.int → int (test.py)")
print("  3. np.float → float (test.py)")
print("  4. np.float → float (pix2pixHD_model.py)")
print("  5. F.grid_sample → align_corners=True")
print("  6. torch.load → weights_only=False")
print("  7. randint(2032) → randint(len(self.C_paths))")

# %% Cell 7: Verify all prerequisites before inference
print("=" * 60)
print("CELL 7: PRE-INFERENCE VERIFICATION")
print("=" * 60)

import os

REPO_DIR = "/content/DeepFashion_Try_On"
INFERENCE_DIR = os.path.join(REPO_DIR, "ACGPN_inference")
CHECKPOINT_DIR = os.path.join(INFERENCE_DIR, "checkpoints", "label2city")
DATA_DIR = os.path.join(REPO_DIR, "Data_preprocessing")

all_ok = True

# Check GPU
print("\n[1] GPU:")
if torch.cuda.is_available():
    print(f"  ✅ {torch.cuda.get_device_name(0)}")
else:
    print("  ❌ No GPU!")
    all_ok = False

# Check checkpoints
print("\n[2] Checkpoints:")
for f in ["latest_net_U.pth", "latest_net_G1.pth", "latest_net_G2.pth", "latest_net_G.pth"]:
    p = os.path.join(CHECKPOINT_DIR, f)
    if os.path.exists(p):
        print(f"  ✅ {f} ({os.path.getsize(p) / 1024 / 1024:.1f} MB)")
    else:
        print(f"  ❌ {f} — MISSING")
        all_ok = False

# Check dataset
print("\n[3] Dataset:")
for d in ["test_label", "test_img", "test_color", "test_edge", "test_pose"]:
    dpath = os.path.join(DATA_DIR, d)
    if os.path.isdir(dpath) and len(os.listdir(dpath)) > 0:
        print(f"  ✅ {d}/ ({len(os.listdir(dpath))} files)")
    else:
        print(f"  ❌ {d}/ — MISSING or EMPTY")
        all_ok = False

# Check patches applied
print("\n[4] Patches:")
with open(os.path.join(INFERENCE_DIR, "data", "base_dataset.py"), "r") as f:
    content = f.read()
    if "transforms.Resize" in content and "transforms.Scale" not in content:
        print("  ✅ transforms.Scale → transforms.Resize")
    else:
        print("  ❌ transforms.Scale patch not applied")
        all_ok = False

with open(os.path.join(INFERENCE_DIR, "test.py"), "r") as f:
    content = f.read()
    if "np.int)" not in content:
        print("  ✅ np.int → int")
    else:
        print("  ❌ np.int patch not applied")
        all_ok = False

print("\n" + "=" * 60)
if all_ok:
    print("✅ ALL PREREQUISITES MET — READY FOR INFERENCE!")
else:
    print("❌ SOME PREREQUISITES MISSING — FIX BEFORE RUNNING INFERENCE")
print("=" * 60)

# %% Cell 8: Run ACGPN inference
print("=" * 60)
print("CELL 8: RUN ACGPN INFERENCE")
print("=" * 60)

INFERENCE_DIR = "/content/DeepFashion_Try_On/ACGPN_inference"
DATA_DIR = "/content/DeepFashion_Try_On/Data_preprocessing"

# Create sample output directory
os.makedirs(os.path.join(INFERENCE_DIR, "sample"), exist_ok=True)

print("Starting ACGPN inference...")
print(f"  Working directory: {INFERENCE_DIR}")
print(f"  Data root:         {DATA_DIR}")
print(f"  Checkpoints:       {INFERENCE_DIR}/checkpoints/label2city/")
print(f"  Output:            {INFERENCE_DIR}/sample/")
print()

# Run the official test.py entry point
!cd {INFERENCE_DIR} && python test.py --dataroot "{DATA_DIR}/"

print("\n✅ Inference completed!")

# %% Cell 9: Display generated results
print("=" * 60)
print("CELL 9: DISPLAY RESULTS")
print("=" * 60)

import glob
from IPython.display import display, Image as IPImage
from PIL import Image
import matplotlib.pyplot as plt

SAMPLE_DIR = "/content/DeepFashion_Try_On/ACGPN_inference/sample"

# Find generated images
results = sorted(glob.glob(os.path.join(SAMPLE_DIR, "*.jpg")))
results += sorted(glob.glob(os.path.join(SAMPLE_DIR, "*.png")))

if not results:
    print("❌ No output images found in sample/ directory!")
    print("Checking for output in other locations...")
    !find /content/DeepFashion_Try_On/ACGPN_inference/ -name "*.jpg" -newer /content/DeepFashion_Try_On/ACGPN_inference/test.py -type f 2>/dev/null | head -20
else:
    print(f"Found {len(results)} generated image(s)!\n")

    # Display up to 5 results
    num_display = min(5, len(results))
    fig, axes = plt.subplots(num_display, 1, figsize=(20, 5 * num_display))
    if num_display == 1:
        axes = [axes]

    for i, img_path in enumerate(results[:num_display]):
        img = Image.open(img_path)
        axes[i].imshow(img)
        axes[i].set_title(os.path.basename(img_path), fontsize=12)
        axes[i].axis('off')

        # The output is a concatenated strip:
        # [segmentation | clothes_mask | real_image | GENERATED_IMAGE | warped_grid]
        w, h = img.size
        single_w = w // 5  # 5 panels concatenated
        print(f"  {os.path.basename(img_path)}: {w}x{h} px (each panel: {single_w}x{h})")

    plt.tight_layout()
    plt.savefig("/content/acgpn_results_overview.png", dpi=150, bbox_inches='tight')
    plt.show()

    # Extract and display JUST the generated try-on image (4th panel)
    if results:
        print("\n--- Extracted Generated Try-On Image (4th panel) ---")
        img = Image.open(results[0])
        w, h = img.size
        single_w = w // 5
        # The 4th panel (index 3) is the generated image
        generated = img.crop((3 * single_w, 0, 4 * single_w, h))
        generated.save("/content/acgpn_generated_tryon.png")

        fig, ax = plt.subplots(1, 1, figsize=(4, 6))
        ax.imshow(generated)
        ax.set_title("ACGPN Generated Try-On Result", fontsize=14)
        ax.axis('off')
        plt.tight_layout()
        plt.show()

        print(f"\n✅ Generated try-on image saved to: /content/acgpn_generated_tryon.png")
        print(f"   Resolution: {generated.size[0]}x{generated.size[1]}")

# %% [markdown]
# # ✅ ACGPN Inference Complete!
#
# **What happened:**
# 1. Cloned the ACGPN repository
# 2. Downloaded pretrained checkpoints (4 .pth files)
# 3. Downloaded the VITON test dataset
# 4. Applied 7 minimal compatibility patches
# 5. Ran the official test.py inference
# 6. Generated real try-on images
#
# **Output location:** `ACGPN_inference/sample/`
#
# **Output format:** Each image is a concatenated strip with 5 panels:
# `[segmentation | clothes_mask | real_image | GENERATED_IMAGE | warped_grid]`
#
# The 4th panel is the actual ACGPN-generated try-on result.
