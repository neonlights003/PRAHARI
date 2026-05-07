# PRAHARI — 5-Minute Demo Video Script
### Follow this document top to bottom. Do not skip any step.

---

## BEFORE YOU HIT RECORD — SETUP CHECKLIST

Do all of this BEFORE starting the screen recording.

### 1. Browser setup
- Open **Google Chrome** (not Safari — PDF viewer works best in Chrome)
- Set zoom to **90%** (`Cmd + -` once) so more content fits on screen
- Open these tabs in this order:
  1. `https://prahari-backend.onrender.com/health` → wait for `{"status":"ok"}`
  2. `https://prahari-zeta.vercel.app` → your landing page
- Close all other tabs, notifications, Slack, Messages

### 2. Wake up the backend
- Click the `/health` tab first
- Wait until you see `{"status":"ok"}` — this prevents a cold-start freeze during recording
- Keep this tab open but you won't show it

### 3. Load demo data (DO THIS BEFORE RECORDING)
Follow these steps in the app so data is ready when you record:

**a) Log in:**
- Go to `https://prahari-zeta.vercel.app`
- Click Login / Admin Login
- Enter your admin credentials

**b) Create the tender:**
- Click "New Tender" or "Create Project"
- Name: `CRPF/PPE/BRJ/2024-25 — Bullet Resistant Jackets`
- Save it

**c) Upload the NIT document:**
- Open the tender
- Upload `sample_data/tender_nit_crpf_ppe_2024.docx`
- Click **Extract Criteria** and wait for C001–C005 to appear

**d) Register 3 bidders:**
- Bidder 1: `Kavach Armour Solutions` | GSTIN: `27AABCK1234F1Z5`
- Bidder 2: `Frontier Defence Systems` | GSTIN: `07AABCF5678G1Z3`
- Bidder 3: `Suraksha Equipment Ltd`   | GSTIN: `29AABCS9012H1Z1`

**e) Upload bidder documents:**
- Kavach → upload `sample_data/bidder1_kavach_armour.docx`
- Frontier → upload `sample_data/bidder2_frontier_defence.docx`
- Suraksha → upload `sample_data/bidder3_suraksha_equipment.docx`

**f) Evaluate all:**
- Click **Evaluate All** — wait 60–90 seconds
- All verdicts must be visible before you record

**g) Run collusion detection:**
- Go to Collusion tab → Run Detection → wait for results

**h) Ask one Q&A question (pre-warm the session):**
- Go to Q&A tab
- Ask: `Why is Frontier Defence in Manual Review?`
- Wait for the answer — keep it visible

**i) Navigate BACK to the landing page**
- Your start position for recording is the landing page

### 4. Screen recording tool
**Option A — QuickTime (recommended, free):**
- Open QuickTime Player → `File → New Screen Recording`
- Click the small arrow next to the record button
- Select your microphone (built-in is fine)
- Do NOT start recording yet

**Option B — Loom:**
- Open Loom → Screen + Camera
- Do NOT start recording yet

### 5. Hide distractions
- Turn on Do Not Disturb: `Cmd + Fn + F6` or System Settings → Focus → Do Not Disturb
- Hide the Dock: System Settings → Dock → Auto-hide
- Close Finder windows
- Your browser should be fullscreen (`Cmd + Ctrl + F`)

---

## THE SCRIPT

Each section has:
- **[TIME]** — where you should be in the video
- **ACTION** — what to click or do on screen
- **SAY THIS** — read this out loud, naturally, not robotically

Speak at a calm, clear pace. Slightly slower than normal conversation.

---

### [0:00 – 0:30] OPENING — The Problem

**ACTION:** You are on the landing page. Let it sit for 3 seconds before speaking.

**SAY THIS:**
> "India processes over ₹40 lakh crore in government procurement every year.
> For forces like the CRPF, evaluating a single tender takes 3 to 6 months,
> hundreds of evaluator-hours, and produces decisions that are difficult to audit
> and even harder to defend in court.
>
> This is PRAHARI — a 9-stage AI evaluation platform that takes that same
> evaluation and completes it in under 10 minutes, with full evidence traceability
> and a tamper-proof audit trail."

**ACTION:** While saying the last sentence, slowly scroll down the landing page to show the feature highlights or hero section.

---

### [0:30 – 1:00] STAGE 1 — Criteria Extraction

**ACTION:** Click into your tender (`CRPF/PPE/BRJ/2024-25`). Navigate to the criteria section. The 5 extracted criteria should already be visible.

**SAY THIS:**
> "The process starts with the NIT — the Notice Inviting Tender.
> PRAHARI reads the document using Google Gemini's multimodal AI and automatically
> extracts every eligibility criterion — including the threshold value, whether it's
> mandatory or just preferred, and its weight in the overall evaluation.
>
> Here we have 5 criteria for a bullet-resistant jacket procurement:
> minimum annual turnover of ₹10 crore, 3 similar completed works,
> a valid GST registration, ISO 9001 certification, and DGQA approval."

**ACTION:** As you name each criterion, hover your mouse over it or point to it slowly. Don't rush this — let viewers read.

---

### [1:00 – 1:20] STAGE 2 — Market Benchmark

**ACTION:** Navigate to the benchmark section or show the benchmark result if it's on the same page.

**SAY THIS:**
> "Before a single bidder is even registered, PRAHARI validates the thresholds
> themselves. Stage 2 benchmarks each criterion against sector data — flagging
> thresholds that are statistically anomalous. This detects threshold-rigging,
> where a corrupt officer sets criteria calibrated to favour one vendor.
> In this tender, all thresholds are within normal range."

**ACTION:** Point to the benchmark results briefly — move on quickly, don't linger here.

---

### [1:20 – 2:00] STAGE 5 — Verdict Heatmap

**ACTION:** Navigate to the Evaluation Board → Heatmap tab. The full verdict matrix must be visible — all 3 bidders, all 5 criteria.

**SAY THIS:**
> "Three bidders have submitted their qualification documents — in PDF, DOCX,
> and scanned formats. PRAHARI evaluated each bidder against each criterion.
> Here is the result."

**ACTION:** Pause 3 full seconds. Let viewers look at the matrix. Then continue:

> "Kavach Armour Solutions — eligible across all 5 criteria.
> Frontier Defence Systems — flagged for manual review. Their average turnover
> is ₹9.83 crore, just below the ₹10 crore threshold. The AI's confidence is
> 78% — below our 90% auto-disqualification threshold — so it routes this
> to a human officer rather than automatically rejecting them.
> Suraksha Equipment — not eligible. Their GST registration is invalid."

**ACTION:** As you mention each bidder, move your mouse to highlight their row.

---

### [2:00 – 2:35] PDF EVIDENCE HIGHLIGHTING — The Wow Moment

**ACTION:** Click the **green Eligible cell for Kavach / C001 (Turnover)**. The PDF viewer modal should open. Wait for it to load fully before speaking.

**SAY THIS:**
> "Every verdict is backed by evidence. Watch what happens when I click
> Kavach's turnover verdict."

**ACTION:** Let the PDF load. The highlighted text should be visible on the page.

> "The source document opens on the exact page — page 12 — where Kavach's
> CA-certified turnover of ₹18.48 crore is stated. The text is highlighted
> in the document itself.
>
> This is not a summary generated by AI. This is the actual bidder document,
> with the exact sentence the AI used to make its decision highlighted in place.
> Any officer, auditor, or court can verify this verdict in 10 seconds."

**ACTION:** Slowly scroll within the PDF viewer to show the highlighted text clearly. Pause for 3 seconds.

**ACTION:** Close the modal.

---

### [2:35 – 3:00] STAGE 6 — Collusion Detection

**ACTION:** Click the **Collusion tab**.

**SAY THIS:**
> "Stage 6 runs cross-bidder collusion detection. PRAHARI compares all bidder
> documents against each other — checking for identical text sections, suspicious
> price coordination, shared email domains, and complementary bidding patterns
> where one bidder consistently scores just above threshold while others score
> just below.
>
> In this evaluation, no high-risk collusion was detected. All three vendors
> appear to be independent submissions."

**ACTION:** Scroll through the collusion report slowly while speaking.

---

### [3:00 – 3:30] Q&A ASSISTANT

**ACTION:** Click the **Q&A tab**. Your pre-asked question and answer should already be there.

**SAY THIS:**
> "Procurement officers can interrogate the evaluation in natural language."

**ACTION:** Point to the question you already asked: *"Why is Frontier Defence in Manual Review?"*

> "I asked: Why is Frontier Defence in Manual Review?
> The AI explains — Frontier's 3-year average turnover is ₹9.83 crore,
> below the mandatory ₹10 crore threshold. However, at 78% confidence,
> it does not meet the 90% threshold for automatic disqualification.
> An officer must review."

**ACTION:** Scroll to show the full answer if it's long.

> "The session history is persisted in the database — if the server restarts
> or a different officer picks up the evaluation, the conversation continues
> exactly where it left off."

---

### [3:30 – 4:00] OFFICER SIGN-OFF

**ACTION:** Navigate to the sign-off button (top of Evaluation Board or wherever it is). Click it.

**SAY THIS:**
> "Once the officer has reviewed all manual cases and is satisfied with the
> evaluation, they apply a digital sign-off."

**ACTION:** Type `Soham Banerjee` in the officer name field. Click confirm.

> "The sign-off is recorded with the officer's name, timestamp, and tender
> reference in the audit trail. It is cryptographically tied to the evaluation
> record — it cannot be backdated or modified."

**ACTION:** Navigate to the Audit Trail tab briefly to show the sign-off event in the log.

---

### [4:00 – 4:30] AUDIT REPORT

**ACTION:** Click **Download Report** or navigate to the report section. If you can show the PDF report opening in a new tab, even better.

**SAY THIS:**
> "Stage 9 generates a complete PDF audit report.
>
> It contains: the full criteria list, the verdict matrix with confidence scores,
> evidence quotes for every decision, the authenticity assessment of each document,
> the collusion detection findings, a complete override history, and the officer's
> digital signature block.
>
> This report is RTI-ready — any Right to Information request about this
> procurement decision can be answered directly from this document."

**ACTION:** Scroll through the PDF report slowly — show the verdicts table, the evidence section, and the signature block at the bottom.

---

### [4:30 – 5:00] CLOSING

**ACTION:** Navigate back to the landing page OR stay on the report — either works.

**SAY THIS:**
> "PRAHARI addresses every failure point in government procurement evaluation —
> manual errors, missing audit trails, undetected forgeries, collusion between
> bidders, and even threshold manipulation by procurement officers themselves.
>
> It does this while keeping the human officer in authority at every step.
> No bidder is automatically disqualified unless the AI is 90% confident
> and the criterion is mandatory. Everything borderline goes to a human.
>
> The system is fully deployed — FastAPI backend on Render, React frontend
> on Vercel, PostgreSQL for persistence, Google Gemini 2.5 Flash for inference.
>
> PRAHARI does not replace the procurement officer.
> It makes the procurement officer unstoppable."

**ACTION:** Let the screen sit for 2 seconds after the last line. Then stop recording.

---

## AFTER RECORDING — EDITING GUIDE

### What to cut
| Problem | Fix |
|---------|-----|
| Waiting for Evaluate All to run | Cut it — jump cut from "Evaluate All clicked" to results visible |
| Waiting for PDF to load | Cut the loading spinner if it takes > 2 seconds |
| Mistakes / restarts mid-sentence | Cut and re-record that section only |
| Dead air / long pauses | Trim to max 1 second between sentences |

### iMovie step-by-step
1. Open iMovie → New Movie → Import your recording
2. Drag recording into the timeline
3. To cut: position playhead at cut point → `Cmd + B` to split clip → delete the unwanted piece
4. To speed up a section: click clip → right click → Speed → 4x (use for waiting screens only)
5. Add title at the very start: click **Titles** tab → drag "Opening" title to start of timeline → type `PRAHARI — AI-Powered Tender Evaluation Platform`
6. Add your name as subtitle: `Soham Banerjee`
7. Export: `File → Share → File → 1080p → High Quality`

### Final video must have
- [ ] Length: 4:45 to 5:15 (trim to fit)
- [ ] PDF evidence highlight moment clearly visible (the most important 20 seconds)
- [ ] Verdict heatmap with all 3 bidders visible
- [ ] Opening title card
- [ ] Audio clear throughout — no background noise

---

## SCREENSHOTS — Take these during the recording pauses

These are the best moments to also grab screenshots (`Cmd + Shift + 4`):

| # | When to take it | What it shows |
|---|-----------------|---------------|
| 1 | During opening (0:00–0:15) | Landing page hero section |
| 2 | After criteria appear (0:45) | Extracted criteria list C001–C005 |
| 3 | On the heatmap (1:20–2:00) | Full verdict matrix with all colours |
| 4 | PDF viewer open with highlight (2:10) | Evidence highlighted in PDF |
| 5 | Collusion tab (2:40) | Collusion detection results |
| 6 | Q&A answer visible (3:10) | Question + AI answer |
| 7 | Audit trail tab (3:45) | SHA-256 event log |
| 8 | PDF report open (4:10) | Generated report with signature block |

> Tip: You can also take screenshots AFTER the video recording from the same browser
> session — the data will still be there. Screenshots don't need to be taken live.

---

## UPLOAD CHECKLIST

- [ ] Video exported as MP4 at 1080p
- [ ] Upload to YouTube → Visibility: **Unlisted** → copy link
  - Title: `PRAHARI — AI-Powered Tender Evaluation Platform Demo`
  - Description: `Demo of the 9-stage AI tender evaluation pipeline built for CRPF procurement.`
- [ ] OR upload to Google Drive → right click → Share → Anyone with link → copy link
- [ ] 8 screenshots saved and renamed: `screenshot_01_landing.png`, `screenshot_02_criteria.png` etc.
- [ ] Paste video link into the submission portal Video Demo field
- [ ] Upload screenshots into the Project Snapshots field (upload all 8)

---

## TIME BUDGET FOR YOUR 4 HOURS

| Task | Time |
|------|------|
| Browser setup + demo data loaded | 20 min |
| First recording attempt | 15 min |
| Second recording attempt if needed | 15 min |
| iMovie editing + title card | 60 min |
| Export (1080p takes ~5 min to render) | 10 min |
| Screenshots (take from browser after recording) | 15 min |
| Upload video + screenshots | 15 min |
| Compile LaTeX report (`cd report && make`) | 5 min |
| Fill submission form | 20 min |
| **Buffer** | **45 min** |
| **Total** | **~4 hours** |

---

## IF SOMETHING GOES WRONG

| Problem | Quick fix |
|---------|-----------|
| Backend is down / slow | Use `docker compose up` locally instead |
| Evaluate All fails | Evaluate bidders one by one manually |
| PDF viewer doesn't open | Refresh the page, try a different verdict cell |
| Gemini times out mid-demo | Retry — it's a network blip, not a code issue |
| Video is too long | Cut the benchmark section (1:00–1:20) — it's the most skippable |
| Video is too short | Slow down the heatmap section, spend more time on PDF highlighting |
| iMovie crashes | Use QuickTime's built-in trim: `Edit → Trim` |
