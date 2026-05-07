# PRAHARI — AI Tender Intelligence Platform

> **Proactive Requisition Audit & Honest AI for Righteous Integrity**

[![CI](https://github.com/your-org/prahari/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/prahari/actions)
[![Python](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-blue.svg)](https://www.typescriptlang.org/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-orange.svg)](https://deepmind.google/technologies/gemini/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Built for Smart India Hackathon 2024 | Ministry of Home Affairs | Problem Statement PS-1571**

PRAHARI is a production-ready AI platform that replaces 3–6 months of manual CRPF tender evaluation with a 9-stage AI pipeline delivering auditable verdicts in minutes. No bidder is automatically disqualified unless the AI is ≥90% confident on a mandatory criterion — everything borderline goes to a human review queue.

---

## The 9-Stage Pipeline

| Stage | What happens |
|-------|-------------|
| 1 — Criteria Extraction | Gemini reads the NIT/tender PDF and extracts all eligibility criteria with thresholds, weights, and mandatory/preferred flags |
| 2 — Market Benchmark | Extracted thresholds are validated against sector averages — suspiciously narrow thresholds (rigged tenders) are flagged |
| 3 — Document Authenticity | Each bidder document is scored for forgery risk: metadata anomalies, digital signature gaps, font embedding checks |
| 4 — Bidder Ingestion | GSTIN/PAN registered; PDF, DOCX, and scanned image uploads accepted; Indic language OCR via Gemini multimodal |
| 5 — Criterion Matching | Gemini evaluates each bidder against each criterion with evidence quote + PDF page → Eligible / Not_Eligible / Manual_Review |
| 6 — Collusion Detection | Cross-bidder NLP analysis: identical text, price coordination, IP/email overlaps, complementary bidding |
| 7 — Differential Privacy | Aggregate analytics with ε-DP mathematical privacy guarantees — statistics without leaking individual bid data |
| 8 — Human Review & Sign-Off | Officers override borderline verdicts with justification; digital sign-off locks the record in the audit trail |
| 9 — Evaluation Report | Full PDF report: criteria, verdicts matrix, authenticity scores, collusion alerts, override history, officer signature block |

---

## Key Features

- **Evidence-linked verdicts** — every AI verdict links to the exact quote and PDF page that drove the decision
- **In-browser PDF highlighting** — click any verdict to open the bidder's document with the evidence highlighted in amber
- **Immutable audit trail** — every event is SHA-256 hashed at write time; retroactive tampering is detectable
- **Non-disqualification guarantee** — below 90% confidence on mandatory criteria → automatic Manual_Review, never auto-reject
- **Bidder self-check portal** — vendors can check their own eligibility before submitting
- **Natural language Q&A** — ask questions like "Why is Frontier in Manual Review?" over the evaluation data
- **Indic language support** — Gemini multimodal OCR handles Hindi, Tamil, Urdu, Marathi scanned documents
- **Multi-format document ingestion** — PDF, DOCX, DOC, JPG, PNG, TIFF accepted

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| AI | Google Gemini 2.5 Flash (multimodal, File API) |
| Backend | FastAPI 0.104, Python 3.11 |
| Database | PostgreSQL (connection pooling via psycopg2) |
| File storage | Cloudinary CDN |
| Frontend | React 18, TypeScript, Tailwind CSS, Vite |
| PDF viewer | react-pdf with custom text renderer for highlighting |
| Auth | JWT (PyJWT HS256, 8-hour expiry) + bcrypt |
| Rate limiting | slowapi (per-IP, per-endpoint) |
| Containerisation | Docker multi-stage, non-root user, healthcheck |
| CI/CD | GitHub Actions (type check → pytest → Docker build) |

---

## Quick Start (Docker)

```bash
# 1. Clone and configure
cp .env.template .env
# Fill in: DATABASE_URL, GEMINI_API_KEY, CLOUDINARY_*, ADMIN_PASSWORD

# 2. Run
docker compose up --build

# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
# API docs: http://localhost:8000/docs
```

## Quick Start (local dev)

```bash
# Backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn backend.app:app --reload --port 8000

# Frontend (separate terminal)
cd frontend && npm install && npm run dev
```

---

## Demo Scenario

Ready-made DOCX files are in `sample_data/`. Run the generator once:

```bash
python sample_data/generate_demo_docx.py
```

Then follow `sample_data/README_DEMO.md` for a 10-minute end-to-end walkthrough with three bidders that produce Eligible, Manual_Review, and Not_Eligible outcomes respectively.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `GEMINI_API_KEY` | Yes | Google AI Studio API key |
| `CLOUDINARY_CLOUD_NAME` | Yes | Cloudinary cloud name |
| `CLOUDINARY_API_KEY` | Yes | Cloudinary API key |
| `CLOUDINARY_API_SECRET` | Yes | Cloudinary API secret |
| `ADMIN_PASSWORD` | Yes | Bcrypt-hashed admin password |
| `JWT_SECRET` | No | Auto-generated if not set |

---

## Running Tests

```bash
pytest tests/ -v
```

Tests cover: JWT encode/decode/expiry/tamper, bcrypt hashing, document type acceptance, PDF text highlighting logic.

---

## Project Structure

```
backend/
  app.py                 — 72 API endpoints, JWT auth, rate limiting
  gemini_client.py       — 9-stage AI pipeline functions
  db.py                  — PostgreSQL ORM (projects, bidders, verdicts, audit trail, QA sessions)
  document_converter.py  — DOCX/image/PDF normalisation for Gemini
  vendor_lookup.py       — Cross-tender vendor history

frontend/src/
  pages/EvaluationBoard.tsx    — Heatmap, collusion, audit, analytics, Q&A, sign-off
  pages/BidderManagement.tsx   — Bidder registration + document upload
  pages/ReviewQueue.tsx        — Human override queue
  pages/SelfCheck.tsx          — Bidder pre-submission portal
  components/PDFViewerModal.tsx — In-browser PDF viewer with evidence highlighting

tests/
  test_auth.py                 — JWT + bcrypt
  test_document_types.py       — Document acceptance and conversion
  test_pdf_highlight_logic.py  — norm() and overlapScore() specification

sample_data/
  generate_demo_docx.py        — Generate 4 demo DOCX files
  README_DEMO.md               — 10-minute demo walkthrough
```

---

**Built with dedication for CRPF AI Procurement — Ministry of Home Affairs**
