"""
Flow-Style-VTON FastAPI Verification Client
Tests /health, /tryon, error cases, and measures latency.
"""

import sys
import time
from pathlib import Path
import requests
from PIL import Image

REPO_ROOT = Path(__file__).resolve().parent.parent
API_URL = "http://127.0.0.1:8000"

# Default test files
TEST_PERSON = REPO_ROOT / "test" / "mini_dataset" / "test_img" / "000001_0.jpg"
TEST_GARMENT = REPO_ROOT / "test" / "garment_tests" / "04_colored_bg.jpg"
OUTPUT_RESULT = REPO_ROOT / "api" / "api_test_result.jpg"


def test_health():
    print("\n[1] Testing GET /health...")
    url = f"{API_URL}/health"
    resp = requests.get(url, timeout=10)
    print(f"    Status Code: {resp.status_code}")
    print(f"    Response JSON: {resp.json()}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.json()
    assert data.get("status") == "ok"
    assert data.get("model") == "PFAFN"
    assert data.get("device") in {"cuda", "cpu"}
    print("    [+] Health endpoint PASSED!")
    return data


def test_docs():
    print("\n[2] Testing GET /docs (Swagger)...")
    url = f"{API_URL}/docs"
    resp = requests.get(url, timeout=10)
    print(f"    Status Code: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert "swagger" in resp.text.lower() or "openapi" in resp.text.lower()
    print("    [+] Swagger docs endpoint PASSED!")


def test_tryon(person_path=TEST_PERSON, garment_path=TEST_GARMENT, bg_mode="ai"):
    print(f"\n[3] Testing POST /tryon (bg_mode='{bg_mode}')...")
    print(f"    Person:  {person_path}")
    print(f"    Garment: {garment_path}")
    url = f"{API_URL}/tryon"

    assert Path(person_path).exists(), f"Missing person file: {person_path}"
    assert Path(garment_path).exists(), f"Missing garment file: {garment_path}"

    t0 = time.time()
    with open(person_path, "rb") as fp, open(garment_path, "rb") as fg:
        files = {
            "person": ("person.jpg", fp, "image/jpeg"),
            "garment": ("garment.jpg", fg, "image/jpeg")
        }
        data = {"bg_mode": bg_mode}
        resp = requests.post(url, files=files, data=data, timeout=60)

    latency = time.time() - t0
    print(f"    Status Code: {resp.status_code}")
    print(f"    Content-Type: {resp.headers.get('content-type')}")
    print(f"    Client-measured latency: {latency:.3f}s")
    print(f"    X-Process-Time-Total:   {resp.headers.get('x-process-time-total')}s")
    print(f"    X-Process-Time-Garment: {resp.headers.get('x-process-time-garment')}s")
    print(f"    X-Process-Time-VTON:    {resp.headers.get('x-process-time-vton')}s")

    assert resp.status_code == 200, f"Try-on failed with status {resp.status_code}: {resp.text}"
    assert "image/jpeg" in resp.headers.get("content-type", "")

    # Save and verify image
    OUTPUT_RESULT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_RESULT, "wb") as f:
        f.write(resp.content)

    img = Image.open(OUTPUT_RESULT)
    print(f"    Saved Result: {OUTPUT_RESULT}")
    print(f"    Result format: {img.format}, size: {img.size}")
    assert img.size == (192, 256), f"Expected 192x256, got {img.size}"
    print("    [+] POST /tryon PASSED!")


def test_invalid_input():
    print("\n[4] Testing POST /tryon with invalid input (should return HTTP 400)...")
    url = f"{API_URL}/tryon"
    fake_bytes = b"This is not a real image file."
    files = {
        "person": ("fake.jpg", fake_bytes, "image/jpeg"),
        "garment": ("fake.jpg", fake_bytes, "image/jpeg")
    }
    resp = requests.post(url, files=files, data={"bg_mode": "ai"}, timeout=10)
    print(f"    Status Code: {resp.status_code}")
    print(f"    Response JSON: {resp.json()}")
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    print("    [+] Error validation PASSED!")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Test Flow-Style-VTON FastAPI")
    parser.add_argument("--url", type=str, default="http://127.0.0.1:8000")
    parser.add_argument("--person", type=str, default=str(TEST_PERSON))
    parser.add_argument("--garment", type=str, default=str(TEST_GARMENT))
    parser.add_argument("--bg_mode", type=str, default="ai")
    args = parser.parse_args()

    API_URL = args.url.rstrip("/")
    print("=" * 60)
    print(f"FLOW-STYLE-VTON FASTAPI TEST CLIENT -> {API_URL}")
    print("=" * 60)

    try:
        test_health()
        test_docs()
        test_tryon(args.person, args.garment, args.bg_mode)
        test_invalid_input()
        print("\n" + "=" * 60)
        print("ALL FASTAPI CLIENT TESTS PASSED SUCCESSFULLY!")
        print("=" * 60)
    except Exception as e:
        print(f"\n[-] TEST FAILED: {e}")
        sys.exit(1)
