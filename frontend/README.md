# FitFusion React + Vite + Tailwind Frontend

The client presentation layer of the MERN stack for the AI Virtual Try-On application.

```
React Frontend (:5173)
       │
       ▼ HTTP (multipart/form-data)
Express Backend Gateway (:5000)
       │
       ▼ HTTP POST /tryon
FastAPI AI Service (:8000 / ngrok)
       │
       ▼ Flow-Style-VTON + U²-Net (GPU)
Synthesized Try-On Result (image/jpeg)
       │
       ▼ Piped back to React
Displayed in ResultViewer & downloadable as JPEG
```

---

## 1. Prerequisites
- **Node.js**: >= v18.0.0 (Tested on Node.js v22.16.0 LTS)
- **npm**: >= 9.0.0 (Tested on npm 10.9.2)
- **Backend**: Running Node.js gateway at `http://localhost:5000`

---

## 2. Installation
From the `frontend/` directory:
```bash
npm install
```

---

## 3. Configuration (`.env`)
```env
VITE_API_BASE_URL=http://localhost:5000/api
```

---

## 4. Development Server
```bash
npm run dev
```
Open your browser at `http://localhost:5173`.

---

## 5. Production Build
```bash
npm run build
```
Generates optimized static assets in `dist/`.

---

## 6. Features & Architecture
- **Vite + React 18**: Fast development server with Hot Module Replacement (HMR).
- **Tailwind CSS v4**: Utility-first styling with fashion-forward aesthetic.
- **Client-Side Image Validation**: Enforces 10MB limit and valid image MIME types before transmission.
- **Memory Safety**: Object URLs created with `URL.createObjectURL()` are strictly revoked via React `useEffect` hooks to prevent browser memory leaks.
- **Direct Binary Streaming**: Receives raw `image/jpeg` Blob directly from backend; does not waste CPU on Base64 encoding.
- **Accessible & Responsive**: Two-column layout on desktop, stacked on mobile. Accessible ARIA roles, live regions, and keyboard-navigable upload areas.
