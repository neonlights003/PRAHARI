import os
import json
import uuid
import secrets
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

import jwt as pyjwt
from fastapi import FastAPI, File, Form, UploadFile, HTTPException, Request as FastAPIRequest
from fastapi.responses import HTMLResponse, JSONResponse, Response, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel
import httpx
import backend.db_config as db_config
from dotenv import load_dotenv
from weasyprint import HTML
import bcrypt

# JWT secret — generated once per process if not in env
_JWT_SECRET = os.getenv("JWT_SECRET") or secrets.token_hex(32)
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 8

# Rate limiter (keyed by client IP)
limiter = Limiter(key_func=get_remote_address)

import backend.db as db
import backend.gemini_client as gemini_client
import backend.report_generator as report_generator
import backend.cloudinary_service as cloudinary_service
import backend.privacy as privacy
import backend.vendor_lookup as vendor_lookup
import backend.market_benchmark as market_benchmark
import backend.document_converter as document_converter

# Load environment variables
load_dotenv()

# Helper function for datetime serialization
def serialize_datetime(obj):
    """Convert datetime objects to ISO format strings for JSON serialization."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif isinstance(obj, dict):
        return {k: serialize_datetime(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize_datetime(item) for item in obj]
    return obj
# Paths
DATA_DIR = Path("data")
SCHEMA_PATH = Path("backend/schema.json")

# Create data directory if it doesn't exist
DATA_DIR.mkdir(exist_ok=True)

# Initialize database
db.init_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    On startup, check for interrupted DPRs and resume processing in background.
    """
    import asyncio
    
    async def resume_processing():
        print("⏳ Checking for interrupted DPR processing...")
        # Run DB query in thread pool to avoid blocking
        processing_dprs = await asyncio.to_thread(db.get_processing_dprs)
        
        if not processing_dprs:
            print("✓ No interrupted DPRs found.")
            return
            
        print(f"⚠ Found {len(processing_dprs)} interrupted DPRs. Resuming processing...")
        
        for dpr in processing_dprs:
            dpr_id = dpr['id']
            filename = dpr['filename']
            file_ref = dpr['uploaded_file_ref']
            filepath = dpr['filepath']
            
            print(f"▶ Resuming analysis for DPR {dpr_id} ({filename})...")
            
            try:
                # Generate analysis (now async)
                parsed_json = await gemini_client.generate_json_from_file(file_ref, str(SCHEMA_PATH))
                
                # Update database (run in thread pool)
                await asyncio.to_thread(db.update_dpr, dpr_id, parsed_json)
                print(f"✓ Completed analysis for DPR {dpr_id}")
                
            except Exception as e:
                error_str = str(e)
                print(f"✗ Failed to resume analysis for DPR {dpr_id}: {error_str}")
                
                # Handle expired file URL
                if "404" in error_str or "403" in error_str or "expired" in error_str.lower():
                    print(f"⚠ File reference expired for DPR {dpr_id}. Re-uploading PDF...")
                    
                    try:
                        # Check if the original file still exists on disk
                        if not os.path.exists(filepath):
                            print(f"✗ Original file not found: {filepath}. Skipping DPR {dpr_id}.")
                            continue
                        
                        # Re-upload the PDF to Gemini
                        new_file_ref = await gemini_client.upload_file(filepath)
                        print(f"✓ Re-uploaded file. New reference: {new_file_ref}")
                        
                        # Update database with new file reference
                        await asyncio.to_thread(db.update_dpr_file_ref, dpr_id, new_file_ref)
                        print(f"✓ Updated database with new file reference")
                        
                        # Retry analysis with new file reference
                        print(f"↺ Retrying analysis for DPR {dpr_id}...")
                        parsed_json = await gemini_client.generate_json_from_file(new_file_ref, str(SCHEMA_PATH))
                        
                        # Update database with analysis results
                        await asyncio.to_thread(db.update_dpr, dpr_id, parsed_json)
                        print(f"✓ Completed analysis for DPR {dpr_id} after re-upload")
                        
                    except Exception as retry_error:
                        print(f"✗ Failed to re-upload and analyze DPR {dpr_id}: {str(retry_error)}")
                        # Leave the DPR in processing state for manual intervention
                else:
                    # For other errors, just log and continue
                    print(f"⚠ Leaving DPR {dpr_id} in processing state for manual review")

    # Start the background task
    asyncio.create_task(resume_processing())
    
    yield
    # Shutdown logic (if any) goes here


# Initialize FastAPI app with lifespan
app = FastAPI(title="PRAHARI — AI Tender Intelligence Platform", version="2.0.0", lifespan=lifespan)

# Attach rate limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5000", "http://127.0.0.1:5000",
        "http://localhost:5001", "http://127.0.0.1:5001",
        "http://localhost:5173", "http://127.0.0.1:5173",
        "http://localhost:5174", "http://127.0.0.1:5174",
        "http://localhost:3000", "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition", "Content-Type", "Content-Length"],
)

DATA_DIR.mkdir(exist_ok=True)

# Initialize database
db.init_db()


# Mount static files and templates
app.mount("/static", StaticFiles(directory="backend/static"), name="static")
app.mount("/data", StaticFiles(directory="data"), name="data")
templates = Jinja2Templates(directory="backend/templates")


# Pydantic models for request/response
class ChatMessage(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str
    sources: list
    message_id: int

class CreateComparisonRequest(BaseModel):
    name: str
    dpr_ids: list[int]




class CreateProjectRequest(BaseModel):
    name: str
    state: str
    scheme: str
    sector: str


class UpdateComplianceWeightsRequest(BaseModel):
    weights: dict
    recalculate: bool = False


class CreateBidderRequest(BaseModel):
    company_name: str
    gstin: str = None
    pan: str = None
    contact_email: str = None


class HumanOverrideRequest(BaseModel):
    override_verdict: str
    justification: str
    officer_id: int


class ResolveAlertRequest(BaseModel):
    disposition: str
    notes: str = None
    officer_id: int



class AdminLoginRequest(BaseModel):
    admin_id: str
    password: str


class AdminLoginResponse(BaseModel):
    success: bool
    message: str


class UserRegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    confirm_password: str


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserAuthResponse(BaseModel):
    success: bool
    message: str
    user: dict = None


# ===== ADMIN AUTH API ROUTES =====

@app.post("/api/admin/login")
@limiter.limit("5/minute")
async def admin_login(http_req: FastAPIRequest, request: AdminLoginRequest):
    """Authenticate admin user with credentials from environment variables."""
    admin_id = os.getenv("ADMIN_ID")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if not admin_id or not admin_password:
        raise HTTPException(status_code=500, detail="Admin credentials not configured")

    if request.admin_id == admin_id and request.password == admin_password:
        now = datetime.now(timezone.utc)
        payload = {
            "sub": admin_id,
            "role": "admin",
            "iat": now,
            "exp": now + timedelta(hours=JWT_EXPIRY_HOURS),
        }
        token = pyjwt.encode(payload, _JWT_SECRET, algorithm=JWT_ALGORITHM)
        return JSONResponse({
            "success": True,
            "message": "Login successful",
            "token": token,
        })
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")


# ===== USER AUTH API ROUTES =====

@app.post("/api/user/register")
async def user_register(request: UserRegisterRequest):
    """Register a new user account."""
    # Validate password match
    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")
    
    # Validate password length
    if len(request.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    
    # Validate email format (basic check)
    if '@' not in request.email or '.' not in request.email:
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    try:
        # Hash password with bcrypt
        # Ensure password is a string, then encode to bytes for bcrypt
        password_str = str(request.password)
        password_bytes = password_str.encode('utf-8')
        
        # Generate salt and hash (cost factor 12 for good security/performance balance)
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Decode back to string for database storage (TEXT column)
        password_hash = hashed.decode('utf-8')
        
        # Create user in database
        user_id = db.create_user(request.email, password_hash, request.name)
        
        return JSONResponse({
            "success": True,
            "message": "Registration successful",
            "user": {
                "id": user_id,
                "name": request.name,
                "email": request.email
            }
        })
    except ValueError as e:
        # Handle duplicate email
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"✗ Registration error: {str(e)}")
        print(f"✗ Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()
        # Return the actual error message
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")


@app.post("/api/user/login")
async def user_login(request: UserLoginRequest):
    """Authenticate user with username/email and password."""
    try:
        # Get user by email
        user = db.get_user_by_email(request.email)
        
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Verify password using bcrypt
        # Ensure password is a string, then encode to bytes for bcrypt
        password_str = str(request.password)
        password_bytes = password_str.encode('utf-8')
        
        # Get stored hash and ensure it's bytes for bcrypt comparison
        stored_hash = user["password_hash"]
        if isinstance(stored_hash, str):
            stored_hash_bytes = stored_hash.encode('utf-8')
        else:
            stored_hash_bytes = stored_hash
        
        # Verify password - bcrypt.checkpw returns True/False
        try:
            password_valid = bcrypt.checkpw(password_bytes, stored_hash_bytes)
        except Exception as bcrypt_error:
            print(f"✗ Bcrypt verification error: {str(bcrypt_error)}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        if not password_valid:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Return success with user info (excluding password hash)
        return JSONResponse({
            "success": True,
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"]
            }
        })
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Login error: {str(e)}")
        raise HTTPException(status_code=500, detail="Login failed")


# ===== CLIENT DPR API ROUTES =====

@app.post("/api/client/dprs/upload")
async def client_upload_dpr(
    client_id: int = Form(...),
    project_id: int = Form(...),
    project_name: str = Form(...),
    file: UploadFile = File(...)
):
    """Upload a DPR PDF for a specific client. Creates an unanalyzed DPR that admin can analyze later."""
    # Validate inputs
    if not project_name or not project_name.strip():
        raise HTTPException(status_code=400, detail="Project name is required")
    
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")
    
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")
    
    try:
        # Check if client already has a DPR for this project
        conn = db_config.get_connection()
        cursor = db_config.get_cursor(conn, dict_cursor=False)
        cursor.execute("""
            SELECT id FROM dprs 
            WHERE project_id = %s AND client_id = %s
        """, (project_id, client_id))
        existing_dpr = cursor.fetchone()
        cursor.close()
        db_config.release_connection(conn)
        
        if existing_dpr:
            raise HTTPException(
                status_code=400, 
                detail="You have already uploaded a DPR for this project. Only one DPR per project is allowed."
            )
        
        original_filename = file.filename
        
        # Generate unique filename for storage (same as admin uploads)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{unique_id}_{original_filename}"
        filepath = DATA_DIR / filename
        
        # Save the uploaded file to data/ directory
        print(f"⏳ Saving client DPR: {filename}")
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)
        print(f"✓ File saved: {filepath} ({len(content)} bytes)")
        
        # Upload to Gemini Files API for future analysis
        file_ref = await gemini_client.upload_file(str(filepath))
        
        # Upload to Cloudinary for persistent storage
        cloudinary_result = cloudinary_service.upload_pdf(str(filepath), public_id=f"dprs/{filename}")
        
        # Insert record into dprs table WITHOUT analysis initially
        print(f"⏳ Inserting client DPR record for {filename}...")
        print(f"🔍 DEBUG: cloudinary_result = {cloudinary_result}")
        print(f"🔍 DEBUG: cloudinary_url = {cloudinary_result.get('secure_url')}")
        print(f"🔍 DEBUG: cloudinary_public_id = {cloudinary_result.get('public_id')}")
        
        dpr_id = db.insert_dpr(
            filename=filename,
            original_filename=original_filename,
            filepath=str(filepath),  # Keep local path for now
            file_ref=file_ref,
            summary_json=None,  # Will be populated after analysis
            project_id=project_id,
            cloudinary_url=cloudinary_result['secure_url'],  # ✅ Cloudinary URL here
            cloudinary_public_id=cloudinary_result['public_id']
        )
        
        print(f"🔍 DEBUG: DPR {dpr_id} inserted")
        
        # Update the record with client_id and set status to 'analyzing'
        conn = db_config.get_connection()
        cursor = db_config.get_cursor(conn, dict_cursor=False)
        cursor.execute("UPDATE dprs SET client_id = %s, status = 'analyzing' WHERE id = %s", (client_id, dpr_id))
        conn.commit()
        cursor.close()
        db_config.release_connection(conn)
        
        # Clean up local file after upload to cloud
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"✓ Cleaned up local file: {filepath}")
        except Exception as e:
            print(f"⚠ Could not delete local file: {e}")
        
        # Automatically analyze the DPR
        try:
            print(f"⏳ Auto-analyzing client DPR {dpr_id}...")
            parsed_json = await gemini_client.generate_json_from_file(file_ref, str(SCHEMA_PATH))
            print(f"✓ Analysis complete for DPR {dpr_id}")
            
            # Validate DPR against project and populate validationFlags
            parsed_json = db.validate_dpr_against_project(dpr_id, project_id, parsed_json)
            
            # Update database with analysis results (including validationFlags)
            db.update_dpr(dpr_id, parsed_json)
            
            conn = db_config.get_connection()
            cursor = db_config.get_cursor(conn, dict_cursor=False)
            cursor.execute("UPDATE dprs SET status = 'completed' WHERE id = %s", (dpr_id,))
            conn.commit()
            cursor.close()
            db_config.release_connection(conn)
            
            return JSONResponse({
                "success": True,
                "message": "DPR uploaded and analyzed successfully!",
                "dpr_id": dpr_id,
                "analyzed": True
            })
            
        except Exception as analysis_error:
            # If analysis fails, set status to 'pending' so admin can retry
            print(f"✗ Auto-analysis failed for DPR {dpr_id}: {str(analysis_error)}")
            
            conn = db_config.get_connection()
            cursor = db_config.get_cursor(conn, dict_cursor=False)
            cursor.execute("UPDATE dprs SET status = 'pending' WHERE id = %s", (dpr_id,))
            conn.commit()
            cursor.close()
            db_config.release_connection(conn)
            
            # Still return success for upload, but note analysis failed
            return JSONResponse({
                "success": True,
                "message": "DPR uploaded successfully, but analysis failed. An admin can analyze it later.",
                "dpr_id": dpr_id,
                "analyzed": False,
                "analysis_error": str(analysis_error)
            })
    
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Client DPR upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload DPR: {str(e)}")




@app.get("/api/client/dprs")
async def get_client_dprs_list(client_id: int):
    """Get all DPRs for a specific client from the main dprs table."""
    try:
        conn = db_config.get_connection()
        cursor = db_config.get_cursor(conn, dict_cursor=True)
        
        cursor.execute("""
            SELECT d.id, d.project_id, d.client_id, d.original_filename, 
                   d.filename as dpr_filename,
                   d.upload_ts as created_at, d.status,
                   d.admin_feedback, d.feedback_timestamp,
                   p.name as project_name
            FROM dprs d
            LEFT JOIN projects p ON d.project_id = p.id
            WHERE d.client_id = %s
            ORDER BY d.upload_ts DESC
        """, (client_id,))
        
        rows = cursor.fetchall()
        cursor.close()
        db_config.release_connection(conn)
        
        dprs = [dict(row) for row in rows]
        dprs = serialize_datetime(dprs)  # Serialize datetime objects
        return JSONResponse({"dprs": dprs, "count": len(dprs)})
    except Exception as e:
        print(f"✗ Get client DPRs error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve DPRs: {str(e)}")




@app.get("/api/client/dprs/{dpr_id}/download")
async def download_client_dpr(dpr_id: int, client_id: int):
    """Download a client's DPR PDF."""
    try:
        # Get DPR record
        dpr = db.get_client_dpr(dpr_id)
        if not dpr:
            raise HTTPException(status_code=404, detail=f"DPR {dpr_id} not found")
        
        # Security check: ensure the DPR belongs to the requesting client
        if dpr["client_id"] != client_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        # Construct file path
        filepath = Path("uploads") / str(client_id) / dpr["dpr_filename"]
        
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="File not found on server")
        
        # Read file and return
        with open(filepath, "rb") as f:
            content = f.read()
        
        return Response(
            content=content,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={dpr['original_filename']}"
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Download client DPR error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to download DPR: {str(e)}")


@app.delete("/api/client/dprs/{dpr_id}")
async def delete_client_dpr(dpr_id: int, client_id: int):
    """Delete a client's DPR. Allows client to upload a new DPR to that project."""
    try:
        # Get DPR record
        dpr = db.get_dpr(dpr_id)
        if not dpr:
            raise HTTPException(status_code=404, detail=f"DPR {dpr_id} not found")
        
        # Debug logging
        print(f"DEBUG: DPR data: {dpr}")
        print(f"DEBUG: dpr.get('client_id') = {dpr.get('client_id')} (type: {type(dpr.get('client_id'))})")
        print(f"DEBUG: client_id parameter = {client_id} (type: {type(client_id)})")
        
        # Security check: ensure the DPR belongs to the requesting client
        if dpr.get("client_id") != client_id:
            print(f"✗ Access denied: DPR client_id={dpr.get('client_id')}, request client_id={client_id}")
            raise HTTPException(status_code=403, detail="Access denied. You can only delete your own DPRs.")
        
        # Delete the file
        filepath = Path(dpr["filepath"])
        if filepath.exists():
            filepath.unlink()
            print(f"✓ Deleted file: {filepath}")
        
        # Delete database record
        db.delete_dpr(dpr_id)
        print(f"✓ Deleted DPR record: {dpr_id}")
        
        return JSONResponse({
            "success": True,
            "message": "DPR deleted successfully. You can now upload a new DPR to this project."
        })
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Delete client DPR error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete DPR: {str(e)}")



# ===== DPR FEEDBACK API ROUTE =====

@app.put("/dprs/{dpr_id}/feedback")
async def update_dpr_feedback_endpoint(dpr_id: int, feedback: str = Form(...)):
    """Admin endpoint to add/update feedback for a DPR."""
    try:
        # Check if DPR exists
        dpr = db.get_dpr(dpr_id)
        if not dpr:
            raise HTTPException(status_code=404, detail=f"DPR {dpr_id} not found")
        
        # Update feedback
        db.update_dpr_feedback(dpr_id, feedback)
        
        return JSONResponse({
            "success": True,
            "message": "Feedback updated successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Update feedback error: {str(e)}") 
        raise HTTPException(status_code=500, detail=f"Failed to update feedback: {str(e)}")


@app.put("/dprs/{dpr_id}/status")
async def update_dpr_status_endpoint(dpr_id: int, status: str = Form(...)):
    """Admin endpoint to update DPR status (accepted, rejected, pending)."""
    try:
        # Validate status
        valid_statuses = ['pending', 'accepted', 'rejected', 'completed', 'analyzing']
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        # Check if DPR exists
        dpr = db.get_dpr(dpr_id)
        if not dpr:
            raise HTTPException(status_code=404, detail=f"DPR {dpr_id} not found")
        
        # Update status
        db.update_dpr_status(dpr_id, status)
        
        return JSONResponse({
            "success": True,
            "message": f"DPR status updated to '{status}' successfully"
        })
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Update status error: {str(e)}") 
        raise HTTPException(status_code=500, detail=f"Failed to update status: {str(e)}")



# ===== PRAHARI TENDER CRITERIA API =====

TENDER_SCHEMA_PATH = Path("backend/tender_schema.json")

@app.post("/api/tenders/{project_id}/extract-criteria")
@limiter.limit("10/minute")
async def extract_tender_criteria(http_req: FastAPIRequest, project_id: int):
    """
    Stage 1 of the PRAHARI pipeline.
    Trigger criteria extraction on an uploaded tender PDF (stored as a DPR in the project).
    Returns the structured criteria schema and self-audit results.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Tender {project_id} not found")

    dprs = db.get_dprs_by_project(project_id)
    if not dprs:
        raise HTTPException(status_code=400, detail="No tender PDF uploaded for this tender yet")

    tender_dpr = dprs[0]
    file_ref = tender_dpr.get("uploaded_file_ref")
    if not file_ref:
        raise HTTPException(status_code=400, detail="Tender PDF has not been uploaded to Gemini yet")

    try:
        criteria_data = await gemini_client.extract_tender_criteria(file_ref)

        conn = db_config.get_connection()
        cursor = db_config.get_cursor(conn, dict_cursor=False)
        cursor.execute(
            "UPDATE dprs SET summary_json = %s, status = 'completed' WHERE id = %s",
            (json.dumps(criteria_data), tender_dpr["id"])
        )
        conn.commit()
        cursor.close()
        db_config.release_connection(conn)

        return JSONResponse({
            "success": True,
            "project_id": project_id,
            "criteria_count": len(criteria_data.get("criteria", [])),
            "document_count": len(criteria_data.get("document_checklist", [])),
            "audit_issues": criteria_data.get("self_audit", {}).get("total_issues", 0),
            "criteria_data": criteria_data
        })

    except Exception as e:
        print(f"✗ Criteria extraction error for project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Criteria extraction failed: {str(e)}")


@app.get("/api/tenders/{project_id}/criteria")
async def get_tender_criteria(project_id: int):
    """Get previously extracted criteria for a tender."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Tender {project_id} not found")

    dprs = db.get_dprs_by_project(project_id)
    if not dprs or not dprs[0].get("summary_json"):
        raise HTTPException(status_code=404, detail="Criteria not yet extracted for this tender")

    criteria_data = dprs[0]["summary_json"]
    if isinstance(criteria_data, str):
        import json as _json
        criteria_data = _json.loads(criteria_data)

    return JSONResponse({
        "success": True,
        "project_id": project_id,
        "criteria_data": criteria_data
    })


# ===== MARKET BENCHMARK VALIDATION (Stage 2) =====

@app.post("/api/tenders/{project_id}/benchmark")
async def run_market_benchmark(project_id: int, enhance: bool = True):
    """
    Stage 2 of the PRAHARI pipeline — validate extracted criteria against
    sector benchmarks and compute the market competition index.

    Query params:
      enhance=true  — also run the Gemini LLM enhancement pass (default: true)
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Tender {project_id} not found")

    dprs = db.get_dprs_by_project(project_id)
    if not dprs or not dprs[0].get("summary_json"):
        raise HTTPException(
            status_code=400,
            detail="Tender criteria not yet extracted. Run /extract-criteria first.",
        )

    raw = dprs[0]["summary_json"]
    criteria_data = json.loads(raw) if isinstance(raw, str) else raw
    criteria      = criteria_data.get("criteria", [])
    tender_meta   = criteria_data.get("tender_metadata", {})

    if not criteria:
        raise HTTPException(status_code=400, detail="No criteria found. Re-run criteria extraction.")

    # Pass 1 — deterministic
    det_result = market_benchmark.run_deterministic_validation(criteria, tender_meta)

    # Pass 2 — LLM enhancement
    llm_result: Dict = {}
    if enhance:
        try:
            llm_result = await gemini_client.enhance_benchmark_analysis(
                criteria=criteria,
                deterministic_result=det_result,
                tender_metadata=tender_meta,
            )
        except Exception as e:
            print(f"⚠ Benchmark LLM pass failed: {e}")

    # Merge
    result = {
        "project_id":   project_id,
        "project_name": project.get("name"),
        **det_result,
        "llm_analysis": llm_result,
    }

    db.insert_audit_event(
        event_type="benchmark_validation",
        payload={
            "competition_index": det_result.get("competition_index"),
            "tender_health":     det_result.get("tender_health"),
            "bid_rigging_risk":  llm_result.get("bid_rigging_risk"),
        },
        project_id=project_id,
    )

    return JSONResponse(serialize_datetime(result))


# ===== PRAHARI BIDDER INGESTION API =====

@app.post("/api/tenders/{project_id}/bidders")
async def register_bidder(project_id: int, request: CreateBidderRequest):
    """
    Stage 2 of the PRAHARI pipeline — register a bidder for a tender.
    Creates the bidder record; documents are uploaded separately.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Tender {project_id} not found")

    if not request.company_name or not request.company_name.strip():
        raise HTTPException(status_code=400, detail="company_name is required")

    try:
        bidder_id = db.create_bidder(
            project_id=project_id,
            company_name=request.company_name.strip(),
            gstin=request.gstin,
            pan=request.pan,
            contact_email=request.contact_email,
        )

        db.insert_audit_event(
            event_type="bidder_registered",
            payload={"company_name": request.company_name, "gstin": request.gstin},
            project_id=project_id,
            bidder_id=bidder_id,
        )

        return JSONResponse({
            "success": True,
            "bidder_id": bidder_id,
            "company_name": request.company_name,
            "project_id": project_id,
        })

    except Exception as e:
        print(f"✗ Register bidder error for project {project_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to register bidder: {str(e)}")


@app.get("/api/tenders/{project_id}/bidders")
async def list_bidders(project_id: int):
    """List all registered bidders for a tender."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Tender {project_id} not found")

    bidders = db.get_bidders_by_project(project_id)
    bidders = serialize_datetime(bidders)
    return JSONResponse({"bidders": bidders, "count": len(bidders)})


@app.get("/api/bidders/{bidder_id}")
async def get_bidder(bidder_id: int):
    """Get bidder details including all uploaded documents."""
    bidder = db.get_bidder(bidder_id)
    if not bidder:
        raise HTTPException(status_code=404, detail=f"Bidder {bidder_id} not found")

    docs = db.get_bidder_documents(bidder_id)
    bidder = serialize_datetime(bidder)
    docs = serialize_datetime(docs)
    bidder["documents"] = docs
    return JSONResponse(bidder)


@app.delete("/api/bidders/{bidder_id}")
async def delete_bidder(bidder_id: int):
    """Remove a bidder and all their documents from a tender."""
    bidder = db.get_bidder(bidder_id)
    if not bidder:
        raise HTTPException(status_code=404, detail=f"Bidder {bidder_id} not found")

    try:
        conn = db_config.get_connection()
        cursor = db_config.get_cursor(conn, dict_cursor=False)
        cursor.execute("DELETE FROM bidders WHERE id = %s", (bidder_id,))
        conn.commit()
        cursor.close()
        db_config.release_connection(conn)

        return JSONResponse({"success": True, "message": f"Bidder {bidder_id} deleted"})

    except Exception as e:
        print(f"✗ Delete bidder error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete bidder: {str(e)}")


@app.post("/api/bidders/{bidder_id}/documents")
async def upload_bidder_document(
    bidder_id: int,
    document_type: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Stage 2 of the PRAHARI pipeline — upload a supporting document for a bidder.
    Accepts PDF, DOCX/DOC (Word), JPG, PNG, WEBP, TIFF — typed or scanned.
    DOCX files are converted to plain text before Gemini ingestion; images are
    processed via Gemini vision multimodal. All originals are stored on Cloudinary.
    """
    bidder = db.get_bidder(bidder_id)
    if not bidder:
        raise HTTPException(status_code=404, detail=f"Bidder {bidder_id} not found")

    if not file.filename:
        raise HTTPException(status_code=400, detail="No file selected")

    if not document_converter.is_accepted(file.filename):
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Accepted: PDF, DOCX, DOC, JPG, PNG, WEBP, TIFF"
        )

    try:
        original_filename = file.filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        stored_name = f"bidder_{bidder_id}_{timestamp}_{unique_id}_{original_filename}"
        filepath = DATA_DIR / stored_name

        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)

        # Convert DOCX/images to Gemini-compatible format if needed, then upload
        gemini_path, _mime = document_converter.prepare_for_gemini(str(filepath), original_filename)
        file_ref = await gemini_client.upload_file(gemini_path)
        # Clean up extracted text file if one was created (DOCX conversion)
        if gemini_path != str(filepath) and os.path.exists(gemini_path):
            try:
                os.remove(gemini_path)
            except Exception:
                pass

        # Upload original file to Cloudinary for persistent storage (resource_type=raw handles all types)
        cloudinary_result = cloudinary_service.upload_pdf(
            str(filepath), public_id=f"bidder_docs/{stored_name}"
        )

        doc_id = db.create_bidder_document(
            bidder_id=bidder_id,
            document_type=document_type,
            original_filename=original_filename,
            uploaded_file_ref=file_ref,
            cloudinary_url=cloudinary_result.get("secure_url"),
            cloudinary_public_id=cloudinary_result.get("public_id"),
        )

        # Clean up local temp file
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception:
            pass

        # Run authenticity scoring immediately after upload
        try:
            auth_result = await gemini_client.score_document_authenticity(file_ref, document_type)
            db.update_bidder_document_authenticity(
                doc_id=doc_id,
                language_detected=auth_result.get("language_detected"),
                authenticity_score=auth_result.get("authenticity_score", 0.5),
                tamper_risk_level=auth_result.get("tamper_risk_level", "Medium"),
                metadata_flags={
                    "flags": auth_result.get("flags", []),
                    "extracted_fields": auth_result.get("extracted_fields", {}),
                    "summary": auth_result.get("summary", ""),
                },
            )
            print(f"✓ Authenticity scored for doc {doc_id}: {auth_result.get('tamper_risk_level')} risk")
        except Exception as auth_err:
            print(f"⚠ Authenticity scoring failed for doc {doc_id}: {auth_err}")
            auth_result = {}

        doc_kind = document_converter.detect_document_kind(original_filename)
        db.insert_audit_event(
            event_type="document_uploaded",
            payload={
                "document_type": document_type,
                "original_filename": original_filename,
                "file_kind": doc_kind,       # pdf | word | image
                "authenticity_score": auth_result.get("authenticity_score"),
                "tamper_risk_level": auth_result.get("tamper_risk_level"),
            },
            project_id=bidder["project_id"],
            bidder_id=bidder_id,
        )

        return JSONResponse({
            "success": True,
            "doc_id": doc_id,
            "bidder_id": bidder_id,
            "document_type": document_type,
            "original_filename": original_filename,
            "authenticity_score": auth_result.get("authenticity_score"),
            "tamper_risk_level": auth_result.get("tamper_risk_level"),
            "authenticity_flags": len(auth_result.get("flags", [])),
        })

    except Exception as e:
        print(f"✗ Upload bidder document error for bidder {bidder_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload document: {str(e)}")


@app.get("/api/bidders/{bidder_id}/documents")
async def list_bidder_documents(bidder_id: int):
    """List all uploaded documents for a bidder."""
    bidder = db.get_bidder(bidder_id)
    if not bidder:
        raise HTTPException(status_code=404, detail=f"Bidder {bidder_id} not found")

    docs = db.get_bidder_documents(bidder_id)
    docs = serialize_datetime(docs)
    return JSONResponse({"bidder_id": bidder_id, "documents": docs, "count": len(docs)})


# ===== PRAHARI CRITERION MATCHING API =====

@app.post("/api/tenders/{project_id}/bidders/{bidder_id}/evaluate")
@limiter.limit("20/minute")
async def evaluate_bidder(http_req: FastAPIRequest, project_id: int, bidder_id: int):
    """
    Stage 5 of the PRAHARI pipeline — run criterion matching for one bidder.
    Reads extracted tender criteria, scores each criterion against the bidder's
    uploaded documents, applies the non-disqualification guarantee, and persists
    all verdicts to the database.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Tender {project_id} not found")

    bidder = db.get_bidder(bidder_id)
    if not bidder:
        raise HTTPException(status_code=404, detail=f"Bidder {bidder_id} not found")
    if bidder["project_id"] != project_id:
        raise HTTPException(status_code=400, detail="Bidder does not belong to this tender")

    # Load tender criteria from the tender's DPR summary_json
    dprs = db.get_dprs_by_project(project_id)
    if not dprs or not dprs[0].get("summary_json"):
        raise HTTPException(status_code=400, detail="Tender criteria not yet extracted. Run /extract-criteria first.")

    criteria_data = dprs[0]["summary_json"]
    if isinstance(criteria_data, str):
        import json as _j
        criteria_data = _j.loads(criteria_data)

    criteria = criteria_data.get("criteria", [])
    if not criteria:
        raise HTTPException(status_code=400, detail="No criteria found in tender. Re-run criteria extraction.")

    bidder_docs = db.get_bidder_documents(bidder_id)
    if not bidder_docs:
        raise HTTPException(status_code=400, detail="No documents uploaded for this bidder yet.")

    try:
        db.update_bidder_status(bidder_id, "evaluating")

        raw_verdicts = await gemini_client.evaluate_bidder_criteria(
            criteria=criteria,
            bidder_documents=bidder_docs,
            company_name=bidder["company_name"],
        )

        # Map evidence_doc_filename → doc_id for FK reference
        filename_to_doc_id = {d["original_filename"]: d["id"] for d in bidder_docs}

        # Build mandatory lookup for the safety-net below
        crit_mandatory_map = {c["criterion_id"]: c.get("mandatory", True) for c in criteria}

        saved_verdicts = []
        has_manual_review = False

        for v in raw_verdicts:
            cid = v.get("criterion_id")
            verdict_str = v.get("verdict", "Manual_Review")
            conf = float(v.get("confidence_score") or 0)

            # Safety net: optional criteria must never produce Not_Eligible
            if verdict_str == "Not_Eligible" and not crit_mandatory_map.get(cid, True):
                verdict_str = "Manual_Review"
                v["verdict"] = "Manual_Review"
                v["reasoning"] = (
                    (v.get("reasoning") or "") +
                    " [Auto-upgraded: preferred/optional criterion — Manual Review instead of disqualification.]"
                ).strip()
            evidence_doc_id = filename_to_doc_id.get(v.get("evidence_doc_filename"))

            # Tamper risk score: average authenticity (1 - score) of docs involved
            tamper_score = None
            if evidence_doc_id:
                for d in bidder_docs:
                    if d["id"] == evidence_doc_id and d.get("authenticity_score") is not None:
                        tamper_score = round(1.0 - float(d["authenticity_score"]), 3)
                        break

            verdict_id = db.upsert_verdict(
                project_id=project_id,
                bidder_id=bidder_id,
                criterion_id=cid,
                verdict=verdict_str,
                confidence_score=conf,
                extracted_value_text=v.get("extracted_value_text"),
                threshold_value=next(
                    (int(c["threshold_value"]) for c in criteria
                     if c["criterion_id"] == cid and c.get("threshold_value") is not None),
                    None
                ),
                evidence_doc_id=evidence_doc_id,
                evidence_quote=v.get("evidence_quote"),
                evidence_page=v.get("evidence_page"),
                reasoning=v.get("reasoning"),
                tamper_risk_score=tamper_score,
            )

            if verdict_str == "Manual_Review":
                has_manual_review = True

            saved_verdicts.append({
                "criterion_id": cid,
                "verdict": verdict_str,
                "confidence_score": conf,
                "verdict_id": verdict_id,
            })

        # Determine final status — only mandatory Not_Eligible = hard disqualification
        has_mandatory_fail = any(
            v["verdict"] == "Not_Eligible" and crit_mandatory_map.get(v["criterion_id"], True)
            for v in saved_verdicts
        )
        if has_mandatory_fail:
            final_status = "not_eligible"
        elif has_manual_review:
            final_status = "manual_review_required"
        else:
            final_status = "evaluated"
        db.update_bidder_status(bidder_id, final_status)

        eligible_count = sum(1 for v in saved_verdicts if v["verdict"] == "Eligible")
        not_eligible_count = sum(1 for v in saved_verdicts if v["verdict"] == "Not_Eligible")
        manual_count = sum(1 for v in saved_verdicts if v["verdict"] == "Manual_Review")

        db.insert_audit_event(
            event_type="bidder_evaluated",
            payload={
                "eligible": eligible_count,
                "not_eligible": not_eligible_count,
                "manual_review": manual_count,
                "final_status": final_status,
            },
            project_id=project_id,
            bidder_id=bidder_id,
        )

        return JSONResponse({
            "success": True,
            "bidder_id": bidder_id,
            "company_name": bidder["company_name"],
            "criteria_evaluated": len(saved_verdicts),
            "eligible": eligible_count,
            "not_eligible": not_eligible_count,
            "manual_review": manual_count,
            "final_status": final_status,
            "verdicts": saved_verdicts,
        })

    except Exception as e:
        db.update_bidder_status(bidder_id, "evaluation_failed")
        print(f"✗ Evaluation error for bidder {bidder_id}: {str(e)}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@app.post("/api/tenders/{project_id}/evaluate-all")
@limiter.limit("5/minute")
async def evaluate_all_bidders(http_req: FastAPIRequest, project_id: int):
    """
    Evaluate every registered bidder for a tender sequentially.
    Returns a summary of results for all bidders.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Tender {project_id} not found")

    bidders = db.get_bidders_by_project(project_id)
    if not bidders:
        raise HTTPException(status_code=400, detail="No bidders registered for this tender.")

    results = []
    for bidder in bidders:
        try:
            # Reuse the per-bidder endpoint logic inline
            bidder_docs = db.get_bidder_documents(bidder["id"])
            if not bidder_docs:
                results.append({"bidder_id": bidder["id"], "company_name": bidder["company_name"], "status": "skipped_no_docs"})
                continue

            dprs = db.get_dprs_by_project(project_id)
            criteria_data = dprs[0]["summary_json"] if dprs and dprs[0].get("summary_json") else {}
            if isinstance(criteria_data, str):
                import json as _j; criteria_data = _j.loads(criteria_data)
            criteria = criteria_data.get("criteria", [])

            db.update_bidder_status(bidder["id"], "evaluating")
            raw_verdicts = await gemini_client.evaluate_bidder_criteria(
                criteria=criteria,
                bidder_documents=bidder_docs,
                company_name=bidder["company_name"],
            )

            filename_to_doc_id = {d["original_filename"]: d["id"] for d in bidder_docs}
            has_manual = False
            counts = {"Eligible": 0, "Not_Eligible": 0, "Manual_Review": 0}

            for v in raw_verdicts:
                vstr = v.get("verdict", "Manual_Review")
                counts[vstr] = counts.get(vstr, 0) + 1
                evidence_doc_id = filename_to_doc_id.get(v.get("evidence_doc_filename"))
                tamper_score = None
                if evidence_doc_id:
                    for d in bidder_docs:
                        if d["id"] == evidence_doc_id and d.get("authenticity_score") is not None:
                            tamper_score = round(1.0 - float(d["authenticity_score"]), 3)
                            break
                db.upsert_verdict(
                    project_id=project_id, bidder_id=bidder["id"],
                    criterion_id=v["criterion_id"], verdict=vstr,
                    confidence_score=float(v.get("confidence_score") or 0),
                    extracted_value_text=v.get("extracted_value_text"),
                    threshold_value=next(
                        (int(c["threshold_value"]) for c in criteria
                         if c["criterion_id"] == v["criterion_id"] and c.get("threshold_value") is not None),
                        None
                    ),
                    evidence_doc_id=evidence_doc_id,
                    evidence_quote=v.get("evidence_quote"),
                    evidence_page=v.get("evidence_page"),
                    reasoning=v.get("reasoning"),
                    tamper_risk_score=tamper_score,
                )
                if vstr == "Manual_Review":
                    has_manual = True

            final_status = "manual_review_required" if has_manual else "evaluated"
            db.update_bidder_status(bidder["id"], final_status)
            results.append({"bidder_id": bidder["id"], "company_name": bidder["company_name"],
                             "status": final_status, **counts})

        except Exception as e:
            db.update_bidder_status(bidder["id"], "evaluation_failed")
            results.append({"bidder_id": bidder["id"], "company_name": bidder["company_name"],
                             "status": "failed", "error": str(e)})

    return JSONResponse({"project_id": project_id, "results": results, "total_bidders": len(results)})


@app.get("/api/tenders/{project_id}/verdicts")
async def get_verdicts_matrix(project_id: int):
    """
    Return the full bidder × criterion verdict matrix for a tender.
    Used to render the confidence heatmap on the frontend.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Tender {project_id} not found")

    matrix = db.get_verdicts_matrix(project_id)
    matrix = serialize_datetime(matrix)
    return JSONResponse({"project_id": project_id, "verdicts": matrix, "count": len(matrix)})


@app.put("/api/verdicts/{verdict_id}/override")
async def override_verdict(verdict_id: int, request: HumanOverrideRequest):
    """
    Human Review & Sign-off (Stage 8): procurement officer overrides a verdict.
    Requires justification and officer ID. Writes an immutable audit event.
    """
    valid_verdicts = ("Eligible", "Not_Eligible", "Manual_Review")
    if request.override_verdict not in valid_verdicts:
        raise HTTPException(status_code=400, detail=f"override_verdict must be one of: {valid_verdicts}")

    try:
        db.apply_human_override(
            verdict_id=verdict_id,
            override_verdict=request.override_verdict,
            justification=request.justification,
            officer_id=request.officer_id,
        )

        db.insert_audit_event(
            event_type="human_override",
            payload={
                "verdict_id": verdict_id,
                "override_verdict": request.override_verdict,
                "justification": request.justification,
            },
            officer_id=request.officer_id,
        )

        return JSONResponse({
            "success": True,
            "verdict_id": verdict_id,
            "override_verdict": request.override_verdict,
        })

    except Exception as e:
        print(f"✗ Override error for verdict {verdict_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Override failed: {str(e)}")


# ===== PRAHARI COLLUSION DETECTION API =====

@app.post("/api/tenders/{project_id}/detect-collusion")
@limiter.limit("5/minute")
async def detect_collusion(http_req: FastAPIRequest, project_id: int):
    """
    Stage 6 of the PRAHARI pipeline — run cross-bidder collusion & integrity analysis.

    Runs deterministic checks (duplicate documents, shared emails, financial clustering)
    plus a multimodal LLM pass over all bidder PDFs simultaneously.
    Persists each alert to the collusion_alerts table and writes an audit event.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Tender {project_id} not found")

    bidders = db.get_bidders_by_project(project_id)
    if len(bidders) < 2:
        raise HTTPException(
            status_code=400,
            detail="At least 2 bidders are required to run collusion detection."
        )

    # Load all bidder documents keyed by bidder_id
    bidder_docs: dict = {}
    for bidder in bidders:
        bidder_docs[bidder["id"]] = db.get_bidder_documents(bidder["id"])

    # Get tender name for context
    dprs = db.get_dprs_by_project(project_id)
    tender_name = project.get("name", f"Tender #{project_id}")
    if dprs and dprs[0].get("summary_json"):
        cd = dprs[0]["summary_json"]
        if isinstance(cd, str):
            import json as _j
            try:
                cd = _j.loads(cd)
            except Exception:
                cd = {}
        tender_name = cd.get("tender_metadata", {}).get("tender_name", tender_name) or tender_name

    try:
        result = await gemini_client.detect_collusion_patterns(
            bidders=bidders,
            bidder_docs=bidder_docs,
            tender_name=tender_name,
        )

        # Map company names back to bidder IDs
        name_to_id = {b["company_name"]: b["id"] for b in bidders}
        saved_alerts = []

        for alert in result.get("alerts", []):
            names = alert.get("bidder_names_involved", [])
            involved_ids = [name_to_id[n] for n in names if n in name_to_id]
            if not involved_ids:
                involved_ids = [b["id"] for b in bidders]

            alert_id = db.insert_collusion_alert(
                project_id=project_id,
                alert_type=alert.get("alert_type", "other"),
                bidder_ids=involved_ids,
                description=alert.get("description", ""),
                confidence_score=float(alert.get("confidence_score", 0)),
            )
            saved_alerts.append({
                "alert_id": alert_id,
                "alert_type": alert.get("alert_type"),
                "severity": alert.get("severity"),
                "confidence_score": alert.get("confidence_score"),
                "bidder_names_involved": names,
                "description": alert.get("description"),
            })

        db.insert_audit_event(
            event_type="collusion_detection_run",
            payload={
                "total_alerts": len(saved_alerts),
                "overall_risk": result.get("overall_risk"),
                "bidder_count": len(bidders),
            },
            project_id=project_id,
        )

        return JSONResponse({
            "success": True,
            "project_id": project_id,
            "overall_risk": result.get("overall_risk"),
            "summary": result.get("summary"),
            "total_alerts": len(saved_alerts),
            "alerts": saved_alerts,
        })

    except Exception as e:
        print(f"✗ Collusion detection error for project {project_id}: {str(e)}")
        import traceback; traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Collusion detection failed: {str(e)}")


@app.get("/api/tenders/{project_id}/collusion-alerts")
async def get_collusion_alerts(project_id: int):
    """Retrieve all collusion alerts for a tender."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Tender {project_id} not found")

    alerts = db.get_collusion_alerts(project_id)
    alerts = serialize_datetime(alerts)
    return JSONResponse({
        "project_id": project_id,
        "alerts": alerts,
        "count": len(alerts),
        "has_high_severity": any(
            float(a.get("confidence_score") or 0) >= 0.85 for a in alerts
        ),
    })


@app.put("/api/tenders/{project_id}/collusion-alerts/{alert_id}/resolve")
async def resolve_collusion_alert(
    project_id: int,
    alert_id: int,
    request: ResolveAlertRequest,
):
    """Officer disposition on a collusion alert (accepted | dismissed | escalated)."""
    valid_dispositions = ("accepted", "dismissed", "escalated", "pending")
    if request.disposition not in valid_dispositions:
        raise HTTPException(
            status_code=400,
            detail=f"disposition must be one of: {valid_dispositions}"
        )

    try:
        db.resolve_collusion_alert(
            alert_id=alert_id,
            disposition=request.disposition,
            notes=request.notes or "",
            officer_id=request.officer_id,
        )

        db.insert_audit_event(
            event_type="collusion_alert_resolved",
            payload={
                "alert_id": alert_id,
                "disposition": request.disposition,
                "notes": request.notes,
            },
            project_id=project_id,
            officer_id=request.officer_id,
        )

        return JSONResponse({
            "success": True,
            "alert_id": alert_id,
            "disposition": request.disposition,
        })

    except Exception as e:
        print(f"✗ Resolve alert error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")


# ===== PROJECT API ROUTES =====

@app.get("/projects")
async def list_projects():
    """Get a list of all projects."""
    projects = db.get_projects()
    # Serialize datetime objects
    projects = serialize_datetime(projects)
    projects = serialize_datetime(projects)
    return JSONResponse({"projects": projects, "count": len(projects)})

@app.post("/projects")
async def create_project(request: CreateProjectRequest):
    """Create a new project."""
    try:
        project_id = db.create_project(request.name, request.state, request.scheme, request.sector)
        return JSONResponse({
            "id": project_id,
            "name": request.name,
            "message": "Project created successfully"
        })
    except Exception as e:
        print(f"✗ Create project error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")

@app.delete("/projects/{project_id}")
async def delete_project(project_id: int):
    """Delete a project."""
    try:
        success = db.delete_project(project_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        return JSONResponse({"message": "Project deleted successfully"})
    except Exception as e:
        print(f"✗ Delete project error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete project: {str(e)}")

@app.get("/projects/{project_id}")
async def get_project(project_id: int):
    """Get project details."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    project = serialize_datetime(project)
    return JSONResponse(project)

@app.get("/projects/{project_id}/dprs")
async def get_project_dprs(project_id: int):
    """Get DPRs for a specific project."""
    dprs = db.get_dprs_by_project(project_id)
    dprs = serialize_datetime(dprs)
    return JSONResponse({"dprs": dprs, "count": len(dprs)})


@app.post("/projects/{project_id}/compare-all")
async def compare_all_project_dprs(project_id: int):
    """
    Compare all DPRs in a project and recommend the best one.
    Uses Gemini AI to analyze all DPR summaries and provide a detailed comparison.
    Saves the result to the database.
    """
    # Get all DPRs for the project
    dprs = db.get_dprs_by_project(project_id)
    
    if not dprs:
        raise HTTPException(status_code=404, detail="No DPRs found in this project")
    
    # Filter to only analyzed DPRs (those with summary_json)
    analyzed_dprs = [dpr for dpr in dprs if dpr.get('summary_json')]
    
    if len(analyzed_dprs) < 2:
        raise HTTPException(
            status_code=400, 
            detail=f"Need at least 2 analyzed DPRs to compare. Found {len(analyzed_dprs)} analyzed DPRs."
        )
    
    # Compare using Gemini
    result = await gemini_client.compare_all_dprs(analyzed_dprs)
    
    if not result.get('success'):
        raise HTTPException(status_code=500, detail=result.get('error', 'Comparison failed'))
    
    # Save comparison result to database
    db.save_project_comparison(project_id, result['comparison'])
    
    return JSONResponse({
        "success": True,
        "comparison": result['comparison'],
        "saved": True
    })


@app.get("/projects/{project_id}/comparison")
async def get_project_comparison(project_id: int):
    """
    Retrieve saved comparison result for a project.
    """
    comparison_data = db.get_project_comparison(project_id)
    
    if not comparison_data:
        raise HTTPException(status_code=404, detail="No saved comparison found for this project")
    
    # Serialize datetime objects
    comparison_data = serialize_datetime(comparison_data)
    
    return JSONResponse({
        "success": True,
        "comparison": comparison_data["comparison"],
        "generated_at": comparison_data["generated_at"]
    })


@app.delete("/projects/{project_id}/comparison")
async def clear_project_comparison(project_id: int):
    """
    Clear/reset saved comparison result for a project.
    """
    db.clear_project_comparison(project_id)
    
    return JSONResponse({
        "success": True,
        "message": "Comparison cleared successfully"
    })


# ===== COMPLIANCE WEIGHTS API ROUTES =====

@app.get("/projects/{project_id}/compliance-weights")
async def get_compliance_weights(project_id: int):
    """
    Get compliance scoring weights for a project.
    Returns project-specific weights or defaults if not set.
    """
    import backend.compliance_calculator as compliance_calc
    
    try:
        # Verify project exists
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        # Get weights (will fall back to defaults if not set)
        weights = compliance_calc.get_project_weights(project_id)
        
        return JSONResponse({
            "success": True,
            "weights": weights,
            "isCustom": project.get("compliance_weights") is not None
        })
    except Exception as e:
        print(f"✗ Get compliance weights error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get compliance weights: {str(e)}")


@app.put("/projects/{project_id}/compliance-weights")
async def update_compliance_weights(project_id: int, request: UpdateComplianceWeightsRequest):
    """
    Update compliance scoring weights for a project.
    Optionally recalculates all DPR scores in the project with new weights.
    """
    import backend.compliance_calculator as compliance_calc
    
    try:
        # Verify project exists
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        # Validate weights
        is_valid, error_msg = compliance_calc.validate_weights(request.weights)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid weights: {error_msg}")
        
        # Update project weights
        success = compliance_calc.update_project_weights(project_id, request.weights)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update project weights")
        
        result = {
            "success": True,
            "message": "Weights updated successfully",
            "weights": request.weights
        }
        
        # Recalculate DPR scores if requested
        if request.recalculate:
            print(f"⏳ Recalculating compliance scores for project {project_id}...")
            count_updated, failed_ids = compliance_calc.recalculate_project_dprs(
                project_id, 
                request.weights
            )
            
            result["recalculated"] = True
            result["dprs_updated"] = count_updated
            result["dprs_failed"] = len(failed_ids)
            
            if failed_ids:
                result["failed_dpr_ids"] = failed_ids
                print(f"⚠ Failed to recalculate {len(failed_ids)} DPRs: {failed_ids}")
        else:
            result["recalculated"] = False
        
        return JSONResponse(result)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Update compliance weights error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to update compliance weights: {str(e)}")


@app.post("/projects/{project_id}/compliance-weights/reset")
async def reset_compliance_weights(project_id: int, recalculate: bool = False):
    """
    Reset compliance weights to defaults for a project.
    Optionally recalculates all DPR scores in the project.
    """
    import backend.compliance_calculator as compliance_calc
    
    try:
        # Verify project exists
        project = db.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        # Get default weights
        default_weights = compliance_calc.get_default_weights()
        
        # Update project with defaults
        success = compliance_calc.update_project_weights(project_id, default_weights)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to reset project weights")
        
        result = {
            "success": True,
            "message": "Weights reset to defaults",
            "weights": default_weights
        }
        
        # Recalculate DPR scores if requested
        if recalculate:
            print(f"⏳ Recalculating compliance scores for project {project_id} with defaults...")
            count_updated, failed_ids = compliance_calc.recalculate_project_dprs(
                project_id, 
                default_weights
            )
            
            result["recalculated"] = True
            result["dprs_updated"] = count_updated
            result["dprs_failed"] = len(failed_ids)
            
            if failed_ids:
                result["failed_dpr_ids"] = failed_ids
        else:
            result["recalculated"] = False
        
        return JSONResponse(result)
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Reset compliance weights error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reset compliance weights: {str(e)}")



# ===== PAGE ROUTES =====

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    """Serve the landing/home page."""
    return templates.TemplateResponse("home.html", {"request": request})


@app.get("/dprs/list", response_class=HTMLResponse)
async def dprs_list_page(request: Request):
    """Serve the DPR list page."""
    return templates.TemplateResponse("list.html", {"request": request})


@app.get("/dpr/{dpr_id}/detail", response_class=HTMLResponse)
async def dpr_detail_page(request: Request, dpr_id: int):
    """Serve the DPR detail/analysis page."""
    return templates.TemplateResponse("detail.html", {"request": request})

@app.get("/comparison-chat/{comparison_id}/detail", response_class=HTMLResponse)
async def comparison_detail_page(request: Request, comparison_id: int):
    """Serve the comparison chat page."""
    return templates.TemplateResponse("comparison.html", {"request": request})


@app.get("/comparisons", response_class=HTMLResponse)
async def comparisons_list_page(request: Request):
    """Serve the comparisons list page."""
    return templates.TemplateResponse("comparisons.html", {"request": request})



# ===== API ROUTES =====

@app.get("/dprs")
async def list_all_dprs():
    """Get a list of all DPRs with metadata."""
    dprs = db.get_all_dprs()
    dprs = serialize_datetime(dprs)
    return JSONResponse({"dprs": dprs, "count": len(dprs)})



@app.post("/upload-dpr")
async def upload_dpr(
    file: UploadFile = File(...), 
    language: str = Form("en"),
    project_id: Optional[int] = Form(None)
):
    """
    Upload a DPR PDF, process it with Gemini, and return structured JSON.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    try:
        original_filename = file.filename
        
        # Check if this PDF already exists
        existing_dpr = db.get_dpr_by_filename(original_filename)
        if existing_dpr:
            print(f"✓ PDF already exists: {original_filename} (ID: {existing_dpr['id']})")
            
            # Update project_id if provided and different
            if project_id is not None and existing_dpr.get('project_id') != project_id:
                print(f"⏳ Updating project association: DPR {existing_dpr['id']} → Project {project_id}")
                conn = db_config.get_connection()
                cursor = db_config.get_cursor(conn, dict_cursor=False)
                cursor.execute("UPDATE dprs SET project_id = %s WHERE id = %s", (project_id, existing_dpr['id']))
                conn.commit()
                cursor.close()
                db_config.release_connection(conn)
                print(f"✓ Project association updated")
            
            return JSONResponse({
                "id": existing_dpr["id"],
                "dpr_id": existing_dpr["id"],
                "summary": existing_dpr["summary_json"],
                "existing": True
            })
        
        # Generate unique filename for storage
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{unique_id}_{original_filename}"
        filepath = DATA_DIR / filename
        
        # Save the uploaded file
        print(f"⏳ Saving uploaded file: {filename}")
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)
        print(f"✓ File saved: {filepath} ({len(content)} bytes)")
        
        # Upload to Gemini Files API
        file_ref = await gemini_client.upload_file(str(filepath))
        
        # Insert initial record into database with project_id
        print(f"⏳ Inserting initial DPR record for {filename}...")
        dpr_id = db.insert_dpr(
            filename=filename,
            original_filename=original_filename,
            filepath=str(filepath),
            file_ref=file_ref,
            summary_json=None,
            project_id=project_id
        )
        
        # Generate analysis in background
        print("⏳ Generating analysis...")
        try:
            parsed_json = await gemini_client.generate_json_from_file(file_ref, str(SCHEMA_PATH))
            print(f"✓ Generated analysis successfully")
            
            # Validate DPR against project if project_id is provided
            validation_flags = None
            if project_id is not None:
                validation_flags = db.validate_dpr_against_project(dpr_id, project_id, parsed_json)
                if validation_flags.get('hasFlags'):
                    print(f"⚠ DPR {dpr_id} has validation flags: {len(validation_flags['flags'])} issue(s)")
            
            db.update_dpr(dpr_id, parsed_json, validation_flags)
            
            return JSONResponse({
                "id": dpr_id,
                "dpr_id": dpr_id,
                "summary": parsed_json,
                "existing": False
            })
        except Exception as e:
            print(f"✗ Analysis failed: {str(e)}")
            raise e
        
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process DPR: {str(e)}")


@app.post("/upload-dpr")
async def upload_dpr(file: UploadFile = File(...), language: str = Form("en")):
    """
    Upload a DPR PDF, process it with Gemini, and return structured JSON.
    
    If a PDF with the same filename already exists, return the existing analysis.
    Otherwise, process the new PDF and store it.
    
    Args:
        file: PDF file to upload
        language: "en" for English, "hi" for Hindi (default: "en")
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted")
    
    try:
        original_filename = file.filename
        
        # Check if this PDF already exists
        existing_dpr = db.get_dpr_by_filename(original_filename)
        if existing_dpr:
            print(f"✓ PDF already exists: {original_filename} (ID: {existing_dpr['id']})")
            return JSONResponse({
                "id": existing_dpr["id"],
                "dpr_id": existing_dpr["id"],
                "summary": existing_dpr["summary_json"],
                "existing": True
            })
        
        # Generate unique filename for storage
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"{timestamp}_{unique_id}_{original_filename}"
        filepath = DATA_DIR / filename
        
        # Save the uploaded file
        print(f"⏳ Saving uploaded file: {filename}")
        with open(filepath, "wb") as f:
            content = await file.read()
            f.write(content)
        print(f"✓ File saved: {filepath} ({len(content)} bytes)")
        try:
            # Single call to get both English and Hindi analysis (now async)
            parsed_json = await gemini_client.generate_json_from_file(file_ref, str(SCHEMA_PATH))
            
            print(f"✓ Generated analysis successfully")
            
            # Update database with analysis results
            db.update_dpr(dpr_id, parsed_json)
            
            return JSONResponse({
                "id": dpr_id,
                "dpr_id": dpr_id,
                "summary": parsed_json,
                "existing": False
            })
            
        except Exception as e:
            print(f"✗ Analysis failed: {str(e)}")
            # Optional: db.delete_dpr(dpr_id)
            raise e
        
    except ValueError as e:
        # JSON validation or parsing error
        print(f"✗ Validation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to parse valid JSON: {str(e)}")
    
    except Exception as e:
        print(f"✗ Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process DPR: {str(e)}")


@app.get("/dpr/{dpr_id}")
async def get_dpr(dpr_id: int):
    """
    Retrieve a stored DPR by ID.
    
    Returns the DPR metadata and parsed JSON.
    
    Args:
        dpr_id: The DPR ID
        
    """
    dpr = db.get_dpr(dpr_id)
    
    if not dpr:
        raise HTTPException(status_code=404, detail=f"DPR {dpr_id} not found")
    
    dpr = serialize_datetime(dpr)  # Serialize datetime objects
    return JSONResponse(dpr)




@app.get("/dpr/{dpr_id}/pdf")
async def get_dpr_pdf(dpr_id: int):
    """
    Serve the PDF file for a DPR.
    Fetches from Cloudinary or local storage and returns content.
    """
    print(f"📄 PDF Request: DPR {dpr_id}")
    
    dpr = db.get_dpr(dpr_id)
    dpr = serialize_datetime(dpr)
    
    if not dpr:
        print(f"❌ DPR {dpr_id} not found in database")
        raise HTTPException(status_code=404, detail=f"DPR {dpr_id} not found")
    
    print(f"✓ DPR {dpr_id} found: {dpr.get('original_filename')}")
    
    # Try Cloudinary URL first
    cloudinary_url = dpr.get("cloudinary_url")
    print(f"  Cloudinary URL: {cloudinary_url}")
    
    if cloudinary_url:
        print(f"  Fetching from Cloudinary...")
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(cloudinary_url)
                print(f"  Cloudinary response: {response.status_code}")
                if response.status_code == 200:
                    print(f"✓ Returning PDF from Cloudinary ({len(response.content)} bytes)")
                    return Response(
                        content=response.content,
                        media_type="application/pdf",
                        headers={
                            "Content-Disposition": f'inline; filename="{dpr.get("original_filename", "document.pdf")}"'
                        }
                    )
        except Exception as e:
            print(f"❌ Cloudinary fetch error: {e}")
    
    # Fallback to local file
    filepath = dpr.get("filepath")
    print(f"  Filepath: {filepath}")
    
    if filepath:
        exists = os.path.exists(filepath)
        print(f"  File exists: {exists}")
        
        if exists:
            print(f"  Reading local file...")
            with open(filepath, "rb") as f:
                file_content = f.read()
            print(f"✓ Returning PDF from local file ({len(file_content)} bytes)")
            return Response(
                content=file_content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'inline; filename="{dpr.get("original_filename", "document.pdf")}"'
                }
            )
    
    print(f"❌ PDF not found: No Cloudinary URL and no local file")
    raise HTTPException(status_code=404, detail="PDF file not found")

@app.post("/dprs/{dpr_id}/analyze")
async def analyze_dpr(dpr_id: int):
    """
    Trigger analysis on an unanalyzed DPR (typically client-uploaded).
    Admin endpoint to run Gemini analysis on uploaded PDFs.
    """
    # Verify DPR exists
    dpr = db.get_dpr(dpr_id)
    if not dpr:
        raise HTTPException(status_code=404, detail=f"DPR {dpr_id} not found")
    
    # Check if already analyzed
    if dpr.get("summary_json"):
        return JSONResponse({
            "message": "DPR already analyzed",
            "dpr_id": dpr_id,
            "existing": True
        })
    
    try:
        # Set status to 'analyzing' before starting
        conn = db_config.get_connection()
        cursor = db_config.get_cursor(conn, dict_cursor=False)
        cursor.execute("UPDATE dprs SET status = 'analyzing' WHERE id = %s", (dpr_id,))
        conn.commit()
        cursor.close()
        db_config.release_connection(conn)
        
        file_ref = dpr["uploaded_file_ref"]
        
        print(f"⏳ Analyzing DPR {dpr_id}...")
        
        # Generate analysis in multiple languages
        parsed_json = await gemini_client.generate_json_from_file(file_ref, str(SCHEMA_PATH))
        
        print(f"✓ Generated analysis successfully")
        
        # Validate DPR against project if project_id exists
        validation_flags = None
        if dpr.get('project_id'):
            validation_flags = db.validate_dpr_against_project(dpr_id, dpr['project_id'], parsed_json)
            if validation_flags.get('hasFlags'):
                print(f"⚠ DPR {dpr_id} has validation flags: {len(validation_flags['flags'])} issue(s)")
        
        # Update database with analysis results and validation flags
        db.update_dpr(dpr_id, parsed_json, validation_flags)
        
        # Set status to 'completed'
        conn = db_config.get_connection()
        cursor = db_config.get_cursor(conn, dict_cursor=False)
        cursor.execute("UPDATE dprs SET status = 'completed' WHERE id = %s", (dpr_id,))
        conn.commit()
        cursor.close()
        db_config.release_connection(conn)
        
        return JSONResponse({
            "message": "Analysis complete",
            "dpr_id": dpr_id,
            "summary": parsed_json
        })
        
    except Exception as e:
        # Reset status to 'pending' on error
        conn = db_config.get_connection()
        cursor = db_config.get_cursor(conn, dict_cursor=False)
        cursor.execute("UPDATE dprs SET status = 'pending' WHERE id = %s", (dpr_id,))
        conn.commit()
        cursor.close()
        db_config.release_connection(conn)
        
        print(f"✗ Analysis failed for DPR {dpr_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to analyze DPR: {str(e)}")



@app.delete("/dpr/{dpr_id}")
async def delete_dpr(dpr_id: int):
    """
    Delete a DPR and all associated data.
    """
    # Verify DPR exists
    dpr = db.get_dpr(dpr_id)
    if not dpr:
        raise HTTPException(status_code=404, detail=f"DPR {dpr_id} not found")
    
    try:
        # Delete from database and get filepath
        filepath = db.delete_dpr(dpr_id)
        
        # Delete file from disk
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"✓ Deleted file: {filepath}")
            except Exception as e:
                print(f"⚠ Failed to delete file {filepath}: {str(e)}")
        
        # Clear in-memory chat session
        gemini_client.clear_chat_session(dpr_id)
        
        return JSONResponse({
            "success": True,
            "message": f"Deleted DPR {dpr_id}"
        })
    except Exception as e:
        print(f"✗ Delete DPR error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete DPR: {str(e)}")


@app.get("/dpr/{dpr_id}/report")
async def generate_dpr_report(dpr_id: int):
    """
    Generate a comprehensive PDF report for a DPR with charts and analysis.
    
    Returns a PDF file with all sections: Overview, Financial Analysis, Timeline, Risk Assessment, Compliance.
    """
    try:
        # Get DPR data
        dpr = db.get_dpr(dpr_id)
        if not dpr:
            raise HTTPException(status_code=404, detail=f"DPR {dpr_id} not found")
        
        # Validate summary_json exists
        summary_json = dpr.get('summary_json')
        if not summary_json:
            raise HTTPException(
                status_code=422, 
                detail=f"DPR {dpr_id} has not been analyzed yet. Please wait for analysis to complete."
            )
        
        # Parse summary_json if it's a string
        if isinstance(summary_json, str):
            import json
            try:
                summary_json = json.loads(summary_json)
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=422,
                    detail=f"DPR {dpr_id} has invalid analysis data: {str(e)}"
                )
        
        # Ensure summary_json is a dict
        if not isinstance(summary_json, dict):
            raise HTTPException(
                status_code=422,
                detail=f"DPR {dpr_id} analysis data is in an unexpected format"
            )
        
        # Generate charts (with error handling inside)
        charts = report_generator.prepare_chart_data(summary_json)
        
        # Prepare template context with safe defaults
        context = {
            'dpr': summary_json,
            'charts': charts,
            'generated_date': datetime.now().strftime('%B %d, %Y at %I:%M %p')
        }
        
        # Render HTML template
        html_content = templates.get_template('reports/dpr_report.html').render(context)
        
        # Convert HTML to PDF
        pdf_bytes = HTML(string=html_content).write_pdf()
        
        # Return PDF as response
        filename = f"DPR_Report_{dpr_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Report generation error: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@app.post("/dpr/{dpr_id}/chat")
async def chat_with_dpr(dpr_id: int, chat_message: ChatMessage):
    """
    Send a chat message about a DPR and get a response.
    
    The chat maintains context and references the uploaded PDF document.
    All messages are stored in SQLite for persistence.
    """
    # Verify DPR exists
    dpr = db.get_dpr(dpr_id)
    if not dpr:
        raise HTTPException(status_code=404, detail=f"DPR {dpr_id} not found")
    
    try:
        # Store user message
        db.insert_message(dpr_id, "user", chat_message.message)
        
        try:
            # Get response from Gemini (now async)
            response = await gemini_client.send_chat_message(
                dpr_id=dpr_id,
                message=chat_message.message,
                file_ref=dpr["uploaded_file_ref"]
            )
        except gemini_client.FileExpiredError:
            print(f"⚠ File for DPR {dpr_id} expired. Re-uploading...")
            
            # Re-upload the file
            if not os.path.exists(dpr["filepath"]):
                raise HTTPException(status_code=404, detail="Original file not found on server, cannot re-upload.")
            
            new_file_ref = await gemini_client.upload_file(dpr["filepath"])
            
            # Update database with new file reference
            db.update_dpr_file_ref(dpr_id, new_file_ref)
            
            # Clear old chat session to force recreation with new file
            gemini_client.clear_chat_session(dpr_id)
            
            # Retry sending message
            print(f"↺ Retrying chat message for DPR {dpr_id} with new file ref...")
            response = await gemini_client.send_chat_message(
                dpr_id=dpr_id,
                message=chat_message.message,
                file_ref=new_file_ref
            )
        
        # Store assistant message
        db.insert_message(dpr_id, "assistant", response['reply'])
        
        # Get the message ID (last inserted)
        messages = db.get_messages(dpr_id)
        message_id = messages[-1]['id'] if messages else 0
        
        return JSONResponse({
            "reply": response['reply'],
            "sources": response.get('sources', []),
            "message_id": message_id
        })
        
    except Exception as e:
        print(f"✗ Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")


@app.get("/dpr/{dpr_id}/chat/history")
async def get_chat_history(dpr_id: int):
    """
    Retrieve the complete chat history for a DPR.
    
    Returns a list of messages in chronological order.
    """
    # Verify DPR exists
    dpr = db.get_dpr(dpr_id)
    if not dpr:
        raise HTTPException(status_code=404, detail=f"DPR {dpr_id} not found")
    
    messages = db.get_messages(dpr_id)
    messages = serialize_datetime(messages)
    
    return JSONResponse({
        "dpr_id": dpr_id,
        "messages": messages,
        "count": len(messages)
    })


@app.delete("/dpr/{dpr_id}/chat")
async def clear_chat(dpr_id: int):
    """
    Clear all chat history for a DPR.
    """
    # Verify DPR exists
    dpr = db.get_dpr(dpr_id)
    if not dpr:
        raise HTTPException(status_code=404, detail=f"DPR {dpr_id} not found")
    
    try:
        # Clear from database
        deleted_count = db.clear_chat_history(dpr_id)
        
        # Clear from in-memory cache
        gemini_client.clear_chat_session(dpr_id)
        
        return JSONResponse({
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Cleared {deleted_count} messages"
        })
    except Exception as e:
        print(f"✗ Clear chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear chat: {str(e)}")




# ===== COMPARISON CHAT API ROUTES =====

@app.get("/comparison-chats")
async def list_comparison_chats():
    """Get a list of all comparison chats."""
    chats = db.get_all_comparison_chats()
    chats = serialize_datetime(chats)
    return JSONResponse({"comparisons": chats, "count": len(chats)})


@app.post("/comparison-chats")
async def create_comparison_chat(request: CreateComparisonRequest):
    """Create a new comparison chat with selected DPRs."""
    if len(request.dpr_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 DPRs required for comparison")
   
    try:
        dprs = []
        for dpr_id in request.dpr_ids:
            dpr = db.get_dpr(dpr_id)
            if not dpr:
                raise HTTPException(status_code=404, detail=f"DPR {dpr_id} not found")
            dprs.append(dpr)
        
        comparison_id = db.create_comparison_chat(request.name, request.dpr_ids)
        print(f"✓ Comparison chat created with ID: {comparison_id} ({len(request.dpr_ids)} PDFs)")
        
        return JSONResponse({
            "comparison_id": comparison_id,
            "name": request.name,
            "dpr_count": len(request.dpr_ids)
        })
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Create comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create comparison: {str(e)}")


@app.get("/comparison-chat/{comparison_id}")
async def get_comparison_chat(comparison_id: int):
    """Retrieve a comparison chat with its associated DPRs."""
    comparison = db.get_comparison_chat(comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail=f"Comparison chat {comparison_id} not found")
    comparison = serialize_datetime(comparison)
    return JSONResponse(comparison)


@app.post("/comparison-chat/{comparison_id}/chat")
async def chat_with_comparison(comparison_id: int, chat_message: ChatMessage):
    """Send a chat message to a comparison and get a response."""
    comparison = db.get_comparison_chat(comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail=f"Comparison chat {comparison_id} not found")
    
    try:
        print(f"⏳ Processing comparison chat message for comparison {comparison_id}")
        db.insert_comparison_message(comparison_id, "user", chat_message.message)
        file_refs = [dpr["uploaded_file_ref"] for dpr in comparison["dprs"]]
        
        try:
            # Get response from Gemini (now async)
            response = await gemini_client.send_comparison_message(
                comparison_id=comparison_id, 
                message=chat_message.message, 
                file_refs=file_refs
            )
        except gemini_client.FileExpiredError:
            print(f"⚠ Files for comparison {comparison_id} expired. Re-uploading all...")
            
            # Re-upload all files in the comparison
            new_file_refs = []
            for dpr in comparison["dprs"]:
                print(f"↺ Re-uploading {dpr['filename']}...")
                if not os.path.exists(dpr["filepath"]):
                    raise HTTPException(status_code=404, detail=f"Original file {dpr['filename']} not found on server.")
                
                new_ref = await gemini_client.upload_file(dpr["filepath"])
                db.update_dpr_file_ref(dpr["id"], new_ref)
                new_file_refs.append(new_ref)
            
            # Clear old session
            gemini_client.clear_comparison_chat_session(comparison_id)
            
            # Retry with new file references
            print(f"↺ Retrying comparison chat message...")
            response = await gemini_client.send_comparison_message(
                comparison_id=comparison_id, 
                message=chat_message.message, 
                file_refs=new_file_refs
            )
        
        db.insert_comparison_message(comparison_id, "assistant", response['reply'])
        messages = db.get_comparison_messages(comparison_id)
        message_id = messages[-1]['id'] if messages else 0
        return JSONResponse({"reply": response['reply'], "sources": response.get('sources', []), "message_id": message_id})
    except Exception as e:
        print(f"✗ Comparison chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Comparison chat failed: {str(e)}")


@app.get("/comparison-chat/{comparison_id}/chat/history")
async def get_comparison_chat_history(comparison_id: int):
    """Retrieve the complete chat history for a comparison."""
    comparison = db.get_comparison_chat(comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail=f"Comparison chat {comparison_id} not found")
    messages = db.get_comparison_messages(comparison_id)
    comparison = serialize_datetime(comparison)
    messages = serialize_datetime(messages)
    return JSONResponse({"comparison_id": comparison_id, "messages": messages, "count": len(messages)})


@app.delete("/comparison-chat/{comparison_id}/chat")
async def clear_comparison_chat(comparison_id: int):
    """Clear all chat history for a comparison."""
    comparison = db.get_comparison_chat(comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail=f"Comparison chat {comparison_id} not found")
    
    try:
        deleted_count = db.clear_comparison_history(comparison_id)
        gemini_client.clear_comparison_chat_session(comparison_id)
        return JSONResponse({"success": True, "deleted_count": deleted_count, "message": f"Cleared {deleted_count} messages"})
    except Exception as e:
        print(f"✗ Clear comparison chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear comparison chat: {str(e)}")


@app.delete("/comparison-chat/{comparison_id}")
async def delete_comparison_chat(comparison_id: int):
    """Delete a comparison chat and all its history."""
    comparison = db.get_comparison_chat(comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail=f"Comparison chat {comparison_id} not found")
    
    try:
        db.delete_comparison_chat(comparison_id)
        # Also clear from in-memory cache if exists
        gemini_client.clear_comparison_chat_session(comparison_id)
        comparison = serialize_datetime(comparison)
        return JSONResponse({"success": True, "message": f"Deleted comparison chat {comparison_id}"})
    except Exception as e:
        print(f"✗ Delete comparison chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete comparison chat: {str(e)}")



@app.post("/comparison-chat/{comparison_id}/add-dpr")
async def add_dpr_to_comparison_endpoint(comparison_id: int, request: dict):
    """Add a DPR to an existing comparison."""
    comparison = db.get_comparison_chat(comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail=f"Comparison chat {comparison_id} not found")
    
    dpr_id = request.get("dpr_id")
    if not dpr_id:
        raise HTTPException(status_code=400, detail="dpr_id is required")
    
    # Check if DPR exists
    dpr = db.get_dpr(dpr_id)
    if not dpr:
        raise HTTPException(status_code=404, detail=f"DPR {dpr_id} not found")
    
    try:
        success = db.add_dpr_to_comparison(comparison_id, dpr_id)
        if not success:
            raise HTTPException(status_code=400, detail="DPR is already in this comparison")
        
        # Clear the chat session so next messages use updated PDF list
        gemini_client.clear_comparison_chat_session(comparison_id)
        print(f"✓ Cleared comparison chat session {comparison_id} after adding DPR")
        
        # Return updated comparison
        updated_comparison = db.get_comparison_chat(comparison_id)
        updated_comparison = serialize_datetime(updated_comparison)
        return JSONResponse(updated_comparison)
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Add DPR to comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add DPR to comparison: {str(e)}")


@app.delete("/comparison-chat/{comparison_id}/remove-dpr/{dpr_id}")
async def remove_dpr_from_comparison_endpoint(comparison_id: int, dpr_id: int):
    """Remove a DPR from a comparison."""
    comparison = db.get_comparison_chat(comparison_id)
    if not comparison:
        raise HTTPException(status_code=404, detail=f"Comparison chat {comparison_id} not found")
    
    try:
        success = db.remove_dpr_from_comparison(comparison_id, dpr_id)
        if not success:
            raise HTTPException(status_code=400, detail="Cannot remove DPR: comparison must have at least 2 DPRs")
        
        # Clear the chat session so next messages use updated PDF list
        gemini_client.clear_comparison_chat_session(comparison_id)
        print(f"✓ Cleared comparison chat session {comparison_id} after removing DPR")
        
        return JSONResponse({"success": True, "message": f"Removed DPR {dpr_id} from comparison {comparison_id}"})
    except HTTPException:
        raise
    except Exception as e:
        print(f"✗ Remove DPR from comparison error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to remove DPR from comparison: {str(e)}")


@app.get("/api/tenders/{project_id}/audit-trail")
async def get_audit_trail(project_id: int):
    """Return the immutable audit trail for a tender."""
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Tender {project_id} not found")
    events = db.get_audit_trail(project_id)
    events = serialize_datetime(events)
    return JSONResponse({"project_id": project_id, "events": events, "count": len(events)})


# ===== VENDOR HISTORY LOOKUP (CPPP + GeM) =====

class VendorLookupRequest(BaseModel):
    company_name: str
    gstin: Optional[str] = None
    pan: Optional[str] = None


@app.post("/api/vendors/lookup")
async def vendor_lookup_single(request: VendorLookupRequest):
    """
    Run CPPP debarment check + GeM seller history for a single vendor.
    Results are cached 24 hours in-process.
    """
    if not request.company_name.strip():
        raise HTTPException(status_code=400, detail="company_name is required")
    result = await vendor_lookup.full_vendor_lookup(
        company_name=request.company_name.strip(),
        gstin=request.gstin,
        pan=request.pan,
    )
    return JSONResponse(result)


@app.get("/api/tenders/{project_id}/vendor-history")
async def vendor_history_for_tender(project_id: int):
    """
    Run CPPP + GeM lookup for ALL bidders registered against a tender.
    Returns a list of per-bidder risk reports.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Tender {project_id} not found")

    bidders = db.get_bidders_by_project(project_id)
    if not bidders:
        return JSONResponse({"project_id": project_id, "results": [], "bidder_count": 0})

    results = await vendor_lookup.bulk_vendor_lookup(bidders)

    # Count risk levels for summary
    risk_counts = {"CRITICAL": 0, "MEDIUM": 0, "LOW": 0, "unknown": 0}
    for r in results:
        lvl = r.get("risk", {}).get("level", "unknown")
        risk_counts[lvl] = risk_counts.get(lvl, 0) + 1

    db.insert_audit_event(
        event_type="vendor_history_lookup",
        payload={"bidder_count": len(bidders), "risk_counts": risk_counts},
        project_id=project_id,
    )

    return JSONResponse({
        "project_id": project_id,
        "bidder_count": len(bidders),
        "risk_summary": risk_counts,
        "results": results,
    })


@app.delete("/api/vendors/cache")
async def clear_vendor_cache():
    """Clear all in-memory vendor lookup caches (forces fresh CPPP + GeM fetches)."""
    vendor_lookup.invalidate_cache()
    return JSONResponse({"success": True, "message": "Vendor lookup cache cleared"})


# ===== PRAHARI OFFICER SIGN-OFF =====

class SignOffRequest(BaseModel):
    officer_name: str

@app.post("/api/tenders/{project_id}/sign-off")
async def sign_off_tender(project_id: int, request: SignOffRequest, req: FastAPIRequest):
    """
    Record a digital sign-off by the responsible CRPF officer.
    Requires valid admin JWT. Idempotent — repeated calls update the signature.
    """
    auth_header = req.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth_header.split(" ", 1)[1]
    try:
        pyjwt.decode(token, _JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except pyjwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    officer = request.officer_name.strip()
    if not officer:
        raise HTTPException(status_code=400, detail="officer_name is required")
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Tender {project_id} not found")

    db.sign_off_project(project_id, officer)
    db.insert_audit_event(
        event_type="tender_signed_off",
        payload={"officer_name": officer},
        project_id=project_id,
    )
    return JSONResponse({"success": True, "signed_by": officer})


# ===== PRAHARI EVALUATION REPORT (9-STAGE) =====

@app.get("/api/tenders/{project_id}/report")
async def generate_evaluation_report(project_id: int):
    """
    Generate a full PRAHARI 9-stage evaluation PDF report for a tender.
    Covers: criteria, bidders, document authenticity, verdicts matrix,
    collusion alerts, human overrides, and the immutable audit trail.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Tender {project_id} not found")

    # ── Load all pipeline data ────────────────────────────────────────────────
    bidders   = db.get_bidders_by_project(project_id)
    verdicts  = db.get_verdicts_matrix(project_id)
    alerts    = db.get_collusion_alerts(project_id)
    audit_evs = db.get_audit_trail(project_id)

    # Tender criteria
    criteria = []
    try:
        dprs = db.get_dprs_by_project(project_id)
        if dprs and dprs[0].get("summary_json"):
            raw = dprs[0]["summary_json"]
            criteria_data = json.loads(raw) if isinstance(raw, str) else raw
            criteria = criteria_data.get("criteria", [])
    except Exception:
        pass

    # Documents per bidder
    all_docs: dict = {}
    doc_counts: dict = {}
    for b in bidders:
        docs = db.get_bidder_documents(b["id"])
        all_docs[b["id"]] = docs
        doc_counts[b["id"]] = len(docs)

    # Verdicts matrix: {bidder_id: {criterion_id: verdict_dict}}
    verdicts_by_bidder: dict = {}
    human_overrides = []
    for v in verdicts:
        bid = v["bidder_id"]
        cid = v["criterion_id"]
        verdicts_by_bidder.setdefault(bid, {})[cid] = v
        if v.get("human_override"):
            human_overrides.append(v)

    criterion_ids = sorted({v["criterion_id"] for v in verdicts}) if verdicts else [c["criterion_id"] for c in criteria]

    # Summary stats
    eligible   = sum(1 for v in verdicts if (v.get("override_verdict") or v.get("verdict")) == "Eligible")
    not_elig   = sum(1 for v in verdicts if (v.get("override_verdict") or v.get("verdict")) == "Not_Eligible")
    manual_rev = sum(1 for v in verdicts if (v.get("override_verdict") or v.get("verdict")) == "Manual_Review")
    avg_conf   = (sum(v.get("confidence_score", 0) for v in verdicts) / max(len(verdicts), 1))

    pipeline_status = "Complete" if verdicts else "Partial — Evaluation Pending"

    context = {
        "project":             project,
        "generated_date":      datetime.now().strftime("%d %B %Y at %I:%M %p"),
        "pipeline_status":     pipeline_status,
        "criteria":            criteria,
        "bidders":             bidders,
        "all_docs":            all_docs,
        "doc_counts":          doc_counts,
        "verdicts_by_bidder":  verdicts_by_bidder,
        "criterion_ids":       criterion_ids[:20],  # cap at 20 columns for readability
        "human_overrides":     human_overrides,
        "collusion_alerts":    alerts,
        "audit_events":        serialize_datetime(audit_evs)[-50:],  # last 50 events
        "summary": {
            "eligible":         eligible,
            "not_eligible":     not_elig,
            "manual_review":    manual_rev,
            "collusion_alerts": len(alerts),
            "avg_confidence":   round(avg_conf, 3),
        },
    }

    html_content = templates.get_template("reports/prahari_evaluation_report.html").render(context)

    try:
        pdf_bytes = HTML(string=html_content).write_pdf()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF rendering failed: {str(e)}")

    safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in project.get("name", "Tender"))
    filename  = f"PRAHARI_Evaluation_{safe_name}_{datetime.now().strftime('%Y%m%d')}.pdf"

    db.insert_audit_event(
        event_type="report_generated",
        payload={"filename": filename, "pages": "full"},
        project_id=project_id,
    )

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# ===== BIDDER PRE-SUBMISSION SELF-CHECK API =====

@app.post("/api/self-check/{project_id}")
async def run_self_check(
    project_id: int,
    company_name: str = Form(...),
    document_types: str = Form(...),   # JSON array of strings, one per file
    files: List[UploadFile] = File(...),
):
    """
    Ephemeral self-check: score documents and run criterion matching for a
    prospective bidder WITHOUT writing anything to the database.
    Used for pre-submission eligibility assessment.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Tender {project_id} not found")

    if not company_name.strip():
        raise HTTPException(status_code=400, detail="company_name is required")

    if not files:
        raise HTTPException(status_code=400, detail="At least one document is required")

    try:
        doc_types: list = json.loads(document_types)
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=400, detail="document_types must be a JSON array of strings")

    if len(doc_types) != len(files):
        raise HTTPException(status_code=400, detail=f"Mismatch: {len(files)} files but {len(doc_types)} document types")

    # Load tender criteria
    dprs = db.get_dprs_by_project(project_id)
    if not dprs or not dprs[0].get("summary_json"):
        raise HTTPException(status_code=400, detail="Tender criteria not yet extracted. Admin must run /extract-criteria first.")

    criteria_data = dprs[0]["summary_json"]
    if isinstance(criteria_data, str):
        criteria_data = json.loads(criteria_data)
    criteria = criteria_data.get("criteria", [])
    if not criteria:
        raise HTTPException(status_code=400, detail="No criteria found in this tender.")

    temp_files: list[str] = []
    bidder_documents = []

    try:
        for file, doc_type in zip(files, doc_types):
            if not file.filename:
                continue
            if not file.filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"Only PDFs accepted; got: {file.filename}")

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            uid = str(uuid.uuid4())[:8]
            stored_name = f"selfcheck_{uid}_{timestamp}_{file.filename}"
            filepath = str(DATA_DIR / stored_name)
            temp_files.append(filepath)

            content = await file.read()
            with open(filepath, "wb") as fh:
                fh.write(content)

            # Upload to Gemini for AI processing
            file_ref = await gemini_client.upload_file(filepath)

            # Run authenticity scoring
            auth_result = {}
            try:
                auth_result = await gemini_client.score_document_authenticity(file_ref, doc_type)
            except Exception as ae:
                print(f"⚠ Self-check auth scoring failed for {file.filename}: {ae}")

            bidder_documents.append({
                "id": None,
                "document_type": doc_type,
                "original_filename": file.filename,
                "uploaded_file_ref": file_ref,
                "authenticity_score": auth_result.get("authenticity_score", 0.5),
                "tamper_risk_level": auth_result.get("tamper_risk_level", "Medium"),
                "metadata_flags": {
                    "flags": auth_result.get("flags", []),
                    "extracted_fields": auth_result.get("extracted_fields", {}),
                    "summary": auth_result.get("summary", ""),
                },
                "language_detected": auth_result.get("language_detected"),
            })

        # Run criterion matching (no DB persistence)
        raw_verdicts = await gemini_client.evaluate_bidder_criteria(
            criteria=criteria,
            bidder_documents=bidder_documents,
            company_name=company_name.strip(),
        )

        # Compute summary
        eligible = sum(1 for v in raw_verdicts if v.get("verdict") == "Eligible")
        not_eligible = sum(1 for v in raw_verdicts if v.get("verdict") == "Not_Eligible")
        manual = sum(1 for v in raw_verdicts if v.get("verdict") == "Manual_Review")
        total = len(raw_verdicts)
        avg_conf = round(sum(v.get("confidence_score", 0) for v in raw_verdicts) / max(total, 1), 3)

        if not_eligible > 0:
            overall = "Likely_Not_Eligible"
        elif manual > 0:
            overall = "Needs_Review"
        else:
            overall = "Likely_Eligible"

        return JSONResponse({
            "success": True,
            "project_id": project_id,
            "project_name": project.get("name"),
            "company_name": company_name.strip(),
            "overall_assessment": overall,
            "summary": {
                "eligible": eligible,
                "not_eligible": not_eligible,
                "manual_review": manual,
                "total_criteria": total,
                "avg_confidence": avg_conf,
            },
            "documents": [
                {
                    "filename": d["original_filename"],
                    "document_type": d["document_type"],
                    "authenticity_score": d["authenticity_score"],
                    "tamper_risk_level": d["tamper_risk_level"],
                    "flags": d["metadata_flags"].get("flags", []),
                    "language": d.get("language_detected"),
                }
                for d in bidder_documents
            ],
            "verdicts": raw_verdicts,
            "disclaimer": (
                "This is a preliminary AI-assisted self-assessment only. "
                "Final eligibility is determined by the authorised procurement officers. "
                "Results are not stored and carry no legal weight."
            ),
        })

    finally:
        # Clean up all local temp files
        for fp in temp_files:
            try:
                if os.path.exists(fp):
                    os.remove(fp)
            except Exception:
                pass


# ===== DIFFERENTIAL PRIVACY ANALYTICS API =====

@app.get("/api/tenders/{project_id}/analytics")
async def get_tender_analytics(
    project_id: int,
    epsilon: float = 1.0,
    reset_budget: bool = False,
):
    """
    Return (ε, δ=0)-DP aggregate analytics for a tender's evaluation state.

    Query parameters:
      epsilon        — privacy loss budget for this query (default 1.0)
      reset_budget   — if true, reset the per-project budget counter first
    """
    if epsilon <= 0 or epsilon > 10:
        raise HTTPException(status_code=400, detail="epsilon must be in (0, 10]")

    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Tender {project_id} not found")

    if reset_budget:
        privacy.reset_budget(project_id)

    bidders = db.get_bidders_by_project(project_id)
    verdicts = db.get_verdicts_matrix(project_id)

    # Gather all bidder documents for auth score analytics
    all_docs = []
    for b in bidders:
        all_docs.extend(db.get_bidder_documents(b['id']))

    analytics = privacy.compute_dp_analytics(
        project_id=project_id,
        bidders=bidders,
        verdicts=verdicts,
        documents=all_docs,
        epsilon=epsilon,
    )

    db.insert_audit_event(
        event_type="dp_analytics_query",
        payload={"epsilon": epsilon, "total_epsilon_spent": analytics["total_epsilon_spent"]},
        project_id=project_id,
    )

    return JSONResponse({"project_id": project_id, **analytics})


# ===== EVALUATION Q&A API =====

class EvaluationQARequest(BaseModel):
    question: str


@app.post("/api/tenders/{project_id}/qa")
@limiter.limit("30/minute")
async def evaluation_qa(http_req: FastAPIRequest, project_id: int, request: EvaluationQARequest):
    """
    Natural-language Q&A over a tender's evaluation results.
    Maintains a per-project stateful Gemini chat session seeded with the
    verdicts matrix, bidder profiles, collusion alerts, and criteria.
    """
    project = db.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Tender {project_id} not found")

    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="question is required")

    # Load evaluation context data
    bidders = db.get_bidders_by_project(project_id)
    verdicts = db.get_verdicts_matrix(project_id)
    alerts = db.get_collusion_alerts(project_id)

    # Try to get tender criteria from the DPR summary
    criteria_data = None
    try:
        dprs = db.get_dprs_by_project(project_id)
        if dprs and dprs[0].get("summary_json"):
            raw = dprs[0]["summary_json"]
            criteria_data = json.loads(raw) if isinstance(raw, str) else raw
    except Exception:
        pass

    context = gemini_client._build_evaluation_context(
        project=project,
        bidders=bidders,
        verdicts=verdicts,
        alerts=alerts,
        criteria_data=criteria_data,
    )

    try:
        answer = await gemini_client.answer_evaluation_question(
            project_id=project_id,
            question=request.question.strip(),
            context=context,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Q&A failed: {str(e)}")

    db.insert_audit_event(
        event_type="evaluation_qa",
        payload={"question": request.question.strip(), "answer_length": len(answer)},
        project_id=project_id,
    )

    return JSONResponse({"answer": answer})


@app.delete("/api/tenders/{project_id}/qa")
async def clear_evaluation_qa(project_id: int):
    """Clear the in-memory Q&A session for a tender (resets chat history)."""
    gemini_client.clear_evaluation_qa_session(project_id)
    return JSONResponse({"success": True, "message": f"Q&A session cleared for tender {project_id}"})


@app.post("/api/landing-chat")
@limiter.limit("20/minute")
async def landing_chat(http_req: FastAPIRequest, request: EvaluationQARequest):
    """
    Public-facing chat on the landing page — answers general questions about
    PRAHARI and CRPF procurement. No tender context required.
    """
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="question is required")

    SYSTEM = """You are PRAHARI AI — an AI-powered tender evaluation assistant for CRPF procurement.
Answer questions about PRAHARI's features, the 9-stage pipeline, how bidder evaluation works,
collusion detection, document authenticity, differential privacy, and government procurement best practices.
Keep answers concise (2-4 sentences). Do not answer questions unrelated to procurement or PRAHARI."""

    import asyncio

    def _ask():
        import google.generativeai as genai
        model = genai.GenerativeModel(
            model_name="gemini-2.5-flash",
            system_instruction=SYSTEM,
            generation_config=genai.types.GenerationConfig(temperature=0.3, max_output_tokens=256),
        )
        return model.generate_content(question).text

    try:
        answer = await asyncio.to_thread(_ask)
    except Exception:
        answer = ("PRAHARI automates CRPF tender evaluation with a 9-stage AI pipeline: "
                  "criteria extraction, market benchmarking, document authenticity, bidder ingestion, "
                  "criterion matching, collusion detection, differential privacy analytics, "
                  "human review & sign-off, and a full audit report.")
    return JSONResponse({"answer": answer})


@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "ok", "service": "prahari"}


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    # Use 1 worker on Windows to avoid WinError 10022
    uvicorn.run(app, host=host, port=port)
