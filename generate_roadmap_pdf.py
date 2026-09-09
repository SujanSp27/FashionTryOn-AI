import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas

class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_number(num_pages)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def draw_page_number(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#4A5568"))
        self.drawString(40, 25, "AI Virtual Try-On Web Application — Engineering Roadmap (MongoDB + Flow-Style-VTON)")
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#718096"))
        self.drawRightString(letter[0] - 40, 25, f"Page {self._pageNumber} of {page_count}")
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(40, 36, letter[0] - 40, 36)
        self.restoreState()

def build_pdf(filename="AI_Virtual_TryOn_Project_Roadmap.pdf"):
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=45,
        bottomMargin=45
    )

    styles = getSampleStyleSheet()
    
    # Custom styles
    primary_color = colors.HexColor("#1E3A8A")   # Deep Navy
    secondary_color = colors.HexColor("#0D9488") # Teal
    dark_text = colors.HexColor("#1F2937")       # Charcoal
    muted_text = colors.HexColor("#4B5563")      # Slate
    card_bg = colors.HexColor("#F8FAFC")         # Off white

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=22,
        leading=26,
        textColor=primary_color,
        spaceAfter=4
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=11,
        leading=15,
        textColor=muted_text,
        spaceAfter=14
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        fontName='Helvetica-Bold',
        fontSize=14,
        leading=18,
        textColor=primary_color,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        fontName='Helvetica-Bold',
        fontSize=11,
        leading=15,
        textColor=secondary_color,
        spaceBefore=8,
        spaceAfter=4,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        fontName='Helvetica',
        fontSize=9,
        leading=12.5,
        textColor=dark_text,
        spaceAfter=4
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=body_style,
        leftIndent=12,
        bulletIndent=4,
        spaceAfter=3
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        fontName='Courier',
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#1E293B")
    )

    table_header_style = ParagraphStyle(
        'TableHeader',
        fontName='Helvetica-Bold',
        fontSize=8.5,
        leading=11,
        textColor=colors.white
    )

    table_cell_style = ParagraphStyle(
        'TableCell',
        fontName='Helvetica',
        fontSize=8,
        leading=10.5,
        textColor=dark_text
    )

    table_cell_bold = ParagraphStyle(
        'TableCellBold',
        fontName='Helvetica-Bold',
        fontSize=8,
        leading=10.5,
        textColor=primary_color
    )

    story = []

    # Title & Metadata Banner
    story.append(Paragraph("AI Virtual Try-On Web Application", title_style))
    story.append(Paragraph("Complete Technical Roadmap: React + Node.js/Express + MongoDB + FastAPI + Flow-Style-VTON", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=primary_color, spaceAfter=10))

    # Executive Overview
    story.append(Paragraph("1. Executive Summary & Production Stack", h1_style))
    overview_text = (
        "This document defines the strict, milestone-driven development roadmap for building an AI-powered "
        "Virtual Try-On (VTON) web platform. The system allows users to upload a portrait photo and a garment image (or "
        "select from a clothing catalog), performs automated background isolation and warping, and synthesizes a "
        "photorealistic virtual try-on image using the peer-reviewed <b>Flow-Style-VTON (CVPR 2022)</b> model. "
        "All catalog items, user session metadata, and try-on history are managed persistently via <b>MongoDB</b>."
    )
    story.append(Paragraph(overview_text, body_style))
    story.append(Spacer(1, 6))

    # Tech Stack Table
    stack_data = [
        [Paragraph("Component", table_header_style), Paragraph("Technology", table_header_style), Paragraph("Architectural Role & Scope", table_header_style)],
        [Paragraph("Frontend", table_cell_bold), Paragraph("React (Vite) + Tailwind CSS", table_cell_style), Paragraph("Responsive client UI, drag-and-drop uploads, catalog browser, live try-on preview, before/after slider.", table_cell_style)],
        [Paragraph("Backend Gateway", table_cell_bold), Paragraph("Node.js + Express.js", table_cell_style), Paragraph("API Gateway, request validation, Multer file handling, forwarding to AI service, error guardrails.", table_cell_style)],
        [Paragraph("Database", table_cell_bold), Paragraph("MongoDB + Mongoose", table_cell_style), Paragraph("Persistent storage for catalog garments, category indices, user sessions, and try-on history logs.", table_cell_style)],
        [Paragraph("AI Microservice", table_cell_bold), Paragraph("FastAPI + Uvicorn (Python)", table_cell_style), Paragraph("Asynchronous REST service running inside Google Colab, executing tensor preprocessing and inference.", table_cell_style)],
        [Paragraph("AI Core Model", table_cell_bold), Paragraph("Flow-Style-VTON (PFAFN)", table_cell_style), Paragraph("Parser-Free Appearance Flow Warping Module (AFWM) + ResUNet Generator using pretrained weights.", table_cell_style)],
        [Paragraph("Preprocessing", table_cell_bold), Paragraph("rembg (U^2-Net) + OpenCV", table_cell_style), Paragraph("Automated garment background removal, binary silhouette mask generation, 256x192 bicubic resizing.", table_cell_style)],
        [Paragraph("Compute / Tunnel", table_cell_bold), Paragraph("Google Colab (T4 GPU) + ngrok", table_cell_style), Paragraph("Free cloud GPU inference accessible by the local backend via secure reverse HTTPS tunnel.", table_cell_style)]
    ]
    t_stack = Table(stack_data, colWidths=[100, 150, 282])
    t_stack.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, card_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_stack)
    story.append(Spacer(1, 10))

    # Architecture & MongoDB Schema
    story.append(Paragraph("2. System Architecture & MongoDB Data Models", h1_style))
    arch_desc = (
        "The architecture is organized into a clean 3-tier decoupling: the <b>Client Layer</b> interacts with the "
        "<b>Application Gateway (Node.js/Express)</b>, which communicates with <b>MongoDB</b> for metadata and "
        "proxies computationally heavy image payloads across a secure <b>ngrok tunnel</b> to the <b>FastAPI GPU Worker</b>."
    )
    story.append(Paragraph(arch_desc, body_style))
    story.append(Spacer(1, 4))

    schema_data = [
        [Paragraph("MongoDB Collection", table_header_style), Paragraph("Field Definitions", table_header_style), Paragraph("Purpose / Use Case", table_header_style)],
        [
            Paragraph("garments", table_cell_bold),
            Paragraph("<b>_id</b>: ObjectId<br/><b>name</b>: String (required)<br/><b>category</b>: String (Shirts/Tees/Dresses)<br/><b>imageUrl</b>: String (path/URL)<br/><b>maskUrl</b>: String (pre-extracted mask)<br/><b>tags</b>: [String]<br/><b>inStock</b>: Boolean<br/><b>createdAt</b>: Date", table_cell_style),
            Paragraph("Stores curated apparel catalog items so users can select garments without uploading. Pre-computed masks eliminate preprocessing latency.", table_cell_style)
        ],
        [
            Paragraph("tryons", table_cell_bold),
            Paragraph("<b>_id</b>: ObjectId<br/><b>sessionId</b>: String (UUID/IP)<br/><b>personImageUrl</b>: String<br/><b>garmentId</b>: ObjectId (ref: Garment, optional)<br/><b>customGarmentUrl</b>: String (optional)<br/><b>resultImageUrl</b>: String<br/><b>latencyMs</b>: Number<br/><b>status</b>: Enum ['success', 'failed']<br/><b>createdAt</b>: Date", table_cell_style),
            Paragraph("Tracks try-on execution history, execution times, success rates, and allows users to revisit recent try-on results.", table_cell_style)
        ]
    ]
    t_schema = Table(schema_data, colWidths=[110, 230, 192])
    t_schema.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), secondary_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, card_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    story.append(t_schema)
    story.append(Spacer(1, 10))

    # Project Phases & Milestones
    story.append(Paragraph("3. Detailed Phase-by-Phase Development Roadmap", h1_style))

    phases = [
        ("Milestone 0: Workspace Architecture & Guardrails",
         "Establish the isolated multi-folder architecture surrounding existing repos without touching stock model code.",
         "Audit local Node.js and Python environments; define .gitignore for checkpoints and temporary files; create clean subdirectories: /ai_service, /backend, /frontend, /docs.",
         "Directories initialized; stock repositories remain untouched.",
         "Low"),

        ("Milestone 1: Google Colab T4 GPU Environment Setup",
         "Spin up a verified cloud GPU environment capable of running PyTorch CUDA operations.",
         "Create Colab notebook; select T4 GPU runtime; verify torch.cuda.is_available() is True; clone Flow-Style-VTON repo; install gdown, opencv, pillow, rembg.",
         "Colab environment running with 15GB Tesla T4 GPU verified.",
         "Low"),

        ("Milestone 2: Pretrained Checkpoints Download & Benchmark Inference",
         "Acquire official weights and verify baseline model execution before writing custom code.",
         "Download PFAFN_warp_epoch_101.pth and PFAFN_gen_epoch_101.pth via gdown; download sample VITON dataset; patch base_dataset.py (transforms.Scale to transforms.Resize); run test.py.",
         "Official test.py completes with 0 errors and generates try-on images in our_t_results/.",
         "Medium"),

        ("Milestone 3: Decoupled Single-Pair Inference Engine",
         "Create a standalone Python function that accepts raw images directly without dataset folder structures.",
         "Write engine.py; load AFWM warp network and ResUnetGenerator into GPU VRAM once on startup; implement tryon_single_pair(person_pil, cloth_pil, mask_pil) returning a PIL Image.",
         "Function executes single try-on pair in <150ms on GPU.",
         "Medium"),

        ("Milestone 4: Automated Preprocessing & Garment Masking",
         "Enable arbitrary user photos to be used by automating background removal and aspect ratio normalization.",
         "Build preprocessing.py; person pipeline: EXIF orientation correction, 3:4 aspect ratio crop, 256x192 bicubic resize, [-1, 1] normalization; garment pipeline: rembg U^2-Net background removal, alpha-to-mask conversion, cloth x mask zeroing.",
         "Arbitrary smartphone photos of people and clothes successfully converted to required tensors.",
         "Medium"),

        ("Milestone 5: FastAPI AI Microservice & Colab ngrok Tunnel",
         "Expose the inference engine over an HTTPS REST API for external web application consumption.",
         "Build server.py using FastAPI and Uvicorn; endpoints: GET /health and POST /api/v1/tryon; integrate pyngrok to expose port 8000 via a secure public URL; add warm-up inference.",
         "Public ngrok HTTPS URL accepts curl POST with images and returns PNG try-on result in <1.5s.",
         "Medium"),

        ("Milestone 6: MongoDB Connection & Mongoose Data Models",
         "Establish persistent data storage for apparel catalog and try-on execution history.",
         "Install mongoose and dotenv in backend; configure MongoDB connection string (local MongoDB or free MongoDB Atlas); create Garment and TryOnHistory schemas; write seed script to populate sample clothing.",
         "MongoDB connects cleanly; garments collection seeded with 8+ sample garments.",
         "Low"),

        ("Milestone 7: Node.js Express Gateway & API Proxy",
         "Build the application gateway to manage catalog APIs, validate uploads, and proxy inference to Colab.",
         "Initialize Express app with CORS and Multer; create routes: GET /api/health, GET /api/garments (reads MongoDB), GET /api/history, POST /api/tryon (saves to MongoDB and proxies to Colab); handle timeouts.",
         "Postman request to http://localhost:5000/api/tryon returns generated try-on and logs record in MongoDB.",
         "Medium"),

        ("Milestone 8: React (Vite) Web Application UI",
         "Develop the modern, responsive web user interface.",
         "Scaffold React app with Vite and Tailwind CSS; create Navbar, PersonUpload (drag-and-drop + camera), GarmentSelector (MongoDB catalog grid + custom upload tab), ActionButton, LoadingOverlay, ResultViewer (with Before/After slider).",
         "React UI runs on port 5173 with smooth previews and responsive layout.",
         "Medium"),

        ("Milestone 9: Full End-to-End System Integration",
         "Wire all layers together into a unified, seamless user experience.",
         "Create api.js in React to call Node.js backend; bind catalog selection to try-on requests; display live Before/After comparison; save completed try-ons to MongoDB and display in recent history drawer.",
         "User uploads photo in React -> Node -> Colab GPU -> Result displayed on screen in <2 seconds.",
         "Medium"),

        ("Milestone 10: System Hardening, Error Handling & Guardrails",
         "Ensure rock-solid reliability against bad inputs, oversized files, and network drops.",
         "Add file type (JPEG/PNG) and size (<10MB) guards; add Colab disconnect detection with user-friendly alert banners; implement automatic temp file cleanup in Node.",
         "System handles invalid uploads and network disconnects gracefully without crashing.",
         "Low"),

        ("Milestone 11: Benchmark Testing & Performance Validation",
         "Empirically test latency, fidelity, and reliability across diverse test cases.",
         "Run 20 diverse test pairs (different poses, lighting, garment types); record mask extraction time, warping time, generator time, and total roundtrip latency; document metrics.",
         "Benchmark report with latency averages and visual output quality logged.",
         "Low"),

        ("Milestone 12: Deployment & Final Verification",
         "Prepare system for final college demonstration and production readiness.",
         "Package backend and frontend startup scripts (npm run dev); verify MongoDB Atlas cloud persistence; verify backup demo video recording in case of campus Wi-Fi failure.",
         "One-command startup; verified live demonstration ready for project evaluation.",
         "Low")
    ]

    for title, obj, tasks, success, diff in phases:
        p_block = []
        p_block.append(Paragraph(f"<b>{title}</b> &nbsp; <font color='#0D9488'>[Difficulty: {diff}]</font>", h2_style))
        p_block.append(Paragraph(f"<b>Objective:</b> {obj}", body_style))
        p_block.append(Paragraph(f"<b>Exact Tasks:</b> {tasks}", body_style))
        p_block.append(Paragraph(f"<b>Success Criteria:</b> {success}", body_style))
        p_block.append(Spacer(1, 4))
        story.append(KeepTogether(p_block))

    story.append(Spacer(1, 10))

    # Exact Antigravity / Gemini Prompts
    story.append(Paragraph("4. Step-by-Step Antigravity Implementation Prompts", h1_style))
    story.append(Paragraph(
        "Copy and paste these exact prompts into Antigravity/Gemini sequentially. "
        "Each prompt enforces rigorous guardrails: inspect before changing code, do not break existing files, "
        "and stop on error.", body_style
    ))
    story.append(Spacer(1, 4))

    prompts = [
        ("PROMPT M1: Google Colab GPU Environment",
         "Act as the lead AI engineer for my Virtual Try-On college project.\n"
         "OBJECTIVE: Setup a clean Google Colab T4 GPU environment for Flow-Style-VTON.\n"
         "INSTRUCTIONS:\n"
         "1. Write Python cells for Google Colab verifying PyTorch CUDA availability and printing GPU name/VRAM.\n"
         "2. Clone https://github.com/SenHe/Flow-Style-VTON.git into /content/Flow-Style-VTON.\n"
         "3. Install dependencies: gdown, opencv-python-headless, pillow, matplotlib, rembg.\n"
         "4. DO NOT download weights or write web services yet.\n"
         "SUCCESS: Colab verifies Tesla T4 GPU active and repository cloned."),

        ("PROMPT M2: Download Weights & Benchmark Test",
         "Act as the lead AI engineer for my Virtual Try-On college project.\n"
         "OBJECTIVE: Download official Flow-Style-VTON pretrained checkpoints and run benchmark test.\n"
         "INSTRUCTIONS:\n"
         "1. Download PFAFN_warp_epoch_101.pth and PFAFN_gen_epoch_101.pth from Google Drive (Folder ID: 1hunG-84GOSq-qviJRvkXeSMFgnItOTTU) to /content/checkpoints/.\n"
         "2. Verify both checkpoint files exist and exceed 100MB in size.\n"
         "3. Download sample test dataset (ID: 1Y7uV0gomwWyxCvvH8TIbY7D9cTAUy6om) and extract it.\n"
         "4. Patch base_dataset.py replacing deprecated torchvision transforms.Scale with transforms.Resize.\n"
         "5. Run test.py with downloaded checkpoints and verify try-on images are saved in our_t_results/.\n"
         "SUCCESS: Official test script completes with 0 errors and generates visual try-on results."),

        ("PROMPT M3: Decoupled Single-Pair Inference Engine",
         "Act as the lead AI engineer for my Virtual Try-On college project.\n"
         "OBJECTIVE: Create a standalone Python inference module engine.py that accepts single person + garment pairs.\n"
         "INSTRUCTIONS:\n"
         "1. Inspect Flow-Style-VTON-main/test/test.py, models/afwm.py, and models/networks.py.\n"
         "2. Load AFWM and ResUnetGenerator into GPU VRAM once on module import.\n"
         "3. Implement tryon_single_pair(person_pil, cloth_pil, mask_pil) -> PIL.Image.\n"
         "4. Preprocess inputs to [1, 3, 256, 192] and [1, 1, 256, 192] tensors normalized to [-1.0, 1.0].\n"
         "5. Execute warp and generator forward passes with torch.no_grad().\n"
         "6. Return composite try-on image as RGB PIL Image. DO NOT touch original repo files.\n"
         "SUCCESS: Single-pair execution returns a try-on image in <200ms on GPU."),

        ("PROMPT M4: Automated Preprocessing & Masking Pipeline",
         "Act as the lead AI engineer for my Virtual Try-On college project.\n"
         "OBJECTIVE: Build preprocessing.py to automate garment background removal and portrait resizing.\n"
         "INSTRUCTIONS:\n"
         "1. Person Pipeline: Correct EXIF orientation, crop/pad to 3:4 aspect ratio, bicubic resize to 256x192, normalize to [-1, 1].\n"
         "2. Garment Pipeline: Remove background via rembg (U^2-Net), convert alpha to binary silhouette mask, zero non-cloth pixels, resize to 256x192.\n"
         "3. Provide fast OpenCV thresholding fallback for clean white-background studio garments.\n"
         "4. Integrate preprocessing.py with engine.py.\n"
         "SUCCESS: Passing unconstrained smartphone photos produces required tensors and a valid try-on image."),

        ("PROMPT M5: FastAPI Service & ngrok Colab Tunnel",
         "Act as the lead software architect for my Virtual Try-On college project.\n"
         "OBJECTIVE: Wrap engine and preprocessing into a FastAPI microservice in Colab exposed via ngrok.\n"
         "INSTRUCTIONS:\n"
         "1. Create server.py using FastAPI and Uvicorn.\n"
         "2. Endpoints: GET /health (GPU status, VRAM) and POST /api/v1/tryon (multipart form with person and garment files, returns PNG bytes).\n"
         "3. Integrate pyngrok to establish a secure public HTTPS tunnel to port 8000.\n"
         "4. Implement warm-up inference on startup to eliminate cold-start latency.\n"
         "SUCCESS: Public ngrok URL returns generated try-on image in response to curl POST within 1.5 seconds."),

        ("PROMPT M6: MongoDB Connection & Mongoose Data Models",
         "Act as the lead backend engineer for my Virtual Try-On college project.\n"
         "OBJECTIVE: Setup MongoDB connection and Mongoose data models in /backend.\n"
         "INSTRUCTIONS:\n"
         "1. Install mongoose and dotenv in /backend.\n"
         "2. Create db.js to handle connection to MongoDB (using process.env.MONGODB_URI).\n"
         "3. Create models/Garment.js: name, category, imageUrl, maskUrl, tags, inStock, createdAt.\n"
         "4. Create models/TryOnHistory.js: sessionId, personImageUrl, garmentId, resultImageUrl, latencyMs, status, createdAt.\n"
         "5. Create scripts/seedGarments.js to populate database with 8 sample garments across categories.\n"
         "SUCCESS: MongoDB connects cleanly and seed script populates sample garments successfully."),

        ("PROMPT M7: Node.js / Express API Gateway",
         "Act as the lead backend engineer for my Virtual Try-On college project.\n"
         "OBJECTIVE: Build the Express API Gateway in /backend.\n"
         "INSTRUCTIONS:\n"
         "1. Initialize Express app with CORS, dotenv, and Multer for multipart form uploads.\n"
         "2. Configure AI_SERVICE_URL in .env to point to the Colab ngrok tunnel.\n"
         "3. Routes: GET /api/health (checks gateway + Colab status), GET /api/garments (fetches from MongoDB), POST /api/tryon (receives person upload + garment, proxies to Colab, logs result in MongoDB).\n"
         "4. Ensure temporary upload files are cleaned up after inference.\n"
         "SUCCESS: Postman POST to http://localhost:5000/api/tryon returns generated image and logs entry in MongoDB."),

        ("PROMPT M8: React (Vite) Web Application",
         "Act as the lead frontend engineer for my Virtual Try-On college project.\n"
         "OBJECTIVE: Build the React web frontend in /frontend using Vite and Tailwind CSS.\n"
         "INSTRUCTIONS:\n"
         "1. Scaffold Vite + React application with Tailwind CSS and Lucide React.\n"
         "2. Components: Navbar (title, status badge), PersonUpload (drag-drop, preview), GarmentSelector (MongoDB catalog grid + custom upload tab), ActionButton (Try On), LoadingOverlay (progress spinner), ResultViewer (Before/After comparison slider, download button).\n"
         "3. Connect API calls to Node.js backend (http://localhost:5000/api).\n"
         "SUCCESS: Web app runs on port 5173 with complete interactive state management and visual previews."),

        ("PROMPT M9: End-to-End System Integration & History",
         "Act as the lead full-stack engineer for my Virtual Try-On college project.\n"
         "OBJECTIVE: Integrate React frontend, Node backend, MongoDB, and Colab AI service.\n"
         "INSTRUCTIONS:\n"
         "1. Wire Try-On button to send multipart POST request through Node to Colab.\n"
         "2. Display synthesized result image on the Before/After comparison canvas.\n"
         "3. Add a Recent Try-On History drawer in the UI that fetches records from GET /api/history.\n"
         "4. Display toast notifications for success and clear error messages on failure.\n"
         "SUCCESS: Complete roundtrip: upload in browser -> GPU inference -> MongoDB log -> screen render in <2s."),

        ("PROMPT M10: System Hardening & Validation Guardrails",
         "Act as the lead QA engineer for my Virtual Try-On college project.\n"
         "OBJECTIVE: Implement error guardrails across frontend and backend.\n"
         "INSTRUCTIONS:\n"
         "1. Client-side guards: validate file format (JPEG/PNG only) and size cap (<10MB).\n"
         "2. Backend guards: Multer error handling, 30-second timeout threshold for Colab requests.\n"
         "3. Disconnect handling: if Colab tunnel is unreachable, show clear banner instructing user to start Colab GPU.\n"
         "SUCCESS: App handles oversized files, wrong formats, and network disconnections gracefully without crashing."),

        ("PROMPT M11: Performance Benchmarking",
         "Act as the lead AI researcher for my Virtual Try-On college project.\n"
         "OBJECTIVE: Benchmark the complete virtual try-on system across 20 test pairs.\n"
         "INSTRUCTIONS:\n"
         "1. Write benchmark script testing 20 diverse person + garment combinations.\n"
         "2. Record: rembg preprocessing latency (ms), warping latency (ms), generator latency (ms), total roundtrip time (ms).\n"
         "3. Generate summary markdown table in docs/benchmarks.md with averages and percentiles.\n"
         "SUCCESS: Comprehensive benchmark report with empirical latency and success rates generated."),

        ("PROMPT M12: Deployment & Final Verification",
         "Act as the lead release engineer for my Virtual Try-On college project.\n"
         "OBJECTIVE: Finalize project package and verify demonstration readiness.\n"
         "INSTRUCTIONS:\n"
         "1. Verify npm run dev starts both backend and frontend cleanly.\n"
         "2. Ensure MongoDB Atlas connection string is documented in backend/.env.example.\n"
         "3. Document 3-step startup instructions in root README.md.\n"
         "SUCCESS: Flawless end-to-end execution ready for final project demonstration.")
    ]

    for p_title, p_content in prompts:
        pr_block = []
        pr_block.append(Paragraph(f"<b>{p_title}</b>", h2_style))
        prompt_table_data = [[Paragraph(p_content.replace('\n', '<br/>'), code_style)]]
        t_prompt = Table(prompt_table_data, colWidths=[532])
        t_prompt.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#F1F5F9")),
            ('BOX', (0, 0), (-1, -1), 0.75, colors.HexColor("#CBD5E1")),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ]))
        pr_block.append(t_prompt)
        pr_block.append(Spacer(1, 4))
        story.append(KeepTogether(pr_block))

    story.append(Spacer(1, 10))

    # Tracking Checklist
    story.append(Paragraph("5. Milestone Execution Checklist", h1_style))
    checklist_data = [
        [Paragraph("Status", table_header_style), Paragraph("Milestone", table_header_style), Paragraph("Deliverable / Goal", table_header_style)],
        [Paragraph("[ ] M0", table_cell_bold), Paragraph("Workspace Architecture", table_cell_style), Paragraph("Clean folder layout (/ai_service, /backend, /frontend, /docs).", table_cell_style)],
        [Paragraph("[ ] M1", table_cell_bold), Paragraph("Colab GPU Environment", table_cell_style), Paragraph("T4 GPU verified, PyTorch/CUDA active, repo cloned.", table_cell_style)],
        [Paragraph("[ ] M2", table_cell_bold), Paragraph("Checkpoints & Benchmark", table_cell_style), Paragraph("PFAFN weights downloaded; official test.py runs with 0 errors.", table_cell_style)],
        [Paragraph("[ ] M3", table_cell_bold), Paragraph("Single-Pair Engine", table_cell_style), Paragraph("engine.py executes single pair in <150ms on GPU.", table_cell_style)],
        [Paragraph("[ ] M4", table_cell_bold), Paragraph("Automated Preprocessing", table_cell_style), Paragraph("rembg background removal and 256x192 resizing pipeline.", table_cell_style)],
        [Paragraph("[ ] M5", table_cell_bold), Paragraph("FastAPI & ngrok Tunnel", table_cell_style), Paragraph("Public HTTPS API running in Colab returning PNG try-on stream.", table_cell_style)],
        [Paragraph("[ ] M6", table_cell_bold), Paragraph("MongoDB Setup & Schemas", table_cell_style), Paragraph("Mongoose Garment and TryOnHistory schemas; seed data loaded.", table_cell_style)],
        [Paragraph("[ ] M7", table_cell_bold), Paragraph("Node.js Express Gateway", table_cell_style), Paragraph("Express API gateway proxying try-on requests to Colab.", table_cell_style)],
        [Paragraph("[ ] M8", table_cell_bold), Paragraph("React (Vite) Frontend", table_cell_style), Paragraph("UI with upload zone, catalog grid, Before/After slider.", table_cell_style)],
        [Paragraph("[ ] M9", table_cell_bold), Paragraph("End-to-End Integration", table_cell_style), Paragraph("Full roundtrip: Upload -> Node -> MongoDB -> GPU -> UI display.", table_cell_style)],
        [Paragraph("[ ] M10", table_cell_bold), Paragraph("Hardening & Error Guards", table_cell_style), Paragraph("File size guards, timeout handling, Colab disconnect alerts.", table_cell_style)],
        [Paragraph("[ ] M11", table_cell_bold), Paragraph("Performance Benchmarking", table_cell_style), Paragraph("Latency metrics recorded across 20 test pairs in docs/.", table_cell_style)],
        [Paragraph("[ ] M12", table_cell_bold), Paragraph("Final Verification", table_cell_style), Paragraph("One-command system startup; live demonstration verified.", table_cell_style)]
    ]
    t_check = Table(checklist_data, colWidths=[65, 160, 307])
    t_check.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), primary_color),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, card_bg]),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(t_check)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[+] Successfully generated {filename}")

if __name__ == "__main__":
    build_pdf()
