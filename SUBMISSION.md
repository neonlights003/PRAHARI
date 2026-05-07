# PRAHARI — Submission Fields
### Copy-paste ready. One section per field.

---

## 1. TITLE

```
PRAHARI — AI-Powered Tender Intelligence Platform for CRPF Procurement
```

---

## 2. DESCRIPTION

```
PRAHARI (Proactive Requisition Audit & Honest AI for Righteous Integrity) is a 
full-stack AI platform that transforms CRPF tender evaluation from a months-long 
manual process into an auditable, bias-resistant pipeline that completes in under 
10 minutes.

The system runs a 9-stage pipeline: it reads the NIT/tender document and extracts 
all eligibility criteria using Google Gemini 2.5 Flash multimodal AI; benchmarks 
thresholds against market data to detect rigged tenders; scores each bidder's 
uploaded documents (PDF, DOCX, scanned images, Indic scripts) for authenticity; 
evaluates every criterion with confidence scores; runs cross-bidder collusion 
detection; applies differential privacy (ε-DP) to aggregate analytics; routes 
borderline cases to a human review queue; and generates a SHA-256 tamper-proof 
PDF audit report with officer digital sign-off.

Core guarantee: no bidder is automatically disqualified unless the AI is ≥90% 
confident AND the criterion is mandatory — everything below that threshold goes 
to a human officer. The system supports three roles: Procurement Officers 
(evaluation + sign-off), Auditors (immutable event trail), and Bidders 
(pre-submission self-check portal). Built with FastAPI, PostgreSQL, React 18 + 
TypeScript, Docker, and GitHub Actions CI.
```

---

## 3. PROJECT SNAPSHOTS

> **You need to take these screenshots yourself** from the running app.
> Priority screens to capture (use `docker compose up` or your live URL):

1. **Landing page** — DPRLandingPage with the PRAHARI hero section + AI chat
2. **Evaluation Board — Heatmap tab** — the verdict matrix with ✅ ⚠️ ❌ cells
3. **PDF Viewer** — a verdict cell clicked, text highlighted in the PDF
4. **Collusion Detection tab** — showing the cross-bidder analysis results
5. **Analytics tab** — DP-protected charts
6. **Q&A Assistant tab** — a question answered in natural language
7. **Audit Trail tab** — the SHA-256 hashed event log
8. **Officer Sign-Off modal** — the sign-off confirmation dialog
9. **PDF Report download** — the generated evaluation report (open the PDF)
10. **Bidder Self-Check page** — `/self-check` route

> Aim for 5–8 screenshots. Crop to the interesting part of the UI.

---

## 4. VIDEO DEMO

> **You need to record this yourself** (Loom, OBS, or QuickTime → upload to YouTube/Drive).
> Follow the script in `sample_data/README_DEMO.md` for a 3-minute walkthrough.

**Recommended structure (3 min):**
- 0:00 – 0:20 → Landing page intro, explain the problem in one sentence
- 0:20 – 0:50 → Upload `tender_nit_crpf_ppe_2024.docx`, watch criteria extract live
- 0:50 – 1:30 → Register Kavach Armour + Frontier Defence, upload their DOCX files, hit Evaluate All
- 1:30 – 2:00 → Click a verdict cell → PDF opens, text highlighted (the wow moment)
- 2:00 – 2:20 → Run Collusion Detection → show alerts
- 2:20 – 2:40 → Ask a Q&A question: "Why is Frontier in Manual Review?"
- 2:40 – 3:00 → Officer Sign-Off → Download PDF Report

---

## 5. PPT / PRESENTATION

> **Slidev presentation** at `presentation/slides.md`
>
> **To run it:**
> ```bash
> cd presentation
> npm install
> npm run dev       # opens browser at localhost:3030
> ```
>
> **To export to PDF:**
> ```bash
> npm run export    # outputs slides-export.pdf
> ```
>
> **To export to PPTX:**
> ```bash
> npm run export-pptx   # outputs slides-export.pptx
> ```
> (Slidev will prompt to install Playwright on first export run — say yes.)
>
> Upload `slides-export.pdf` or `slides-export.pptx` as the PPT field.

---

## 6. DEMO LINK

> **Fill in after deployment.**
>
> Backend → deploy using `render.yaml` (Render.com, free tier):
> ```
> https://prahari-backend.onrender.com
> ```
>
> Frontend → deploy using `frontend/vercel.json` (Vercel, free):
> ```
> https://prahari.vercel.app
> ```
>
> If you haven't deployed yet, for the demo link field write:
> ```
> Live demo: [your-vercel-url] | Backend API: [your-render-url]/health
> ```
>
> If running locally for the demo, use:
> ```
> http://localhost:5173  (run: docker compose up)
> ```

---

## 7. REPO URL

> Push to GitHub first, then paste the URL here.
>
> ```bash
> git init
> git add .
> git commit -m "PRAHARI: AI-powered tender intelligence platform for CRPF"
> git remote add origin https://github.com/YOUR_USERNAME/prahari.git
> git push -u origin main
> ```
>
> Then the repo URL is:
> ```
> https://github.com/YOUR_USERNAME/prahari
> ```

---

## 8. SOURCE CODE (max 50 MB)

```
File: prahari_submission.zip   (location: project root)
Size: ~520 KB
```

**What's included:**
- `backend/` — FastAPI app, Gemini client, DB layer, report generator (full source)
- `frontend/src/` — React + TypeScript UI (all components, pages, API client)
- `tests/` — pytest test suite (auth, document types, PDF highlight logic)
- `sample_data/` — 4 demo DOCX files + walkthrough guide
- `presentation/slides.md` — Slidev pitch deck
- `Dockerfile` + `docker-compose.yml` + `render.yaml` + `vercel.json`
- `.github/workflows/ci.yml` — GitHub Actions CI pipeline
- `README.md` — full technical documentation

**What's excluded** (regeneratable, not source):
- `venv/`, `node_modules/` — install with `pip install -r requirements.txt` / `npm install`
- `pgdata/` — database data directory
- `.env` — secrets (use `.env.template` as guide)
- `frontend/dist/` — build output (run `npm run build`)

---

## 9. INSTRUCTIONS TO RUN

```
PRAHARI — Local Setup Instructions
===================================

Prerequisites
-------------
- Docker + Docker Compose  (recommended — zero config)
- OR: Python 3.11+, Node.js 18+, PostgreSQL 14+

Option A — Docker (recommended, ~3 minutes)
-------------------------------------------
1. Clone / unzip the source code
2. Copy environment template:
      cp .env.template .env
3. Fill in .env with your keys:
      DATABASE_URL=postgresql://postgres:postgres@db:5432/prahari
      GEMINI_API_KEY=<your Google AI Studio key>
      JWT_SECRET=<any random string, min 32 chars>
      CLOUDINARY_CLOUD_NAME=<your Cloudinary name>
      CLOUDINARY_API_KEY=<your Cloudinary key>
      CLOUDINARY_API_SECRET=<your Cloudinary secret>
4. Start everything:
      docker compose up --build
5. Open http://localhost:5173 in your browser
6. Create an admin account at http://localhost:5173/admin-login

Option B — Manual (backend + frontend separately)
--------------------------------------------------
Backend:
  cd <project-root>
  python -m venv venv && source venv/bin/activate
  pip install -r requirements.txt
  cp .env.template .env  # fill in values
  uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload

Frontend:
  cd frontend
  npm install
  npm run dev
  # opens at http://localhost:5173

Database:
  # Ensure PostgreSQL is running on port 5432
  # Tables are auto-created on first backend startup

Running Tests:
  pytest tests/ -v

Demo Data (optional):
  pip install python-docx
  python sample_data/generate_demo_docx.py
  # generates 4 DOCX files in sample_data/
  # follow sample_data/README_DEMO.md for the full demo walkthrough

API Keys Required:
  GEMINI_API_KEY  → https://aistudio.google.com/app/apikey  (free)
  CLOUDINARY      → https://cloudinary.com  (free tier, 25GB)
  JWT_SECRET      → any random string (openssl rand -hex 32)
```

---

## 10. CUSTOM ATTACHMENT

> Attach **one** of the following as the custom attachment:
>
> - `README.md` — comprehensive technical documentation (best for judges who want depth)
> - `sample_data/README_DEMO.md` — step-by-step 10-minute demo guide
> - `SCALABILITY_ISSUES.md` — honest engineering limitations with mitigations (shows maturity)
>
> **Recommended:** `README.md` — it has ASCII architecture diagrams, DB schema,
> 7 key engineering problems with code solutions, full API reference, and deployment guide.

---

## QUICK CHECKLIST

- [ ] Title — copy from Section 1
- [ ] Description — copy from Section 2
- [ ] Screenshots — take 5–8 from running app (see Section 3 list)
- [ ] Video — record 3-min demo following `sample_data/README_DEMO.md`
- [ ] PPT — export `presentation/slides.md` via `npm run export-pptx`
- [ ] Demo Link — deploy to Render + Vercel, or paste localhost URL
- [ ] Repo URL — push to GitHub, paste URL
- [ ] Source Code — upload `prahari_submission.zip` (520 KB, already in project root)
- [ ] Instructions to Run — copy from Section 9
- [ ] Custom Attachment — attach `README.md`
