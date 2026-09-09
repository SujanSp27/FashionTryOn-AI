# Flow-Style-VTON FastAPI Service

Production-ready, high-performance HTTP REST API wrapping the Flow-Style-VTON (PFAFN) virtual try-on engine with U\u00b2-Net AI garment background removal.

---

## 1. Architecture Overview

```
Client (Web / Mobile / Node.js Backend)
                  │
                  ▼
         [ POST /tryon ]
                  │
        FastAPI Application (:8000)
                  │
                  ├── Image validation & decoding (in-memory)
                  ├── Request serialization via asyncio.Lock
                  │
                  ▼
         TryOnEngine (Memory-Cached)
                  │
                  ├── GarmentPreprocessor (U²-Net / rembg)
                  │   └── Background removal & edge mask extraction
                  │
                  ├── Appearance Flow Warping Module (AFWM)
                  │   └── Coarse-to-fine appearance flow estimation
                  │
                  └── Style-Based ResUnet Generator
                      └── Final try-on image synthesis [192x256]
                  │
                  ▼
      HTTP 200: image/jpeg Response (Direct Binary Stream)
```

### Key Design Principles:
- **Zero Model Reloading**: Flow-Style-VTON warp model, generator, and U²-Net background remover are loaded **once** during startup (via FastAPI lifespan context) and cached permanently in memory.
- **In-Memory Image Processing**: No temporary disk files are created during standard request handling. Uploaded bytes are decoded into PIL images, processed through tensors, and encoded directly to JPEG byte streams.
- **Concurrency Safety**: GPU inference is serialized using an `asyncio.Lock()` to prevent race conditions, memory corruption, and CUDA out-of-memory errors on single-GPU hardware.
- **Single Worker Model**: Uvicorn is executed with `--workers 1` to share the single GPU context safely.

---

## 2. Installation & Prerequisites

From the `Flow-Style-VTON-main` directory:

```bash
pip install -r api/requirements.txt
```

### Dependencies
- `fastapi>=0.100.0`
- `uvicorn[standard]>=0.22.0`
- `python-multipart>=0.0.6`
- `pillow>=9.0.0`
- `torch>=1.1.0`
- `torchvision>=0.3.0`
- `rembg>=2.0.50`
- `pyngrok>=7.0.0`
- `requests>=2.28.0`

---

## 3. Environment Variables & Configuration

Configure the service via environment variables:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `HOST` | `0.0.0.0` | Bind host address. |
| `PORT` | `8000` | Bind port. |
| `DEVICE` | *Auto-detected* | Force compute device (`cuda`, `cuda:0`, `cpu`). |
| `CHECKPOINT_DIR` | `test/checkpoints` | Path to directory containing `PFAFN_*.pth` checkpoints. |
| `DEFAULT_BG_MODE`| `ai` | Default background removal mode (`ai`, `simple`, `provided_mask`). |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Comma-separated list of allowed CORS origins. |
| `MAX_UPLOAD_BYTES`| `20971520` (20 MB) | Maximum permitted file upload size in bytes. |
| `NGROK_AUTHTOKEN` | *None* | ngrok authentication token for public tunneling. |

---

## 4. Starting the Service

### Development / Local Server
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 1
```

### Google Colab (Tesla T4 GPU)
```python
# In a Colab cell:
!uvicorn api.main:app --host 0.0.0.0 --port 8000 --workers 1 &
```

### Startup Log Output
```
[API] Starting Flow-Style-VTON service
[API] Loading AI engine...
[API] CUDA available: True
[API] GPU: Tesla T4
[API] Loading background remover (U²-Net)...
[TryOnEngine] Initializing engine on device: cuda:0
[TryOnEngine] Active GPU: Tesla T4 (15.00 GB VRAM)
[TryOnEngine] Loading Warp Checkpoint:      PFAFN_warp_epoch_101.pth (127.16 MB)
[TryOnEngine] Loading Generator Checkpoint: PFAFN_gen_epoch_101.pth (167.61 MB)
[GarmentPreprocessor] Initializing AI background remover (u2net)...
[GarmentPreprocessor] AI session ready in 0.96s!
[TryOnEngine] Models and preprocessor cached successfully in 2.15s!
[API] Engine ready in 2.15s
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 5. API Endpoints

### A. Health Diagnostic: `GET /health`
Verifies service availability and active hardware acceleration.

- **URL**: `/health`
- **Method**: `GET`
- **Response**: `application/json`

#### Example Response (GPU / Production):
```json
{
    "status": "ok",
    "service": "flow-style-vton",
    "model": "PFAFN",
    "device": "cuda",
    "background_removal": "u2net",
    "gpu": "Tesla T4"
}
```

#### Example Response (CPU / Fallback):
```json
{
    "status": "ok",
    "service": "flow-style-vton",
    "model": "PFAFN",
    "device": "cpu",
    "background_removal": "u2net"
}
```

---

### B. Virtual Try-On: `POST /tryon`
Executes single-pair virtual try-on on a person portrait and garment photo.

- **URL**: `/tryon`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`

#### Form Fields:
| Field | Type | Required | Description |
| :--- | :--- | :---: | :--- |
| `person` | File | Yes | Person portrait image (JPG, PNG, WEBP, BMP). |
| `garment` | File | Yes | Garment photo with any background (JPG, PNG, WEBP, BMP). |
| `bg_mode` | String | No | Background removal mode: `'ai'` (default), `'simple'`, or `'provided_mask'`. |

#### Successful Response (HTTP 200):
- **Content-Type**: `image/jpeg`
- **Body**: Binary JPEG image bytes ($192 \times 256$ pixels).
- **Custom Response Headers**:
  - `X-Process-Time-Total`: Total processing duration in seconds.
  - `X-Process-Time-Garment`: U²-Net background removal and edge extraction duration.
  - `X-Process-Time-VTON`: Flow-Style-VTON warping and generator duration.

#### Error Responses:
- **HTTP 400 Bad Request** (Invalid image, corrupted file, or unsupported format):
  ```json
  {
      "detail": {
          "error": "Invalid garment image",
          "detail": "The uploaded file could not be decoded as an image."
      }
  }
  ```
- **HTTP 503 Service Unavailable** (CUDA Out of Memory):
  ```json
  {
      "detail": {
          "error": "CUDA Out of Memory",
          "detail": "GPU memory exhausted during try-on. Try uploading a smaller image or retry shortly."
      }
  }
  ```
- **HTTP 500 Internal Server Error** (Model synthesis failure):
  ```json
  {
      "detail": {
          "error": "Inference failure",
          "detail": "Failed to synthesize virtual try-on image due to internal model error."
      }
  }
  ```

---

## 6. Testing the Service

### 1. Interactive Swagger UI
Open your browser at:
```
http://localhost:8000/docs
```
You can upload person and garment images directly and view the generated JPEG image inline.

### 2. Python Test Client
Run the automated test script:
```bash
python api/test_api.py --url http://127.0.0.1:8000
```

### 3. cURL Command
```bash
curl -X POST http://127.0.0.1:8000/tryon \
  -F "person=@test/mini_dataset/test_img/000001_0.jpg" \
  -F "garment=@test/garment_tests/04_colored_bg.jpg" \
  --output result.jpg
```

---

## 7. Exposing via ngrok Tunnel

To allow remote access from Google Colab or external clients:

1. Obtain an authtoken from [ngrok.com](https://ngrok.com).
2. Start the tunnel:
   ```bash
   python api/tunnel.py --token YOUR_NGROK_AUTHTOKEN
   ```
3. The script outputs a public HTTPS endpoint:
   ```
   [+] NGROK TUNNEL ONLINE: https://abcd-123-456.ngrok-free.app
       Health:  https://abcd-123-456.ngrok-free.app/health
       Swagger: https://abcd-123-456.ngrok-free.app/docs
       Try-On:  https://abcd-123-456.ngrok-free.app/tryon
   ```
4. Test the public URL:
   ```bash
   python api/test_api.py --url https://abcd-123-456.ngrok-free.app
   ```
