# PRAHARI — Demo Walkthrough

This folder contains everything needed to run a fully-realistic end-to-end demo of the PRAHARI system in under 10 minutes.

## Scenario

**Tender**: Supply and Installation of Bullet-Resistant Jackets (NIJ Level IIIA) for CRPF Battalions — 2024-25
**NIT No**: CRPF/HQ/PPE/2024-25/001
**Estimated Value**: INR 25 Crore

Three bidders have submitted qualification packages. The expected outcomes are:

| Bidder | Company | Expected Verdict | Why |
|--------|---------|-----------------|-----|
| 1 | Kavach Armour Solutions Pvt Ltd | **Eligible** | Meets all criteria; avg turnover INR 18.48 Cr; 4 works; active GST; ISO + DGQA |
| 2 | Frontier Defence Gear Ltd | **Manual Review** | Avg turnover INR 9.83 Cr (below INR 10 Cr threshold); otherwise compliant |
| 3 | Suraksha Equipment Suppliers | **Not Eligible** | No valid GST registration (mandatory criterion C003 fails) |

---

## Step 0 — Generate the DOCX files

```bash
cd /path/to/AI-For-Bharat
pip install python-docx   # already in requirements.txt
python sample_data/generate_demo_docx.py
```

This creates four files in `sample_data/`:
- `tender_nit_crpf_ppe_2024.docx` — the Tender NIT
- `bidder1_kavach_armour.docx` — eligible bidder
- `bidder2_frontier_defence.docx` — manual review (borderline turnover)
- `bidder3_suraksha_equipment.docx` — not eligible (no GST)

---

## Step 1 — Create a new project

1. Open PRAHARI → **Admin Login** (`admin` / your configured password)
2. Navigate to **Projects** → **New Project**
3. Fill in:
   - Name: `CRPF PPE 2024-25 — Bullet-Resistant Jackets`
   - State: `Delhi`
   - Scheme: `MHA Central Procurement`
   - Sector: `Defence & Security`
4. Click **Create**

---

## Step 2 — Upload the Tender NIT and extract criteria

1. Inside the project, click **Upload DPR / NIT Document**
2. Upload `tender_nit_crpf_ppe_2024.docx`
3. Once processed, click **Extract Criteria** (Stage 1)
4. PRAHARI will extract:
   - **C001** — Annual Turnover ≥ INR 10 Crore (Mandatory)
   - **C002** — 3+ Similar Works (Mandatory)
   - **C003** — Valid GST Registration (Mandatory)
   - **C004** — ISO 9001:2015 Certification (Preferred)
   - **C005** — BIS/DGQA Approval (Preferred)

---

## Step 3 — Register bidders and upload their documents

Go to **Evaluation Board** → **Manage Bidders** for the project.

### Bidder 1 — Kavach Armour Solutions
- Company Name: `Kavach Armour Solutions Pvt Ltd`
- GSTIN: `07AABCK1234A1Z5`
- PAN: `AABCK1234A`
- Upload: `bidder1_kavach_armour.docx`

### Bidder 2 — Frontier Defence Gear
- Company Name: `Frontier Defence Gear Ltd`
- GSTIN: `27AABCF5678B1Z3`
- PAN: `AABCF5678B`
- Upload: `bidder2_frontier_defence.docx`

### Bidder 3 — Suraksha Equipment Suppliers
- Company Name: `Suraksha Equipment Suppliers`
- GSTIN: *(leave blank — no active GST)*
- PAN: `AABCS9012C`
- Upload: `bidder3_suraksha_equipment.docx`

---

## Step 4 — Run evaluation

1. On the Evaluation Board, click **Evaluate All**
2. PRAHARI runs 9-stage AI evaluation against all 5 criteria × 3 bidders = 15 verdicts
3. Expected results:

| Criterion | Kavach | Frontier | Suraksha |
|-----------|--------|----------|----------|
| C001 Turnover | Eligible (18.48 Cr) | Manual_Review (9.83 Cr) | Eligible (22.13 Cr) |
| C002 Prior Works | Eligible (4 works) | Eligible (5 works) | Eligible (6 works) |
| C003 GST | Eligible | Eligible | Not_Eligible |
| C004 ISO | Eligible | Manual_Review (none) | Eligible |
| C005 DGQA | Eligible | Eligible | Manual_Review (pending) |

**Final verdicts**: Kavach → Eligible · Frontier → Manual_Review · Suraksha → Not_Eligible

---

## Step 5 — Explore features

### Confidence heatmap
- View the colour-coded matrix; hover any cell for evidence quote and PDF page
- Click the **book icon** to open the evidence in the inline PDF viewer with highlighting

### Collusion detection
- Click **Detect Collusion** — with only 3 diverse bidders you expect no alerts
- Try again after duplicating a bidder's document to see the similarity detector fire

### Q&A Assistant
Ask questions like:
- *"Which bidder has the highest average confidence score?"*
- *"Why is Frontier Defence in Manual Review?"*
- *"Summarise the mandatory criterion failures."*
- *"If we lower the turnover threshold to 9 crore, how many bidders would be eligible?"*

### Override a verdict
- Click any Manual_Review cell → **Override** → set Frontier's C001 to Eligible with justification
- The override is recorded in the immutable audit trail

### Officer sign-off
- Once all Manual_Review items are resolved, the **Sign Off** button becomes active
- Enter the officer's name + designation and confirm
- The signed-off state appears in the PDF report's signature block

### Download report
- Click **Report** to download the full 9-stage PRAHARI evaluation PDF
- The report includes: criteria breakdown, verdicts matrix, authenticity scores, collusion alerts, audit trail, and the officer signature block

---

## Criteria reference card

| ID | Name | Type | Threshold | Evidence to look for |
|----|------|------|-----------|---------------------|
| C001 | Annual Turnover | Mandatory | ≥ INR 10 Crore (avg 3yr) | CA-certified turnover statements |
| C002 | Prior Experience | Mandatory | ≥ 3 similar works ≥ INR 1 Cr | Work completion certificates |
| C003 | GST Registration | Mandatory | Active GSTIN | GST registration certificate |
| C004 | ISO Certification | Preferred | ISO 9001:2015, NABCB accredited | ISO certificate copy |
| C005 | BIS/DGQA Approval | Preferred | DGQA approval or BIS licence | Approval letter |
