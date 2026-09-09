"""
Setup test fixture images for the Quality Test Matrix (Tests A through E).
Scans actual repository directories (data_viton, mini_dataset, garment_tests)
and builds/verifies all 5 test cases.
"""

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw
import numpy as np

SCRIPT_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = SCRIPT_DIR / "quality_fixtures"
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)


def find_file(relative_subpaths, filename):
    """Searches multiple candidate directories for a specific filename."""
    candidates = [
        SCRIPT_DIR / "data_viton" / "VITON_test",
        Path("/content/Flow-Style-VTON/test/data_viton/VITON_test"),
        SCRIPT_DIR / "mini_dataset",
        Path("/content/Flow-Style-VTON/test/mini_dataset"),
        SCRIPT_DIR,
        Path("/content/Flow-Style-VTON/test")
    ]
    for c in candidates:
        for sub in relative_subpaths:
            cand = c / sub / filename
            if cand.exists():
                return cand
            cand_direct = c / filename
            if cand_direct.exists():
                return cand_direct
    return None


def find_garment_test_file(filename):
    """Locates a file inside garment_tests."""
    candidates = [
        SCRIPT_DIR / "garment_tests" / filename,
        Path("/content/Flow-Style-VTON/test/garment_tests") / filename
    ]
    for c in candidates:
        if c.exists():
            return c
    return None


def setup_fixtures():
    print("=" * 70)
    print("SETTING UP QUALITY TEST FIXTURES (TESTS A - E)")
    print("=" * 70)

    # 1. Locate base assets
    viton_person = find_file(["test_img"], "000001_0.jpg")
    viton_person_2 = find_file(["test_img"], "000010_0.jpg")
    viton_garment = find_file(["test_clothes"], "001744_1.jpg")

    garment_patterned = find_garment_test_file("10_patterned.jpg")
    garment_dark = find_garment_test_file("03_dark_bg.jpg")
    garment_bright = find_garment_test_file("01_white_bg.jpg")
    garment_colored = find_garment_test_file("04_colored_bg.jpg")

    missing = []
    if not viton_person: missing.append("000001_0.jpg")
    if not viton_garment: missing.append("001744_1.jpg")
    if not garment_patterned: missing.append("10_patterned.jpg")
    if not garment_dark: missing.append("03_dark_bg.jpg")
    if not garment_bright: missing.append("01_white_bg.jpg")
    if not garment_colored: missing.append("04_colored_bg.jpg")

    if missing:
        print(f"[-] WARNING: Missing source assets: {missing}")

    # TEST A: Official VITON person + official garment
    test_a_p = FIXTURES_DIR / "test_a_viton_person.jpg"
    test_a_g = FIXTURES_DIR / "test_a_viton_garment.jpg"
    if viton_person and viton_garment:
        Image.open(viton_person).save(test_a_p)
        Image.open(viton_garment).save(test_a_g)
        print(f"[+] Test A ready: {test_a_p.name} + {test_a_g.name}")

    # TEST B: White-shirt person + black patterned garment
    test_b_p = FIXTURES_DIR / "test_b_white_shirt_person.jpg"
    test_b_g = FIXTURES_DIR / "test_b_black_patterned_garment.jpg"
    if viton_person and garment_patterned:
        Image.open(viton_person).save(test_b_p)
        Image.open(garment_patterned).save(test_b_g)
        print(f"[+] Test B ready: {test_b_p.name} + {test_b_g.name}")

    # TEST C & D: Male person with crossed arms wearing dark blue/navy T-shirt
    test_c_p = FIXTURES_DIR / "test_c_male_crossed_arms_navy.jpg"
    test_c_g = FIXTURES_DIR / "test_c_dark_navy_garment.jpg"
    test_d_g = FIXTURES_DIR / "test_d_bright_garment.jpg"

    if viton_person and garment_dark and garment_bright:
        # Construct realistic crossed arms navy portrait
        base_im = Image.open(viton_person).resize((192, 256)).convert("RGB")
        male_arr = np.array(base_im, dtype=np.float32)

        # Re-shade clothing area to dark navy blue (R~22, G~30, B~58)
        h, w = male_arr.shape[:2]
        torso_mask = np.zeros((h, w), dtype=bool)
        for y in range(55, 195):
            for x in range(30, 162):
                if male_arr[y, x].mean() > 140 and male_arr[y, x, 0] > 160:
                    torso_mask[y, x] = True

        navy_rgb = np.array([22.0, 30.0, 58.0], dtype=np.float32)
        for c in range(3):
            male_arr[torso_mask, c] = male_arr[torso_mask, c] * 0.15 + navy_rgb[c] * 0.85

        crossed_img = Image.fromarray(np.clip(male_arr, 0, 255).astype(np.uint8), "RGB")
        draw = ImageDraw.Draw(crossed_img)
        # Crossed arms across chest
        skin_color = (210, 160, 135)
        skin_shadow = (175, 125, 105)
        draw.polygon([(45, 140), (145, 125), (148, 142), (48, 158)], fill=skin_color, outline=skin_shadow)
        draw.polygon([(145, 138), (55, 122), (52, 140), (142, 155)], fill=skin_color, outline=skin_shadow)

        # Save as 3:4 portrait (384x512)
        portrait_canvas = Image.new("RGB", (384, 512), (230, 232, 235))
        portrait_canvas.paste(crossed_img.resize((384, 512), Image.Resampling.BICUBIC), (0, 0))
        portrait_canvas.save(test_c_p, quality=95)

        # Garment C: Dark Navy
        d_arr = np.array(Image.open(garment_dark).convert("RGB"), dtype=np.float32)
        g_mask = d_arr.mean(axis=-1) > 25
        d_arr[g_mask, 0] = d_arr[g_mask, 0] * 0.2 + 20.0
        d_arr[g_mask, 1] = d_arr[g_mask, 1] * 0.2 + 28.0
        d_arr[g_mask, 2] = d_arr[g_mask, 2] * 0.2 + 58.0
        Image.fromarray(np.clip(d_arr, 0, 255).astype(np.uint8)).save(test_c_g)

        # Garment D: Bright
        Image.open(garment_bright).save(test_d_g)

        print(f"[+] Test C ready: {test_c_p.name} + {test_c_g.name}")
        print(f"[+] Test D ready: {test_c_p.name} + {test_d_g.name}")

    # TEST E: Person with colored background + clearly different garment
    test_e_p = FIXTURES_DIR / "test_e_person_colored_bg.jpg"
    test_e_g = FIXTURES_DIR / "test_e_colored_garment.jpg"
    base_e = viton_person_2 or viton_person
    if base_e and garment_colored:
        p2_arr = np.array(Image.open(base_e).convert("RGB"))
        bg_mask = (p2_arr[:, :, 0] > 240) & (p2_arr[:, :, 1] > 240) & (p2_arr[:, :, 2] > 240)
        p2_arr[bg_mask] = [235, 185, 160]
        Image.fromarray(p2_arr).save(test_e_p)
        Image.open(garment_colored).save(test_e_g)
        print(f"[+] Test E ready: {test_e_p.name} + {test_e_g.name}")

    print("=" * 70)
    print(f"[+] All fixtures saved to: {FIXTURES_DIR.resolve()}")


if __name__ == "__main__":
    setup_fixtures()
