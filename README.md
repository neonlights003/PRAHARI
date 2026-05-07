<div align="center">

# PRAHARI
### प्रहरी — The Guardian of Public Procurement

**Proactive Requisition Audit & Honest AI for Righteous Integrity**

*AI-Powered Tender Intelligence Platform for CRPF Procurement*

[![CI](https://github.com/neonlights003/PRAHARI/actions/workflows/ci.yml/badge.svg)](https://github.com/neonlights003/PRAHARI/actions)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Gemini](https://img.shields.io/badge/Gemini-2.5_Flash-FF6F00?logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white)](https://postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-multi--stage-2496ED?logo=docker&logoColor=white)](https://docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

**Smart India Hackathon 2024 · Ministry of Home Affairs · Problem Statement PS-1571**

[Live Demo](https://prahari-frontend.onrender.com) · [API Docs](https://prahari-backend.onrender.com/docs) · [Demo Walkthrough](sample_data/README_DEMO.md) · [Pitch Deck](PITCH_DECK.md)

</div>

---

## The Problem We Are Solving

India's government procurement machinery is broken in ways that cost lives — not just money.

```
The status quo:

  Tender Published
       │
       ▼
  ┌──────────────────────────────────────────────┐
  │  5-8 evaluators manually read                │
  │  100s of pages per bidder                    │  3–6 MONTHS
  │                                              │  200–400 hrs
  │  No standard scoring → subjective verdicts  │  per tender
  │  No cross-bidder analysis → collusion missed │
  │  No document verification → forgeries pass  │
  │  No audit trail → decisions challenged       │
  └──────────────────────────────────────────────┘
       │
       ▼
  Equipment delayed → CRPF personnel go without
  bullet-resistant jackets, body armour, critical gear
```

### Scale of the Crisis

| Metric | Reality |
|--------|---------|
| India's annual government procurement | **₹40 lakh crore (≈ 20% of GDP)** |
| CRPF tenders per year | **500+** |
| Average evaluation time | **3–6 months, 200–400 evaluator-hours** |
| Criteria missed per evaluation (human error rate) | **8–12%** |
| Procurement fraud detected (CAG, last 5 years) | **₹3.5 lakh crore** |
| Procurement decisions challenged in court | **1 in 4** |
| Scanned Hindi/Tamil/Urdu PDFs that go unread | **Common in paramilitary tenders** |

### Root Causes

**1. Manual evaluation at scale is impossible**
A single large CRPF tender can have 50 bidders, each submitting a 100-page qualification dossier. That is 5,000 pages for one evaluator team. Human fatigue guarantees missed criteria.

**2. No standardised scoring → litigation bait**
Without a documented, reproducible scoring method, losing bidders challenge every major decision. 1 in 4 procurement decisions ends up in arbitration or court.

**3. Collusion goes undetected**
Bid-rigging (identical pricing, complementary bidding, shared vendors) is invisible to evaluators reading one file at a time. Cross-bidder analysis requires comparing all submissions simultaneously.

**4. Document forgery has no systematic check**
Forged CA certificates, fake completion certificates, and tampered ISO documents routinely pass manual review. There is no scalable authenticity scoring.

**5. No audit trail → no accountability**
Decisions made verbally or on paper cannot be reconstructed months later when an RTI query or CBI investigation arrives.

---

## Our Solution: PRAHARI

```
PRAHARI replaces the entire manual pipeline with a 9-stage AI system
that delivers verifiable, evidence-linked verdicts in under 10 minutes.

Core guarantee:
┌─────────────────────────────────────────────────────────────────┐
│  No bidder is automatically disqualified unless:                │
│    (a) the criterion is MANDATORY, AND                          │
│    (b) AI confidence is ≥ 90%                                   │
│                                                                 │
│  Everything below → Human Review queue.                         │
│  Officer makes final call. AI provides evidence.                │
└─────────────────────────────────────────────────────────────────┘
```

### Three Roles, One System

| Role | What PRAHARI gives them |
|------|------------------------|
| **Procurement Officer** | Instant eligibility verdicts with exact evidence quotes and PDF page links — decisions in minutes, not months |
| **Auditor / RTI Officer** | Immutable SHA-256 hashed audit trail — every decision is reproducible and tamper-detectable |
| **Bidder (Vendor)** | Pre-submission self-check portal — know your gaps *before* you submit, not after rejection |

---

## The 9-Stage Pipeline

```
  ┌──────────────────────────────────────────────────────────────────────┐
  │                    PRAHARI EVALUATION PIPELINE                       │
  └──────────────────────────────────────────────────────────────────────┘

  ┌─────────────┐
  │   NIT / RFP │  (PDF, DOCX, Scanned)
  │   Document  │
  └──────┬──────┘
         │
         ▼
  ╔══════════════════╗
  ║  STAGE 1         ║  extract_tender_criteria()
  ║  Criteria        ║  → Gemini reads tender document
  ║  Extraction      ║  → Extracts all criteria with:
  ╚══════╤═══════════╝    - criterion_id, name, description
         │               - threshold_value, threshold_text
         │               - mandatory (bool), weight (0-1)
         │               - category (Financial/Technical/Legal)
         ▼
  ╔══════════════════╗
  ║  STAGE 2         ║  enhance_benchmark_analysis()
  ║  Market          ║  → Validates thresholds against sector averages
  ║  Benchmark       ║  → Flags suspicious thresholds (rigged tender signal)
  ╚══════╤═══════════╝  → e.g. "Turnover ≥ ₹47.3 Cr" in a ₹25 Cr contract = 🚩
         │
  ┌──────┴──────┐
  │  Bidder     │  (PDF, DOCX, JPG, PNG, TIFF)
  │  Documents  │
  └──────┬──────┘
         │
         ▼
  ╔══════════════════╗
  ║  STAGE 3         ║  score_document_authenticity()
  ║  Document        ║  → Each bidder document scored for:
  ║  Authenticity    ║    - Metadata anomalies (creation date vs claim date)
  ╚══════╤═══════════╝    - Digital signature gaps
         │               - Font embedding irregularities
         │               - Scanned vs. digital inconsistencies
         ▼
  ╔══════════════════╗
  ║  STAGE 4         ║  prepare_for_gemini() via document_converter
  ║  Bidder          ║  → GSTIN / PAN registered in DB
  ║  Ingestion       ║  → PDF → Gemini File API (native multimodal)
  ╚══════╤═══════════╝  → DOCX → python-docx → text extraction → upload
         │             → Images → Gemini vision (OCR for scanned docs)
         │             → Indic scripts: Hindi, Tamil, Urdu, Marathi
         ▼
  ╔══════════════════╗
  ║  STAGE 5         ║  evaluate_bidder_criteria()
  ║  Criterion       ║  Per bidder × per criterion:
  ║  Matching        ║  → Deterministic pre-check (regex, pattern match)
  ╚══════╤═══════════╝  → Gemini LLM evaluation with structured JSON output
         │             → Verdict: Eligible | Not_Eligible | Manual_Review
         │             → Confidence score (0.0–1.0)
         │             → Evidence quote + PDF page number
         │             → Safety net: optional criteria NEVER → Not_Eligible
         ▼
  ╔══════════════════╗
  ║  STAGE 6         ║  detect_collusion_patterns()
  ║  Collusion       ║  Deterministic checks:
  ║  Detection       ║    - Identical/near-identical text blocks across submissions
  ╚══════╤═══════════╝    - Complementary bids (one always just above another)
         │               - Shared contact details, IP patterns
         │             Gemini LLM checks:
         │               - Strategic withdrawal patterns
         │               - Suspicious pricing coordination
         ▼
  ╔══════════════════╗
  ║  STAGE 7         ║  Differential Privacy analytics
  ║  DP Analytics    ║  → Laplace mechanism noise on aggregate stats
  ╚══════╤═══════════╝  → ε-DP budget tracked per project per query type
         │             → Statistics without leaking individual bid data
         ▼
  ╔══════════════════╗
  ║  STAGE 8         ║  Human review queue + officer sign-off
  ║  Human Review    ║  → Manual_Review verdicts routed to officer queue
  ║  & Sign-Off      ║  → Officer overrides with written justification
  ╚══════╤═══════════╝  → Digital sign-off locks evaluation record
         │             → All overrides SHA-256 hashed into audit trail
         ▼
  ╔══════════════════╗
  ║  STAGE 9         ║  generate_evaluation_report()
  ║  Audit Report    ║  WeasyPrint PDF containing:
  ╚══════════════════╝    - Criteria breakdown (mandatory / preferred)
                          - Full verdicts matrix with confidence scores
                          - Document authenticity scores per bidder
                          - Collusion alerts and disposition
                          - Human override log with justifications
                          - Immutable audit trail (last 50 events)
                          - Officer signature block (signed or pending)
```

---

## System Architecture

```
  ┌─────────────────────────────────────────────────────────────────┐
  │                         CLIENT TIER                             │
  │                                                                 │
  │   Browser (React 18 + TypeScript + Tailwind CSS + Vite)        │
  │                                                                 │
  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
  │   │ Landing Page │  │  Admin Panel │  │  Bidder Self-Check   │ │
  │   │ + AI Chat    │  │  (JWT-gated) │  │  Portal (public)     │ │
  │   └──────────────┘  └──────┬───────┘  └──────────────────────┘ │
  │                            │  JWT Bearer token                  │
  └────────────────────────────┼────────────────────────────────────┘
                               │  HTTPS / Vite proxy (dev)
  ┌────────────────────────────┼────────────────────────────────────┐
  │                       API TIER                                  │
  │                                                                 │
  │   FastAPI 0.104 · Python 3.11 · Uvicorn                        │
  │                                                                 │
  │   ┌────────────┐  ┌────────────┐  ┌──────────────────────────┐ │
  │   │  Auth      │  │  Rate      │  │  CORS Middleware          │ │
  │   │  (JWT)     │  │  Limiting  │  │  (configurable origins)  │ │
  │   │  bcrypt    │  │  (slowapi) │  └──────────────────────────┘ │
  │   └────────────┘  └────────────┘                               │
  │                                                                 │
  │   72 REST endpoints across 12 functional groups                │
  └──────────────┬──────────────────────┬──────────────────────────┘
                 │                      │
     ┌───────────┼──────────────────────┼─────────────────┐
     │           │                      │                  │
     ▼           ▼                      ▼                  ▼
  ┌──────────┐  ┌────────────────┐  ┌──────────┐  ┌──────────────┐
  │PostgreSQL│  │ Google Gemini  │  │Cloudinary│  │  WeasyPrint  │
  │   15     │  │  2.5 Flash     │  │   CDN    │  │  PDF Engine  │
  │          │  │  (File API +   │  │          │  │              │
  │ 13 tables│  │   multimodal)  │  │  signed  │  │  Jinja2      │
  │  + indexes│  │               │  │   URLs   │  │  templates   │
  └──────────┘  └────────────────┘  └──────────┘  └──────────────┘
```

### Data Flow: Bidder Evaluation Request

```
  Officer clicks "Evaluate All"
         │
         ▼
  POST /api/tenders/{id}/evaluate-all
         │
         ├─ Fetch all bidders from DB
         ├─ Fetch tender criteria from DB
         │
         ▼  for each bidder:
  ┌─────────────────────────────────────────────────────┐
  │  1. Load bidder documents from DB                   │
  │  2. Run deterministic pre-checks (GSTIN regex,      │
  │     turnover numeric extraction, date parsing)      │
  │  3. If pre-check conclusive → skip LLM call (fast)  │
  │  4. Build Gemini prompt with:                       │
  │     - System instruction (PRAHARI analyst role)     │
  │     - Tender criteria JSON                          │
  │     - Document file references (Gemini File API)    │
  │  5. Call Gemini 2.5 Flash (asyncio.to_thread)       │
  │  6. Parse structured JSON response:                 │
  │     { criterion_id, verdict, confidence,            │
  │       evidence_quote, evidence_page, reasoning }    │
  │  7. Apply safety nets:                              │
  │     - mandatory=false + Not_Eligible → Manual_Review│
  │     - confidence < 0.9 + mandatory → Manual_Review  │
  │  8. Write verdict rows to Postgres                  │
  │  9. Write audit event (SHA-256 hashed)              │
  └─────────────────────────────────────────────────────┘
         │
         ▼
  Return summary JSON to frontend
  Frontend re-renders heatmap with live verdicts
```

---

## Database Schema

```sql
-- Core procurement entity
projects
  id, name, state, scheme, sector, created_at
  comparison_result JSONB, compliance_weights JSONB
  signed_by TEXT, signed_at TIMESTAMP            -- Gap 5: officer sign-off

-- DPR / NIT documents (the tender itself)
dprs
  id, project_id → projects, filename, original_filename
  filepath, uploaded_file_ref (Gemini), upload_ts
  summary_json TEXT (extracted criteria), status, validation_flags

-- Bidder companies registered for a tender
bidders
  id, project_id → projects, company_name
  gstin, pan, contact_email, status, created_at

-- Individual documents submitted by a bidder
bidder_documents
  id, bidder_id → bidders, document_type, original_filename
  uploaded_file_ref (Gemini), cloudinary_url
  authenticity_score NUMERIC(4,3)               -- 0.0–1.0
  tamper_risk_level TEXT                        -- Low/Medium/High
  metadata_flags JSONB, language_detected

-- AI verdict per bidder per criterion
verdicts
  id, project_id → projects, bidder_id → bidders
  criterion_id TEXT, verdict TEXT               -- Eligible|Not_Eligible|Manual_Review
  confidence_score NUMERIC(4,3)
  extracted_value_text, threshold_value BIGINT
  evidence_doc_id → bidder_documents
  evidence_quote TEXT, evidence_page INTEGER
  reasoning TEXT, tamper_risk_score NUMERIC(4,3)
  human_override BOOLEAN                        -- officer-set
  override_verdict TEXT, override_justification TEXT
  override_by → users, override_at TIMESTAMP

-- Cross-bidder collusion flags
collusion_alerts
  id, project_id → projects
  alert_type TEXT, bidder_ids INTEGER[]
  description TEXT, confidence_score NUMERIC(4,3)
  officer_disposition TEXT                      -- pending/dismissed/confirmed
  disposition_notes, disposition_by → users, disposition_at

-- Immutable event log (tamper-detectable)
audit_events
  event_id UUID PRIMARY KEY
  event_type TEXT, project_id → projects, bidder_id → bidders
  criterion_id TEXT, payload_hash TEXT          -- SHA-256, set at write time
  model_version TEXT, confidence_score NUMERIC(4,3)
  language_detected TEXT, dp_epsilon NUMERIC(6,4)
  officer_id → users, created_at TIMESTAMP

-- User accounts (admin + client roles)
users
  id, email UNIQUE, password_hash (bcrypt)
  name, username, created_at

-- Persistent Q&A session history (Gap 6: replaced in-memory dict)
qa_sessions
  id, project_id INTEGER, role TEXT            -- 'user' | 'model'
  content TEXT, created_at TIMESTAMP
```

**13 tables · 8 foreign key relationships · 7 indexes for query performance**

---

## Key Problems & Engineering Solutions

### Problem 1: PDF text highlighting across multi-word spans

**The challenge:** react-pdf renders documents as individual text "items" — each word or phrase is a separate DOM element. A 10-word evidence quote like "annual turnover of INR 7.5 crore" may be split across 4–6 different items. Standard string matching fails.

**Our solution — `overlapScore()` with two-tier matching:**

```typescript
// frontend/src/components/PDFViewerModal.tsx

function norm(s: string): string {
  return s
    .toLowerCase()
    .replace(/[''""]/g, "'")       // curly quotes → straight
    .replace(/[\s\-–—]+/g, ' ')   // dashes / whitespace → single space
    .replace(/[^\w\s]/g, '')       // strip all other punctuation
    .trim()
}

function overlapScore(itemStr: string, quoteNorm: string): number {
  const nItem = norm(itemStr)
  if (!nItem || nItem.length < 3) return 0

  // Tier 1: Direct containment → score 1.0 (strong match)
  // Either the item is a substring of the quote, or vice versa
  if (quoteNorm.includes(nItem) || nItem.includes(quoteNorm)) return 1.0

  // Tier 2: Token overlap → score is fraction of significant words matched
  // "Significant" = more than 3 characters (filters out "of", "the", "an")
  const tokens = nItem.split(' ').filter(t => t.length > 3)
  if (tokens.length === 0) return 0
  const matched = tokens.filter(t => quoteNorm.includes(t))
  return matched.length / tokens.length
}

// In customTextRenderer:
// score >= 1.0 → amber solid highlight (strong match)
// score >= 0.6 → amber faint highlight (partial match)
// score < 0.6  → no highlight
```

**Why this works:** "INR 7.5 crore" as a text item scores 1.0 because it is contained in the normalised quote. "7.5" alone scores 0.0 (too short). "annual turnover" scores 1.0 because it is contained in the quote. This correctly handles the fragmented text layer.

**Scanned PDF fallback:** If the PDF has no text layer (scanned), `customTextRenderer` is never called, `highlightCount` stays 0, and the header shows "scanned page — highlights unavailable". No crash, clean UX.

---

### Problem 2: Bidder documents arrive in many formats

**The challenge:** Bidders submit CA certificates as scanned JPEGs, completion certificates as Word documents, and GST certificates as native PDFs. The system must handle all formats uniformly for Gemini.

**Our solution — `document_converter.py` as a pre-processing gate:**

```
  Uploaded file
       │
       ├─ .pdf  ──────────────────────────────► Gemini File API (native multimodal)
       │                                        handles digital + scanned PDFs
       │
       ├─ .docx / .doc ──► python-docx         ► Extracts paragraphs + table cells
       │                   text extraction     ► Writes .txt with [Extracted from: X]
       │                                       ► Uploads as text/plain to Gemini
       │
       ├─ .jpg / .png / .webp / .tiff ─────────► Gemini File API (vision)
       │                                        Gemini OCR reads image directly
       │
       └─ anything else ──────────────────────► HTTP 400 "Unsupported format"
                                                Accepted: pdf docx doc jpg jpeg
                                                          png webp tiff tif
```

**Indic language handling:** The Gemini prompt includes explicit instructions to handle Hindi, Tamil, Urdu, and Marathi scripts in scanned documents, with confidence calibration for low-quality scans.

---

### Problem 3: Optional criteria must never disqualify a bidder

**The challenge:** AI models can misclassify an optional criterion failure (e.g. "no ISO certificate") as a disqualification. In government procurement this is legally and procedurally wrong.

**Our solution — mandatory safety net in `evaluate_bidder_criteria()`:**

```python
# backend/gemini_client.py — applied after every AI verdict

# Build mandatory lookup from criteria list
crit_mandatory_map = {c["criterion_id"]: c.get("mandatory", True) for c in criteria}

for v in verdicts:
    is_mandatory = crit_mandatory_map.get(v["criterion_id"], True)
    
    # Safety net 1: optional criterion → never Not_Eligible
    if not is_mandatory and v["verdict"] == "Not_Eligible":
        v["verdict"] = "Manual_Review"
        v["reasoning"] += " [System: Optional criterion — auto-upgraded to Manual_Review]"
    
    # Safety net 2: low confidence on mandatory → Manual_Review
    if is_mandatory and v["confidence_score"] < 0.90 and v["verdict"] == "Not_Eligible":
        v["verdict"] = "Manual_Review"
        v["reasoning"] += " [System: Confidence below 90% threshold — routed to human review]"
```

**Final status calculation:** A bidder is `not_eligible` only if at least one *mandatory* criterion is `Not_Eligible` with ≥90% confidence. All other combinations produce `manual_review_required` or `evaluated` (eligible).

---

### Problem 4: QA sessions lost on server restart (in-memory state)

**The challenge:** Multi-turn Q&A chat history was stored in `_evaluation_qa_sessions: Dict[int, dict]` — a Python dict in process memory. Server restart = lost conversation. Multiple workers = split sessions.

**Our solution — Postgres-persisted history with fresh context injection:**

```python
# backend/gemini_client.py — answer_evaluation_question()

def _run(q: str) -> str:
    # 1. Load all prior turns from Postgres
    history_rows = _db.get_qa_history(project_id)
    
    # 2. Build Gemini history: always inject fresh context preamble
    #    (so model sees current evaluation state, not stale snapshot)
    preamble_user  = {"role": "user",  "parts": [f"Context:\n\n{context}"]}
    preamble_model = {"role": "model", "parts": ["Understood. Ready to answer."]}
    prior = [{"role": r["role"], "parts": [r["content"]]} for r in history_rows]
    
    # 3. Start stateless Gemini chat with full reconstructed history
    chat = model.start_chat(history=[preamble_user, preamble_model] + prior)
    
    # 4. Send new question, get answer
    answer = chat.send_message(q).text
    
    # 5. Persist both sides of the exchange
    _db.append_qa_messages(project_id, q, answer)
    return answer
```

**Why this design:** The context is rebuilt from *current DB state* on every request — if a new evaluation runs mid-conversation, the next Q&A turn sees the updated verdicts. The chat object itself is created and discarded per-request (stateless), but the history is durable in Postgres.

---

### Problem 5: Auth token has no expiry check on the frontend

**The challenge:** The original system used `login()` with no token — a boolean flag in localStorage. After JWT was added, existing tokens persisted in localStorage with no expiry validation.

**Our solution — client-side JWT exp claim check without an npm package:**

```typescript
// frontend/src/contexts/RoleContext.tsx

function parseJwtExp(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return typeof payload.exp === 'number' ? payload.exp : null
  } catch {
    return null
  }
}

function isTokenValid(token: string): boolean {
  const exp = parseJwtExp(token)
  if (!exp) return false
  return Date.now() / 1000 < exp   // compare Unix timestamps
}

// On app init:
const stored = localStorage.getItem('adminToken')
if (stored && isTokenValid(stored)) {
  setIsAdmin(true)   // restore session
} else {
  localStorage.removeItem('adminToken')   // clear expired/invalid token
}
```

**Server-side verification** is also done on the sign-off endpoint (the most sensitive action) using `pyjwt.decode()` with the same secret.

---

### Problem 6: Threshold rigging — tenders written to favour specific vendors

**The challenge:** Corrupt procurement officials can write eligibility thresholds that only one vendor can meet. "Minimum turnover of exactly ₹47.3 crore" in a ₹25 crore contract is a red flag — but a manual evaluator would never catch it.

**Our solution — Stage 2 Market Benchmark validation:**

```
  Extracted criteria
         │
         ▼
  enhance_benchmark_analysis()
         │
         ├─ Threshold unusually high for contract value? → 🚩 flag
         ├─ Threshold suspiciously precise (decimal places)? → 🚩 flag
         ├─ Experience requirement matches exactly one known vendor? → 🚩 flag
         ├─ Timeline impossible except for incumbent? → 🚩 flag
         └─ Criteria weight distribution anomalous? → 🚩 flag
         │
         ▼
  Returns benchmark_flags[] with reasoning
  Stored in DPR summary, visible to officer before evaluation begins
```

**This runs before any bidder is registered** — it audits the procurement officer's own tender document. Officers who receive a benchmark flag must acknowledge it before proceeding.

---

### Problem 7: Collusion undetectable from single-document review

**The challenge:** Bid rigging requires comparing ALL submissions simultaneously — something a manual process never does (evaluators see one bid at a time).

**Our solution — two-layer collusion detection in Stage 6:**

```
  All bidder documents for a tender
         │
         ▼  Layer 1: Deterministic checks (fast, rule-based)
  ┌─────────────────────────────────────────────────────────┐
  │  • Text similarity: Levenshtein / cosine on key sections│
  │  • Identical paragraphs hash comparison                 │
  │  • Shared contact email / phone / GSTIN prefix          │
  │  • Pricing: one bid is always 3-5% above another        │
  │  • Complementary bids: X bids high, Y bids low          │
  └──────────────────────┬──────────────────────────────────┘
                         │ Deterministic flags passed to LLM
                         ▼  Layer 2: Gemini LLM analysis (context-aware)
  ┌─────────────────────────────────────────────────────────┐
  │  • Strategic withdrawal patterns                        │
  │  • Cover bidding (deliberate losing bids)               │
  │  • Market allocation signals                            │
  │  • Coordinated document preparation evidence            │
  └──────────────────────┬──────────────────────────────────┘
                         │
                         ▼
  collusion_alerts[] with:
    - alert_type, bidder_ids[]
    - confidence_score, description
    - officer_disposition (pending → confirmed/dismissed)
```

---

## API Reference

### Authentication

```
POST /api/admin/login          Login → JWT token (8-hour, HS256)
POST /api/user/register        Register client account (bcrypt)
POST /api/user/login           Client login
```

Rate limits: admin login = **5/min**, client login = **5/min**

### PRAHARI Tender Pipeline

```
POST /api/tenders/{id}/extract-criteria    Stage 1: extract criteria from NIT PDF
POST /api/tenders/{id}/benchmark           Stage 2: market benchmark validation
POST /api/tenders/{id}/sign-off            Stage 8: officer digital sign-off (JWT required)
GET  /api/tenders/{id}/report              Stage 9: download full evaluation PDF
```

### Bidder Management

```
POST   /api/tenders/{id}/bidders               Register bidder
GET    /api/tenders/{id}/bidders               List all bidders
GET    /api/bidders/{id}                       Get single bidder
DELETE /api/bidders/{id}                       Remove bidder
POST   /api/bidders/{id}/documents             Upload document (PDF/DOCX/image)
GET    /api/bidders/{id}/documents             List bidder documents
```

### Evaluation

```
POST /api/tenders/{id}/bidders/{bid}/evaluate  Evaluate single bidder (Stage 5)
POST /api/tenders/{id}/evaluate-all            Evaluate all bidders
GET  /api/tenders/{id}/verdicts                Get full verdicts matrix
PUT  /api/verdicts/{id}/override               Officer override (JWT required)
GET  /api/tenders/{id}/criteria                Get extracted criteria
```

### Collusion & Integrity

```
POST /api/tenders/{id}/detect-collusion        Stage 6: run collusion analysis
GET  /api/tenders/{id}/collusion-alerts        List collusion alerts
PUT  /api/tenders/{id}/collusion-alerts/{id}/resolve  Officer disposition
```

### Analytics & Intelligence

```
GET  /api/tenders/{id}/analytics       Stage 7: DP aggregate statistics
GET  /api/tenders/{id}/audit-trail     Full immutable event log
POST /api/vendors/lookup               Cross-tender vendor history check
GET  /api/tenders/{id}/vendor-history  Vendor participation history
```

### Q&A & Self-Check

```
POST   /api/tenders/{id}/qa    Natural language Q&A over evaluation data
DELETE /api/tenders/{id}/qa    Clear Q&A session history
POST   /api/self-check/{id}    Bidder pre-submission eligibility check
POST   /api/landing-chat       Public AI assistant on landing page
```

### Compliance Weights

```
GET  /projects/{id}/compliance-weights        Get criteria weights
PUT  /projects/{id}/compliance-weights        Update weights (custom scoring)
POST /projects/{id}/compliance-weights/reset  Reset to defaults
```

**Total: 75+ endpoints across 12 functional groups**

---

## Frontend Architecture

```
frontend/src/
├── pages/
│   ├── DPRLandingPage.tsx      Landing page with dark mode, AI chat widget
│   ├── EvaluationBoard.tsx     Core evaluation UI (7 tabs, 1,200+ lines)
│   │   ├── ConfidenceHeatmap   Bidder × Criterion matrix with colour coding
│   │   ├── CollusionPanel      Alert cards with disposition controls
│   │   ├── AuditTrailPanel     Chronological event log
│   │   ├── VendorHistoryPanel  Cross-tender vendor intelligence
│   │   ├── AnalyticsPanel      ε-DP aggregate charts
│   │   ├── EvaluationQAPanel   Multi-turn Q&A chat
│   │   └── CriteriaWeightsPanel Slider-based weight adjustment
│   ├── BidderManagement.tsx    Bidder registration + document upload
│   ├── ReviewQueue.tsx         Human review queue for Manual_Review verdicts
│   ├── SelfCheck.tsx           Bidder pre-submission portal (public)
│   ├── DocumentDetail.tsx      DPR analysis detail view
│   ├── ProjectDetail.tsx       Project overview + comparison
│   └── AdminLogin.tsx          JWT-based admin authentication
├── components/
│   ├── PDFViewerModal.tsx      In-browser PDF viewer with text highlighting
│   │   ├── norm()              Text normaliser (lowercase, dashes, punctuation)
│   │   └── overlapScore()      Two-tier match scoring for highlight injection
│   ├── AuthModal.tsx           Auth prompt for protected actions
│   ├── Header.tsx              Navigation with language + theme toggle
│   ├── LanguageDropdown.tsx    English / हिन्दी switcher
│   └── ChatMessageFormatter.tsx Markdown + citation rendering for Q&A
├── contexts/
│   ├── RoleContext.tsx         JWT parse + expiry check + admin state
│   └── LanguageContext.tsx     i18n context with Hindi translations
└── lib/
    ├── api.ts                  Typed API client (75+ methods, JWT headers)
    └── i18n.ts                 Translation strings (English + Hindi)
```

### Verdict Display — Hindi Bilingual Labels

Every verdict cell in the heatmap shows both English and Hindi labels, making the interface accessible to CRPF officers regardless of language preference:

```
┌─────────────────────────┐
│ ✓ Eligible  योग्य       │  ← amber confidence bar
│ ████████████░░ 94%      │
└─────────────────────────┘

┌─────────────────────────┐
│ ✗ Not Eligible  अयोग्य  │
│ ██████████████░░ 91%    │
└─────────────────────────┘

┌─────────────────────────┐
│ ⏱ Manual Review  समीक्षा│
│ ██████████░░░░░░ 78%    │
└─────────────────────────┘
```

---

## Security Design

```
  Request arrives
       │
       ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  CORS Middleware                                            │
  │  Only configured origins accepted                          │
  └──────────────────────────┬──────────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  Rate Limiting (slowapi, per-IP)                            │
  │  /api/admin/login     → 5 req/min                          │
  │  extract-criteria     → 10 req/min                         │
  │  evaluate-all         → 5 req/min                          │
  │  detect-collusion     → 5 req/min                          │
  │  /api/tenders/*/qa    → 30 req/min                         │
  │  landing-chat         → 20 req/min                         │
  └──────────────────────────┬──────────────────────────────────┘
                             │ (JWT-protected endpoints only)
                             ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  JWT Verification (PyJWT, HS256)                            │
  │  Authorization: Bearer <token>                              │
  │  → decode with JWT_SECRET                                   │
  │  → check exp claim                                          │
  │  → 401 on invalid / expired                                 │
  └──────────────────────────┬──────────────────────────────────┘
                             │
                             ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  Business Logic                                             │
  │  Passwords: bcrypt (cost factor 12)                         │
  │  Audit events: SHA-256 payload hash at write time           │
  │  File uploads: Cloudinary signed URLs                       │
  │  Docker: non-root user `prahari`, read-only mounts          │
  │  Env secrets: never in code, always from ENV                │
  └─────────────────────────────────────────────────────────────┘
```

| Concern | Implementation |
|---------|---------------|
| Password storage | bcrypt, cost factor 12, never plaintext |
| Session tokens | HS256 JWT, 8-hour expiry, checked server-side on destructive actions |
| Rate limiting | slowapi per-IP — prevents Gemini API abuse and brute-force |
| Audit integrity | SHA-256 hash of every event payload at write time |
| Secrets | All from environment variables, `JWT_SECRET` auto-generates if unset |
| Container | Multi-stage Docker, non-root `prahari` user |
| Document storage | Cloudinary CDN with signed URLs — no public guessable links |

---

## Differential Privacy Analytics

PRAHARI's analytics (Stage 7) use the Laplace mechanism to add mathematically calibrated noise before returning aggregate statistics. This ensures individual bid data cannot be inferred from the outputs, even by repeated queries.

```
  Raw aggregate (e.g. avg turnover of all bidders)
          │
          ▼
  Laplace noise = Sensitivity / ε
  where:
    Sensitivity = max change one bidder's data can cause
    ε (epsilon) = privacy budget per query (default 1.0)
          │
          ▼
  Noisy result returned to officer
  (accurate enough for decisions, private enough for compliance)

  Budget tracking:
    Each query consumes ε from a per-project budget
    Repeat queries on the same data → increasing privacy cost
    Budget tracked in audit_events (dp_epsilon column)
```

This is implemented using `diffprivlib` (IBM's differential privacy library) and is one of the few production tender evaluation systems anywhere that provides mathematical privacy guarantees on aggregate procurement statistics.

---

## CI/CD Pipeline

```
  git push to main / PR
         │
         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  Job 1: frontend                                            │
  │    npm ci                                                   │
  │    npx tsc --noEmit          ← 0 type errors enforced       │
  │    npm run build             ← Vite production build        │
  └──────────────────────────────────┬──────────────────────────┘
                                     │ parallel
  ┌──────────────────────────────────┼──────────────────────────┐
  │  Job 2: backend                  │                          │
  │    python -m py_compile ...      │ ← syntax check all files │
  │    pytest tests/ -v              │ ← 23 test assertions     │
  └──────────────────────────────────┘                          │
                                     │ both pass                │
                                     ▼
  ┌─────────────────────────────────────────────────────────────┐
  │  Job 3: docker                                              │
  │    docker build --target production                         │
  │    (validates multi-stage build, layer cache)               │
  └─────────────────────────────────────────────────────────────┘
```

### Test Coverage

```
tests/
├── test_auth.py               (12 assertions)
│   ├── JWT encode / decode
│   ├── JWT expiry detection
│   ├── JWT tampering detection
│   ├── Wrong secret rejected
│   ├── bcrypt hash + verify
│   ├── bcrypt wrong password
│   └── Module import checks (slowapi, pyjwt)
│
├── test_document_types.py     (8 assertions)
│   ├── Accepted extensions gate
│   ├── Rejected formats (exe, html, csv, etc.)
│   ├── Document kind detection (pdf/word/image)
│   ├── DOCX text extraction smoke test
│   └── PDF/image passthrough (no conversion)
│
└── test_pdf_highlight_logic.py  (12 assertions)
    ├── norm(): lowercase, whitespace collapse,
    │          punctuation strip, curly quotes, dashes
    ├── overlapScore(): exact match → 1.0
    ├── overlapScore(): substring → 1.0
    ├── overlapScore(): case-insensitive → 1.0
    ├── overlapScore(): partial ≥ 0.6
    ├── overlapScore(): below threshold < 0.6
    ├── overlapScore(): unrelated → 0.0
    └── overlapScore(): empty/short → 0.0
```

---

## Deployment

### Docker (recommended)

```bash
# Production
docker compose up --build -d

# Backend runs on port 8000 with 2 Uvicorn workers
# Frontend served via Vite build (nginx in production)
# PostgreSQL in separate container with healthcheck
```

### Render + Vercel (cloud)

**Backend → Render:**
1. Connect your GitHub repo to Render
2. `render.yaml` is already configured — Render detects it automatically
3. Set environment variables in Render dashboard:
   `DATABASE_URL`, `GEMINI_API_KEY`, `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET`, `ADMIN_PASSWORD`
4. `JWT_SECRET` auto-generates (set by `render.yaml`)

**Frontend → Vercel:**
1. Import repo to Vercel, set root to `frontend/`
2. `vercel.json` is already configured (SPA routing + security headers)
3. Set `VITE_API_BASE_URL` to your Render backend URL

### Environment Variables

```bash
# Required
DATABASE_URL=postgresql://user:pass@host:5432/prahari
GEMINI_API_KEY=your-google-ai-studio-key
CLOUDINARY_CLOUD_NAME=your-cloud
CLOUDINARY_API_KEY=your-key
CLOUDINARY_API_SECRET=your-secret
ADMIN_PASSWORD=your-bcrypt-hashed-password

# Optional (auto-generated if not set)
JWT_SECRET=your-32-char-secret

# Generate a bcrypt password hash:
python3 -c "import bcrypt; print(bcrypt.hashpw(b'yourpassword', bcrypt.gensalt(12)).decode())"
```

---

## Local Development

```bash
# 1. Clone
git clone https://github.com/neonlights003/PRAHARI.git
cd prahari

# 2. Backend setup
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.template .env             # fill in your keys

# 3. Start backend (auto-reload)
uvicorn backend.app:app --reload --port 8000

# 4. Frontend setup (separate terminal)
cd frontend
npm install
npm run dev
# → http://localhost:5173

# 5. Run tests
pytest tests/ -v

# 6. Generate demo data
python sample_data/generate_demo_docx.py
# → 4 DOCX files ready to upload
# → follow sample_data/README_DEMO.md for the walkthrough
```

---

## Demo Scenario

The `sample_data/` directory contains a ready-to-use demo with **three bidders that produce three different verdicts**, designed to showcase the full pipeline in under 10 minutes.

**Tender:** Supply of Bullet-Resistant Jackets (NIJ Level IIIA) — CRPF 2024-25

| Bidder | Expected Outcome | Reason |
|--------|:----------------:|--------|
| Kavach Armour Solutions Pvt Ltd | **Eligible** | All criteria met: ₹18.48 Cr turnover, 4 works, GST active, ISO + DGQA |
| Frontier Defence Gear Ltd | **Manual Review** | Avg turnover ₹9.83 Cr (below ₹10 Cr threshold); no ISO cert |
| Suraksha Equipment Suppliers | **Not Eligible** | GST registration surrendered — mandatory criterion C003 fails |

Run the generator then follow the step-by-step walkthrough:

```bash
python sample_data/generate_demo_docx.py
# See: sample_data/README_DEMO.md
```

---

## Known Limitations & Roadmap

See [`SCALABILITY_ISSUES.md`](SCALABILITY_ISSUES.md) for the full technical debt register with root causes and mitigations.

| Issue | Status | Priority |
|-------|--------|----------|
| Gemini calls are synchronous (blocks worker during long evaluations) | Known | P0 — background task queue |
| Rate limiter is in-process (not shared across workers) | Known | P1 — Redis backend |
| No JWT token revocation | Known | P2 — jti deny-list |
| No upload size limit enforcement | Known | P3 — Content-Length check |
| DP epsilon budget not globally tracked | Known | P3 — per-project budget table |

**Phase 2 Roadmap:**
- [ ] Hindi / regional language full UI translation
- [ ] Mobile-responsive evaluation board
- [ ] RTI-ready automated response generation from audit trail
- [ ] Integration with GeM (Govt e-Marketplace) and CPPP portal
- [ ] Multi-force deployment (CISF, BSF, SSB, ITBP, NSG)
- [ ] Background evaluation jobs with progress bar
- [ ] Blockchain-anchored audit events for court-admissible records

---

## Project Structure

```
prahari/
├── backend/
│   ├── app.py                  75+ REST endpoints, JWT auth, rate limiting
│   ├── gemini_client.py        9-stage AI pipeline functions
│   ├── db.py                   PostgreSQL ORM — all 13 tables
│   ├── db_config.py            Connection pool configuration
│   ├── document_converter.py   DOCX/image/PDF → Gemini pre-processing
│   ├── vendor_lookup.py        Cross-tender vendor history intelligence
│   ├── compliance_calculator.py Weighted scoring engine
│   ├── report_generator.py     WeasyPrint PDF helper utilities
│   └── templates/
│       └── reports/
│           └── prahari_evaluation_report.html   Jinja2 PDF template
│
├── frontend/
│   ├── src/
│   │   ├── pages/              17 page components
│   │   ├── components/         15 reusable components
│   │   ├── contexts/           RoleContext (JWT), LanguageContext (i18n)
│   │   └── lib/
│   │       ├── api.ts          Typed API client, 75+ methods
│   │       └── i18n.ts         English + Hindi translation strings
│   └── vercel.json             SPA routing + security headers for Vercel
│
├── tests/
│   ├── test_auth.py            JWT + bcrypt — 12 assertions
│   ├── test_document_types.py  Format acceptance — 8 assertions
│   └── test_pdf_highlight_logic.py  norm() + overlapScore() — 12 assertions
│
├── sample_data/
│   ├── generate_demo_docx.py   Generates 4 demo .docx files
│   ├── tender_nit_crpf_ppe_2024.docx     (generated)
│   ├── bidder1_kavach_armour.docx        (generated)
│   ├── bidder2_frontier_defence.docx     (generated)
│   ├── bidder3_suraksha_equipment.docx   (generated)
│   └── README_DEMO.md          10-minute walkthrough
│
├── Dockerfile                  Multi-stage, non-root user, healthcheck
├── docker-compose.yml          Backend + PostgreSQL with healthchecks
├── render.yaml                 One-click Render deployment config
├── pytest.ini                  Test configuration
├── requirements.txt            Python dependencies
├── PITCH_DECK.md               Copy-paste pitch deck (16 slides)
├── SCALABILITY_ISSUES.md       10 known issues with mitigations
└── .github/
    └── workflows/
        └── ci.yml              3-job CI pipeline
```

---

## Tech Stack — Complete List

| Category | Library / Tool | Version | Purpose |
|----------|---------------|---------|---------|
| AI | google-generativeai | latest | Gemini 2.5 Flash inference |
| AI privacy | diffprivlib | latest | Laplace mechanism DP |
| Backend | fastapi | 0.104 | REST API framework |
| Backend | uvicorn | 0.24 | ASGI server |
| Backend | pydantic | 2.x | Request/response validation |
| Auth | PyJWT | latest | HS256 JWT tokens |
| Auth | bcrypt | latest | Password hashing |
| Rate limiting | slowapi | latest | Per-IP rate limits |
| Database | psycopg2-binary | latest | PostgreSQL driver |
| Documents | python-docx | latest | DOCX text extraction |
| PDF reports | weasyprint | latest | HTML→PDF rendering |
| PDF reports | Jinja2 | 3.1 | Report templating |
| Charts | plotly + kaleido | latest | Chart rendering |
| File storage | cloudinary | latest | CDN + signed URLs |
| HTTP | httpx | latest | Async HTTP client |
| Frontend | react | 18 | UI framework |
| Frontend | typescript | 5 | Type safety |
| Frontend | vite | 5 | Build tool |
| Frontend | tailwindcss | 3 | Utility CSS |
| PDF viewer | react-pdf | 7 | In-browser PDF rendering |
| Icons | lucide-react | latest | Icon set |
| Routing | react-router-dom | 6 | SPA routing |
| Container | docker | 24 | Multi-stage build |
| CI | github-actions | — | 3-job pipeline |

---

<div align="center">

**PRAHARI** — *Because procurement decisions should be fast, fair, and provable.*

Built with dedication for CRPF AI Procurement · Ministry of Home Affairs · SIH 2024

</div>
