# Flow-Style-VTON Compatibility Patches & Audit Log

This document records every source code modification made to the official [SenHe/Flow-Style-VTON](https://github.com/SenHe/Flow-Style-VTON) repository to ensure seamless compatibility with modern Google Colab environments (Ubuntu 22.04, Python 3.10+, PyTorch 2.x / CUDA 12.x on Tesla T4 GPU) as well as local verification environments.

---

## Patch 1: Deprecated transforms.Scale in PyTorch Vision
- **File modified:** Flow-Style-VTON-main/test/data/base_dataset.py
- **Original issue:** In get_transform_resize() and get_transform(), the codebase called transforms.Scale(osize, method). transforms.Scale was deprecated and removed in torchvision $\ge$ 0.5.0, resulting in AttributeError: module \'torchvision.transforms\' has no attribute \'Scale\'.
- **Exact change made:** Replaced all calls to transforms.Scale(osize, method) with transforms.Resize(osize, interpolation=method).
- **Reason for change:** transforms.Resize is the official torchvision replacement and provides identical spatial transformation behavior.

---

## Patch 2: Cross-Platform File Name Extraction in Dataset
- **File modified:** Flow-Style-VTON-main/test/data/aligned_dataset_test.py
- **Original issue:** Line 64 originally used 'p_name': self.im_name[index].split('/')[-1]. On operating systems or paths using standard filesystem separators (e.g., Windows backslashes \\), split('/')[-1] fails to extract the basename, leaving the full absolute path and causing downstream saving failures in utils.save_image.
- **Exact change made:** Replaced with os.path.basename(self.im_name[index]).
- **Reason for change:** os.path.basename() is standard, robust, and platform-independent across Linux, macOS, and Windows.

---

## Patch 3: Flexible test_pairs.txt Resolution
- **File modified:** Flow-Style-VTON-main/test/data/aligned_dataset_test.py
- **Original issue:** Line 14 hardcoded self.text = './test_pairs.txt'. If the script was launched from an arbitrary directory or if the dataset directory provided its own test_pairs.txt, a FileNotFoundError was raised.
- **Exact change made:** Implemented candidate searching order:
  1. os.path.join(opt.dataroot, 'test_pairs.txt')
  2. ./test_pairs.txt
  3. os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'test_pairs.txt')
- **Reason for change:** Allows test.py to seamlessly find test pairs whether pointing to a standalone test data root or running from the test folder.

---

## Patch 4: Safe Checkpoint Deserialization on Modern PyTorch
- **File modified:** Flow-Style-VTON-main/test/models/networks.py
- **Original issue:** load_checkpoint() called torch.load(checkpoint_path) without map_location. When running on machines with different GPU configurations or on CPU, this raises CUDA device mapping errors. Furthermore, in PyTorch 2.6+, the default weights_only=True can trigger unpickling exceptions.
- **Exact change made:** Added dynamic device mapping:
  `python
  map_loc = 'cuda' if torch.cuda.is_available() else 'cpu'
  try:
      checkpoint = torch.load(checkpoint_path, map_location=map_loc, weights_only=False)
  except TypeError:
      checkpoint = torch.load(checkpoint_path, map_location=map_loc)
  `
- **Reason for change:** Ensures model checkpoints deserialize safely regardless of whether running on CUDA or CPU, and across legacy and modern PyTorch releases.

---

## Patch 5: torch.meshgrid Indexing Compatibility
- **File modified:** Flow-Style-VTON-main/test/models/afwm.py
- **Original issue:** In apply_offset(), torch.meshgrid(...) was called without the indexing parameter. PyTorch 1.10+ emits UserWarning: torch.meshgrid: in an upcoming release, it will be required to pass the indexing argument.
- **Exact change made:** 
  `python
  sizes = list(offset.size()[2:])
  try:
      grid_list = torch.meshgrid([torch.arange(size, device=offset.device) for size in sizes], indexing='ij')
  except TypeError:
      grid_list = torch.meshgrid([torch.arange(size, device=offset.device) for size in sizes])
  `
- **Reason for change:** Eliminates runtime warnings and guarantees forward compatibility with PyTorch 2.x while preserving Python/PyTorch 1.x compatibility.

---

## Patch 6: Explicit lign_corners=False in Grid Sample & Interpolation
- **File modified:** Flow-Style-VTON-main/test/models/afwm.py and Flow-Style-VTON-main/test/test.py
- **Original issue:** F.grid_sample() and F.interpolate() calls in fwm.py and test.py omitted lign_corners, which triggers continuous UserWarning: Default grid_sample and affine_grid behavior has changed to align_corners=False since 1.3.0. for every batch.
- **Exact change made:** Explicitly passed lign_corners=False across all F.grid_sample() and F.interpolate() invocations.
- **Reason for change:** Preserves the exact mathematical behavior of Flow-Style-VTON while removing spammy warnings.

---

## Patch 7: CUDA Device Initialization Safety
- **File modified:** Flow-Style-VTON-main/test/options/base_options.py
- **Original issue:** torch.cuda.set_device(self.opt.gpu_ids[0]) was called unconditionally whenever gpu_ids was populated, crashing on systems where CUDA runtime is initializing or when testing in CPU mode.
- **Exact change made:** Added guard: if len(self.opt.gpu_ids) > 0 and torch.cuda.is_available():.
- **Reason for change:** Prevents startup crashes when falling back to CPU or before GPU detection.

---

## Patch 8: Multiprocessing Spawn Safety (if __name__ == '__main__':)
- **File modified:** Flow-Style-VTON-main/test/test.py
- **Original issue:** The official test.py executed procedural code in module top-level scope without a main() guard. On Windows or with Python multiprocessing environments utilizing spawn, workers crash with RuntimeError: An attempt has been made to start a new process before the current process has finished its bootstrapping phase.
- **Exact change made:** Encapsulated execution in def main(): and added if __name__ == '__main__': main().
- **Reason for change:** Standard Python multiprocessing requirement; prevents bootstrap crashes in DataLoader worker processes.

---

## Patch 9: Device-Agnostic Model & Tensor Transfers
- **File modified:** Flow-Style-VTON-main/test/test.py
- **Original issue:** Hardcoded .cuda() calls on warp_model, gen_model, 
eal_image, clothes, and edge prevented clean fallback and raised errors if GPU was unavailable.
- **Exact change made:** Resolved active device cleanly:
  `python
  device = torch.device(f'cuda:{opt.gpu_ids[0]}' if (torch.cuda.is_available() and len(opt.gpu_ids) > 0 and opt.gpu_ids[0] >= 0) else 'cpu')
  `
  and converted calls to .to(device).
- **Reason for change:** Allows testing on T4 GPU (--gpu_ids 0) while also supporting CPU debugging (--gpu_ids -1) without modifying code.

---

## Patch 10: Robust Image Saving Across Torchvision Versions
- **File modified:** Flow-Style-VTON-main/test/test.py
- **Original issue:** torchvision.utils.save_image changed its parameter from 
ange=(-1, 1) (torchvision $\le$ 0.9) to alue_range=(-1, 1) (torchvision $\ge$ 0.10). Passing the wrong parameter raises a fatal TypeError.
- **Exact change made:**
  `python
  try:
      utils.save_image(p_tryon, save_path, nrow=1, normalize=True, value_range=(-1, 1))
  except TypeError:
      utils.save_image(p_tryon, save_path, nrow=1, normalize=True, range=(-1, 1))
  `
- **Reason for change:** Ensures test.py saves images without error across both legacy and modern torchvision versions.

---

## Patch 11: Python 3.12 Regex Escape Syntax
- **File modified:** Flow-Style-VTON-main/test/util/flow_util.py
- **Original issue:** 
e.split('(\d+)', text) triggered SyntaxWarning: invalid escape sequence '\d' in modern Python.
- **Exact change made:** Changed to raw string literal 
e.split(r'(\d+)', text).
- **Reason for change:** Conforms to Python regex string syntax standards.
