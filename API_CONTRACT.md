# Flow-Style-VTON: API Contract Specification

This document defines the formal, stable HTTP REST API contract between the **FastAPI AI Virtual Try-On Service** and consuming clients (specifically the future **Node.js / Express backend**).

---

## 1. Architectural Relationship

```
+-------------------------------------------------------------+
|                 MERN Application Layer                     |
|                                                             |
|  [React Frontend] <==== REST / JSON ====> [Express Backend] |
+-------------------------------------------------------------+
                                                    │
                                                    │ HTTP Client (Axios / Fetch)
                                                    ▼
+-------------------------------------------------------------+
|              FastAPI AI Inference Service                   |
|                                                             |
|   GET  /health                                              |
|   POST /tryon  (multipart/form-data)                        |
|                                                             |
|   [TryOnEngine] ──> [U²-Net] ──> [Flow-Style-VTON (GPU)]   |
+-------------------------------------------------------------+
```

### Protocol Rules:
1. **Separation of Concerns**: The Node.js backend MUST NOT attempt to import Python modules or execute Python subprocesses directly. All AI inference is consumed via standard HTTP requests to the FastAPI service.
2. **Stateless Requests**: The FastAPI service does not maintain session or user database records. Each `/tryon` request is fully self-contained.
3. **Response Encoding**: Successful try-on requests return raw binary image streams (`image/jpeg`), NOT base64-encoded strings or JSON wrappers.

---

## 2. Endpoints Specification

### Endpoint 1: Health Check

- **Path**: `/health`
- **HTTP Method**: `GET`
- **Purpose**: Liveness probe, readiness probe, and hardware acceleration diagnostics.

#### Request:
- Headers: None required.
- Query Parameters: None.
- Body: Empty.

#### Response (HTTP 200 OK):
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

| Property | Type | Description |
| :--- | :--- | :--- |
| `status` | `string` | Always `"ok"` when running normally. |
| `service`| `string` | Always `"flow-style-vton"`. |
| `model` | `string` | Core architecture name (`"PFAFN"`). |
| `device` | `string` | Compute runtime (`"cuda"` or `"cpu"`). |
| `background_removal` | `string` | Background segmenter name (`"u2net"`). |
| `gpu` | `string` | *(Optional)* Name of active GPU device (omitted if CPU). |

---

### Endpoint 2: Virtual Try-On

- **Path**: `/tryon`
- **HTTP Method**: `POST`
- **Purpose**: Synthesizes a virtual try-on image from uploaded person and garment images.

#### Request Headers:
- `Content-Type`: `multipart/form-data`

#### Request Body (Multipart Form Data):

| Field Name | Type | Presence | Description |
| :--- | :--- | :---: | :--- |
| `person` | Binary File | **Required** | Person portrait image. Supported: JPG, JPEG, PNG, WEBP, BMP. Max size: 20 MB. |
| `garment` | Binary File | **Required** | Garment clothing image. Any background. Max size: 20 MB. |
| `bg_mode` | String | Optional | Background removal mode. Allowed: `"ai"` (default), `"simple"`, `"provided_mask"`. |

#### Response: HTTP 200 OK (Success)
- **Headers**:
  - `Content-Type`: `image/jpeg`
  - `X-Process-Time-Total`: e.g. `"0.3120"` (total latency in seconds)
  - `X-Process-Time-Garment`: e.g. `"0.1420"` (U²-Net duration in seconds)
  - `X-Process-Time-VTON`: e.g. `"0.1510"` (Flow-Style-VTON neural net duration)
- **Body**:
  - Binary image stream of synthesized virtual try-on photograph ($192 \times 256$ pixels, RGB, JPEG quality 95).

#### Response: Error Codes & JSON Schemas

##### HTTP 400 Bad Request
Returned when input images are missing, empty, exceed size limit, or fail image decoding.
```json
{
  "detail": {
    "error": "Invalid garment image",
    "detail": "The uploaded file could not be decoded as an image."
  }
}
```

##### HTTP 500 Internal Server Error
Returned if internal model inference or matrix computation fails.
```json
{
  "detail": {
    "error": "Inference failure",
    "detail": "Failed to synthesize virtual try-on image due to internal model error."
  }
}
```

##### HTTP 503 Service Unavailable
Returned if GPU VRAM is temporarily exhausted or AI engine is not initialized.
```json
{
  "detail": {
    "error": "CUDA Out of Memory",
    "detail": "GPU memory exhausted during try-on. Try uploading a smaller image or retry shortly."
  }
}
```

---

## 3. Node.js Backend Integration Example (Axios)

The following reference implementation shows how the Node.js / Express backend consumes the FastAPI service:

```javascript
const axios = require('axios');
const FormData = require('form-data');
const fs = require('fs');

const FASTAPI_URL = process.env.FASTAPI_URL || 'http://127.0.0.1:8000';

/**
 * Calls FastAPI service to generate a virtual try-on result.
 * @param {Buffer|ReadableStream} personStream - Person image data
 * @param {Buffer|ReadableStream} garmentStream - Garment image data
 * @returns {Promise<Buffer>} - Generated JPEG image buffer
 */
async function generateTryOn(personStream, garmentStream) {
  const form = new FormData();
  form.append('person', personStream, { filename: 'person.jpg', contentType: 'image/jpeg' });
  form.append('garment', garmentStream, { filename: 'garment.jpg', contentType: 'image/jpeg' });
  form.append('bg_mode', 'ai');

  try {
    const response = await axios.post(`${FASTAPI_URL}/tryon`, form, {
      headers: form.getHeaders(),
      responseType: 'arraybuffer', // Receive binary image buffer
      timeout: 30000 // 30 second timeout
    });

    console.log(`[TryOn] Completed in ${response.headers['x-process-time-total']}s`);
    return Buffer.from(response.data);
  } catch (error) {
    if (error.response && error.response.data) {
      // Decode error JSON from arraybuffer
      const errorJson = JSON.parse(Buffer.from(error.response.data).toString('utf-8'));
      throw new Error(`AI Service Error (${error.response.status}): ${JSON.stringify(errorJson)}`);
    }
    throw error;
  }
}
```

---

## 4. Timeout & Retry Policy Recommendations

1. **Cold Start**: If the FastAPI server is running in a serverless or auto-starting container, allow up to **30 seconds** for initial model loading.
2. **Warm Inference**: Once initialized, expect **0.15s - 0.35s** on a Tesla T4 GPU (or ~1.8s on CPU). Recommend a client timeout of **15-30 seconds**.
3. **Retry Strategy**: If an HTTP 503 (CUDA Out of Memory) occurs, delay retry by 2 seconds with exponential backoff (up to 2 retries). Do NOT retry HTTP 400 errors.
