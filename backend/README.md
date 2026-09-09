# Virtual Try-On Node.js + Express Backend Gateway

The orchestration and gateway layer of the MERN stack for the AI Virtual Try-On system, backed by **MongoDB Atlas** and **Mongoose**.

```
React (Frontend)
       │
       ▼ HTTP
Express Gateway (:5000)
       │
       ├── MongoDB Atlas (Users, Garments, TryOnHistory)
       │
       ▼ HTTP POST /tryon
FastAPI AI Service (:8000 / ngrok)
       │
       ├── U²-Net Background Removal
       └── Flow-Style-VTON Warping & Synthesis (GPU)
```

---

## 1. Prerequisites
- **Node.js**: >= v18.0.0 (Tested on Node.js v22.16.0 LTS)
- **npm**: >= 9.0.0 (Tested on npm 10.9.2)
- **MongoDB Atlas**: Cluster URI configured via `MONGODB_URI`
- **AI Service**: Running FastAPI instance (local `http://127.0.0.1:8000` or public ngrok HTTPS URL).

---

## 2. Configuration (`.env`)
Create `.env` based on `.env.example`:

```env
PORT=5000
NODE_ENV=development
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/fitfusion?retryWrites=true&w=majority
AI_SERVICE_URL=http://127.0.0.1:8000
CORS_ORIGIN=http://localhost:5173
AI_REQUEST_TIMEOUT_MS=120000
MAX_FILE_SIZE_MB=10
```

---

## 3. Starting the Server
```bash
# Production mode:
npm start

# Development mode (auto-reload):
npm run dev
```

Startup sequence:
1. Environment configuration validated
2. Connects to MongoDB Atlas securely (credentials never logged)
3. Express server starts on port 5000
4. Downstream AI service connectivity checked

---

## 4. Running Tests
```bash
# Run Gateway & E2E Integration Suite:
npm test

# Run MongoDB & Models CRUD Suite:
node tests/database.test.js
```
