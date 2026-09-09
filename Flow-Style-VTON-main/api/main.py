"""
Flow-Style-VTON FastAPI Service
Production-ready virtual try-on HTTP API.

Endpoints:
    GET  /health  - Health & runtime diagnostic check
    POST /tryon   - Single-pair virtual try-on inference (multipart/form-data)
    GET  /docs    - Interactive OpenAPI Swagger documentation
"""

import os
import sys
import io
import time
import logging
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional, Tuple, Dict, Any

from PIL import Image, UnidentifiedImageError
import torch
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, status
from fastapi.responses import Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# Ensure Flow-Style-VTON root and test directories are on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
TEST_DIR = REPO_ROOT / "test"

for path_dir in [str(REPO_ROOT), str(TEST_DIR)]:
    if path_dir not in sys.path:
        sys.path.insert(0, path_dir)

from tryon_engine import TryOnEngine

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("tryon_api")

# Configuration via Environment Variables with sensible defaults
CORS_ORIGINS_ENV = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
ALLOWED_ORIGINS = [orig.strip() for orig in CORS_ORIGINS_ENV.split(",") if orig.strip()]
DEFAULT_BG_MODE = os.getenv("DEFAULT_BG_MODE", "ai").lower()
DEVICE_OVERRIDE = os.getenv("DEVICE", None)
CHECKPOINT_DIR = os.getenv("CHECKPOINT_DIR", None)

MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", 20 * 1024 * 1024))  # 20 MB max
SUPPORTED_FORMATS = {"JPEG", "PNG", "WEBP", "BMP", "MPO"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application Lifespan Context Manager.
    Initializes models ONCE at server startup and keeps them cached in memory.
    """
    print("[API] Starting Flow-Style-VTON service")
    print("[API] Loading AI engine...")

    cuda_avail = torch.cuda.is_available()
    print(f"[API] CUDA available: {cuda_avail}")
    if cuda_avail and DEVICE_OVERRIDE != "cpu":
        gpu_name = torch.cuda.get_device_name(0)
        print(f"[API] GPU: {gpu_name}")
    else:
        print("[API] Device: CPU")

    print("[API] Loading background remover (U\u00b2-Net)...")
    t0 = time.time()
    try:
        engine = TryOnEngine(
            warp_checkpoint=(Path(CHECKPOINT_DIR) / "PFAFN_warp_epoch_101.pth") if CHECKPOINT_DIR else None,
            gen_checkpoint=(Path(CHECKPOINT_DIR) / "PFAFN_gen_epoch_101.pth") if CHECKPOINT_DIR else None,
            device=DEVICE_OVERRIDE,
            background_removal_mode=DEFAULT_BG_MODE,
            debug=False
        )
        init_duration = time.time() - t0
        print(f"[API] Engine ready in {init_duration:.2f}s")
    except Exception as e:
        logger.critical(f"[API] FATAL: Model initialization failed: {e}", exc_info=True)
        print(f"[API] Model initialization failed: {e}")
        # Terminate startup so partially broken service is never exposed
        raise RuntimeError(f"Flow-Style-VTON startup aborted: {e}") from e

    # Store state on application object
    app.state.engine = engine
    app.state.inference_lock = asyncio.Lock()
    app.state.start_time = time.time()

    yield

    # Clean shutdown
    print("[API] Shutting down Flow-Style-VTON service...")
    if hasattr(app.state, "engine"):
        del app.state.engine
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


# Create FastAPI application instance
app = FastAPI(
    title="Flow-Style-VTON Virtual Try-On API",
    description="High-performance AI Virtual Try-On service powered by Flow-Style-VTON (PFAFN) and U\u00b2-Net.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _validate_and_decode_image(file_bytes: bytes, field_name: str) -> Image.Image:
    """
    Validates uploaded image bytes:
    - Non-empty
    - Under maximum size limit
    - Decodable via PIL
    - Supported graphic format
    - Sensible dimensions (min 32x32, max 4096x4096)
    """
    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": f"Invalid {field_name} image",
                "detail": f"The uploaded {field_name} file is empty (0 bytes)."
            }
        )

    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": f"Invalid {field_name} image",
                "detail": f"The file exceeds the maximum allowed size of {MAX_UPLOAD_BYTES // (1024*1024)} MB."
            }
        )

    try:
        img = Image.open(io.BytesIO(file_bytes))
        img.load()  # Force decoding
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": f"Invalid {field_name} image",
                "detail": "The uploaded file could not be decoded as an image."
            }
        )

    fmt = (img.format or "").upper()
    if fmt not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": f"Unsupported format for {field_name}",
                "detail": f"Image format '{fmt}' is not supported. Supported: {sorted(list(SUPPORTED_FORMATS))}."
            }
        )

    w, h = img.size
    if w < 32 or h < 32:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": f"Resolution too small for {field_name}",
                "detail": f"Dimensions ({w}x{h}) are below minimum required 32x32."
            }
        )

    if w > 4096 or h > 4096:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": f"Resolution too large for {field_name}",
                "detail": f"Dimensions ({w}x{h}) exceed maximum allowed 4096x4096."
            }
        )

    return img


def _run_tryon_sync(
    engine: TryOnEngine,
    person_img: Image.Image,
    garment_img: Image.Image,
    bg_mode: str,
    crop_mode: str = "auto",
    normalize_color: bool = False
) -> Tuple[Image.Image, Dict[str, float]]:
    """
    Synchronous inference worker executed inside thread executor.
    Sets preprocessor mode and calls engine.try_on with canonical alignment and crop_mode.
    """
    engine.garment_preprocessor.mode = bg_mode
    res_img = engine.try_on(
        person_image=person_img,
        garment_image=garment_img,
        save_path=None,
        crop_mode=crop_mode,
        normalize_color=normalize_color
    )
    timings = dict(engine.last_timing)
    return res_img, timings


@app.get("/health", tags=["Diagnostic"])
async def health_check():
    """
    Health diagnostic endpoint.
    Returns status, active model, actual compute device, and background remover info.
    """
    engine: Optional[TryOnEngine] = getattr(app.state, "engine", None)
    if engine is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "error",
                "service": "flow-style-vton",
                "detail": "AI Engine is not initialized."
            }
        )

    is_cuda = engine.device.type == "cuda" and torch.cuda.is_available()
    device_val = "cuda" if is_cuda else "cpu"

    resp = {
        "status": "ok",
        "service": "flow-style-vton",
        "model": "PFAFN",
        "device": device_val,
        "background_removal": "u2net"
    }
    if is_cuda:
        resp["gpu"] = torch.cuda.get_device_name(engine.device)

    return resp


@app.post(
    "/tryon",
    tags=["Virtual Try-On"],
    summary="Execute Virtual Try-On",
    description="Takes a person portrait and garment photo, performs AI background removal and Flow-Style-VTON warping, and returns the synthesized try-on image directly as image/jpeg.",
    response_class=Response,
    responses={
        200: {
            "content": {"image/jpeg": {}},
            "description": "Synthesized virtual try-on photograph (192x256 JPEG)."
        },
        400: {
            "description": "Invalid image upload or unsupported format."
        },
        500: {
            "description": "Internal model inference failure."
        },
        503: {
            "description": "CUDA Out of Memory or engine unavailable."
        }
    }
)
async def virtual_try_on(
    person: UploadFile = File(..., description="Person portrait photograph (JPG/PNG/WEBP)"),
    garment: UploadFile = File(..., description="Target garment photo with any background (JPG/PNG/WEBP)"),
    bg_mode: str = Form("ai", description="Background removal mode: 'ai' (U\u00b2-Net), 'simple' (threshold), 'provided_mask'"),
    crop_mode: Optional[str] = Form("auto", description="Person cropping mode: 'auto', 'upper_body', 'center'"),
    normalize_color: Optional[bool] = Form(False, description="Optional subtle brightness harmonization")
):
    t_req_start = time.time()
    engine: Optional[TryOnEngine] = getattr(app.state, "engine", None)
    if engine is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"error": "Service unavailable", "detail": "AI Engine is not initialized."}
        )

    # 1. Validate bg_mode parameter
    mode_clean = bg_mode.strip().lower()
    if mode_clean not in {"ai", "simple", "provided_mask"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "Invalid bg_mode",
                "detail": f"Mode '{bg_mode}' is not valid. Choose from: 'ai', 'simple', 'provided_mask'."
            }
        )

    crop_mode_clean = (crop_mode or "auto").strip().lower()
    if crop_mode_clean not in {"auto", "upper_body", "center"}:
        crop_mode_clean = "auto"

    # 2. Read and decode images (in-memory, outside lock)
    t_dec0 = time.time()
    person_bytes = await person.read()
    garment_bytes = await garment.read()

    person_pil = _validate_and_decode_image(person_bytes, "person")
    garment_pil = _validate_and_decode_image(garment_bytes, "garment")
    decode_duration = time.time() - t_dec0

    # 3. Acquire inference lock to serialize requests across GPU/model
    inference_lock: asyncio.Lock = app.state.inference_lock
    async with inference_lock:
        loop = asyncio.get_running_loop()
        try:
            result_pil, engine_timings = await loop.run_in_executor(
                None,
                _run_tryon_sync,
                engine,
                person_pil,
                garment_pil,
                mode_clean,
                crop_mode_clean,
                bool(normalize_color)
            )
        except torch.cuda.OutOfMemoryError as oom:
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            logger.error("[API] CUDA Out Of Memory during try-on inference.", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "error": "CUDA Out of Memory",
                    "detail": "GPU memory exhausted during try-on. Try uploading a smaller image or retry shortly."
                }
            )
        except Exception as exc:
            logger.error(f"[API] Internal error during try-on: {exc}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "Inference failure",
                    "detail": "Failed to synthesize virtual try-on image due to internal model error."
                }
            )

    # 4. Encode result image to JPEG in memory
    t_enc0 = time.time()
    out_buffer = io.BytesIO()
    result_pil.convert("RGB").save(out_buffer, format="JPEG", quality=95)
    jpeg_bytes = out_buffer.getvalue()
    encode_duration = time.time() - t_enc0

    total_duration = time.time() - t_req_start

    # 5. Performance Logging
    p_time = engine_timings.get("person_time", 0.0)
    g_time = engine_timings.get("garment_time", 0.0)
    v_time = engine_timings.get("vton_time", 0.0)

    print("-" * 40)
    print("[TRYON]")
    print(f"Person decode:        {decode_duration:.3f}s")
    print(f"Garment preprocessing:{g_time:.3f}s")
    print(f"VTON forward:         {v_time:.3f}s")
    print(f"Output encoding:      {encode_duration:.3f}s")
    print(f"Total request:        {total_duration:.3f}s")
    print("-" * 40)

    # 6. Return response directly with performance metadata headers
    headers = {
        "X-Process-Time-Total": f"{total_duration:.4f}",
        "X-Process-Time-Garment": f"{g_time:.4f}",
        "X-Process-Time-VTON": f"{v_time:.4f}",
        "Cache-Control": "no-store, no-cache, must-revalidate"
    }

    return Response(
        content=jpeg_bytes,
        media_type="image/jpeg",
        headers=headers
    )


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    print(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, workers=1)
