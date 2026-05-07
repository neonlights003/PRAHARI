import os
import json
import time
import asyncio
from typing import Dict, List, Optional
import google.generativeai as genai
from dotenv import load_dotenv
import backend.db as _db

load_dotenv()  # ensure .env is loaded

# Some versions of the google-genai SDK expect genai.configure(...)
try:
    import google.generativeai as genai
    key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if key:
        try:
            genai.configure(api_key=key)
            print("Configured google.generativeai with GEMINI_API_KEY from .env")
        except AttributeError:
            # older/newer SDK may not have configure(); we'll still continue and rely on env var
            print("genai.configure not present; relying on GOOGLE_API_KEY env var")
except Exception as e:
    print("Could not import google.generativeai to configure automatically:", e)


# Configure Gemini
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))


# Custom exception for expired file references
class FileExpiredError(Exception):
    """Raised when a Gemini file reference has expired (404/403)."""
    pass


# In-memory chat sessions: {dpr_id: chat_object}
_chat_sessions = {}


async def upload_file(file_path: str) -> str:
    """
    Upload a file to Gemini Files API and wait for it to be processed.
    Returns the file reference (name/uri) that can be used in generation requests.
    """
    print(f"⏳ Uploading file to Gemini: {file_path}")
    start_time = time.time()
    
    # Upload the file (blocking call offloaded to thread)
    uploaded_file = await asyncio.to_thread(genai.upload_file, file_path)
    
    # Poll until the file is processed
    print(f"⏳ Waiting for file to be processed: {uploaded_file.name}")
    while uploaded_file.state.name == "PROCESSING":
        await asyncio.sleep(2)
        uploaded_file = await asyncio.to_thread(genai.get_file, uploaded_file.name)
    
    if uploaded_file.state.name == "FAILED":
        raise ValueError(f"File processing failed: {uploaded_file.name}")
    
    elapsed = time.time() - start_time
    print(f"✓ File uploaded and processed in {elapsed:.2f}s: {uploaded_file.name}")
    
    # Return the file reference (name is stable across SDK versions)
    return uploaded_file.name


async def generate_json_from_file(file_ref: str, schema_path: str) -> Dict:
    """
    Generate structured JSON from an uploaded file using Gemini in English only.
    """
    print(f"⏳ Generating JSON from file: {file_ref}")
    start_time = time.time()
    
    # Read the schema
    with open(schema_path, 'r') as f:
        schema_content = f.read()
    
    # Create a strict system prompt (English only) - TENDER EVALUATION
    system_instruction = f"""You are an expert Tender/Bid Proposal Analyst. Read the attached PDF (tender document or bid proposal) and produce EXACTLY one valid JSON object containing analysis in English.

MANDATORY BEHAVIOR:
1) OUTPUT: Return exactly one JSON object. Do NOT add markdown or extra text.
2) ANALYZE & INFER: You must both extract explicit values from the PDF and also ANALYZE the information and INFER values where the document does not state them. In particular you MUST compute:
   - overallScore: a numeric score 0-100 (see scoring rubric below). Do NOT return null for overallScore.
   - recommendation: one of exactly ["Shortlist", "Select", "Reject", "Review"]. Do NOT return null.
   - financialAnalysis: populate bidAmount and pricingStructure fields.
   - riskAssessment: identify top risks, severity and evidence (these are analytical outputs).
3) REQUIRED NON-NULL FIELDS: The following fields MUST NOT be null (fill them or infer if missing): 
   `"tenderDetails.tenderName"`, `"tenderDetails.bidderName"`, `"executiveSummary"`, `"overallScore"`, `"recommendation"`, and the entire `"financialAnalysis"` object.

4) TRACEABILITY: If you infer or compute any field (overallScore, recommendation, any financial number, or risk severity), include an explanation in the findings field.

5) **VERBATIM QUOTE EXTRACTION (CRITICAL FOR ALL EVIDENCE FIELDS)**:
   When extracting quotes for ANY evidence field (riskAssessment, evaluationCriteria, inconsistencyDetection, etc.):
   
   **STRICT RULES**:
   - Extract ONLY the actual text content from the PDF body - NO section headers, NO bullet points, NO labels
   - Copy the text EXACTLY as it appears - character-for-character, word-for-word
   - Include COMPLETE sentences (don't truncate mid-sentence)
   - Preserve ALL punctuation, capitalization, spacing
   - Do NOT paraphrase, summarize, reword, or interpret
   - The quote MUST be findable using Ctrl+F search in the original PDF
   - If a passage is very long (>200 words), extract 1-2 complete sentences verbatim
   
   **EXAMPLES**:
    GOOD quote: "The bidder has completed 5 similar projects in the last 3 years."
    BAD quote: "Past Experience: The bidder has completed 5 similar projects..." (includes header)

5b) **PAGE NUMBER ACCURACY (CRITICAL FOR PDF HIGHLIGHTING)**:
   For EVERY evidence item's `pageLocation` field:
   
   **STRICT RULES**:
   - You MUST provide the EXACT page number where the quote appears in the PDF
   - Double-check that the page number is CORRECT - the quote MUST exist on that page
   - Format: "Page X" or "Page X, Section Y.Z" (where X is the actual page number)
   - NEVER guess or estimate page numbers
   - If you're unsure of the exact page, search the PDF to find where the quote actually appears
   - The system will use this page number to jump to and highlight the quote in the PDF viewer
   - INCORRECT page numbers will break the highlighting feature
   
   **EXAMPLES**:
    GOOD: "Page 15, Section 3.2" (if quote is actually on page 15)
    BAD: "Page 15, Section 3.2" (if quote is actually on page 18)
    BAD: "Section 3.2" (missing page number)


6) **STATE AND SECTOR EXTRACTION** (CRITICAL FOR VALIDATION):
   
   Extract the project state and sector from the PDF:
   
   **State Extraction (`tenderDetails.projectLocation.state`):**
   - Carefully read the PDF to find the project location/state
   - Match it EXACTLY against one of these 36 Indian States/UTs:
     Andhra Pradesh, Arunachal Pradesh, Assam, Bihar, Chhattisgarh, Goa, Gujarat,
     Haryana, Himachal Pradesh, Jharkhand, Karnataka, Kerala, Madhya Pradesh,
     Maharashtra, Manipur, Meghalaya, Mizoram, Nagaland, Odisha, Punjab, Rajasthan,
     Sikkim, Tamil Nadu, Telangana, Tripura, Uttar Pradesh, Uttarakhand, West Bengal,
     Andaman and Nicobar Islands, Chandigarh, Dadra and Nagar Haveli and Daman and Diu,
     Delhi, Jammu and Kashmir, Ladakh, Lakshadweep, Puducherry
   - Return the EXACT matching state name from the list above
   - If state is not clearly mentioned or doesn't match any state, return "Not Specified"
   
   **Sector Extraction (`extractedSector`):**
   - Identify the project sector/category/type from the PDF content
   - Match it against these sectors (from all schemes):
     Roads, Railways, Airports, Ports & Waterways, Logistics Infra, Pipelines,
     Power Generation, Power Transmission, Power Distribution, Urban Transit, Rural Infra, Large Water,
     SEZs, Industrial Parks, Textile Parks, Electronics Hubs, Defense Corridors, Common Effluent,
     Data Centers, Telecom Towers, Fixed Networks, Smart Systems, SATCOM,
     Water Supply, Sewage, Solid Waste, Desalination, Storm Water,
     Cold Chain, Cold Storage, Silos, Processing Units, Terminal Markets, Testing Labs,
     Healthcare, Education, Sports, Tourism, Exhibition,
     Solar, Wind, Green Hydrogen, EV Infra, Storage (ESS), Bio-Energy,
     Metals, Mining, Chemicals, Cement, Manufacturing,
     IT Parks, Retail, Hospitality, Residential, Co-working
   - Return the CLOSEST matching sector name from the list above
   - If sector is not clearly mentioned, infer from project description and return best match
   
   **Validation Flags (`validationFlags`):**
   - Leave ALL validation flag fields as null/empty - the backend will populate these
   - Do NOT set stateMismatch, sectorMismatch, or details fields

7) RISK ANALYSIS (CRITICAL - STRUCTURED EVIDENCE ARRAY REQUIRED): For `riskAssessment`, list the top 3-6 risks. For EACH risk you MUST provide:
   - `riskCategory`: Clear name of the risk type
   - `severity`: Exactly one of: High / Medium / Low
   - `description`: Detailed explanation of the risk and its potential impact
   - `mitigationStrategy`: How the risk can be mitigated
   - `evidence`: REQUIRED array of evidence objects. Provide 1-3 evidence items per risk, where EACH evidence item has TWO fields:
     * `quote`: VERBATIM quote from the document - copy EXACT text word-for-word as it appears in the PDF, including all punctuation. Do NOT paraphrase or summarize. Must be searchable with Ctrl+F in the original PDF.
     * `pageLocation`: Specific page and section reference (e.g., "Page 23, Section 4.2" or "Table 5.1, Page 34")

7) **TENDER DETAILS EXTRACTION**:
   - `tenderName`: Name/title of the tender
   - `tenderReferenceNumber`: Reference/ID number
   - `issuingAuthority`: Organization issuing the tender
   - `bidderName`: Name of the bidder/vendor submitting
   - `projectLocation`: city, state, country
   - `tenderType`: Type (Open, Limited, RFP, RFQ, etc.)
   - `submissionDate`: When the bid was submitted
   - `bidValidityPeriod`: How long the bid is valid

8) **FINANCIAL ANALYSIS**:
   - `bidAmount.totalBidValue`: Total bid value
   - `bidAmount.currency`: Currency (INR, USD, etc.)
   - `bidAmount.basePrice`: Base price
   - `bidAmount.taxesAndDuties`: Taxes
   - `bidAmount.totalPriceWithTax`: Total with tax
   - `pricingStructure.itemizedCostBreakdown`: Array of cost items
   - `pricingStructure.paymentTerms`: Payment schedule
   - `financialHealth`: bidder's turnover, networth, solvency

9) **TECHNICAL EVALUATION**:
   - `technicalScore`: 0-100 score for technical capability
   - `complianceMatrix`: technical specs met, deviations
   - `methodologyAndApproach`: with score, findings, strengths, weaknesses, evidence array (EACH evidence item MUST have `quote` field with VERBATIM text from PDF - follow section 5 rules, and `pageLocation`)
   - `projectTimeline`: proposedDuration (MUST be concise like "24 months" or "2 years"), milestones, isTimelineRealistic


10) **BIDDER QUALIFICATIONS**:
    - `experienceScore`: 0-100
    - `pastRelevantProjects`: Array of similar projects completed
    - `teamComposition.keyPersonnel`: Key team members with role, name, experience, qualification

11) **INCONSISTENCY DETECTION** (CRITICAL):
    Thoroughly analyze the document for inconsistencies and populate the `inconsistencyDetection` object:
    - Verify financial figures are consistent across sections
    - Identify timeline conflicts
    - Find conflicting data between sections
    - For EACH issue: provide category, severity (Critical/High/Medium/Low), description, location, detected values, impact, AND evidence
    - **EVIDENCE REQUIRED**: For each inconsistency, provide 1-2 evidence items. Each evidence item MUST have:
      * `quote`: VERBATIM quote from the document
      * `pageLocation`: Specific page and section reference
    - Set `hasInconsistencies` to true if ANY issues found
    - Count total inconsistencies accurately

12) **EVALUATION CRITERIA SCORING** (CRITICAL - WITH EVIDENCE):
    
    Calculate scores in `evaluationCriteria.criteriaBreakdown` based on these 6 pan-India tender evaluation parameters:
    
    - **technicalFeasibilityAndDesign (20%)**: 
      * Does the proposed engineering solution or technology match the specific requirements of the tender?
      * Are specifications of machinery, construction materials, or software stacks compatible and up-to-date?
      * Will the project fail due to outdated or incompatible technology?
      * Score 0-100
    
    - **implementationSchedule (15%)**:
      * Is the total project duration realistic?
      * Are phase-wise deadlines achievable?
      * Analyze the Gantt chart or PERT/CPM network
      * Identify the critical path
      * Is there a risk of time overruns?
      * Score 0-100
    
    - **costEstimateAndBOQ (25%)**:
      * Analyze the Bill of Quantities (BOQ)
      * Are unit rates for major line items accurate?
      * Do they match current Market Rates or Schedule of Rates (SOR)?
      * Is there evidence of cost loading (inflated prices)?
      * Is the budget sufficient to complete the work?
      * Score 0-100
    
    - **riskMitigationAndEnvironment (15%)**:
      * Are risks identified (geological, legal, supply chain)?
      * Are mitigation strategies adequate?
      * Are environmental clearances obtained?
      * Does it ensure regulatory compliance (pollution, land use, etc.)?
      * Does it protect from future liabilities?
      * Score 0-100
    
    - **financialViability (15%)**:
      * Analyze the Financial Internal Rate of Return (FIRR)
      * Evaluate Net Present Value (NPV) and payback period
      * Are projected cash flows realistic?
      * Is the break-even analysis sound?
      * Is the project financially sustainable and does it offer good return on investment?
      * Score 0-100
    
    - **resourceAllocationAndSite (10%)**:
      * What is the land acquisition status?
      * Is there availability of water/power/logistics?
      * Is the manpower plan adequate?
      * Can the project start immediately without Right of Way (ROW) or utility hurdles?
      * Is the site suitable?
      * Score 0-100
    
    For EACH criterion you MUST provide:
    - `score`: 0-100
    - `weight`: decimal (0.20, 0.15, 0.25, 0.15, 0.15, 0.10 respectively)
    - `findings`: what was found
    - `detailedReasoning`: why this score was given (answer the questions above)
    - `evidence`: Array of 1-3 evidence objects with `quote` (VERBATIM - follow section 5 rules EXACTLY) and `pageLocation`
      * CRITICAL: The `quote` field MUST contain EXACT text from the PDF - character-for-character, word-for-word
      * Extract COMPLETE sentences only (no truncation)
      * Do NOT paraphrase, summarize, or add headers
      * The quote MUST be searchable with Ctrl+F in the original PDF
    - `met`: boolean - whether minimum requirements are met

    
    Calculate `overallComplianceScore` = weighted sum of all 6 criteria scores.

13) **SMART RECOMMENDATIONS** (CRITICAL):
    Generate actionable recommendations in `smartRecommendations`:
    - **Critical Actions**: Must-address items before selection
    - **Improvement Suggestions**: Areas where bidder could improve
    - **Negotiation Points**: Areas where the buyer can negotiate better terms
    - **Next Steps**: Prioritized actionable steps

14) JSON ONLY: Your entire response must be parseable JSON ONLY. No extra lines or text.


Scoring rubric (apply to compute overallScore 0-100):
- Weighted components: 
  * Technical Feasibility & Design: 20%
  * Implementation Schedule: 15%
  * Cost Estimate & BOQ: 25%
  * Risk Mitigation & Environment: 15%
  * Financial Viability (FIRR/NPV): 15%
  * Resource Allocation & Site: 10%
- Recommendation thresholds:
  - overallScore >= 80 → "Select"
  - 60 <= overallScore < 80 → "Shortlist"
  - 40 <= overallScore < 60 → "Review"
  - overallScore < 40 → "Reject"


Follow the rubric and trace any deviations. Return only the JSON object.

SCHEMA:
{schema_content}

"""

    
    # Create the user prompt with schema
    user_prompt = f"""Analyze the attached PDF (tender document or bid proposal) and return EXACTLY one JSON object following the schema below.


ADDITIONAL INSTRUCTIONS:
- overallScore: compute a number 0-100 based on the 6 evaluation criteria (technical feasibility, schedule, cost/BOQ, risk/environment, financial viability, resources/site).
- recommendation: one of ["Select", "Shortlist", "Review", "Reject"].
- tenderDetails: extract tender name, reference number, issuing authority, bidder name, location, tender type, submission date.
- financialAnalysis: extract bid amount, pricing structure, and bidder's financial health.
- technicalEvaluation: score technical capability, assess methodology, evaluate timeline.
- bidderQualifications: assess experience, past projects, and team composition.
- evaluationCriteria: score each of the 6 criteria (technicalFeasibilityAndDesign, implementationSchedule, costEstimateAndBOQ, riskMitigationAndEnvironment, financialViability, resourceAllocationAndSite) with findings, reasoning, and evidence with quote and pageLocation.
- riskAssessment: list top 3-6 risks; each risk must include evidence array with quote and pageLocation.
- Always include page references for key citations where possible.

Now analyze the attached file and return EXACTLY the one JSON object described above. No extra text."""
    
    # Create the model with strict instructions
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=system_instruction
    )
    
    def _generate():
        file_obj = genai.get_file(file_ref)
        return model.generate_content([file_obj, user_prompt])

    response = await asyncio.to_thread(_generate)
    
    elapsed = time.time() - start_time
    print(f"✓ JSON generated in {elapsed:.2f}s (response length: {len(response.text)} chars)")
    
    # Parse and validate the JSON
    try:
        # Clean up response text (remove markdown if present)
        response_text = response.text.strip()
        if response_text.startswith('```json'):
            response_text = response_text[7:]
        elif response_text.startswith('```'):
            response_text = response_text[3:]
        
        if response_text.endswith('```'):
            response_text = response_text[:-3]
            
        response_text = response_text.strip()
        
        try:
            parsed_json = json.loads(response_text)
        except json.JSONDecodeError:
            print("⚠ Initial JSON parse failed, attempting robust extraction...")
            # Fallback: try to find JSON object boundaries
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}')
            
            if start_idx != -1 and end_idx != -1:
                json_str = response_text[start_idx:end_idx+1]
                parsed_json = json.loads(json_str)
                print("✓ Robust extraction succeeded")
            else:
                raise
        
        # Validate structure
        if not isinstance(parsed_json, dict):
            raise ValueError("Response is not a JSON object")
        
        # Validate required keys (new tender schema)
        required_keys = [
            "tenderDetails", "executiveSummary", "overallScore", "recommendation",
            "financialAnalysis", "technicalEvaluation", "bidderQualifications",
            "riskAssessment", "inconsistencyDetection", "evaluationCriteria", "smartRecommendations"
        ]
        
        missing_keys = [key for key in required_keys if key not in parsed_json]
        if missing_keys:
            raise ValueError(f"Missing required keys: {missing_keys}")
        
        print(f"✓ JSON validated successfully")
        return parsed_json
        
    except json.JSONDecodeError as e:
        print(f"✗ JSON parsing failed: {e}")
        print(f"Raw response: {response.text[:500]}...")
        raise ValueError(f"Failed to parse JSON from Gemini response: {str(e)}")


async def create_chat_session(dpr_id: int, file_ref: str) -> None:
    """
    Create a new chat session for a DPR if it doesn't exist.
    """
    if dpr_id in _chat_sessions:
        return
    
    print(f"⏳ Creating chat session for DPR {dpr_id}")
    
    def _create_session():
        try:
            # Get the file object
            file_obj = genai.get_file(file_ref)
            
            # Check if file is still valid
            if file_obj.state.name == "FAILED":
                raise ValueError(f"File has expired or is no longer available: {file_ref}")
        except Exception as e:
            error_msg = str(e)
            if "403" in error_msg or "404" in error_msg or "permission" in error_msg.lower() or "not found" in error_msg.lower():
                # Raise specific error for expiration so app.py can handle re-upload
                raise FileExpiredError(f"File {file_ref} has expired or is inaccessible.")
            raise ValueError(f"Cannot access file {file_ref}: {error_msg}")
        
        # Create model with system instructions for chat
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction="""You are a helpful assistant analyzing a Tender/Bid Proposal document.
When answering questions, USE CREATIVE FORMATTING to make responses easy to read:

FORMATTING RULES (Use these liberally):
1. **Bullet Points**: Use - or • for key points, lists, and features
2. **Numbered Lists**: Use 1. 2. 3. for step-by-step or priority ordering
3. **Tables**: Use | for comparisons, metrics, or structured data (example: | Feature | Value |)
4. **Bold**: Use **text** to highlight important terms
5. **Inline Code**: Use `code` for technical terms or references
6. **Sections**: Separate different topics with blank lines

CONTENT REQUIREMENTS:
- Reference specific information from the document
- Cite pages or sections using format: (page: X) or (section: Y)
- Be concise but comprehensive
- If information is not in the document, say so clearly
- Do not make up or hallucinate page numbers or facts

RESPONSE STYLE:
- Prefer visual structure (tables, lists) over paragraphs
- Use formatting to make data scannable
- Group related information together
- Always explain what the numbers or data mean
- For comparisons: use tables with clear headers"""
        )
        
        # Start chat with the document
        chat = model.start_chat(history=[])
        
        return chat, file_obj

    # Offload session creation to thread
    chat, file_obj = await asyncio.to_thread(_create_session)
    
    # Store the chat session and file reference
    _chat_sessions[dpr_id] = {
        'chat': chat,
        'file': file_obj
    }
    
    print(f"✓ Chat session created for DPR {dpr_id}")


async def send_chat_message(dpr_id: int, message: str, file_ref: str) -> Dict:
    """
    Send a message in the chat session and get a response.
    """
    print(f"⏳ Processing chat message for DPR {dpr_id}")
    start_time = time.time()
    
    # Create session if it doesn't exist
    if dpr_id not in _chat_sessions:
        await create_chat_session(dpr_id, file_ref)
    
    session = _chat_sessions[dpr_id]
    chat = session['chat']
    file_obj = session['file']
    
    # Send message with file context (blocking call offloaded)
    response = await asyncio.to_thread(chat.send_message, [file_obj, message])
    
    elapsed = time.time() - start_time
    print(f"✓ Chat response generated in {elapsed:.2f}s (length: {len(response.text)} chars)")
    
    return {
        'reply': response.text,
        'sources': []  # Gemini will include sources in text if instructed properly
    }


# Fallback note for REST API implementation:
# TODO: If google-generativeai SDK is not available, implement REST API fallback:
# - File upload: POST https://generativelanguage.googleapis.com/v1beta/files
# - File status: GET https://generativelanguage.googleapis.com/v1beta/files/{name}
# - Generate: POST https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent
# - Use Authorization: Bearer {GEMINI_API_KEY} header
# - See: https://ai.google.dev/api/rest

def clear_chat_session(dpr_id: int) -> None:
    """Clear the in-memory chat session for a DPR."""
    if dpr_id in _chat_sessions:
        del _chat_sessions[dpr_id]
        print(f"✓ Cleared chat session for DPR {dpr_id}")


# ===== PRAHARI MARKET BENCHMARK ENHANCEMENT (Stage 2) =====

async def enhance_benchmark_analysis(
    criteria: List[Dict],
    deterministic_result: Dict,
    tender_metadata: Dict,
) -> Dict:
    """
    Stage 2 LLM pass: given the deterministic benchmark flags, ask Gemini to:
      - Surface hidden exclusion mechanisms (criteria that seem mild individually
        but together lock out most of the market)
      - Identify potential bid-rigging signals (criteria tailored to a specific vendor)
      - Provide concrete recommendations to improve competition
      - Estimate if the tender is suitable for MSME / startup participation
    Returns a dict with keys: llm_flags, recommendations, msme_suitable, bid_rigging_risk, analysis_text
    """
    import asyncio

    flagged = [
        c for c in deterministic_result.get("per_criterion", [])
        if c.get("flags")
    ]

    prompt = f"""You are a senior government procurement audit specialist analysing a CRPF tender for market competitiveness.

SECTOR: {deterministic_result.get('sector', 'general')}
CONTRACT VALUE: {tender_metadata.get('estimated_contract_value_paise', 'unknown')} paise
COMPETITION INDEX (deterministic): {deterministic_result.get('competition_index')}%
TENDER HEALTH: {deterministic_result.get('tender_health')}

=== CRITERIA LIST ===
{json.dumps(criteria[:25], indent=2, default=str)}

=== DETERMINISTIC FLAGS ===
{json.dumps(flagged, indent=2, default=str)}

TASKS:
1. Identify any COMBINATION of criteria that together exclude most of the market even if each looks reasonable alone.
2. Flag any criterion that appears specifically calibrated for a particular vendor (unusual specificity, niche certifications, non-standard formats).
3. Assess MSME suitability: can a small or medium enterprise realistically compete?
4. Provide 3–5 concrete, actionable recommendations to improve market participation.
5. Rate bid-rigging risk: Low | Medium | High.

Return ONLY a JSON object (no markdown):
{{
  "hidden_exclusion_mechanisms": ["string — describe each combination issue"],
  "tailored_criteria_flags":    ["string — criteria that may be vendor-specific"],
  "msme_suitable":              true | false,
  "msme_barriers":              ["string — specific barriers for MSMEs"],
  "bid_rigging_risk":           "Low | Medium | High",
  "bid_rigging_rationale":      "string",
  "recommendations":            ["string — actionable, numbered 1-5"],
  "analysis_text":              "string — 2-3 sentence executive summary"
}}"""

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        generation_config=genai.types.GenerationConfig(temperature=0.15, max_output_tokens=1024),
    )

    def _run():
        resp = model.generate_content(prompt)
        txt  = resp.text.strip().lstrip("```json").lstrip("```").rstrip("```").strip()
        return json.loads(txt)

    try:
        result = await asyncio.to_thread(_run)
        print(f"✓ Benchmark LLM enhancement complete (bid-rigging risk: {result.get('bid_rigging_risk')})")
        return result
    except Exception as e:
        print(f"⚠ Benchmark LLM enhancement failed: {e}")
        return {
            "hidden_exclusion_mechanisms": [],
            "tailored_criteria_flags":     [],
            "msme_suitable":               None,
            "msme_barriers":               [],
            "bid_rigging_risk":            "Unknown",
            "bid_rigging_rationale":       "LLM analysis unavailable",
            "recommendations":             [],
            "analysis_text":               "LLM enhancement unavailable. Refer to deterministic flags.",
        }


# ===== PRAHARI TENDER CRITERIA EXTRACTION =====

TENDER_SCHEMA_PATH = "backend/tender_schema.json"

async def extract_tender_criteria(file_ref: str) -> Dict:
    """
    Stage 1 of the PRAHARI pipeline: extract all eligibility criteria from a tender PDF.
    Returns a structured dict conforming to tender_schema.json.
    """
    print(f"⏳ Extracting tender criteria from: {file_ref}")
    start_time = time.time()

    with open(TENDER_SCHEMA_PATH, 'r') as f:
        schema_content = f.read()

    system_instruction = f"""You are an expert CRPF government procurement analyst. A procurement officer has uploaded a tender PDF. Your job is Stage 1 of the PRAHARI pipeline: extract ALL eligibility criteria from the tender document and run a self-audit on the tender quality.

MANDATORY RULES:
1. OUTPUT: Return exactly one valid JSON object. No markdown, no extra text.
2. CRITERIA EXTRACTION — extract EVERY eligibility criterion. Miss none. Common types:
   - Financial thresholds: minimum annual turnover, net worth, solvency
   - Technical experience: years of experience, number of similar projects
   - Similar work: specific project types completed in last N years
   - Certifications: ISO, BIS, MSME, DPIIT, etc.
   - Compliance: GST registration, PAN, blacklisting declaration, EMD/BG
   - Personnel: key staff qualifications, experience requirements
   - Infrastructure: owned machinery, lab facilities, manufacturing capacity
   - Document requirements: any document the bidder must submit
3. VERBATIM QUOTES: For every criterion's source_quote field, copy the EXACT text word-for-word from the PDF clause. Include complete sentences. Must be searchable with Ctrl+F.
4. PAGE NUMBERS: Every source_page must be the exact page where the clause appears. Double-check.
5. NORMALISE MONETARY VALUES: Always convert to paise for threshold_value (1 crore = 10,000,000,00 paise = 10^10 paise). Set threshold_unit to "INR_paise".
6. DATE PERIODS: threshold_period must be one of: last_3_financial_years, last_5_years, last_7_years, last_10_years, null.
7. SELF-AUDIT: After extracting all criteria, check the tender for:
   - Contradictions between clauses
   - Ambiguous date references (e.g. "last 5 years" without specifying base date)
   - Combinations of criteria so restrictive that zero bidders could qualify
   - Criteria that require evidence but don't specify what documents are acceptable
   - Threshold values that are unusually high without apparent justification (flag in market_benchmark_flags)
8. DOCUMENT CHECKLIST: List every document the tender explicitly requires bidders to submit.
9. MANDATORY vs PREFERRED: Use modal verbs — "shall", "must", "is required to" = mandatory: true. "Preferred", "desirable", "may" = mandatory: false.
10. JSON ONLY: Entire response must be parseable JSON. No trailing commas.

CRITERION ID FORMAT: CRIT_001, CRIT_002, ... (zero-padded, sequential)
DOCUMENT ID FORMAT: DOC_001, DOC_002, ...
AUDIT ISSUE ID FORMAT: AUDIT_001, AUDIT_002, ...

SCHEMA:
{schema_content}
"""

    user_prompt = """Analyze the attached tender PDF and return EXACTLY one JSON object following the schema.

Extract:
1. tender_metadata — reference number, issuing authority, submission deadline, contract value, evaluation method
2. criteria — EVERY eligibility criterion (financial, technical, compliance, certification, documents, personnel)
3. document_checklist — every document the bidder must submit
4. self_audit — contradictions, ambiguities, over-restrictive combinations, missing doc specifications
5. market_benchmark_flags — any unusually high/low financial thresholds
6. summary — counts and executive summary

Return ONLY the JSON object."""

    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=system_instruction,
        generation_config={"temperature": 0.1}
    )

    def _generate():
        file_obj = genai.get_file(file_ref)
        return model.generate_content([file_obj, user_prompt])

    response = await asyncio.to_thread(_generate)
    elapsed = time.time() - start_time
    print(f"✓ Tender criteria extracted in {elapsed:.2f}s (response: {len(response.text)} chars)")

    response_text = response.text.strip()
    if response_text.startswith('```json'):
        response_text = response_text[7:]
    elif response_text.startswith('```'):
        response_text = response_text[3:]
    if response_text.endswith('```'):
        response_text = response_text[:-3]
    response_text = response_text.strip()

    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError:
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            parsed = json.loads(response_text[start_idx:end_idx+1])
        else:
            raise

    required_keys = ["tender_metadata", "criteria", "document_checklist", "self_audit", "summary"]
    missing = [k for k in required_keys if k not in parsed]
    if missing:
        raise ValueError(f"Criteria extraction missing keys: {missing}")

    print(f"✓ Extracted {len(parsed.get('criteria', []))} criteria, {len(parsed.get('document_checklist', []))} documents, {parsed.get('self_audit', {}).get('total_issues', 0)} audit issues")
    return parsed


# ===== PRAHARI DOCUMENT AUTHENTICITY SCORING =====

_AUTHENTICITY_SCHEMA = {
    "language_detected": "string — BCP-47 code e.g. 'en', 'hi', 'ta', 'te', 'bn', 'mr'",
    "authenticity_score": "float 0.0–1.0 — 1.0 = fully authentic, 0.0 = almost certainly forged",
    "tamper_risk_level": "string — exactly one of: Low | Medium | High",
    "extracted_fields": {
        "document_date": "string — date on the document (ISO 8601) or null",
        "issuing_authority": "string — name of the organisation that issued the document or null",
        "subject_entity": "string — company / person the document is issued to or null",
        "key_numeric_value": "number or null — primary financial or quantitative figure (e.g. turnover in INR)",
        "key_numeric_unit": "string or null — e.g. 'INR_crore', 'INR_lakh', 'years', 'count'",
        "period_covered": "string or null — e.g. '2023-24', 'FY 2021-22 to 2023-24'"
    },
    "flags": [
        {
            "flag_type": "string — one of: font_anomaly | date_inconsistency | signature_anomaly | stamp_anomaly | layout_irregularity | financial_inconsistency | missing_mandatory_element | language_mismatch | seal_anomaly | watermark_anomaly | metadata_mismatch | other",
            "severity": "string — one of: Critical | High | Medium | Low",
            "description": "string — plain-English description of the specific anomaly observed",
            "location": "string or null — where in the document this was observed (e.g. 'Page 1, top-right corner', 'Signature block')"
        }
    ],
    "summary": "string — 2-3 sentence plain-English assessment of authenticity and main concerns"
}


async def score_document_authenticity(file_ref: str, document_type: str) -> Dict:
    """
    Stage 3 of the PRAHARI pipeline: score the authenticity of a bidder-submitted document.

    Uses Gemini's native multimodal vision to inspect the PDF for tampering signals,
    font anomalies, date inconsistencies, signature/stamp irregularities, and OCR
    extraction of key fields (turnover, issuing authority, period covered).

    Returns a dict with keys: language_detected, authenticity_score,
    tamper_risk_level, extracted_fields, flags, summary.
    """
    print(f"⏳ Scoring document authenticity: {file_ref} (type={document_type})")
    start_time = time.time()

    schema_str = json.dumps(_AUTHENTICITY_SCHEMA, indent=2)

    system_instruction = f"""You are a forensic document analyst working for CRPF (Central Reserve Police Force) procurement. A bidder has submitted a supporting document and you must assess its authenticity.

YOUR TASK — analyse the attached document visually, page-by-page, and return EXACTLY one valid JSON object.

DOCUMENT FORMAT HANDLING:
- Typed digital PDFs: inspect the text layer for anomalies AND render each page visually.
- Scanned PDFs: each page is a raster image — apply OCR and inspect for scan-quality based anomalies (low DPI, skew, shadow artefacts, re-scanning artefacts).
- Photographs of physical certificates: check perspective distortion, background uniformity, shadow consistency, and whether the document appears to be photographed flat or at an angle.
- Indic scripts: read all text including Hindi, Bengali, Gujarati, Tamil, etc. Language alone is not an authenticity flag.
- For any page that is partially illegible, note it as a "scan_quality" flag with severity "Low" or "Medium" as appropriate.

AUTHENTICITY SIGNALS TO CHECK (be thorough on every one):
1. **Font anomalies** — inconsistent fonts within a line, pixel artefacts around pasted text, kerning irregularities
2. **Date anomalies** — dates that are logically impossible, future-dated certificates, inconsistent date formats on the same page
3. **Signature / stamp anomalies** — blurred or pixelated signatures, stamps with cut-off edges, digitally pasted seals (sharp outline against background)
4. **Layout irregularities** — misaligned text blocks, inconsistent line spacing, copy-paste artefacts, differing background shades
5. **Financial inconsistency** — figures that change between pages, totals that don't add up, currency symbols mixed
6. **Missing mandatory elements** — e.g. Audited Balance Sheet without CA signature, GST certificate without GSTIN, ISO certificate without accreditation body
7. **Language / script mismatch** — English header but Hindi body without transliteration, inconsistent script
8. **Watermark / seal integrity** — government seals that look like clip-art, low-DPI scans of seals

SCORING RULES:
- authenticity_score 0.9–1.0: No anomalies found, document appears genuine
- authenticity_score 0.7–0.89: Minor anomalies (low-quality scan, slight layout issues), likely genuine
- authenticity_score 0.4–0.69: Moderate anomalies (some suspicious elements), needs human review
- authenticity_score 0.1–0.39: Serious anomalies (multiple red flags), probable forgery
- authenticity_score 0.0–0.09: Almost certainly forged

tamper_risk_level mapping:
- authenticity_score >= 0.7 → "Low"
- 0.4 <= authenticity_score < 0.7 → "Medium"
- authenticity_score < 0.4 → "High"

FIELD EXTRACTION:
- Detect the primary language of the document body (BCP-47 code)
- Extract: document date, issuing authority, subject entity (company name), primary financial figure
- For financial figures: extract as a number and specify unit (INR_crore, INR_lakh, etc.)

OUTPUT RULES:
- Return EXACTLY one JSON object conforming to this schema:
{schema_str}
- No markdown, no extra text
- flags array may be empty [] if no anomalies found
- Every flag entry MUST have flag_type, severity, description, location"""

    user_prompt = f"""Document type submitted by bidder: {document_type}

Carefully examine every page of the attached PDF. Check for all authenticity signals listed in your instructions. Extract the key fields. Return ONLY the JSON object."""

    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=system_instruction,
        generation_config={"temperature": 0.05},
    )

    def _generate():
        file_obj = genai.get_file(file_ref)
        return model.generate_content([file_obj, user_prompt])

    response = await asyncio.to_thread(_generate)
    elapsed = time.time() - start_time
    print(f"✓ Authenticity scoring completed in {elapsed:.2f}s (response: {len(response.text)} chars)")

    response_text = response.text.strip()
    if response_text.startswith('```json'):
        response_text = response_text[7:]
    elif response_text.startswith('```'):
        response_text = response_text[3:]
    if response_text.endswith('```'):
        response_text = response_text[:-3]
    response_text = response_text.strip()

    try:
        parsed = json.loads(response_text)
    except json.JSONDecodeError:
        start_idx = response_text.find('{')
        end_idx = response_text.rfind('}')
        if start_idx != -1 and end_idx != -1:
            parsed = json.loads(response_text[start_idx:end_idx + 1])
        else:
            raise

    # Clamp and normalise
    score = float(parsed.get("authenticity_score", 0.5))
    score = max(0.0, min(1.0, score))
    parsed["authenticity_score"] = round(score, 3)

    if score >= 0.7:
        parsed["tamper_risk_level"] = "Low"
    elif score >= 0.4:
        parsed["tamper_risk_level"] = "Medium"
    else:
        parsed["tamper_risk_level"] = "High"

    if "flags" not in parsed:
        parsed["flags"] = []

    print(f"  → score={parsed['authenticity_score']} risk={parsed['tamper_risk_level']} flags={len(parsed['flags'])} lang={parsed.get('language_detected', '?')}")
    return parsed


# ===== PRAHARI CRITERION MATCHING ENGINE =====

# Non-disqualification confidence threshold — below this, verdict is forced to Manual_Review
_CONFIDENCE_THRESHOLD = 0.90

_VERDICT_SCHEMA = {
    "verdicts": [
        {
            "criterion_id": "string — e.g. CRIT_001",
            "verdict": "string — exactly one of: Eligible | Not_Eligible | Manual_Review",
            "confidence_score": "float 0.0–1.0",
            "extracted_value_text": "string or null — the specific value found in documents, e.g. 'Annual turnover FY 2023-24: INR 18.5 crore'",
            "evidence_quote": "string or null — VERBATIM text from the document that proves/disproves this criterion",
            "evidence_page": "integer or null — page number in the document where evidence was found",
            "evidence_doc_filename": "string or null — which uploaded document contained the evidence",
            "reasoning": "string — plain-English 1-2 sentence explanation of the verdict",
            "missing_docs": "array of strings — document types the bidder should have submitted but didn't"
        }
    ],
    "overall_eligibility": "string — one of: Eligible | Not_Eligible | Manual_Review — based on all mandatory criteria",
    "overall_assessment": "string — 2-3 sentence plain-English summary"
}


def _deterministic_match(criterion: Dict, bidder_docs: List[Dict]) -> Optional[Dict]:
    """
    Fast-path numeric comparison for well-defined financial thresholds.
    Returns a verdict dict if deterministically matchable, else None.

    Handles criteria where:
    - criterion_type in (financial_threshold, turnover, net_worth)
    - comparison_op == 'gte'
    - threshold_value and threshold_unit are set
    - at least one document has extracted_fields.key_numeric_value set
    """
    ctype = criterion.get("criterion_type", "")
    comp_op = criterion.get("comparison_op", "")
    threshold = criterion.get("threshold_value")
    unit = criterion.get("threshold_unit", "")

    if ctype not in ("financial_threshold", "turnover", "net_worth"):
        return None
    if comp_op != "gte" or threshold is None:
        return None
    if unit not in ("INR_paise", "INR_crore", "INR_lakh"):
        return None

    # Convert threshold to crore for comparison
    if unit == "INR_paise":
        threshold_crore = threshold / 1e10
    elif unit == "INR_lakh":
        threshold_crore = threshold / 100
    else:
        threshold_crore = threshold  # already crore

    best_doc = None
    best_value_crore = None

    for doc in bidder_docs:
        meta = doc.get("metadata_flags") or {}
        if isinstance(meta, str):
            try:
                meta = json.loads(meta)
            except Exception:
                continue
        ef = meta.get("extracted_fields") or {}
        val = ef.get("key_numeric_value")
        doc_unit = ef.get("key_numeric_unit", "INR_crore")
        if val is None:
            continue
        try:
            val = float(val)
        except (TypeError, ValueError):
            continue

        if doc_unit == "INR_paise":
            val_crore = val / 1e10
        elif doc_unit == "INR_lakh":
            val_crore = val / 100
        else:
            val_crore = val

        if best_value_crore is None or val_crore > best_value_crore:
            best_value_crore = val_crore
            best_doc = doc

    if best_value_crore is None or best_doc is None:
        return None  # No numeric evidence found — fall through to LLM

    meets = best_value_crore >= threshold_crore
    tamper_risk = best_doc.get("tamper_risk_level", "Medium")
    # Confidence is lower when the document has tamper risk
    if tamper_risk == "Low":
        conf = 0.95
    elif tamper_risk == "Medium":
        conf = 0.80  # not enough for auto-Eligible → Manual_Review
    else:
        conf = 0.55  # High tamper risk → Manual_Review regardless

    meta = best_doc.get("metadata_flags") or {}
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except Exception:
            meta = {}
    ef = meta.get("extracted_fields") or {}

    return {
        "criterion_id": criterion["criterion_id"],
        "verdict": "Eligible" if (meets and conf >= _CONFIDENCE_THRESHOLD) else
                   ("Not_Eligible" if (not meets and conf >= _CONFIDENCE_THRESHOLD) else "Manual_Review"),
        "confidence_score": round(conf, 3),
        "extracted_value_text": f"INR {best_value_crore:.2f} crore — {ef.get('period_covered', '')}".strip(" —"),
        "evidence_quote": None,
        "evidence_page": None,
        "evidence_doc_filename": best_doc.get("original_filename"),
        "reasoning": (
            f"Deterministic match: bidder value {best_value_crore:.2f} crore "
            f"{'meets' if meets else 'does not meet'} threshold {threshold_crore:.2f} crore."
            + (f" Document tamper risk is {tamper_risk} — routed to Manual Review." if not meets or conf < _CONFIDENCE_THRESHOLD else "")
        ),
        "missing_docs": [],
        "_match_method": "deterministic",
    }


async def evaluate_bidder_criteria(
    criteria: List[Dict],
    bidder_documents: List[Dict],
    company_name: str,
) -> List[Dict]:
    """
    Stage 5 of the PRAHARI pipeline: evaluate a bidder against all tender criteria.

    For financial thresholds with numeric evidence: runs a deterministic comparison.
    For everything else: single multimodal Gemini call with all bidder PDFs + all criteria.

    Non-disqualification guarantee: any verdict with confidence_score < 0.90 is
    automatically overridden to Manual_Review.

    Returns a list of verdict dicts (one per criterion).
    """
    print(f"⏳ Evaluating {len(criteria)} criteria for bidder '{company_name}' ({len(bidder_documents)} documents)")
    start_time = time.time()

    # ── Step 1: Deterministic pre-pass ───────────────────────────────────────
    verdicts: Dict[str, Dict] = {}
    remaining_criteria = []

    for crit in criteria:
        det = _deterministic_match(crit, bidder_documents)
        if det is not None:
            verdicts[crit["criterion_id"]] = det
            print(f"  [DET] {crit['criterion_id']} → {det['verdict']} (conf={det['confidence_score']})")
        else:
            remaining_criteria.append(crit)

    # ── Step 2: LLM pass for remaining criteria ───────────────────────────────
    if remaining_criteria:
        # Build file refs list for documents that have one
        file_refs = [
            d["uploaded_file_ref"] for d in bidder_documents if d.get("uploaded_file_ref")
        ]

        # Compact criteria summary to keep prompt tight
        criteria_block = json.dumps([
            {
                "criterion_id": c["criterion_id"],
                "criterion_type": c["criterion_type"],
                "mandatory": c["mandatory"],
                "description": c["description"],
                "comparison_op": c.get("comparison_op"),
                "threshold_value": c.get("threshold_value"),
                "threshold_unit": c.get("threshold_unit"),
                "threshold_period": c.get("threshold_period"),
                "threshold_count": c.get("threshold_count"),
                "accepted_docs": c.get("accepted_docs", []),
                "source_quote": c.get("source_quote", ""),
            }
            for c in remaining_criteria
        ], indent=2)

        # Compact document inventory (metadata already extracted by authenticity scorer)
        doc_inventory = []
        for d in bidder_documents:
            meta = d.get("metadata_flags") or {}
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            doc_inventory.append({
                "filename": d.get("original_filename"),
                "document_type": d.get("document_type"),
                "authenticity_score": d.get("authenticity_score"),
                "tamper_risk_level": d.get("tamper_risk_level"),
                "extracted_fields": meta.get("extracted_fields", {}),
                "language_detected": d.get("language_detected"),
            })
        doc_inventory_str = json.dumps(doc_inventory, indent=2, default=str)

        schema_str = json.dumps(_VERDICT_SCHEMA, indent=2)

        system_instruction = f"""You are a CRPF government procurement evaluator using the PRAHARI AI system. You are assessing whether a bidder meets the eligibility criteria for a tender.

BIDDER: {company_name}

DOCUMENT INVENTORY (metadata already extracted):
{doc_inventory_str}

YOUR TASK:
For each criterion below, examine the attached bidder documents and determine:
1. Does the bidder satisfy this criterion based on the uploaded documents?
2. What is your confidence (0.0–1.0) in this assessment?
3. Quote the specific evidence from the documents.

DOCUMENT FORMAT HANDLING (CRITICAL — read every page regardless of format):
- Typed digital PDFs: extract text directly from the text layer.
- Scanned PDFs: use your OCR vision capability to read text from each scanned page image. Do not skip pages that appear to be images.
- Photographs of certificates / stamps: apply vision OCR to read all visible text, including stamps, seals, handwritten annotations, and watermarks.
- Indic-script documents (Hindi, Bengali, Gujarati, Tamil, Telugu, Kannada, Malayalam, Odia, Punjabi, Assamese, Manipuri): read natively and extract relevant values. Do not treat a non-English document as unreadable.
- Low-quality or partially legible scans: extract what is readable, note the quality issue in reasoning, and set confidence ≤ 0.60.
- Image-only pages with no extractable text: treat the entire page as a photograph and apply visual extraction.

CRITICAL RULES:
1. OUTPUT: Return EXACTLY one JSON object conforming to the schema. No markdown, no extra text.
2. VERBATIM QUOTES: evidence_quote MUST be exact text copied from the document. Searchable with Ctrl+F.
3. PAGE NUMBERS: evidence_page must be the exact page where the evidence appears. Do not guess.
4. CONFIDENCE: Be conservative. Only give confidence >= 0.90 when you can clearly see the evidence in the documents.
   - Scanned document, text clearly readable: confidence 0.80–0.90
   - Scanned document, partially legible: confidence 0.50–0.75 → must be Manual_Review
   - Document in another language but content is clear: confidence 0.85
   - Document present but doesn't clearly satisfy criterion: confidence 0.70–0.84
   - Document missing entirely: confidence 0.15–0.30 for Not_Eligible
   - Clear unambiguous evidence in a digital PDF: confidence 0.90–0.98
5. MISSING DOCS: If the criterion requires a document type that wasn't uploaded, list it in missing_docs.
6. TAMPER RISK: If a document has tamper_risk_level "High", lower your confidence by 0.20 for any verdict based on it.
7. NON-DISQUALIFICATION: You MAY return "Not_Eligible" but ONLY with confidence >= 0.90 AND clear evidence of non-compliance. When in doubt, use "Manual_Review".
8. MANDATORY vs PREFERRED VERDICT LOGIC (STRICT):
   - mandatory=true  → use Eligible / Not_Eligible / Manual_Review normally.
   - mandatory=false → NEVER return "Not_Eligible" unless the bidder explicitly states in writing they do not possess this.
     Absent evidence for an optional criterion → "Manual_Review", not "Not_Eligible".
     Clearly meeting an optional criterion → "Eligible".

VERDICTS:
- "Eligible": Bidder clearly satisfies the criterion.
- "Not_Eligible": Clear documentary evidence the bidder does NOT satisfy the criterion.
- "Manual_Review": Evidence is ambiguous, missing, in a language you cannot read, or confidence < 0.90.

CRITERIA TO EVALUATE:
{criteria_block}

OUTPUT SCHEMA:
{schema_str}"""

        user_prompt = f"""Examine the attached documents for bidder '{company_name}' and evaluate each criterion listed.
Return ONLY the JSON object. No preamble, no explanation outside the JSON."""

        def _generate(refs: list):
            model = genai.GenerativeModel(
                model_name="gemini-2.5-flash",
                system_instruction=system_instruction,
                generation_config={"temperature": 0.05},
            )
            file_objs = [genai.get_file(r) for r in refs]
            return model.generate_content(file_objs + [user_prompt])

        response = await asyncio.to_thread(_generate, file_refs)
        elapsed_llm = time.time() - start_time
        print(f"  [LLM] Response in {elapsed_llm:.2f}s ({len(response.text)} chars)")

        response_text = response.text.strip()
        for prefix in ("```json", "```"):
            if response_text.startswith(prefix):
                response_text = response_text[len(prefix):]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        response_text = response_text.strip()

        try:
            parsed = json.loads(response_text)
        except json.JSONDecodeError:
            s = response_text.find('{')
            e = response_text.rfind('}')
            if s != -1 and e != -1:
                parsed = json.loads(response_text[s:e + 1])
            else:
                raise

        for v in parsed.get("verdicts", []):
            cid = v.get("criterion_id")
            if cid:
                v["_match_method"] = "llm"
                verdicts[cid] = v
                print(f"  [LLM] {cid} → {v.get('verdict')} (conf={v.get('confidence_score')})")

    # ── Step 3: Non-disqualification guarantee ────────────────────────────────
    result = []
    for crit in criteria:
        cid = crit["criterion_id"]
        v = verdicts.get(cid)
        if v is None:
            # Criterion was not evaluated — route to Manual Review
            v = {
                "criterion_id": cid,
                "verdict": "Manual_Review",
                "confidence_score": 0.0,
                "extracted_value_text": None,
                "evidence_quote": None,
                "evidence_page": None,
                "evidence_doc_filename": None,
                "reasoning": "Criterion could not be evaluated — no evidence found.",
                "missing_docs": crit.get("accepted_docs", []),
                "_match_method": "fallback",
            }

        conf = float(v.get("confidence_score") or 0)
        if conf < _CONFIDENCE_THRESHOLD and v["verdict"] != "Manual_Review":
            v["verdict"] = "Manual_Review"
            v["reasoning"] = (
                v.get("reasoning", "") +
                f" [Auto-routed: confidence {conf:.2f} < {_CONFIDENCE_THRESHOLD} threshold]"
            )

        result.append(v)

    elapsed_total = time.time() - start_time
    counts = {k: sum(1 for v in result if v["verdict"] == k) for k in ("Eligible", "Not_Eligible", "Manual_Review")}
    print(f"✓ Evaluation complete in {elapsed_total:.2f}s — Eligible:{counts['Eligible']} Not_Eligible:{counts['Not_Eligible']} Manual_Review:{counts['Manual_Review']}")
    return result


# ===== PRAHARI COLLUSION DETECTION ENGINE =====

_COLLUSION_ALERT_TYPES = (
    "duplicate_document",
    "financial_figure_clustering",
    "common_personnel",
    "identical_certificate",
    "shared_contact_info",
    "timing_anomaly",
    "template_similarity",
    "common_issuing_authority",
    "bid_price_coordination",
    "other",
)

_COLLUSION_SCHEMA = {
    "alerts": [
        {
            "alert_type": f"string — one of: {' | '.join(_COLLUSION_ALERT_TYPES)}",
            "bidder_names_involved": ["array of company name strings"],
            "description": "string — plain-English description of the suspicious pattern",
            "confidence_score": "float 0.0–1.0",
            "evidence": "string — specific details: page numbers, quoted values, filenames",
            "severity": "string — one of: High | Medium | Low",
        }
    ],
    "overall_risk": "string — one of: Low | Medium | High",
    "summary": "string — 2-3 sentence plain-English summary of collusion risk for this tender",
}


def _deterministic_collusion_checks(
    bidders: List[Dict],
    bidder_docs: Dict[int, List[Dict]],
) -> List[Dict]:
    """
    Fast deterministic checks that don't need an LLM:
      1. Duplicate Cloudinary URLs / file_refs across bidders (same PDF re-submitted)
      2. Identical contact emails across bidders
      3. Financial figure clustering (extracted turnover within 2% of each other)
    Returns a list of raw alert dicts (without bidder_ids — app.py fills those).
    """
    alerts = []

    # ── 1. Duplicate document references ─────────────────────────────────────
    ref_to_bidders: Dict[str, List[str]] = {}
    for bidder in bidders:
        bid = bidder["id"]
        for doc in bidder_docs.get(bid, []):
            for ref_key in ("cloudinary_url", "uploaded_file_ref", "cloudinary_public_id"):
                ref = doc.get(ref_key)
                if ref:
                    ref_to_bidders.setdefault(ref, [])
                    entry = f"{bidder['company_name']}:{doc.get('original_filename', '')}"
                    if entry not in ref_to_bidders[ref]:
                        ref_to_bidders[ref].append(entry)

    for ref, entries in ref_to_bidders.items():
        if len(entries) > 1:
            names = list({e.split(":")[0] for e in entries})
            alerts.append({
                "alert_type": "duplicate_document",
                "bidder_names_involved": names,
                "description": f"Identical document file reference shared across {len(names)} bidders.",
                "confidence_score": 0.97,
                "evidence": f"File ref '{ref[:60]}...' appears for: {', '.join(entries)}",
                "severity": "High",
                "_det": True,
            })

    # ── 2. Shared contact email ───────────────────────────────────────────────
    email_to_bidders: Dict[str, List[str]] = {}
    for bidder in bidders:
        email = (bidder.get("contact_email") or "").strip().lower()
        if email:
            email_to_bidders.setdefault(email, []).append(bidder["company_name"])

    for email, names in email_to_bidders.items():
        if len(names) > 1:
            alerts.append({
                "alert_type": "shared_contact_info",
                "bidder_names_involved": names,
                "description": f"Multiple bidders registered with identical contact email '{email}'.",
                "confidence_score": 0.95,
                "evidence": f"Email '{email}' used by: {', '.join(names)}",
                "severity": "High",
                "_det": True,
            })

    # ── 3. Financial figure clustering (within 2%) ────────────────────────────
    fin_vals: List[tuple] = []  # (bidder_name, value_crore, doc_type)
    for bidder in bidders:
        for doc in bidder_docs.get(bidder["id"], []):
            meta = doc.get("metadata_flags") or {}
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    continue
            ef = meta.get("extracted_fields") or {}
            val = ef.get("key_numeric_value")
            unit = ef.get("key_numeric_unit", "INR_crore")
            if val is None:
                continue
            try:
                val = float(val)
            except (TypeError, ValueError):
                continue
            if unit == "INR_paise":
                val_crore = val / 1e10
            elif unit == "INR_lakh":
                val_crore = val / 100
            else:
                val_crore = val
            fin_vals.append((bidder["company_name"], val_crore, doc.get("document_type", "")))

    # Pairwise comparison
    flagged_pairs: set = set()
    for i in range(len(fin_vals)):
        for j in range(i + 1, len(fin_vals)):
            n1, v1, t1 = fin_vals[i]
            n2, v2, t2 = fin_vals[j]
            if n1 == n2:
                continue
            if v1 == 0 and v2 == 0:
                continue
            denom = max(abs(v1), abs(v2))
            if denom > 0 and abs(v1 - v2) / denom < 0.02:
                key = tuple(sorted([n1, n2]))
                if key not in flagged_pairs:
                    flagged_pairs.add(key)
                    alerts.append({
                        "alert_type": "financial_figure_clustering",
                        "bidder_names_involved": list(key),
                        "description": (
                            f"Suspiciously similar financial figures: "
                            f"{n1} reports {v1:.2f} Cr vs {n2} reports {v2:.2f} Cr (within 2%)."
                        ),
                        "confidence_score": 0.75,
                        "evidence": (
                            f"{n1} ({t1}): {v1:.2f} Cr | {n2} ({t2}): {v2:.2f} Cr "
                            f"| Diff: {abs(v1-v2):.4f} Cr"
                        ),
                        "severity": "Medium",
                        "_det": True,
                    })

    return alerts


async def detect_collusion_patterns(
    bidders: List[Dict],
    bidder_docs: Dict[int, List[Dict]],
    tender_name: str = "",
) -> Dict:
    """
    Stage 6 of the PRAHARI pipeline: cross-bidder collusion and integrity analysis.

    Combines deterministic checks (duplicate files, shared emails, financial clustering)
    with a multimodal LLM pass over all bidder documents to detect:
    - Identical/templated certificates, work orders, or balance sheets
    - Common personnel names across competing companies
    - Shared issuing authorities for financial certificates
    - Timing anomalies in document dates
    - Template similarity suggesting coordination

    Returns:
        {
          "alerts": [...],        # merged det + LLM alerts
          "overall_risk": str,    # Low | Medium | High
          "summary": str,
        }
    """
    print(f"⏳ Running collusion detection for tender '{tender_name}' ({len(bidders)} bidders)")
    start_time = time.time()

    # ── Deterministic pass ────────────────────────────────────────────────────
    det_alerts = _deterministic_collusion_checks(bidders, bidder_docs)
    print(f"  [DET] {len(det_alerts)} deterministic alerts")

    # ── LLM pass ─────────────────────────────────────────────────────────────
    all_file_refs: List[str] = []
    bidder_manifest = []
    for bidder in bidders:
        docs = bidder_docs.get(bidder["id"], [])
        doc_list = []
        for d in docs:
            if d.get("uploaded_file_ref"):
                all_file_refs.append(d["uploaded_file_ref"])
            meta = d.get("metadata_flags") or {}
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            doc_list.append({
                "filename": d.get("original_filename"),
                "document_type": d.get("document_type"),
                "authenticity_score": d.get("authenticity_score"),
                "tamper_risk_level": d.get("tamper_risk_level"),
                "extracted_fields": meta.get("extracted_fields", {}),
                "language": d.get("language_detected"),
            })
        bidder_manifest.append({
            "company_name": bidder["company_name"],
            "gstin": bidder.get("gstin"),
            "pan": bidder.get("pan"),
            "contact_email": bidder.get("contact_email"),
            "documents": doc_list,
        })

    schema_str = json.dumps(_COLLUSION_SCHEMA, indent=2)
    manifest_str = json.dumps(bidder_manifest, indent=2, default=str)

    system_instruction = f"""You are a CRPF anti-corruption analyst working on the PRAHARI procurement integrity platform.

You have been given the documents of ALL bidders who applied to the same tender: "{tender_name}"

YOUR TASK: Perform a cross-bidder integrity analysis to detect signs of bid rigging, collusion, or document fraud.

PATTERNS TO LOOK FOR:
1. **Template similarity**: Different companies submitting work orders / certificates that look like they came from the same template (same font, layout, even wording)
2. **Common personnel**: Same person's name appearing as signatory, director, or key staff across multiple supposedly independent companies
3. **Identical issuing authority**: Financial certificates (Turnover, Net Worth) all issued by the same CA firm or same bank — possible coordination
4. **Date clustering**: Multiple companies getting certificates notarised / issued on the same day, especially unusual dates
5. **Inconsistent financial figures**: A company's claimed turnover on one document differs from another they submitted
6. **Shell company signals**: Very similar registered addresses, identical memorandum-of-association templates, same company secretary
7. **Bid price coordination**: If pricing documents are included, prices that are suspiciously close or seem pre-coordinated

BIDDER MANIFEST (already extracted metadata):
{manifest_str}

OUTPUT RULES:
- Return EXACTLY one JSON object. No markdown.
- Only flag patterns you actually observe in the documents — do NOT fabricate
- Each alert must have a specific, evidence-backed description
- confidence_score >= 0.85: strong evidence visible in documents
- confidence_score 0.60–0.84: suggestive but not definitive — Medium severity
- confidence_score < 0.60: weak signal — Low severity
- If no issues found, return alerts: [] and overall_risk: "Low"

OUTPUT SCHEMA:
{schema_str}"""

    user_prompt = f"""Examine all the attached bidder documents for tender '{tender_name}' and identify any collusion or integrity concerns. Return ONLY the JSON object."""

    llm_alerts = []
    overall_risk = "Low"
    summary = "No significant collusion signals detected."

    if all_file_refs:
        try:
            def _generate(refs: list):
                model = genai.GenerativeModel(
                    model_name="gemini-2.5-flash",
                    system_instruction=system_instruction,
                    generation_config={"temperature": 0.05},
                )
                file_objs = [genai.get_file(r) for r in refs]
                return model.generate_content(file_objs + [user_prompt])

            response = await asyncio.to_thread(_generate, all_file_refs)
            elapsed_llm = time.time() - start_time
            print(f"  [LLM] Response in {elapsed_llm:.2f}s ({len(response.text)} chars)")

            rt = response.text.strip()
            for prefix in ("```json", "```"):
                if rt.startswith(prefix):
                    rt = rt[len(prefix):]
            if rt.endswith("```"):
                rt = rt[:-3]
            rt = rt.strip()

            try:
                parsed = json.loads(rt)
            except json.JSONDecodeError:
                s, e = rt.find('{'), rt.rfind('}')
                parsed = json.loads(rt[s:e + 1]) if s != -1 and e != -1 else {"alerts": []}

            llm_alerts = parsed.get("alerts", [])
            overall_risk = parsed.get("overall_risk", "Low")
            summary = parsed.get("summary", summary)
            print(f"  [LLM] {len(llm_alerts)} LLM alerts, overall_risk={overall_risk}")

        except Exception as llm_err:
            print(f"  [LLM] Warning: LLM collusion pass failed: {llm_err}")

    # ── Merge and deduplicate ────────────────────────────────────────────────
    all_alerts = det_alerts + llm_alerts
    # Promote overall_risk if deterministic pass found High severity alerts
    if any(a.get("severity") == "High" for a in det_alerts):
        if overall_risk in ("Low", "Medium"):
            overall_risk = "High"
    elif any(a.get("severity") == "Medium" for a in det_alerts) and overall_risk == "Low":
        overall_risk = "Medium"

    # Strip internal _det flag before returning
    for a in all_alerts:
        a.pop("_det", None)

    elapsed_total = time.time() - start_time
    print(f"✓ Collusion detection complete in {elapsed_total:.2f}s — {len(all_alerts)} alerts, risk={overall_risk}")

    return {
        "alerts": all_alerts,
        "overall_risk": overall_risk,
        "summary": summary,
    }


# ===== COMPARISON CHAT FUNCTIONS =====

# In-memory evaluation Q&A sessions: {project_id: {chat, history}}
# QA sessions are now stored in Postgres (qa_sessions table) — no in-memory dict needed.


def _build_evaluation_context(project: dict, bidders: List[Dict], verdicts: List[Dict],
                               alerts: List[Dict], criteria_data: Optional[Dict]) -> str:
    """Serialise evaluation state into a compact text context for the LLM."""
    lines = []
    lines.append(f"=== TENDER: {project.get('name', 'Unknown')} (ID {project.get('id')}) ===")
    if project.get('description'):
        lines.append(f"Description: {project['description']}")

    # Criteria summary
    if criteria_data:
        criteria_list = criteria_data.get('criteria', [])
        lines.append(f"\n--- ELIGIBILITY CRITERIA ({len(criteria_list)} total) ---")
        for c in criteria_list[:30]:
            lines.append(f"  [{c.get('criterion_id','?')}] {c.get('name','')} | type={c.get('criterion_type','')} | weight={c.get('weight','')} | threshold={c.get('threshold_text','')}")

    # Bidder summary
    lines.append(f"\n--- BIDDERS ({len(bidders)} registered) ---")
    for b in bidders:
        lines.append(f"  [{b['id']}] {b['company_name']} | status={b.get('status','?')} | gstin={b.get('gstin','—')} | pan={b.get('pan','—')}")

    # Verdicts matrix
    lines.append(f"\n--- VERDICTS MATRIX ({len(verdicts)} entries) ---")
    by_bidder: Dict[int, list] = {}
    for v in verdicts:
        by_bidder.setdefault(v['bidder_id'], []).append(v)
    for bid_id, bvs in by_bidder.items():
        name = bvs[0].get('company_name', f'Bidder {bid_id}')
        eligible   = sum(1 for v in bvs if (v.get('override_verdict') or v.get('verdict')) == 'Eligible')
        not_elig   = sum(1 for v in bvs if (v.get('override_verdict') or v.get('verdict')) == 'Not_Eligible')
        manual_rev = sum(1 for v in bvs if (v.get('override_verdict') or v.get('verdict')) == 'Manual_Review')
        avg_conf   = (sum(v.get('confidence_score', 0) for v in bvs) / len(bvs)) if bvs else 0
        lines.append(f"  {name}: Eligible={eligible} Not_Eligible={not_elig} Manual_Review={manual_rev} avg_conf={avg_conf:.2f}")
        for v in bvs:
            eff = v.get('override_verdict') or v.get('verdict', '?')
            conf = v.get('confidence_score', 0)
            ev = v.get('extracted_value_text', '')
            override = ' [OFFICER OVERRIDE]' if v.get('human_override') else ''
            lines.append(f"    criterion={v.get('criterion_id','?')} verdict={eff} conf={conf:.2f}{override} value='{ev}'")

    # Collusion alerts
    if alerts:
        lines.append(f"\n--- COLLUSION ALERTS ({len(alerts)}) ---")
        for a in alerts:
            lines.append(f"  [{a['id']}] type={a['alert_type']} conf={a.get('confidence_score', 0):.2f} bidders={a.get('bidder_ids',[])} | {a.get('description','')[:120]}")

    return "\n".join(lines)


async def answer_evaluation_question(project_id: int, question: str, context: str) -> str:
    """
    Answer a natural-language question about tender evaluation results.
    Chat history is persisted in Postgres so sessions survive server restarts
    and are shared across workers.
    """
    SYSTEM_PROMPT = """You are PRAHARI AI — an expert procurement analyst embedded in the CRPF tender evaluation system.
You have full access to the verdicts matrix, bidder profiles, collusion alerts, and eligibility criteria for this tender.

RULES:
- Answer concisely and precisely. Use bullet points or tables when it aids clarity.
- Always cite criterion IDs and bidder names when discussing specific findings.
- If you mention a confidence score, state it as a percentage (e.g., 87%).
- Never hallucinate data not in the context.
- Flag conflicts of interest, missing evidence, or low-confidence verdicts proactively.
- For monetary thresholds, convert paise to crore (÷10^7) for readability.
- You are an internal tool for authorised CRPF procurement officers only."""

    def _run(q: str) -> str:
        # Load persisted history from Postgres
        history_rows = _db.get_qa_history(project_id)

        # Build Gemini history list from DB rows
        # Always prepend a fresh context preamble so the model has current data
        preamble_user = {"role": "user", "parts": [
            f"Here is the current evaluation context for this tender. Use it to answer subsequent questions.\n\n{context}"
        ]}
        preamble_model = {"role": "model", "parts": [
            "Understood. I have reviewed the evaluation context and am ready to answer your questions about this tender."
        ]}
        prior_history = [{"role": r["role"], "parts": [r["content"]]} for r in history_rows]

        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM_PROMPT,
            generation_config=genai.types.GenerationConfig(
                temperature=0.2,
                max_output_tokens=1024,
            ),
        )
        chat = model.start_chat(history=[preamble_user, preamble_model] + prior_history)
        response = chat.send_message(q)
        answer = response.text

        # Persist the new exchange
        _db.append_qa_messages(project_id, q, answer)
        return answer

    try:
        print(f"⏳ Evaluation Q&A for project {project_id}: {question[:80]}")
        answer = await asyncio.to_thread(_run, question)
        print(f"✓ Evaluation Q&A answered ({len(answer)} chars)")
        return answer
    except Exception as e:
        print(f"✗ Evaluation Q&A error: {e}")
        raise


def clear_evaluation_qa_session(project_id: int) -> None:
    """Delete the persisted Q&A session for a project from Postgres."""
    _db.clear_qa_history(project_id)
    print(f"✓ Cleared evaluation Q&A session for project {project_id}")


# In-memory comparison chat sessions: {comparison_id: chat_object}
_comparison_chat_sessions = {}


async def create_comparison_chat_session(comparison_id: int, file_refs: list[str]) -> None:
    """
    Create a new comparison chat session with multiple files.
    """
    if comparison_id in _comparison_chat_sessions:
        return
    
    print(f"⏳ Creating comparison chat session for comparison {comparison_id} with {len(file_refs)} files")
    
    def _create_session():
        try:
            # Get all file objects
            file_objs = []
            for ref in file_refs:
                try:
                    file_obj = genai.get_file(ref)
                    # Check if file is still valid
                    if file_obj.state.name == "FAILED":
                        raise ValueError(f"File has expired or is no longer available: {ref}")
                    file_objs.append(file_obj)
                except Exception as e:
                    error_msg = str(e)
                    if "403" in error_msg or "404" in error_msg or "permission" in error_msg.lower() or "not found" in error_msg.lower():
                        # Raise specific error for expiration so app.py can handle re-upload
                        raise FileExpiredError(f"File {ref} has expired or is inaccessible.")
                    raise ValueError(f"Cannot access file {ref}: {error_msg}")
        except FileExpiredError:
            raise  # Re-raise to propagate to caller
        except Exception as e:
            raise ValueError(f"Failed to create comparison session: {str(e)}")
        
        # Create detailed system instruction for comparison
        system_instruction = """You are an expert Detailed Project Report (DPR) Analyzer and Comparison Assistant.

Your role is to help users analyze and compare multiple DPR documents simultaneously. When users ask questions, you should:

1. **Cross-Document Analysis**: Compare and contrast information across all provided DPRs
2. **Identify Patterns**: Highlight common themes, differences, strengths, and weaknesses across documents
3. **Financial Comparison**: Compare financial metrics like costs, revenues, IRR, DSCR, payback periods
4. **Risk Assessment Comparison**: Compare risk profiles and mitigation strategies
5. **Recommendations**: Provide comparative insights and recommendations based on the analysis

**Response Guidelines**:
- Always specify which document(s) you're referencing (e.g., "Document 1 shows...", "Compared to Document 2...")
- Use clear comparisons: "higher/lower", "better/worse", "more/less comprehensive"
- Cite page numbers when available, format: (Doc 1, page: X)
- Be objective and data-driven in comparisons
- When asked about specific aspects, compare across ALL documents
- If information is missing from some documents, explicitly state which ones lack that information 
- Provide tabular or structured responses when comparing metrics
- Do not make up or hallucinate facts or page numbers

**Your expertise includes**:
- Financial viability analysis and comparison
- Risk assessment across multiple projects
- Timeline and implementation feasibility comparison
- Resource allocation and cost structure comparison
- Compliance and regulatory requirement comparison

Always maintain a professional, analytical tone and provide actionable insights from your comparisons."""
        
        # Create model with system instructions for comparison
        model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            system_instruction=system_instruction
        )
        
        # Start chat with all documents
        chat = model.start_chat(history=[])
        
        return chat, file_objs

    # Offload to thread
    chat, file_objs = await asyncio.to_thread(_create_session)
    
    # Store the chat session and file references
    _comparison_chat_sessions[comparison_id] = {
        'chat': chat,
        'files': file_objs
    }
    
    print(f"✓ Comparison chat session created for comparison {comparison_id}")


async def send_comparison_message(comparison_id: int, message: str, file_refs: list[str]) -> Dict:
    """
    Send a message in the comparison chat session and get a response.
    """
    print(f"⏳ Processing comparison chat message for comparison {comparison_id}")
    start_time = time.time()
    
    # Create session if it doesn't exist
    if comparison_id not in _comparison_chat_sessions:
        await create_comparison_chat_session(comparison_id, file_refs)
    
    session = _comparison_chat_sessions[comparison_id]
    chat = session['chat']
    file_objs = session['files']
    
    # Send message with all file contexts (blocking call offloaded)
    response = await asyncio.to_thread(chat.send_message, file_objs + [message])
    
    elapsed = time.time() - start_time
    print(f"✓ Comparison chat response generated in {elapsed:.2f}s (length: {len(response.text)} chars)")
    
    return {
        'reply': response.text,
        'sources': []
    }


def clear_comparison_chat_session(comparison_id: int) -> None:
    """Clear the in-memory comparison chat session."""
    if comparison_id in _comparison_chat_sessions:
        del _comparison_chat_sessions[comparison_id]
        print(f"✓ Cleared comparison chat session for comparison {comparison_id}")


# ===== COMPARE ALL DPRs FUNCTION =====

async def compare_all_dprs(dprs: list[dict]) -> dict:
    """
    Compare all DPRs in a project and recommend the best one.
    
    Args:
        dprs: List of DPR objects with id, original_filename, and summary_json
        
    Returns:
        Comparison result with best DPR recommendation and analysis
    """
    print(f"⏳ Comparing {len(dprs)} DPRs...")
    start_time = time.time()
    
    if len(dprs) < 2:
        return {
            'success': False,
            'error': 'Need at least 2 analyzed DPRs to compare'
        }
    
    # Build context with all DPRs
    dprs_context = []
    for i, dpr in enumerate(dprs, 1):
        summary = dpr.get('summary_json', {})
        dprs_context.append(f"""
=== DPR {i}: {dpr.get('original_filename', f'DPR_{dpr.get("id")}')} (ID: {dpr.get('id')}) ===
{json.dumps(summary, indent=2, default=str)}
""")
    
    combined_context = "\n".join(dprs_context)
    
    prompt = f"""You are an expert DPR (Detailed Project Report) analyst. You have been given {len(dprs)} DPR documents for comparison.

YOUR TASK: Analyze all the DPRs below and determine which one is the BEST choice for implementation.

{combined_context}

CRITICAL JSON OUTPUT RULES:
1. Return ONLY a single valid JSON object
2. NO markdown code blocks, NO extra text before or after the JSON
3. ALL string values must have quotes properly escaped
4. Use double quotes for all strings
5. No trailing commas
6. All text in strings must be on a single line (no newlines inside strings)

Please provide your analysis in the following JSON format:
{{
    "bestDprId": <number>,
    "bestDprName": "<filename>",
    "recommendation": "<2-3 sentence summary on ONE line>",
    "comparisonSummary": "<Overview paragraph on ONE line>",
    "keyMetrics": [
        {{
            "metric": "<metric name>",
            "winner": "<filename>",
            "analysis": "<brief comparison on ONE line>"
        }}
    ],
    "dprAnalysis": [
        {{
            "dprId": <number>,
            "dprName": "<filename>",
            "strengths": ["<strength 1>", "<strength 2>"],
            "weaknesses": ["<weakness 1>", "<weakness 2>"],
            "overallScore": "<score out of 10>",
            "verdict": "<1 sentence on ONE line>"
        }}
    ]
}}

Evaluate based on:
1. Financial viability (cost estimates, ROI, funding structure)
2. Technical feasibility (scope, methodology, risk management)
3. Environmental & social impact
4. Implementation timeline and milestones
5. Completeness and quality of documentation

REMEMBER: Return ONLY the JSON object. No markdown, no explanation text."""


    try:
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            generation_config={
                "temperature": 0.2,  # Lower temperature for more consistent JSON
                "max_output_tokens": 8192,  # Increased for detailed comparison
            }
        )
        
        response = await asyncio.to_thread(model.generate_content, prompt)
        
        # Get raw response
        response_text = response.text.strip()
        
        # Debug: Print first 500 chars of raw response
        print(f"🔍 Raw response preview: {response_text[:500]}...")
        
        # Clean up markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split('\n')
            # Remove opening code fence
            if lines[0].startswith("```"):
                lines = lines[1:]
            # Remove closing code fence
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = '\n'.join(lines).strip()
        
        # Try to parse JSON
        try:
            comparison_result = json.loads(response_text)
        except json.JSONDecodeError as json_err:
            # If JSON parsing fails, log detailed info and return error
            print(f"✗ JSON Parse Error: {json_err}")
            print(f"✗ Response text (first 1000 chars): {response_text[:1000]}")
            
            # Try to extract JSON if it's embedded in text
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                try:
                    comparison_result = json.loads(json_match.group(0))
                    print("✓ Successfully extracted JSON from response")
                except:
                    raise json_err
            else:
                raise json_err
        
        elapsed = time.time() - start_time
        print(f"✓ DPR comparison completed in {elapsed:.2f}s")
        
        return {
            'success': True,
            'comparison': comparison_result
        }
        
    except json.JSONDecodeError as e:
        print(f"✗ Failed to parse comparison response as JSON: {e}")
        raw_text = response.text if 'response' in locals() else "No response captured"
        print(f"✗ Full raw response:\n{raw_text}")
        return {
            'success': False,
            'error': f'AI returned invalid JSON format. Please try again.',
            'details': str(e)
        }
    except Exception as e:
        print(f"✗ Comparison error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }

