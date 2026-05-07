import json
from datetime import datetime
from typing import Optional, Dict, List
import backend.db_config as db_config



def init_db():
    """Initialize PostgreSQL database with required tables."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    try:
        # Create Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                state TEXT NOT NULL,
                scheme TEXT NOT NULL,
                sector TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL,
                comparison_result TEXT,
                comparison_generated_at TIMESTAMP,
                compliance_weights JSONB
            )
        """)
    
        # Create DPRs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dprs (
                id SERIAL PRIMARY KEY,
                project_id INTEGER REFERENCES projects(id),
                filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                uploaded_file_ref TEXT NOT NULL,
                upload_ts TIMESTAMP NOT NULL,
                summary_json TEXT,
                client_id INTEGER,
                status TEXT DEFAULT 'completed',
                admin_feedback TEXT,
                feedback_timestamp TIMESTAMP,
                validation_flags TEXT
            )
        """)
        
        # Create index on original_filename for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_original_filename 
            ON dprs(original_filename)
        """)
        
        # Create messages table for chat history
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id SERIAL PRIMARY KEY,
                dpr_id INTEGER NOT NULL REFERENCES dprs(id),
                role TEXT NOT NULL,
                text TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL
            )
        """)
        
        # Create comparison_chats table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comparison_chats (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL,
                created_ts TIMESTAMP NOT NULL
            )
        """)
        
        # Create comparison_chat_pdfs table (junction table)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comparison_chat_pdfs (
                id SERIAL PRIMARY KEY,
                comparison_chat_id INTEGER NOT NULL REFERENCES comparison_chats(id),
                dpr_id INTEGER NOT NULL REFERENCES dprs(id),
                UNIQUE (comparison_chat_id, dpr_id)
            )
        """)
        
        # Create comparison_messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS comparison_messages (
                id SERIAL PRIMARY KEY,
                comparison_chat_id INTEGER NOT NULL REFERENCES comparison_chats(id),
                role TEXT NOT NULL,
                text TEXT NOT NULL,
                timestamp TIMESTAMP NOT NULL
            )
        """)
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                name TEXT,
                username TEXT,
                created_at TIMESTAMP NOT NULL
            )
        """)
        
        # Create unique index for email
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email
            ON users(email)
        """)
        
        # Create client_dprs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS client_dprs (
                id SERIAL PRIMARY KEY,
                client_id INTEGER NOT NULL REFERENCES users(id),
                project_name TEXT NOT NULL,
                dpr_filename TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'Review',
                created_at TIMESTAMP NOT NULL
            )
        """)
        
        # Create index on client_id for faster lookups
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_client_dprs_client_id
            ON client_dprs(client_id)
        """)

        # ===== PRAHARI PIPELINE TABLES =====

        # Bidders — one row per company per tender
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bidders (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                company_name TEXT NOT NULL,
                gstin TEXT,
                pan TEXT,
                contact_email TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bidders_project_id ON bidders(project_id)
        """)

        # Bidder documents — individual PDF files per bidder
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bidder_documents (
                id SERIAL PRIMARY KEY,
                bidder_id INTEGER NOT NULL REFERENCES bidders(id) ON DELETE CASCADE,
                document_type TEXT NOT NULL,
                original_filename TEXT NOT NULL,
                uploaded_file_ref TEXT,
                cloudinary_url TEXT,
                cloudinary_public_id TEXT,
                language_detected TEXT,
                authenticity_score NUMERIC(4,3),
                tamper_risk_level TEXT DEFAULT 'unknown',
                metadata_flags JSONB,
                upload_ts TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_bidder_docs_bidder_id ON bidder_documents(bidder_id)
        """)

        # Verdicts — one row per (bidder × criterion)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS verdicts (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                bidder_id INTEGER NOT NULL REFERENCES bidders(id) ON DELETE CASCADE,
                criterion_id TEXT NOT NULL,
                verdict TEXT NOT NULL CHECK (verdict IN ('Eligible', 'Not_Eligible', 'Manual_Review')),
                confidence_score NUMERIC(4,3),
                extracted_value_text TEXT,
                threshold_value BIGINT,
                evidence_doc_id INTEGER REFERENCES bidder_documents(id),
                evidence_quote TEXT,
                evidence_page INTEGER,
                reasoning TEXT,
                tamper_risk_score NUMERIC(4,3),
                human_override BOOLEAN DEFAULT FALSE,
                override_verdict TEXT,
                override_justification TEXT,
                override_by_officer_id INTEGER REFERENCES users(id),
                override_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT NOW(),
                UNIQUE (bidder_id, criterion_id)
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verdicts_project_id ON verdicts(project_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verdicts_bidder_id ON verdicts(bidder_id)
        """)

        # Collusion alerts — cross-bidder integrity analysis
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS collusion_alerts (
                id SERIAL PRIMARY KEY,
                project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
                alert_type TEXT NOT NULL,
                bidder_ids INTEGER[] NOT NULL,
                description TEXT NOT NULL,
                confidence_score NUMERIC(4,3),
                officer_disposition TEXT DEFAULT 'pending',
                disposition_notes TEXT,
                disposition_by INTEGER REFERENCES users(id),
                disposition_at TIMESTAMP,
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_collusion_project_id ON collusion_alerts(project_id)
        """)

        # Audit events — immutable append-only log
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_events (
                event_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                event_type TEXT NOT NULL,
                project_id INTEGER REFERENCES projects(id),
                bidder_id INTEGER REFERENCES bidders(id),
                criterion_id TEXT,
                payload_hash TEXT NOT NULL,
                model_version TEXT,
                confidence_score NUMERIC(4,3),
                language_detected TEXT,
                dp_epsilon NUMERIC(6,4),
                officer_id INTEGER REFERENCES users(id),
                created_at TIMESTAMP NOT NULL DEFAULT NOW()
            )
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_project_id ON audit_events(project_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_bidder_id ON audit_events(bidder_id)
        """)

        # Immutable trigger — blocks UPDATE and DELETE on audit_events
        cursor.execute("""
            CREATE OR REPLACE FUNCTION prevent_audit_mutation()
            RETURNS TRIGGER AS $$
            BEGIN
                RAISE EXCEPTION 'audit_events is append-only: UPDATE and DELETE are not permitted';
            END;
            $$ LANGUAGE plpgsql
        """)
        cursor.execute("""
            DROP TRIGGER IF EXISTS audit_events_immutable ON audit_events
        """)
        cursor.execute("""
            CREATE TRIGGER audit_events_immutable
            BEFORE UPDATE OR DELETE ON audit_events
            FOR EACH ROW EXECUTE FUNCTION prevent_audit_mutation()
        """)

        conn.commit()
        print("✓ PostgreSQL database initialized successfully")
    
    except Exception as e:
        conn.rollback()
        print(f"✗ Database initialization failed: {e}")
        raise
    finally:
        cursor.close()
        db_config.release_connection(conn)


def insert_dpr(filename: str, original_filename: str, filepath: str, file_ref: str, 
               summary_json: dict, project_id: int = None, 
               cloudinary_url: str = None, cloudinary_public_id: str = None) -> int:
    """Insert a new DPR record and return its ID."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    timestamp = datetime.now()
    json_str = json.dumps(summary_json, indent=2) if summary_json else None
    
    # DEBUG LOGGING
    print(f"🔍 DB.INSERT_DPR CALLED:")
    print(f"  filename: {filename}")
    print(f"  cloudinary_url: {cloudinary_url}")
    print(f"  cloudinary_public_id: {cloudinary_public_id}")
    print(f"  cloudinary_url is None: {cloudinary_url is None}")
    
    cursor.execute("""
        INSERT INTO dprs (filename, original_filename, filepath, uploaded_file_ref, upload_ts, summary_json, project_id, cloudinary_url, cloudinary_public_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (filename, original_filename, filepath, file_ref, timestamp, json_str, project_id, cloudinary_url, cloudinary_public_id))
    
    dpr_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    
    print(f"✓ DPR inserted with ID: {dpr_id}")
    print(f"  Inserted cloudinary_url: {cloudinary_url}")
    return dpr_id


def update_dpr(dpr_id: int, summary_json: dict, validation_flags: dict = None):
    """Update an existing DPR record with analysis results and validation flags."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    # DEBUG: Check cloudinary_url BEFORE update
    cursor.execute("SELECT cloudinary_url, cloudinary_public_id FROM dprs WHERE id = %s", (dpr_id,))
    before = cursor.fetchone()
    print(f"🔍 BEFORE UPDATE - DPR {dpr_id}: cloudinary_url={before[0] if before else 'NOT_FOUND'}")
    
    json_str = json.dumps(summary_json, indent=2)
    
    if validation_flags is not None:
        validation_flags_str = json.dumps(validation_flags)
        cursor.execute("""
            UPDATE dprs 
            SET summary_json = %s, validation_flags = %s
            WHERE id = %s
        """, (json_str, validation_flags_str, dpr_id))
    else:
        cursor.execute("""
            UPDATE dprs 
            SET summary_json = %s
            WHERE id = %s
        """, (json_str, dpr_id))
    
    conn.commit()
    
    # DEBUG: Check cloudinary_url AFTER update
    cursor.execute("SELECT cloudinary_url, cloudinary_public_id FROM dprs WHERE id = %s", (dpr_id,))
    after = cursor.fetchone()
    print(f"🔍 AFTER UPDATE - DPR {dpr_id}: cloudinary_url={after[0] if after else 'NOT_FOUND'}")
    
    cursor.close()
    db_config.release_connection(conn)
    print(f"✓ DPR {dpr_id} updated with analysis results")


def update_dpr_file_ref(dpr_id: int, file_ref: str):
    """Update the uploaded_file_ref for a DPR when re-uploading an expired file."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    cursor.execute("""
        UPDATE dprs 
        SET uploaded_file_ref = %s
        WHERE id = %s
    """, (file_ref, dpr_id))
    
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    print(f"✓ DPR {dpr_id} file reference updated: {file_ref}")


def update_dpr_feedback(dpr_id: int, feedback: str):
    """Update admin feedback for a DPR."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    timestamp = datetime.now()
    
    cursor.execute("""
        UPDATE dprs 
        SET admin_feedback = %s, feedback_timestamp = %s
        WHERE id = %s
    """, (feedback, timestamp, dpr_id))
    
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    print(f"✓ DPR {dpr_id} feedback updated")


def update_dpr_status(dpr_id: int, status: str):
    """Update the status of a DPR (accepted, rejected, pending, etc.)."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    cursor.execute("""
        UPDATE dprs 
        SET status = %s
        WHERE id = %s
    """, (status, dpr_id))
    
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    print(f"✓ DPR {dpr_id} status updated to: {status}")


def validate_dpr_against_project(dpr_id: int, project_id: int, summary_json: dict) -> dict:
    """
    Validate DPR against project requirements and return validation flags.
    Checks if DPR state and sector match the project.
    
    Args:
        dpr_id: DPR ID
        project_id: Project ID
        summary_json: Parsed DPR analysis JSON
        
    Returns:
        Updated summary_json with validationFlags populated
    """
    # Get project details
    project = get_project(project_id)
    if not project or not summary_json:
        return summary_json
    
    # Extract DPR state and sector from correct paths
    dpr_state = summary_json.get("tenderDetails", {}).get("projectLocation", {}).get("state", "").strip()
    dpr_sector = summary_json.get("extractedSector", "").strip()
    
    project_state = project.get("state", "").strip()
    project_sector = project.get("sector", "").strip()
    
    # Initialize validationFlags if not present
    if "validationFlags" not in summary_json:
        summary_json["validationFlags"] = {}
    
    # Check state mismatch (case-insensitive)
    state_mismatch = False
    if dpr_state and project_state:
        state_mismatch = (dpr_state.lower() != project_state.lower())
    
    # Check sector mismatch (case-insensitive, partial match allowed)
    sector_mismatch = False
    if dpr_sector and project_sector:
        # Allow partial match (e.g., "Roads" matches "Roads and Bridges")
        sector_mismatch = (
            dpr_sector.lower() not in project_sector.lower() and 
            project_sector.lower() not in dpr_sector.lower()
        )
    
    # Populate validationFlags
    summary_json["validationFlags"]["stateMismatch"] = state_mismatch
    summary_json["validationFlags"]["sectorMismatch"] = sector_mismatch
    
    if state_mismatch:
        summary_json["validationFlags"]["stateMismatchDetails"] = (
            f"PDF mentions '{dpr_state}' but project is for '{project_state}'"
        )
    else:
        summary_json["validationFlags"]["stateMismatchDetails"] = "State matches project"
    
    if sector_mismatch:
        summary_json["validationFlags"]["sectorMismatchDetails"] = (
            f"PDF mentions '{dpr_sector}' but project sector is '{project_sector}'"
        )
    else:
        summary_json["validationFlags"]["sectorMismatchDetails"] = "Sector matches project"
    
    # Log validation results
    if state_mismatch or sector_mismatch:
        print(f"⚠ DPR {dpr_id} validation flags:")
        if state_mismatch:
            print(f"  - State mismatch: PDF='{dpr_state}' vs Project='{project_state}'")
        if sector_mismatch:
            print(f"  - Sector mismatch: PDF='{dpr_sector}' vs Project='{project_sector}'")
    else:
        print(f"✓ DPR {dpr_id} validation passed")
    
    return summary_json




def delete_dpr(dpr_id: int) -> Optional[str]:
    """
    Delete a DPR and all associated data.
    Returns the filepath of the deleted DPR so it can be removed from disk.
    """
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    # Get filepath before deletion
    cursor.execute("SELECT filepath FROM dprs WHERE id = %s", (dpr_id,))
    row = cursor.fetchone()
    filepath = row[0] if row else None
    
    # Delete from messages (chat history)
    cursor.execute("DELETE FROM messages WHERE dpr_id = %s", (dpr_id,))
    
    # Delete from comparison_chat_pdfs (remove from comparisons)
    cursor.execute("DELETE FROM comparison_chat_pdfs WHERE dpr_id = %s", (dpr_id,))
    
    # Delete from dprs table
    cursor.execute("DELETE FROM dprs WHERE id = %s", (dpr_id,))
    
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    
    print(f"✓ Deleted DPR {dpr_id} from database")
    return filepath


def get_dpr(dpr_id: int) -> Optional[Dict]:
    """Retrieve a DPR by ID."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)
    
    cursor.execute("""
        SELECT id, filename, original_filename, filepath, uploaded_file_ref, 
               upload_ts, summary_json, project_id, status, client_id,
               admin_feedback, feedback_timestamp, validation_flags,
               cloudinary_url, cloudinary_public_id
        FROM dprs 
        WHERE id = %s
    """, (dpr_id,))
    
    row = cursor.fetchone()
    cursor.close()
    db_config.release_connection(conn)
    
    if row:
        result = {
            "id": row["id"],
            "filename": row["filename"],
            "original_filename": row["original_filename"],
            "filepath": row["filepath"],
            "uploaded_file_ref": row["uploaded_file_ref"],
            "upload_ts": row["upload_ts"]
        }
        
        # Add client_id if it exists
        if "client_id" in row.keys():
            result["client_id"] = row["client_id"]
        
        # Add status if it exists
        if "status" in row.keys():
            result["status"] = row["status"]
        
        # Add feedback fields if they exist
        if "admin_feedback" in row.keys():
            result["admin_feedback"] = row["admin_feedback"]
        
        if "feedback_timestamp" in row.keys():
            result["feedback_timestamp"] = row["feedback_timestamp"]
        
        # Add Cloudinary fields
        if "cloudinary_url" in row.keys():
            result["cloudinary_url"] = row["cloudinary_url"]
        
        if "cloudinary_public_id" in row.keys():
            result["cloudinary_public_id"] = row["cloudinary_public_id"]
        
        # Parse summary_json if it exists and is not None
        if row["summary_json"]:
            try:
                result["summary_json"] = json.loads(row["summary_json"])
            except:
                result["summary_json"] = None
        else:
            result["summary_json"] = None
        
        # Parse validation_flags if it exists and is not None
        if "validation_flags" in row.keys() and row["validation_flags"]:
            try:
                result["validation_flags"] = json.loads(row["validation_flags"])
            except:
                result["validation_flags"] = None
        else:
            result["validation_flags"] = None
            
        return result
    return None


def get_dpr_by_filename(original_filename: str) -> Optional[Dict]:
    """Retrieve a DPR by original filename."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)
    
    cursor.execute("""
        SELECT id, filename, original_filename, filepath, uploaded_file_ref, upload_ts, summary_json
        FROM dprs WHERE original_filename = %s
    """, (original_filename,))
    
    row = cursor.fetchone()
    cursor.close()
    db_config.release_connection(conn)
    
    if row:
        return {
            "id": row["id"],
            "filename": row["filename"],
            "original_filename": row["original_filename"],
            "filepath": row["filepath"],
            "uploaded_file_ref": row["uploaded_file_ref"],
            "upload_ts": row["upload_ts"],
            "summary_json": json.loads(row["summary_json"]) if row["summary_json"] else None
        }
    return None


def get_all_dprs() -> List[Dict]:
    """Retrieve all DPRs with metadata."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)
    
    cursor.execute("""
        SELECT d.id, d.filename, d.original_filename, d.filepath, d.uploaded_file_ref, 
               d.upload_ts, d.summary_json, d.client_id, u.email as client_email
        FROM dprs d
        LEFT JOIN users u ON d.client_id = u.id
        ORDER BY d.upload_ts DESC
    """)
    
    rows = cursor.fetchall()
    cursor.close()
    db_config.release_connection(conn)
    
    return [
        {
            "id": row["id"],
            "filename": row["filename"],
            "original_filename": row["original_filename"],
            "filepath": row["filepath"],
            "uploaded_file_ref": row["uploaded_file_ref"],
            "upload_ts": row["upload_ts"],
            "summary_json": json.loads(row["summary_json"]) if row["summary_json"] else None,
            "client_id": row["client_id"],
            "client_email": row["client_email"]
        }
        for row in rows
    ]


def get_processing_dprs() -> List[Dict]:
    """Retrieve all DPRs that are still processing (summary_json is NULL)."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)
    
    cursor.execute("""
        SELECT id, filename, original_filename, filepath, uploaded_file_ref, upload_ts
        FROM dprs
        WHERE summary_json IS NULL OR summary_json = ''
    """)
    
    rows = cursor.fetchall()
    cursor.close()
    db_config.release_connection(conn)
    
    return [
        {
            "id": row["id"],
            "filename": row["filename"],
            "original_filename": row["original_filename"],
            "filepath": row["filepath"],
            "uploaded_file_ref": row["uploaded_file_ref"],
            "upload_ts": row["upload_ts"]
        }
        for row in rows
    ]


def insert_message(dpr_id: int, role: str, text: str):
    """Insert a chat message (role: 'user' or 'assistant')."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    timestamp = datetime.now()
    
    cursor.execute("""
        INSERT INTO messages (dpr_id, role, text, timestamp)
        VALUES (%s, %s, %s, %s)
    """, (dpr_id, role, text, timestamp))
    
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)


def get_messages(dpr_id: int) -> List[Dict]:
    """Retrieve all chat messages for a DPR."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)
    
    cursor.execute("""
        SELECT id, dpr_id, role, text, timestamp
        FROM messages
        WHERE dpr_id = %s
        ORDER BY timestamp ASC
    """, (dpr_id,))
    
    rows = cursor.fetchall()
    cursor.close()
    db_config.release_connection(conn)
    
    return [
        {
            "id": row["id"],
            "dpr_id": row["dpr_id"],
            "role": row["role"],
            "text": row["text"],
            "timestamp": row["timestamp"]
        }
        for row in rows
    ]


def clear_chat_history(dpr_id: int):
    """Delete all chat messages for a specific DPR."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    cursor.execute("DELETE FROM messages WHERE dpr_id = %s", (dpr_id,))
    
    deleted_count = cursor.rowcount
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    print(f"✓ Chat history cleared for DPR {dpr_id}")
    return deleted_count

# ===== COMPARISON CHAT FUNCTIONS =====

def create_comparison_chat(name: str, dpr_ids: List[int]) -> int:
    """Create a new comparison chat with associated DPRs."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    timestamp = datetime.now()
    
    # Insert comparison chat
    cursor.execute("""
        INSERT INTO comparison_chats (name, created_ts)
        VALUES (%s, %s)
        RETURNING id
    """, (name, timestamp))
    
    comparison_id = cursor.fetchone()[0]
    
    # Link DPRs to this comparison
    for dpr_id in dpr_ids:
        cursor.execute("""
            INSERT INTO comparison_chat_pdfs (comparison_chat_id, dpr_id)
            VALUES (%s, %s)
        """, (comparison_id, dpr_id))
    
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    
    print(f"✓ Comparison chat created with ID: {comparison_id} ({len(dpr_ids)} PDFs)")
    return comparison_id


def get_comparison_chat(comparison_id: int) -> Optional[Dict]:
    """Retrieve a comparison chat with its associated DPRs."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)
    
    # Get comparison chat
    cursor.execute("""
        SELECT id, name, created_ts
        FROM comparison_chats WHERE id = %s
    """, (comparison_id,))
    
    row = cursor.fetchone()
    if not row:
        cursor.close()
        db_config.release_connection(conn)
        return None
    
    # Get associated DPRs
    cursor.execute("""
        SELECT d.id, d.filename, d.original_filename, d.filepath, 
               d.uploaded_file_ref, d.upload_ts, d.summary_json
        FROM dprs d
        JOIN comparison_chat_pdfs ccp ON d.id = ccp.dpr_id
        WHERE ccp.comparison_chat_id = %s
    """, (comparison_id,))
    
    dprs = [
        {
            "id": dpr["id"],
            "filename": dpr["filename"],
            "original_filename": dpr["original_filename"],
            "filepath": dpr["filepath"],
            "uploaded_file_ref": dpr["uploaded_file_ref"],
            "upload_ts": dpr["upload_ts"],
            "summary_json": json.loads(dpr["summary_json"])
        }
        for dpr in cursor.fetchall()
    ]
    
    cursor.close()
    db_config.release_connection(conn)
    
    return {
        "id": row["id"],
        "name": row["name"],
        "created_ts": row["created_ts"],
        "dprs": dprs
    }


def get_all_comparison_chats() -> List[Dict]:
    """Retrieve all comparison chats with metadata."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)
    
    cursor.execute("""
        SELECT id, name, created_ts
        FROM comparison_chats
        ORDER BY created_ts DESC
    """)
    
    chats = []
    for row in cursor.fetchall():
        comparison_id = row["id"]
        
        # Get count of PDFs in this comparison
        cursor.execute("""
            SELECT COUNT(*) as pdf_count
            FROM comparison_chat_pdfs
            WHERE comparison_chat_id = %s
        """, (comparison_id,))
        
        pdf_count = cursor.fetchone()["pdf_count"]
        
        # Get count of messages in this comparison
        cursor.execute("""
            SELECT COUNT(*) as message_count
            FROM comparison_messages
            WHERE comparison_chat_id = %s
        """, (comparison_id,))
        
        message_count = cursor.fetchone()["message_count"]
        
        chats.append({
            "id": row["id"],
            "name": row["name"],
            "created_ts": row["created_ts"],
            "dpr_count": pdf_count,
            "message_count": message_count
        })
    
    cursor.close()
    db_config.release_connection(conn)
    return chats


def insert_comparison_message(comparison_id: int, role: str, text: str):
    """Insert a chat message for a comparison (role: 'user' or 'assistant')."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    timestamp = datetime.now()
    
    cursor.execute("""
        INSERT INTO comparison_messages (comparison_chat_id, role, text, timestamp)
        VALUES (%s, %s, %s, %s)
    """, (comparison_id, role, text, timestamp))
    
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)


def get_comparison_messages(comparison_id: int) -> List[Dict]:
    """Retrieve all chat messages for a comparison."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)
    
    cursor.execute("""
        SELECT id, comparison_chat_id, role, text, timestamp
        FROM comparison_messages
        WHERE comparison_chat_id = %s
        ORDER BY timestamp ASC
    """, (comparison_id,))
    
    rows = cursor.fetchall()
    cursor.close()
    db_config.release_connection(conn)
    
    return [
        {
            "id": row["id"],
            "comparison_chat_id": row["comparison_chat_id"],
            "role": row["role"],
            "text": row["text"],
            "timestamp": row["timestamp"]
        }
        for row in rows
    ]


def clear_comparison_history(comparison_id: int):
    """Delete all chat messages for a specific comparison."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    cursor.execute("""
        DELETE FROM comparison_messages WHERE comparison_chat_id = %s
    """, (comparison_id,))
    
    deleted_count = cursor.rowcount
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    
    print(f"✓ Cleared {deleted_count} messages for comparison chat {comparison_id}")
    return deleted_count


def delete_comparison_chat(comparison_id: int):
    """Delete a comparison chat and all associated data."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    # Delete messages
    cursor.execute("""
        DELETE FROM comparison_messages WHERE comparison_chat_id = %s
    """, (comparison_id,))
    
    # Delete PDF associations
    cursor.execute("""
        DELETE FROM comparison_chat_pdfs WHERE comparison_chat_id = %s
    """, (comparison_id,))
    
    # Delete the comparison chat itself
    cursor.execute("""
        DELETE FROM comparison_chats WHERE id = %s
    """, (comparison_id,))
    
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    print(f"✓ Deleted comparison chat {comparison_id}")


def add_dpr_to_comparison(comparison_id: int, dpr_id: int) -> bool:
    """Add a DPR to an existing comparison."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    try:
        # Check if DPR is already in the comparison
        cursor.execute("""
            SELECT COUNT(*) FROM comparison_chat_pdfs 
            WHERE comparison_chat_id = %s AND dpr_id = %s
        """, (comparison_id, dpr_id))
        
        if cursor.fetchone()[0] > 0:
            cursor.close()
            db_config.release_connection(conn)
            print(f"⚠ DPR {dpr_id} is already in comparison {comparison_id}")
            return False
        
        # Add the DPR to the comparison
        cursor.execute("""
            INSERT INTO comparison_chat_pdfs (comparison_chat_id, dpr_id)
            VALUES (%s, %s)
        """, (comparison_id, dpr_id))
        
        conn.commit()
        cursor.close()
        db_config.release_connection(conn)
        print(f"✓ Added DPR {dpr_id} to comparison {comparison_id}")
        return True
    except Exception as e:
        cursor.close()
        db_config.release_connection(conn)
        print(f"✗ Failed to add DPR to comparison: {str(e)}")
        return False


def remove_dpr_from_comparison(comparison_id: int, dpr_id: int) -> bool:
    """Remove a DPR from a comparison. Requires at least 2 DPRs to remain."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    try:
        # Check current count of DPRs in comparison
        cursor.execute("""
            SELECT COUNT(*) FROM comparison_chat_pdfs 
            WHERE comparison_chat_id = %s
        """, (comparison_id,))
        
        current_count = cursor.fetchone()[0]
        
        if current_count <= 2:
            cursor.close()
            db_config.release_connection(conn)
            print(f"⚠ Cannot remove DPR: comparison {comparison_id} must have at least 2 DPRs")
            return False
        
        # Remove the DPR from the comparison
        cursor.execute("""
            DELETE FROM comparison_chat_pdfs 
            WHERE comparison_chat_id = %s AND dpr_id = %s
        """, (comparison_id, dpr_id))
        
        deleted = cursor.rowcount > 0
        conn.commit()
        cursor.close()
        db_config.release_connection(conn)
        
        if deleted:
            print(f"✓ Removed DPR {dpr_id} from comparison {comparison_id}")
        else:
            print(f"⚠ DPR {dpr_id} was not in comparison {comparison_id}")
        
        return deleted
    except Exception as e:
        cursor.close()
        db_config.release_connection(conn)
        print(f"✗ Failed to remove DPR from comparison: {str(e)}")
        return False


# ===== PROJECT FUNCTIONS =====

def get_projects() -> List[Dict]:
    """Retrieve all projects with their DPR counts and comparison status."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)
    
    cursor.execute("""
        SELECT p.*, COUNT(d.id) as dpr_count
        FROM projects p
        LEFT JOIN dprs d ON p.id = d.project_id
        GROUP BY p.id
        ORDER BY p.created_at DESC
    """)
    
    rows = cursor.fetchall()
    cursor.close()
    db_config.release_connection(conn)
    
    projects = []
    for row in rows:
        project = dict(row)
        # Add has_comparison flag
        project['has_comparison'] = project.get('comparison_result') is not None
        projects.append(project)
    
    return projects


def create_project(name: str, state: str, scheme: str, sector: str) -> int:
    """Create a new project."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    timestamp = datetime.now()
    
    cursor.execute("""
        INSERT INTO projects (name, state, scheme, sector, created_at)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (name, state, scheme, sector, timestamp))
    
    project_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    
    print(f"✓ Project created with ID: {project_id}")
    return project_id


def delete_project(project_id: int) -> List[str]:
    """
    Delete a project and all its associated DPRs.
    Returns a list of filepaths that should be deleted from disk.
    """
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    # Get all DPR filepaths for this project before deletion
    cursor.execute("""
        SELECT filepath FROM dprs WHERE project_id = %s
    """, (project_id,))
    
    filepaths = [row[0] for row in cursor.fetchall()]
    
    # Get all DPR IDs for this project
    cursor.execute("""
        SELECT id FROM dprs WHERE project_id = %s
    """, (project_id,))
    
    dpr_ids = [row[0] for row in cursor.fetchall()]
    
    # Delete messages for each DPR
    for dpr_id in dpr_ids:
        cursor.execute("DELETE FROM messages WHERE dpr_id = %s", (dpr_id,))
        cursor.execute("DELETE FROM comparison_chat_pdfs WHERE dpr_id = %s", (dpr_id,))
    
    # Delete all DPRs in this project
    cursor.execute("""
        DELETE FROM dprs WHERE project_id = %s
    """, (project_id,))
    
    # Delete the project itself
    cursor.execute("""
        DELETE FROM projects WHERE id = %s
    """, (project_id,))
    
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    
    print(f"✓ Deleted project {project_id} and {len(dpr_ids)} associated DPRs")
    return filepaths


def get_project(project_id: int) -> Optional[Dict]:
    """Get project details with comparison status."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)
    
    cursor.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
    row = cursor.fetchone()
    cursor.close()
    db_config.release_connection(conn)
    
    if row:
        project = dict(row)
        # Add has_comparison flag
        project['has_comparison'] = project.get('comparison_result') is not None
        return project
    return None


def sign_off_project(project_id: int, officer_name: str) -> None:
    """Record a digital sign-off by the named officer on a tender."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    cursor.execute("""
        ALTER TABLE projects
        ADD COLUMN IF NOT EXISTS signed_by TEXT,
        ADD COLUMN IF NOT EXISTS signed_at TIMESTAMP
    """)
    cursor.execute("""
        UPDATE projects SET signed_by = %s, signed_at = NOW()
        WHERE id = %s
    """, (officer_name.strip(), project_id))
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    print(f"✓ Project {project_id} signed off by '{officer_name}'")


def get_dprs_by_project(project_id: int) -> List[Dict]:
    """Get all DPRs for a specific project."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)
    
    cursor.execute("""
        SELECT d.id, d.filename, d.original_filename, d.upload_ts, d.summary_json, 
               d.project_id, d.status, d.client_id, d.validation_flags, u.email as client_email
        FROM dprs d
        LEFT JOIN users u ON d.client_id = u.id
        WHERE d.project_id = %s
        ORDER BY d.upload_ts DESC
    """, (project_id,))
    
    rows = cursor.fetchall()
    cursor.close()

    db_config.release_connection(conn)
    
    dprs = []
    for row in rows:
        dpr = dict(row)
        if dpr['summary_json']:
            try:
                dpr['summary_json'] = json.loads(dpr['summary_json'])
            except:
                dpr['summary_json'] = None
        
        if dpr.get('validation_flags'):
            try:
                dpr['validation_flags'] = json.loads(dpr['validation_flags'])
            except:
                dpr['validation_flags'] = None
        
        dprs.append(dpr)
        
    return dprs


def save_project_comparison(project_id: int, comparison_json: dict) -> None:
    """Save comparison result for a project."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    timestamp = datetime.now()
    json_str = json.dumps(comparison_json, indent=2)
    
    cursor.execute("""
        UPDATE projects 
        SET comparison_result = %s, comparison_generated_at = %s
        WHERE id = %s
    """, (json_str, timestamp, project_id))
    
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    print(f"✓ Saved comparison result for project {project_id}")


def get_project_comparison(project_id: int) -> Optional[Dict]:
    """Retrieve saved comparison result for a project."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)
    
    cursor.execute("""
        SELECT comparison_result, comparison_generated_at
        FROM projects 
        WHERE id = %s
    """, (project_id,))
    
    row = cursor.fetchone()
    cursor.close()

    db_config.release_connection(conn)
    
    if row and row["comparison_result"]:
        return {
            "comparison": json.loads(row["comparison_result"]),
            "generated_at": row["comparison_generated_at"]
        }
    return None


def clear_project_comparison(project_id: int) -> None:
    """Clear/reset comparison result for a project."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    cursor.execute("""
        UPDATE projects 
        SET comparison_result = NULL, comparison_generated_at = NULL
        WHERE id = %s
    """, (project_id,))
    
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    print(f"✓ Cleared comparison result for project {project_id}")


# ===== USER AUTHENTICATION FUNCTIONS =====

def create_user(email: str, password_hash: str, name: str = None, username: str = None) -> int:
    """Create a new user and return the user ID."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    timestamp = datetime.now()
    
    try:
        cursor.execute("""
            INSERT INTO users (email, password_hash, name, username, created_at)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (email, password_hash, name, username, timestamp))
        
        user_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        db_config.release_connection(conn)
        
        print(f"✓ User created with ID: {user_id}")
        return user_id
    except Exception as e:  # TODO: Use psycopg2.IntegrityError as e:
        cursor.close()
        db_config.release_connection(conn)
        if 'email' in str(e) or 'UNIQUE' in str(e):
            raise ValueError("Email already exists")
        else:
            raise ValueError("User creation failed")


def get_user_by_username(username: str) -> Optional[Dict]:
    """Retrieve a user by username."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)
    
    cursor.execute("""
        SELECT id, username, email, password_hash, name, created_at
        FROM users WHERE username = %s
    """, (username,))
    
    row = cursor.fetchone()
    cursor.close()

    db_config.release_connection(conn)
    
    if row:
        return {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "password_hash": row["password_hash"],
            "name": row["name"],
            "created_at": row["created_at"]
        }
    return None


def get_user_by_email(email: str) -> Optional[Dict]:
    """Retrieve a user by email."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)
    
    cursor.execute("""
        SELECT id, username, email, password_hash, name, created_at
        FROM users WHERE email = %s
    """, (email,))
    
    row = cursor.fetchone()
    cursor.close()

    db_config.release_connection(conn)
    
    if row:
        return {
            "id": row["id"],
            "username": row["username"] if "username" in row.keys() else None,
            "email": row["email"],
            "password_hash": row["password_hash"],
            "name": row["name"],
            "created_at": row["created_at"]
        }
    return None


def get_user_by_email(email: str) -> Optional[Dict]:
    """Retrieve a user by email."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)
    
    cursor.execute("""
        SELECT id, username, email, password_hash, created_at
        FROM users WHERE email = %s
    """, (email,))
    
    row = cursor.fetchone()
    cursor.close()

    db_config.release_connection(conn)
    
    if row:
        return {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "password_hash": row["password_hash"],
            "created_at": row["created_at"]
        }
    return None


def get_user_by_username_or_email(identifier: str) -> Optional[Dict]:
    """Retrieve a user by username or email."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)
    
    cursor.execute("""
        SELECT id, username, email, password_hash, created_at
        FROM users WHERE username = %s OR email = %s
    """, (identifier, identifier))
    
    row = cursor.fetchone()
    cursor.close()

    db_config.release_connection(conn)
    
    if row:
        return {
            "id": row["id"],
            "username": row["username"],
            "email": row["email"],
            "password_hash": row["password_hash"],
            "created_at": row["created_at"]
        }
    return None


def get_user_by_email(email: str) -> Optional[Dict]:
    """Retrieve a user by email."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)
    
    cursor.execute("""
        SELECT id, username, email, password_hash, name, created_at
        FROM users WHERE email = %s
    """, (email,))
    
    row = cursor.fetchone()
    cursor.close()

    db_config.release_connection(conn)
    
    if row:
        return {
            "id": row["id"],
            "username": row["username"] if "username" in row.keys() else None,
            "email": row["email"],
            "password_hash": row["password_hash"],
            "name": row["name"],
            "created_at": row["created_at"]
        }
    return None


# ===== CLIENT DPR FUNCTIONS =====

def create_client_dpr(client_id: int, project_name: str, filename: str, original_filename: str) -> int:
    """Create a new client DPR record and return its ID."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    
    timestamp = datetime.now()
    status = "Review"
    
    cursor.execute("""
        INSERT INTO client_dprs (client_id, project_name, dpr_filename, original_filename, status, created_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (client_id, project_name, filename, original_filename, status, timestamp))
    
    dpr_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    
    print(f"✓ Client DPR created with ID: {dpr_id} for client {client_id}")
    return dpr_id


def get_client_dprs(client_id: int) -> List[Dict]:
    """Retrieve all DPRs for a specific client."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)
    
    cursor.execute("""
        SELECT id, client_id, project_name, dpr_filename, original_filename, status, created_at
        FROM client_dprs
        WHERE client_id = %s
        ORDER BY created_at DESC
    """, (client_id,))
    
    rows = cursor.fetchall()
    cursor.close()

    db_config.release_connection(conn)
    
    return [dict(row) for row in rows]


def get_client_dpr(dpr_id: int) -> Optional[Dict]:
    """Retrieve a specific client DPR by ID."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)

    cursor.execute("""
        SELECT id, client_id, project_name, dpr_filename, original_filename, status, created_at
        FROM client_dprs
        WHERE id = %s
    """, (dpr_id,))

    row = cursor.fetchone()
    cursor.close()

    db_config.release_connection(conn)

    if row:
        return dict(row)
    return None


# ===== PRAHARI BIDDER FUNCTIONS =====

def create_bidder(project_id: int, company_name: str, gstin: str = None,
                  pan: str = None, contact_email: str = None) -> int:
    """Register a new bidder for a tender and return the bidder ID."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)

    cursor.execute("""
        INSERT INTO bidders (project_id, company_name, gstin, pan, contact_email)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (project_id, company_name, gstin, pan, contact_email))

    bidder_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)

    print(f"✓ Bidder created with ID: {bidder_id} for project {project_id}")
    return bidder_id


def get_bidders_by_project(project_id: int) -> List[Dict]:
    """Retrieve all bidders registered for a tender."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)

    cursor.execute("""
        SELECT id, project_id, company_name, gstin, pan, contact_email, status, created_at
        FROM bidders
        WHERE project_id = %s
        ORDER BY created_at ASC
    """, (project_id,))

    rows = cursor.fetchall()
    cursor.close()
    db_config.release_connection(conn)

    return [dict(row) for row in rows]


def get_bidder(bidder_id: int) -> Optional[Dict]:
    """Retrieve a single bidder by ID."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)

    cursor.execute("""
        SELECT id, project_id, company_name, gstin, pan, contact_email, status, created_at
        FROM bidders WHERE id = %s
    """, (bidder_id,))

    row = cursor.fetchone()
    cursor.close()
    db_config.release_connection(conn)

    return dict(row) if row else None


def update_bidder_status(bidder_id: int, status: str) -> None:
    """Update the evaluation status of a bidder."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)

    cursor.execute("""
        UPDATE bidders SET status = %s WHERE id = %s
    """, (status, bidder_id))

    conn.commit()
    cursor.close()
    db_config.release_connection(conn)


# ===== PRAHARI BIDDER DOCUMENT FUNCTIONS =====

def create_bidder_document(bidder_id: int, document_type: str, original_filename: str,
                           uploaded_file_ref: str = None, cloudinary_url: str = None,
                           cloudinary_public_id: str = None) -> int:
    """Register an uploaded document for a bidder and return the document ID."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)

    cursor.execute("""
        INSERT INTO bidder_documents
            (bidder_id, document_type, original_filename, uploaded_file_ref,
             cloudinary_url, cloudinary_public_id)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
    """, (bidder_id, document_type, original_filename, uploaded_file_ref,
          cloudinary_url, cloudinary_public_id))

    doc_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)

    print(f"✓ Bidder document created with ID: {doc_id} for bidder {bidder_id}")
    return doc_id


def update_bidder_document_authenticity(doc_id: int, language_detected: str,
                                        authenticity_score: float,
                                        tamper_risk_level: str,
                                        metadata_flags: dict = None) -> None:
    """Store authenticity scoring results for a bidder document."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)

    flags_json = json.dumps(metadata_flags) if metadata_flags else None

    cursor.execute("""
        UPDATE bidder_documents
        SET language_detected = %s,
            authenticity_score = %s,
            tamper_risk_level = %s,
            metadata_flags = %s
        WHERE id = %s
    """, (language_detected, authenticity_score, tamper_risk_level, flags_json, doc_id))

    conn.commit()
    cursor.close()
    db_config.release_connection(conn)


def get_bidder_documents(bidder_id: int) -> List[Dict]:
    """Retrieve all uploaded documents for a bidder."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)

    cursor.execute("""
        SELECT id, bidder_id, document_type, original_filename, uploaded_file_ref,
               cloudinary_url, cloudinary_public_id, language_detected,
               authenticity_score, tamper_risk_level, metadata_flags, upload_ts
        FROM bidder_documents
        WHERE bidder_id = %s
        ORDER BY upload_ts ASC
    """, (bidder_id,))

    rows = cursor.fetchall()
    cursor.close()
    db_config.release_connection(conn)

    docs = []
    for row in rows:
        doc = dict(row)
        if doc.get('metadata_flags') and isinstance(doc['metadata_flags'], str):
            try:
                doc['metadata_flags'] = json.loads(doc['metadata_flags'])
            except Exception:
                doc['metadata_flags'] = None
        docs.append(doc)
    return docs


# ===== PRAHARI VERDICT FUNCTIONS =====

def upsert_verdict(project_id: int, bidder_id: int, criterion_id: str,
                   verdict: str, confidence_score: float,
                   extracted_value_text: str = None, threshold_value: int = None,
                   evidence_doc_id: int = None, evidence_quote: str = None,
                   evidence_page: int = None, reasoning: str = None,
                   tamper_risk_score: float = None) -> int:
    """Insert or update a verdict for a (bidder, criterion) pair. Returns verdict row ID."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)

    cursor.execute("""
        INSERT INTO verdicts
            (project_id, bidder_id, criterion_id, verdict, confidence_score,
             extracted_value_text, threshold_value, evidence_doc_id,
             evidence_quote, evidence_page, reasoning, tamper_risk_score)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (bidder_id, criterion_id) DO UPDATE SET
            verdict = EXCLUDED.verdict,
            confidence_score = EXCLUDED.confidence_score,
            extracted_value_text = EXCLUDED.extracted_value_text,
            threshold_value = EXCLUDED.threshold_value,
            evidence_doc_id = EXCLUDED.evidence_doc_id,
            evidence_quote = EXCLUDED.evidence_quote,
            evidence_page = EXCLUDED.evidence_page,
            reasoning = EXCLUDED.reasoning,
            tamper_risk_score = EXCLUDED.tamper_risk_score
        RETURNING id
    """, (project_id, bidder_id, criterion_id, verdict, confidence_score,
          extracted_value_text, threshold_value, evidence_doc_id,
          evidence_quote, evidence_page, reasoning, tamper_risk_score))

    verdict_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)

    return verdict_id


def apply_human_override(verdict_id: int, override_verdict: str,
                         justification: str, officer_id: int) -> None:
    """Record a procurement officer's manual override on a verdict."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)

    cursor.execute("""
        UPDATE verdicts SET
            human_override = TRUE,
            override_verdict = %s,
            override_justification = %s,
            override_by_officer_id = %s,
            override_at = NOW()
        WHERE id = %s
    """, (override_verdict, justification, officer_id, verdict_id))

    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    print(f"✓ Human override applied to verdict {verdict_id} by officer {officer_id}")


def get_verdicts_matrix(project_id: int) -> List[Dict]:
    """
    Return all verdicts for a project as a flat list.
    Frontend pivots this into a bidder × criterion heatmap.
    """
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)

    cursor.execute("""
        SELECT v.id, v.bidder_id, b.company_name, v.criterion_id,
               v.verdict, v.confidence_score, v.extracted_value_text,
               v.threshold_value, v.evidence_doc_id, v.evidence_quote,
               v.evidence_page, v.reasoning, v.tamper_risk_score,
               v.human_override, v.override_verdict, v.override_justification,
               v.override_by_officer_id, v.override_at, v.created_at
        FROM verdicts v
        JOIN bidders b ON v.bidder_id = b.id
        WHERE v.project_id = %s
        ORDER BY b.company_name, v.criterion_id
    """, (project_id,))

    rows = cursor.fetchall()
    cursor.close()
    db_config.release_connection(conn)

    return [dict(row) for row in rows]


def get_verdict(bidder_id: int, criterion_id: str) -> Optional[Dict]:
    """Retrieve the current verdict for a specific (bidder, criterion) pair."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)

    cursor.execute("""
        SELECT * FROM verdicts WHERE bidder_id = %s AND criterion_id = %s
    """, (bidder_id, criterion_id))

    row = cursor.fetchone()
    cursor.close()
    db_config.release_connection(conn)

    return dict(row) if row else None


# ===== PRAHARI COLLUSION ALERT FUNCTIONS =====

def insert_collusion_alert(project_id: int, alert_type: str, bidder_ids: List[int],
                           description: str, confidence_score: float) -> int:
    """Insert a new collusion / integrity alert and return its ID."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)

    cursor.execute("""
        INSERT INTO collusion_alerts
            (project_id, alert_type, bidder_ids, description, confidence_score)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    """, (project_id, alert_type, bidder_ids, description, confidence_score))

    alert_id = cursor.fetchone()[0]
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)

    print(f"✓ Collusion alert {alert_id} created for project {project_id} ({alert_type})")
    return alert_id


def resolve_collusion_alert(alert_id: int, disposition: str,
                            notes: str, officer_id: int) -> None:
    """Record an officer's disposition on a collusion alert."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)

    cursor.execute("""
        UPDATE collusion_alerts SET
            officer_disposition = %s,
            disposition_notes = %s,
            disposition_by = %s,
            disposition_at = NOW()
        WHERE id = %s
    """, (disposition, notes, officer_id, alert_id))

    conn.commit()
    cursor.close()
    db_config.release_connection(conn)


def get_collusion_alerts(project_id: int) -> List[Dict]:
    """Retrieve all collusion alerts for a project."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)

    cursor.execute("""
        SELECT id, project_id, alert_type, bidder_ids, description,
               confidence_score, officer_disposition, disposition_notes,
               disposition_by, disposition_at, created_at
        FROM collusion_alerts
        WHERE project_id = %s
        ORDER BY created_at DESC
    """, (project_id,))

    rows = cursor.fetchall()
    cursor.close()
    db_config.release_connection(conn)

    return [dict(row) for row in rows]


# ===== PRAHARI AUDIT EVENT FUNCTIONS =====

def insert_audit_event(event_type: str, payload: dict,
                       project_id: int = None, bidder_id: int = None,
                       criterion_id: str = None, model_version: str = None,
                       confidence_score: float = None, language_detected: str = None,
                       dp_epsilon: float = None, officer_id: int = None) -> str:
    """
    Append an immutable audit event. payload_hash is SHA-256 of the JSON payload.
    Returns the UUID event_id.
    """
    import hashlib

    payload_str = json.dumps(payload, sort_keys=True, default=str)
    payload_hash = hashlib.sha256(payload_str.encode()).hexdigest()

    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)

    cursor.execute("""
        INSERT INTO audit_events
            (event_type, project_id, bidder_id, criterion_id, payload_hash,
             model_version, confidence_score, language_detected, dp_epsilon, officer_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING event_id
    """, (event_type, project_id, bidder_id, criterion_id, payload_hash,
          model_version, confidence_score, language_detected, dp_epsilon, officer_id))

    event_id = str(cursor.fetchone()[0])
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)

    return event_id


def get_audit_trail(project_id: int) -> List[Dict]:
    """Retrieve the full audit trail for a project, ordered chronologically."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)

    cursor.execute("""
        SELECT event_id, event_type, project_id, bidder_id, criterion_id,
               payload_hash, model_version, confidence_score, language_detected,
               dp_epsilon, officer_id, created_at
        FROM audit_events
        WHERE project_id = %s
        ORDER BY created_at ASC
    """, (project_id,))

    rows = cursor.fetchall()
    cursor.close()
    db_config.release_connection(conn)

    return [dict(row) for row in rows]


# ── QA session persistence ──────────────────────────────────────────────────

def _ensure_qa_sessions_table(cursor) -> None:
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS qa_sessions (
            id         SERIAL PRIMARY KEY,
            project_id INTEGER NOT NULL,
            role       TEXT    NOT NULL,
            content    TEXT    NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)


def get_qa_history(project_id: int) -> List[Dict]:
    """Return ordered [{role, content}] rows for a project's QA session."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=True)
    _ensure_qa_sessions_table(cursor)
    cursor.execute(
        "SELECT role, content FROM qa_sessions WHERE project_id = %s ORDER BY created_at ASC",
        (project_id,)
    )
    rows = cursor.fetchall()
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    return [dict(r) for r in rows]


def append_qa_messages(project_id: int, user_msg: str, model_msg: str) -> None:
    """Persist a user→model exchange to the QA session table."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    _ensure_qa_sessions_table(cursor)
    cursor.execute(
        "INSERT INTO qa_sessions (project_id, role, content) VALUES (%s, %s, %s)",
        (project_id, 'user', user_msg)
    )
    cursor.execute(
        "INSERT INTO qa_sessions (project_id, role, content) VALUES (%s, %s, %s)",
        (project_id, 'model', model_msg)
    )
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    print(f"✓ QA exchange persisted for project {project_id}")


def clear_qa_history(project_id: int) -> None:
    """Delete all QA session rows for a project."""
    conn = db_config.get_connection()
    cursor = db_config.get_cursor(conn, dict_cursor=False)
    _ensure_qa_sessions_table(cursor)
    cursor.execute("DELETE FROM qa_sessions WHERE project_id = %s", (project_id,))
    conn.commit()
    cursor.close()
    db_config.release_connection(conn)
    print(f"✓ QA history cleared for project {project_id}")

