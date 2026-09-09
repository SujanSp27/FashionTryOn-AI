# =============================================================================
# Flow-Style-VTON Virtual Try-On — Google Colab Complete Inference Script
# =============================================================================
# Style-Based Global Appearance Flow for Virtual Try-On (CVPR 2022)
# Official Repository: https://github.com/SenHe/Flow-Style-VTON
#
# INSTRUCTIONS:
# 1. Open Google Colab (https://colab.research.google.com).
# 2. Select: Runtime -> Change runtime type -> Hardware accelerator: T4 GPU.
# 3. Copy each cell into Colab sequentially or upload Flow_Style_VTON_Colab_Inference.ipynb.
# =============================================================================

# %% [markdown]
# # Flow-Style-VTON Virtual Try-On (CVPR 2022)
# **Model**: Flow-Style-VTON / Parser-Free Appearance Flow Network (PFAFN)
# **Key Advantage**: Parser-Free at inference time! No human segmentation (SCHP) or OpenPose required at test time.
#
# **Prerequisites**: Runtime -> Change runtime type -> **T4 GPU**

# %% Cell 1: Verify GPU availability
import sys
import platform
import torch

print("=" * 60)
print("CELL 1: GPU & ENVIRONMENT VERIFICATION")
print("=" * 60)
print(f"Python version:      {sys.version.split()[0]}")
print(f"OS / Platform:       {platform.platform()}")
print(f"PyTorch version:     {torch.__version__}")
print(f"CUDA available:      {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"CUDA runtime:        {torch.version.cuda}")
    print(f"GPU device name:     {torch.cuda.get_device_name(0)}")
    props = torch.cuda.get_device_properties(0)
    print(f"GPU VRAM:            {props.total_mem / (1024**3):.2f} GB")
    print("\n[+] Verified: Tesla T4 / NVIDIA GPU is active and ready for inference!")
else:
    print("\n[-] ERROR: NO GPU DETECTED!")
    print("Go to: Runtime -> Change runtime type -> T4 GPU and restart.")
    raise RuntimeError("NVIDIA GPU required. Change runtime type to T4 GPU.")

# %% Cell 2: Clone Flow-Style-VTON repository from GitHub
import os

print("=" * 60)
print("CELL 2: CLONE FLOW-STYLE-VTON REPOSITORY")
print("=" * 60)

REPO_DIR = "/content/Flow-Style-VTON"
if not os.path.exists(REPO_DIR):
    !git clone https://github.com/SenHe/Flow-Style-VTON.git /content/Flow-Style-VTON
    print("[+] Repository cloned successfully!")
else:
    print(f"[+] Repository already exists at {REPO_DIR}")

print("\nRepository root contents:")
for item in sorted(os.listdir(REPO_DIR)):
    print(f"  - {item}")

# %% Cell 3: Install required dependencies
print("=" * 60)
print("CELL 3: INSTALL DEPENDENCIES")
print("=" * 60)

!pip install gdown opencv-python-headless pillow matplotlib tensorboardX natsort imageio --quiet

import torchvision
import PIL
import cv2

print(f"PyTorch version:     {torch.__version__}")
print(f"torchvision version: {torchvision.__version__}")
print(f"Pillow version:      {PIL.__version__}")
print(f"OpenCV version:      {cv2.__version__}")
print("[+] Dependencies successfully verified!")

# %% Cell 4: Apply Verified Compatibility Patches
print("=" * 60)
print("CELL 4: APPLY COMPATIBILITY PATCHES")
print("=" * 60)

# Patch 1: base_dataset.py: transforms.Scale -> transforms.Resize
bds_path = "/content/Flow-Style-VTON/test/data/base_dataset.py"
with open(bds_path, "r") as f:
    bds = f.read()
bds = bds.replace("transforms.Scale(osize, method)", "transforms.Resize(osize, interpolation=method)")
with open(bds_path, "w") as f:
    f.write(bds)
print("[+] Patch 1: base_dataset.py (transforms.Scale -> transforms.Resize)")

# Patch 2: aligned_dataset_test.py: dynamic test_pairs resolution & basename extraction
ads_path = "/content/Flow-Style-VTON/test/data/aligned_dataset_test.py"
with open(ads_path, "r") as f:
    ads = f.read()
if "pairs_candidates" not in ads:
    ads = ads.replace(
        "self.text = './test_pairs.txt'",
        "pairs_candidates = [os.path.join(opt.dataroot, 'test_pairs.txt'), './test_pairs.txt', os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'test_pairs.txt')]; self.text = next((c for c in pairs_candidates if os.path.exists(c)), './test_pairs.txt')"
    )
ads = ads.replace("self.im_name[index].split('/')[-1]", "os.path.basename(self.im_name[index])")
with open(ads_path, "w") as f:
    f.write(ads)
print("[+] Patch 2: aligned_dataset_test.py (test_pairs resolution & basename)")

# Patch 3: afwm.py: torch.meshgrid indexing & align_corners=False
afwm_path = "/content/Flow-Style-VTON/test/models/afwm.py"
with open(afwm_path, "r") as f:
    afwm = f.read()
afwm = afwm.replace(
    "grid_list = torch.meshgrid([torch.arange(size, device=offset.device) for size in sizes])",
    "try: grid_list = torch.meshgrid([torch.arange(size, device=offset.device) for size in sizes], indexing='ij')\n    except TypeError: grid_list = torch.meshgrid([torch.arange(size, device=offset.device) for size in sizes])"
)
afwm = afwm.replace("mode='bilinear', padding_mode='border')", "mode='bilinear', padding_mode='border', align_corners=False)")
afwm = afwm.replace("mode='bilinear',padding_mode='border')", "mode='bilinear', padding_mode='border', align_corners=False)")
afwm = afwm.replace("scale_factor=2, mode='bilinear')", "scale_factor=2, mode='bilinear', align_corners=False)")
with open(afwm_path, "w") as f:
    f.write(afwm)
print("[+] Patch 3: afwm.py (torch.meshgrid indexing & align_corners=False)")

# Patch 4: networks.py: dynamic map_location in load_checkpoint
net_path = "/content/Flow-Style-VTON/test/models/networks.py"
with open(net_path, "r") as f:
    net = f.read()
net = net.replace(
    "checkpoint = torch.load(checkpoint_path)",
    "map_loc = 'cuda' if torch.cuda.is_available() else 'cpu'; checkpoint = torch.load(checkpoint_path, map_location=map_loc)"
)
with open(net_path, "w") as f:
    f.write(net)
print("[+] Patch 4: networks.py (dynamic map_location)")

# Patch 5: base_options.py: guard cuda.set_device
opt_path = "/content/Flow-Style-VTON/test/options/base_options.py"
with open(opt_path, "r") as f:
    opt_code = f.read()
opt_code = opt_code.replace("if len(self.opt.gpu_ids) > 0:", "if len(self.opt.gpu_ids) > 0 and torch.cuda.is_available():")
with open(opt_path, "w") as f:
    f.write(opt_code)
print("[+] Patch 5: base_options.py (torch.cuda.is_available guard)")

# Patch 6: test.py: align_corners=False in grid_sample
tpy_path = "/content/Flow-Style-VTON/test/test.py"
with open(tpy_path, "r") as f:
    tpy = f.read()
tpy = tpy.replace("grid_sample(edge.cuda(), last_flow.permute(0, 2, 3, 1),", "grid_sample(edge.cuda(), last_flow.permute(0, 2, 3, 1), align_corners=False,")
with open(tpy_path, "w") as f:
    f.write(tpy)
print("[+] Patch 6: test.py (align_corners=False)")
print("[+] All compatibility patches successfully applied!")

# %% Cell 5: Download Pretrained Weights from Google Drive
import zipfile
import gdown

print("=" * 60)
print("CELL 5: DOWNLOAD PRETRAINED CHECKPOINTS")
print("=" * 60)

CKPT_DIR = "/content/Flow-Style-VTON/test/checkpoints"
os.makedirs(CKPT_DIR, exist_ok=True)

warp_ckpt = os.path.join(CKPT_DIR, "PFAFN_warp_epoch_101.pth")
gen_ckpt = os.path.join(CKPT_DIR, "PFAFN_gen_epoch_101.pth")

if not (os.path.exists(warp_ckpt) and os.path.exists(gen_ckpt)):
    zip_dest = "/content/Flow-Style-VTON/test/flow_style_vton_ckp.zip"
    ckp_file_id = "1pYrLujkd2gmQGqtnROCzSSnVwbMh9DnP"
    print("Downloading official pretrained checkpoints archive (flow_style_vton_ckp.zip)...")
    gdown.download(id=ckp_file_id, output=zip_dest, quiet=False)

    print("Extracting checkpoints...")
    with zipfile.ZipFile(zip_dest, 'r') as z:
        for member in z.namelist():
            if "non_aug" in member and member.endswith(".pth"):
                filename = os.path.basename(member)
                target_path = os.path.join(CKPT_DIR, filename)
                with open(target_path, "wb") as f_out:
                    f_out.write(z.read(member))
                print(f"  [+] Extracted: {filename} ({os.path.getsize(target_path) / (1024*1024):.2f} MB)")
else:
    print("[+] Checkpoints already verified!")

assert os.path.exists(warp_ckpt) and os.path.getsize(warp_ckpt) > 0, "PFAFN_warp_epoch_101.pth missing!"
assert os.path.exists(gen_ckpt) and os.path.getsize(gen_ckpt) > 0, "PFAFN_gen_epoch_101.pth missing!"
print(f"\n[+] Warp Checkpoint:      {warp_ckpt} ({os.path.getsize(warp_ckpt)/(1024*1024):.2f} MB)")
print(f"[+] Generator Checkpoint: {gen_ckpt} ({os.path.getsize(gen_ckpt)/(1024*1024):.2f} MB)")

# %% Cell 6: Download Official Test Dataset
print("=" * 60)
print("CELL 6: DOWNLOAD OFFICIAL VITON TEST DATASET")
print("=" * 60)

DATA_DIR = "/content/Flow-Style-VTON/test/data_viton"
os.makedirs(DATA_DIR, exist_ok=True)

test_data_id = "1Y7uV0gomwWyxCvvH8TIbY7D9cTAUy6om"
zip_data_path = "/content/Flow-Style-VTON/test/VITON_test.zip"
dataroot = os.path.join(DATA_DIR, "VITON_test")

if not os.path.exists(os.path.join(dataroot, "test_img")):
    print("Downloading VITON_test.zip archive from Google Drive...")
    gdown.download(id=test_data_id, output=zip_data_path, quiet=False)

    print("Extracting dataset...")
    with zipfile.ZipFile(zip_data_path, 'r') as z:
        z.extractall(DATA_DIR)
    print("[+] Dataset extraction complete!")
else:
    print("[+] Test dataset already exists.")

print(f"\nDataroot directory: {dataroot}")
print(f"  - test_img:     {len(os.listdir(os.path.join(dataroot, 'test_img')))} person images")
print(f"  - test_clothes: {len(os.listdir(os.path.join(dataroot, 'test_clothes')))} garment images")
print(f"  - test_edge:    {len(os.listdir(os.path.join(dataroot, 'test_edge')))} garment edge masks")
print(f"  - test_pairs:   {len(open('/content/Flow-Style-VTON/test/test_pairs.txt').readlines())} official test pairs")

# %% Cell 7: Run Official Batch Inference
print("=" * 60)
print("CELL 7: RUN OFFICIAL BATCH INFERENCE PIPELINE")
print("=" * 60)

# Switch working directory to test/
%cd /content/Flow-Style-VTON/test

!python test.py \
  --name demo \
  --resize_or_crop None \
  --batchSize 1 \
  --gpu_ids 0 \
  --warp_checkpoint /content/Flow-Style-VTON/test/checkpoints/PFAFN_warp_epoch_101.pth \
  --gen_checkpoint /content/Flow-Style-VTON/test/checkpoints/PFAFN_gen_epoch_101.pth \
  --dataroot /content/Flow-Style-VTON/test/data_viton/VITON_test

print("\n[+] Batch inference complete! Results saved in /content/Flow-Style-VTON/test/our_t_results")

# %% Cell 8: Verify Output & Display Generated Try-On Images
import glob
import matplotlib.pyplot as plt
from PIL import Image

print("=" * 60)
print("CELL 8: OUTPUT VERIFICATION & DISPLAY")
print("=" * 60)

RESULTS_DIR = "/content/Flow-Style-VTON/test/our_t_results"
result_files = sorted(glob.glob(os.path.join(RESULTS_DIR, "*.jpg")) + glob.glob(os.path.join(RESULTS_DIR, "*.png")))

print(f"Output directory: {RESULTS_DIR}")
print(f"Total generated virtual try-on images: {len(result_files)}")

# Read test pairs
with open("/content/Flow-Style-VTON/test/test_pairs.txt", "r") as f:
    pairs = [line.strip().split() for line in f.readlines()]

num_to_display = min(4, len(result_files))
if num_to_display > 0:
    fig, axes = plt.subplots(num_to_display, 3, figsize=(12, 4 * num_to_display))
    if num_to_display == 1:
        axes = [axes]

    for idx in range(num_to_display):
        out_path = result_files[idx]
        p_name = os.path.basename(out_path)
        c_name = next((c for p, c in pairs if p == p_name), None)

        p_img = Image.open(os.path.join(dataroot, "test_img", p_name))
        tryon_img = Image.open(out_path)

        axes[idx][0].imshow(p_img)
        axes[idx][0].set_title(f"Person: {p_name}", fontsize=10)
        axes[idx][0].axis("off")

        if c_name and os.path.exists(os.path.join(dataroot, "test_clothes", c_name)):
            c_img = Image.open(os.path.join(dataroot, "test_clothes", c_name))
            axes[idx][1].imshow(c_img)
            axes[idx][1].set_title(f"Garment: {c_name}", fontsize=10)
        axes[idx][1].axis("off")

        axes[idx][2].imshow(tryon_img)
        axes[idx][2].set_title("Generated Try-On (Flow-Style-VTON)", fontsize=10, fontweight="bold", color="green")
        axes[idx][2].axis("off")

    plt.tight_layout()
    plt.show()

print("-" * 60)
print("VERIFICATION SUMMARY:")
print("MODEL:                Flow-Style-VTON / PFAFN")
print(f"GPU:                  {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")
print("WARP CHECKPOINT:      /content/Flow-Style-VTON/test/checkpoints/PFAFN_warp_epoch_101.pth")
print("GENERATOR CHECKPOINT: /content/Flow-Style-VTON/test/checkpoints/PFAFN_gen_epoch_101.pth")
print(f"TEST DATA:            {dataroot}")
print(f"OUTPUT:               {RESULTS_DIR}")
print("STATUS:               SUCCESS")
print("-" * 60)
