# Virtual Try-On Backend API Contract

This document defines the formal HTTP REST API contract provided by the **Node.js + Express Backend Gateway** (`http://localhost:5000`) backed by **MongoDB Atlas** for consumption by the **React Frontend**.

---

## 1. Gateway Architecture & Data Layer

```
React (Frontend)
       │
       ▼ HTTP
Express Gateway (:5000)
       │
       ├── MongoDB Atlas (Mongoose ODM)
       │   ├── users (User accounts & profile metadata)
       │   ├── garments (Garment catalog & custom uploads)
       │   └── tryonhistories (Try-on activity logs & status)
       │
       ▼ HTTP POST /tryon
FastAPI AI Service (:8000 / ngrok)
       │
       ├── U²-Net Garment Background Removal
       └── Flow-Style-VTON Warping & Synthesis (GPU)
```

---

## 2. API Endpoints Specification

### A. Health & Diagnostics

#### 1. `GET /api/health`
Checks backend gateway and database connectivity.
- **Response**: `HTTP 200 OK`
```json
{
  "status": "ok",
  "service": "virtual-try-on-backend",
  "database": {
    "status": "connected"
  }
}
```

#### 2. `GET /api/health/db`
Dedicated MongoDB diagnostic endpoint.
- **Success Response**: `HTTP 200 OK`
```json
{
  "status": "ok",
  "database": "mongodb",
  "connection": "connected"
}
```
- **Failure Response**: `HTTP 503 Service Unavailable`
```json
{
  "status": "error",
  "database": "mongodb",
  "connection": "disconnected"
}
```

#### 3. `GET /api/health/ai`
Checks downstream connection to the FastAPI virtual try-on engine.
- **Success Response**: `HTTP 200 OK`
```json
{
  "status": "ok",
  "backend": "healthy",
  "aiService": {
    "status": "ok",
    "service": "flow-style-vton",
    "model": "PFAFN",
    "device": "cuda",
    "background_removal": "u2net",
    "gpu": "Tesla T4"
  }
}
```
- **Failure Response**: `HTTP 502 Bad Gateway` if FastAPI is unreachable.

---

### B. Virtual Try-On

#### `POST /api/tryon`
Executes single-pair virtual try-on and automatically logs the event to `tryonhistories`.

- **Content-Type**: `multipart/form-data`
- **Fields**:
  - `person`: File (Required). Portrait image (JPG, PNG, WEBP, BMP). Max 10MB.
  - `garment`: File (Required). Garment photo with any background. Max 10MB.
  - `bg_mode`: String (Optional). `'ai'` (default), `'simple'`, or `'provided_mask'`.
  - `user`: String (Optional). MongoDB User ObjectId.
  - `garmentId`: String (Optional). MongoDB Garment ObjectId.
- **Success Response**: `HTTP 200 OK`, `Content-Type: image/jpeg` (raw binary stream).
- **Headers**:
  - `X-Request-ID`: Unique tracking UUID
  - `X-History-ID`: MongoDB `TryOnHistory` document ID
  - `X-Gateway-Elapsed-Sec`: Total duration in seconds
  - `X-AI-Process-Time-Total`: AI inference duration

---

### C. Garments Catalog CRUD

#### 1. `POST /api/garments`
Creates a new garment record.
- **Body**: `application/json`
```json
{
  "name": "Classic Oxford Shirt",
  "description": "Slim fit cotton shirt",
  "category": "shirt",
  "imageUrl": "/uploads/oxford.jpg",
  "thumbnailUrl": "/uploads/oxford_thumb.jpg",
  "createdBy": "6aa16602d92155fe4bece312"
}
```
- **Response**: `HTTP 201 Created`

#### 2. `GET /api/garments`
Lists garments with optional filters.
- **Query Params**: `category`, `createdBy`, `limit`, `skip`
- **Response**: `HTTP 200 OK`
```json
{
  "status": "success",
  "total": 12,
  "count": 12,
  "data": [ ... ]
}
```

#### 3. `GET /api/garments/:id`
Fetches a single garment by ObjectId.
- **Response**: `HTTP 200 OK` (or `404 Not Found`, `400 Invalid ID`)

#### 4. `PUT /api/garments/:id`
Updates garment details.
- **Response**: `HTTP 200 OK` with updated document.

#### 5. `DELETE /api/garments/:id`
Deletes a garment by ID.
- **Response**: `HTTP 200 OK`

---

### D. Try-On History

#### 1. `POST /api/history`
Manually records a try-on history entry.
- **Body**: `application/json`
```json
{
  "user": "6aa16602d92155fe4bece312",
  "garment": "6aa16602d92155fe4bece313",
  "status": "completed",
  "processingTimeMs": 350
}
```
- **Response**: `HTTP 201 Created`

#### 2. `GET /api/history`
Retrieves history records sorted by `createdAt DESC`.
- **Query Params**: `user`, `status`, `limit`, `skip`
- **Response**: `HTTP 200 OK`

#### 3. `GET /api/history/:id`
Retrieves a populated history entry.
- **Response**: `HTTP 200 OK`

#### 4. `DELETE /api/history/:id`
Deletes a history record by ID.
- **Response**: `HTTP 200 OK`
