"""
Database client module for MCP Server.

This module provides functions to query the DPR Analyzer via HTTP API.
All operations go through the backend API for consistency.
"""

import httpx
import sys
from typing import List, Dict, Optional
from config import get_backend_url


def get_projects() -> List[Dict]:
    """
    Retrieve all projects with their DPR counts via backend API.
    
    Returns:
        List[Dict]: List of project dictionaries with metadata
        Returns empty list on error.
    """
    try:
        backend_url = get_backend_url()
        
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{backend_url}/projects")
            response.raise_for_status()
            
            data = response.json()
            projects = data.get("projects", [])
            
            print(f"✓ Retrieved {len(projects)} projects from backend API", file=sys.stderr)
            return projects
        
    except Exception as e:
        print(f"✗ Error retrieving projects: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return []


def get_project_with_dprs(project_id: int) -> Optional[Dict]:
    """
    Get detailed information about a specific project including all DPRs via backend API.
    
    Args:
        project_id: The ID of the project to retrieve
        
    Returns:
        Dict: Project details with nested 'dprs' list containing all DPRs
        None: If project not found or error occurs
    """
    try:
        backend_url = get_backend_url()
        
        with httpx.Client(timeout=30.0) as client:
            # Get project details
            project_response = client.get(f"{backend_url}/projects/{project_id}")
            
            if project_response.status_code == 404:
                print(f"⚠ Project {project_id} not found", file=sys.stderr)
                return None
            
            project_response.raise_for_status()
            project = project_response.json()
            
            # Get project DPRs
            dprs_response = client.get(f"{backend_url}/projects/{project_id}/dprs")
            dprs_response.raise_for_status()
            
            dprs_data = dprs_response.json()
            dprs = dprs_data.get("dprs", [])
            
            # Add DPRs to project
            project['dprs'] = dprs
            
            print(f"✓ Retrieved project {project_id} with {len(dprs)} DPRs from backend API", file=sys.stderr)
            return project
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            print(f"⚠ Project {project_id} not found", file=sys.stderr)
            return None
        print(f"✗ HTTP error retrieving project {project_id}: {str(e)}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"✗ Error retrieving project {project_id}: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None


def get_all_dprs() -> List[Dict]:
    """
    Retrieve all DPRs from all projects via backend API.
    
    Returns:
        List[Dict]: List of all DPR dictionaries with metadata
        Returns empty list on error.
    """
    try:
        backend_url = get_backend_url()
        
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{backend_url}/dprs")
            response.raise_for_status()
            
            data = response.json()
            dprs = data.get("dprs", [])
            
            print(f"✓ Retrieved {len(dprs)} DPRs from backend API", file=sys.stderr)
            return dprs
        
    except Exception as e:
        print(f"✗ Error retrieving DPRs: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return []


def get_dpr_analysis(dpr_id: int) -> Optional[Dict]:
    """
    Retrieve the full analysis for a specific DPR via backend API.
    
    Args:
        dpr_id: The ID of the DPR to retrieve
        
    Returns:
        Dict: DPR details with summary_json (the AI analysis)
        None: If DPR not found or error occurs
    """
    try:
        backend_url = get_backend_url()
        
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{backend_url}/dpr/{dpr_id}")
            
            if response.status_code == 404:
                print(f"⚠ DPR {dpr_id} not found", file=sys.stderr)
                return None
            
            response.raise_for_status()
            dpr = response.json()
            
            print(f"✓ Retrieved DPR {dpr_id} analysis from backend API", file=sys.stderr)
            return dpr
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            print(f"⚠ DPR {dpr_id} not found", file=sys.stderr)
            return None
        print(f"✗ HTTP error retrieving DPR {dpr_id}: {str(e)}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"✗ Error retrieving DPR {dpr_id}: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None


def get_project_comparison(project_id: int) -> Optional[Dict]:
    """
    Retrieve saved comparison result for a project via backend API.
    
    Args:
        project_id: The ID of the project
        
    Returns:
        Dict: Comparison result with 'comparison' and 'generated_at' fields
        None: If no comparison exists or error occurs
    """
    try:
        backend_url = get_backend_url()
        
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{backend_url}/projects/{project_id}/comparison")
            
            if response.status_code == 404:
                print(f"⚠ No comparison found for project {project_id}", file=sys.stderr)
                return None
            
            response.raise_for_status()
            comparison = response.json()
            
            print(f"✓ Retrieved comparison for project {project_id} from backend API", file=sys.stderr)
            return comparison
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        print(f"✗ HTTP error retrieving comparison for project {project_id}: {str(e)}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"✗ Error retrieving comparison for project {project_id}: {str(e)}", file=sys.stderr)
        return None


def get_compliance_weights(project_id: int) -> Optional[Dict]:
    """
    Retrieve compliance weights for a project via backend API.
    
    Args:
        project_id: The ID of the project
        
    Returns:
        Dict: Compliance weights with 'weights' and 'isCustom' fields
        None: If error occurs
    """
    try:
        backend_url = get_backend_url()
        
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{backend_url}/projects/{project_id}/compliance-weights")
            
            if response.status_code == 404:
                print(f"⚠ Project {project_id} not found", file=sys.stderr)
                return None
            
            response.raise_for_status()
            weights = response.json()
            
            print(f"✓ Retrieved compliance weights for project {project_id}", file=sys.stderr)
            return weights
        
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return None
        print(f"✗ HTTP error retrieving compliance weights: {str(e)}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"✗ Error retrieving compliance weights: {str(e)}", file=sys.stderr)
        return None


def test_connection() -> bool:
    """
    Test backend API connection.
    
    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        backend_url = get_backend_url()
        
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{backend_url}/projects")
            response.raise_for_status()
            
            data = response.json()
            count = data.get("count", 0)
            
            print(f"✓ Backend API connection successful. Found {count} projects.", file=sys.stderr)
            return True
    except Exception as e:
        print(f"✗ Backend API connection failed: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return False


def update_dpr_status(dpr_id: int, status: str) -> Optional[Dict]:
    """
    Update the status of a DPR (admin action).
    
    Args:
        dpr_id: The ID of the DPR to update
        status: New status (pending, accepted, rejected, completed, analyzing)
        
    Returns:
        Dict: Success response with message
        None: If error occurs
    """
    try:
        backend_url = get_backend_url()
        
        with httpx.Client(timeout=30.0) as client:
            # Send as form data
            response = client.put(
                f"{backend_url}/dprs/{dpr_id}/status",
                data={"status": status}
            )
            
            if response.status_code == 404:
                print(f"⚠ DPR {dpr_id} not found", file=sys.stderr)
                return None
            
            response.raise_for_status()
            result = response.json()
            
            print(f"✓ Updated DPR {dpr_id} status to '{status}'", file=sys.stderr)
            return result
        
    except Exception as e:
        print(f"✗ Error updating DPR status: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None


def send_dpr_feedback(dpr_id: int, feedback: str) -> Optional[Dict]:
    """
    Send feedback to a DPR (admin action).
    
    Args:
        dpr_id: The ID of the DPR to send feedback to
        feedback: Feedback message/text
        
    Returns:
        Dict: Success response with message
        None: If error occurs
    """
    try:
        backend_url = get_backend_url()
        
        with httpx.Client(timeout=30.0) as client:
            # Send as form data
            response = client.put(
                f"{backend_url}/dprs/{dpr_id}/feedback",
                data={"feedback": feedback}
            )
            
            if response.status_code == 404:
                print(f"⚠ DPR {dpr_id} not found", file=sys.stderr)
                return None
            
            response.raise_for_status()
            result = response.json()
            
            print(f"✓ Sent feedback to DPR {dpr_id}", file=sys.stderr)
            return result
        
    except Exception as e:
        print(f"✗ Error sending feedback: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None


def trigger_project_comparison(project_id: int) -> Optional[Dict]:
    """
    Trigger AI comparison of all DPRs in a project (admin action).
    
    Args:
        project_id: The ID of the project to compare DPRs for
        
    Returns:
        Dict: Comparison result with recommendations
        None: If error occurs
    """
    try:
        backend_url = get_backend_url()
        
        with httpx.Client(timeout=120.0) as client:  # Longer timeout for AI operation
            response = client.post(f"{backend_url}/projects/{project_id}/compare-all")
            
            if response.status_code == 404:
                print(f"⚠ Project {project_id} not found or no DPRs", file=sys.stderr)
                return None
            
            response.raise_for_status()
            result = response.json()
            
            print(f"✓ Triggered comparison for project {project_id}", file=sys.stderr)
            return result
        
    except Exception as e:
        print(f"✗ Error triggering comparison: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None


def analyze_dpr(dpr_id: int) -> Optional[Dict]:
    """
    Trigger AI analysis on an unanalyzed DPR (admin action).
    
    Args:
        dpr_id: The ID of the DPR to analyze
        
    Returns:
        Dict: Analysis result
        None: If error occurs
    """
    try:
        backend_url = get_backend_url()
        
        with httpx.Client(timeout=180.0) as client:  # Long timeout for AI operation
            response = client.post(f"{backend_url}/dprs/{dpr_id}/analyze")
            
            if response.status_code == 404:
                print(f"⚠ DPR {dpr_id} not found", file=sys.stderr)
                return None
            
            response.raise_for_status()
            result = response.json()
            
            print(f"✓ Triggered analysis for DPR {dpr_id}", file=sys.stderr)
            return result
        
    except Exception as e:
        print(f"✗ Error analyzing DPR: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None


def create_project(name: str, state: str, scheme: str, sector: str) -> Optional[Dict]:
    """
    Create a new project (admin action).
    
    Args:
        name: Project name
        state: State/location
        scheme: Scheme (e.g., PMGSY)
        sector: Sector (e.g., Infrastructure)
        
    Returns:
        Dict: Created project info with id
        None: If error occurs
    """
    try:
        backend_url = get_backend_url()
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                f"{backend_url}/projects",
                json={
                    "name": name,
                    "state": state,
                    "scheme": scheme,
                    "sector": sector
                }
            )
            
            response.raise_for_status()
            result = response.json()
            
            print(f"✓ Created project '{name}' with ID {result.get('id')}", file=sys.stderr)
            return result
        
    except Exception as e:
        print(f"✗ Error creating project: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None


def delete_project(project_id: int) -> Optional[Dict]:
    """
    Delete a project and all its DPRs (admin action).
    
    Args:
        project_id: The ID of the project to delete
        
    Returns:
        Dict: Success response
        None: If error occurs
    """
    try:
        backend_url = get_backend_url()
        
        with httpx.Client(timeout=30.0) as client:
            response = client.delete(f"{backend_url}/projects/{project_id}")
            
            if response.status_code == 404:
                print(f"⚠ Project {project_id} not found", file=sys.stderr)
                return None
            
            response.raise_for_status()
            result = response.json()
            
            print(f"✓ Deleted project {project_id}", file=sys.stderr)
            return result
        
    except Exception as e:
        print(f"✗ Error deleting project: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None


def delete_dpr(dpr_id: int) -> Optional[Dict]:
    """
    Delete a DPR permanently (admin action).
    
    Args:
        dpr_id: The ID of the DPR to delete
        
    Returns:
        Dict: Success response
        None: If error occurs
    """
    try:
        backend_url = get_backend_url()
        
        with httpx.Client(timeout=30.0) as client:
            response = client.delete(f"{backend_url}/dpr/{dpr_id}")
            
            if response.status_code == 404:
                print(f"⚠ DPR {dpr_id} not found", file=sys.stderr)
                return None
            
            response.raise_for_status()
            result = response.json()
            
            print(f"✓ Deleted DPR {dpr_id}", file=sys.stderr)
            return result
        
    except Exception as e:
        print(f"✗ Error deleting DPR: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None


def trigger_dpr_analysis(dpr_id: int) -> Optional[Dict]:
    """
    Trigger AI analysis on a pending DPR (admin action).
    
    Args:
        dpr_id: The ID of the DPR to analyze
        
    Returns:
        Dict: Analysis result with summary
        None: If error occurs
    """
    try:
        backend_url = get_backend_url()
        
        with httpx.Client(timeout=180.0) as client:  # Long timeout for AI
            response = client.post(f"{backend_url}/dprs/{dpr_id}/analyze")
            
            if response.status_code == 404:
                print(f"⚠ DPR {dpr_id} not found", file=sys.stderr)
                return None
            
            response.raise_for_status()
            result = response.json()
            
            print(f"✓ Analysis triggered for DPR {dpr_id}", file=sys.stderr)
            return result
        
    except Exception as e:
        print(f"✗ Error triggering analysis: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        return None


def approve_and_reject_others(project_id: int, approved_dpr_id: int, feedback: Optional[str] = None) -> Dict:
    """
    Approve one DPR and reject all others in a project (admin action).
    
    Args:
        project_id: The project ID
        approved_dpr_id: The DPR ID to approve
        feedback: Optional feedback for rejected DPRs
        
    Returns:
        Dict: Result with approved_id and rejected_ids
    """
    results = {
        "success": False,
        "approved_id": None,
        "rejected_ids": [],
        "errors": []
    }
    
    try:
        backend_url = get_backend_url()
        
        # Get all DPRs in the project
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{backend_url}/projects/{project_id}/dprs")
            response.raise_for_status()
            dprs_data = response.json()
            dprs = dprs_data.get("dprs", [])
        
        if not dprs:
            results["errors"].append(f"No DPRs found in project {project_id}")
            return results
        
        # Approve the selected DPR
        approve_result = update_dpr_status(approved_dpr_id, "accepted")
        if approve_result:
            results["approved_id"] = approved_dpr_id
        else:
            results["errors"].append(f"Failed to approve DPR {approved_dpr_id}")
            return results
        
        # Reject all others
        for dpr in dprs:
            dpr_id = dpr.get("id")
            if dpr_id != approved_dpr_id:
                reject_result = update_dpr_status(dpr_id, "rejected")
                if reject_result:
                    results["rejected_ids"].append(dpr_id)
                    # Send feedback if provided
                    if feedback:
                        send_dpr_feedback(dpr_id, feedback)
                else:
                    results["errors"].append(f"Failed to reject DPR {dpr_id}")
        
        results["success"] = True
        print(f"✓ Approved DPR {approved_dpr_id}, rejected {len(results['rejected_ids'])} others", file=sys.stderr)
        return results
        
    except Exception as e:
        results["errors"].append(str(e))
        print(f"✗ Error in approve_and_reject_others: {str(e)}", file=sys.stderr)
        return results


def batch_approve_dprs(dpr_ids: List[int]) -> Dict:
    """
    Approve multiple DPRs at once (admin action).
    
    Args:
        dpr_ids: List of DPR IDs to approve
        
    Returns:
        Dict: Result with approved_ids and failed_ids
    """
    results = {
        "success": False,
        "approved_ids": [],
        "failed_ids": []
    }
    
    for dpr_id in dpr_ids:
        result = update_dpr_status(dpr_id, "accepted")
        if result:
            results["approved_ids"].append(dpr_id)
        else:
            results["failed_ids"].append(dpr_id)
    
    results["success"] = len(results["failed_ids"]) == 0
    print(f"✓ Batch approved {len(results['approved_ids'])} DPRs, {len(results['failed_ids'])} failed", file=sys.stderr)
    return results


def send_bulk_feedback(dpr_ids: List[int], feedback: str) -> Dict:
    """
    Send the same feedback to multiple DPRs (admin action).
    
    Args:
        dpr_ids: List of DPR IDs to send feedback to
        feedback: Feedback message
        
    Returns:
        Dict: Result with sent_ids and failed_ids
    """
    results = {
        "success": False,
        "sent_ids": [],
        "failed_ids": []
    }
    
    for dpr_id in dpr_ids:
        result = send_dpr_feedback(dpr_id, feedback)
        if result:
            results["sent_ids"].append(dpr_id)
        else:
            results["failed_ids"].append(dpr_id)
    
    results["success"] = len(results["failed_ids"]) == 0
    print(f"✓ Sent feedback to {len(results['sent_ids'])} DPRs, {len(results['failed_ids'])} failed", file=sys.stderr)
    return results


if __name__ == "__main__":
    # Test the backend API connection and functions
    print("Testing backend API connection...")
    if test_connection():
        print("\nTesting get_projects()...")
        projects = get_projects()
        print(f"Found {len(projects)} projects")
        
        if projects:
            print("\nTesting get_project_with_dprs()...")
            project_id = projects[0]['id']
            project = get_project_with_dprs(project_id)
            if project:
                print(f"Project: {project['name']}")
                print(f"DPRs: {len(project['dprs'])}")
                if project['dprs']:
                    first_dpr = project['dprs'][0]
                    print(f"First DPR: {first_dpr.get('original_filename', 'N/A')}")
                    print(f"Cloudinary URL: {first_dpr.get('cloudinary_url', 'N/A')}")
                    
                    # Test get_dpr_analysis
                    print(f"\nTesting get_dpr_analysis({first_dpr['id']})...")
                    dpr_detail = get_dpr_analysis(first_dpr['id'])
                    if dpr_detail:
                        print(f"DPR ID: {dpr_detail.get('id')}")
                        print(f"Has summary_json: {dpr_detail.get('summary_json') is not None}")
        
        print("\nTesting get_all_dprs()...")
        all_dprs = get_all_dprs()
        print(f"Found {len(all_dprs)} total DPRs across all projects")
