"""
MCP Server for DPR Analyzer Project Management.

This server exposes project management functions as MCP tools for AI models.
It connects to the backend API via HTTP for all data access.
"""

import asyncio
import json
import sys
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    INVALID_PARAMS,
    INTERNAL_ERROR,
)
import mcp.types as types

import db_client
from config import get_backend_url


# Create server instance
server = Server("dpr-analyzer-mcp")


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    """
    List available MCP tools.
    
    Returns:
        list[Tool]: List of available tools with their schemas
    """
    return [
        Tool(
            name="list_projects",
            description="Get a list of all projects with their metadata including state, scheme, sector, and DPR counts. Use this to see what projects exist in the system.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_project_details",
            description="Get detailed information about a specific project including all DPRs and their analyzed JSON data (summary, financial analysis, risks, compliance scores). This provides comprehensive project details along with all associated DPR documents.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project to retrieve"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="list_all_dprs",
            description="Get a list of ALL DPRs across all projects with their metadata including filename, upload date, status (pending/analyzing/completed), and project association. Use this to get an overview of all documents in the system.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="get_dpr_analysis",
            description="Get the full AI-generated analysis for a specific DPR document. Returns the complete summary_json including project overview, financial analysis, timeline, risks, compliance scores, and sectional breakdowns. Use this when you need detailed analysis of a specific document.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dpr_id": {
                        "type": "integer",
                        "description": "The ID of the DPR to retrieve analysis for"
                    }
                },
                "required": ["dpr_id"]
            }
        ),
        Tool(
            name="get_project_comparison",
            description="Get the saved comparison analysis for a project that has multiple DPRs. Returns AI-generated comparison of all DPRs including rankings and recommendations. Only works if a comparison has been previously generated.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project to get comparison for"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="get_compliance_info",
            description="Get compliance scoring weights and settings for a project. Returns the weight distribution used for calculating compliance scores (e.g., financial weight, technical weight, environmental weight).",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project to get compliance info for"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="approve_dpr",
            description="Approve a DPR by setting its status to 'accepted' (ADMIN ACTION). Use this when a DPR meets all requirements and should be marked as approved. This is a write operation that changes the database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dpr_id": {
                        "type": "integer",
                        "description": "The ID of the DPR to approve"
                    }
                },
                "required": ["dpr_id"]
            }
        ),
        Tool(
            name="reject_dpr",
            description="Reject a DPR by setting its status to 'rejected' (ADMIN ACTION). Use this when a DPR does not meet requirements. Optionally send feedback explaining why. This is a write operation that changes the database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dpr_id": {
                        "type": "integer",
                        "description": "The ID of the DPR to reject"
                    },
                    "feedback": {
                        "type": "string",
                        "description": "Optional feedback message explaining the rejection reason"
                    }
                },
                "required": ["dpr_id"]
            }
        ),
        Tool(
            name="send_feedback_to_dpr",
            description="Send feedback/review comments to a DPR (ADMIN ACTION). This updates the admin_feedback field for the DPR. Useful for providing detailed review comments to clients. This is a write operation that changes the database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dpr_id": {
                        "type": "integer",
                        "description": "The ID of the DPR to send feedback to"
                    },
                    "feedback": {
                        "type": "string",
                        "description": "The feedback message/review comments"
                    }
                },
                "required": ["dpr_id", "feedback"]
            }
        ),
        Tool(
            name="trigger_comparison",
            description="Trigger AI-powered comparison of all DPRs in a project (ADMIN ACTION). This uses Gemini AI to analyze and compare all DPRs, providing rankings and recommendations. Requires at least 2 analyzed DPRs. This may take 30-60 seconds. This is a write operation that saves results to database.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project to compare DPRs for"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="create_project",
            description="Create a new project (ADMIN ACTION). Creates a project with the specified name, state, scheme, and sector. Returns the new project ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Project name"
                    },
                    "state": {
                        "type": "string",
                        "description": "State/location (e.g., Maharashtra)"
                    },
                    "scheme": {
                        "type": "string",
                        "description": "Scheme name (e.g., PMGSY, NABARD)"
                    },
                    "sector": {
                        "type": "string",
                        "description": "Sector (e.g., Infrastructure, Agriculture)"
                    }
                },
                "required": ["name", "state", "scheme", "sector"]
            }
        ),
        Tool(
            name="delete_project",
            description="Delete a project and all its DPRs (ADMIN ACTION). WARNING: This is irreversible and will delete ALL DPRs in the project.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The ID of the project to delete"
                    }
                },
                "required": ["project_id"]
            }
        ),
        Tool(
            name="delete_dpr",
            description="Permanently delete a DPR (ADMIN ACTION). WARNING: This is irreversible and will delete the DPR and its associated files.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dpr_id": {
                        "type": "integer",
                        "description": "The ID of the DPR to delete"
                    }
                },
                "required": ["dpr_id"]
            }
        ),
        Tool(
            name="trigger_dpr_analysis",
            description="Trigger AI analysis on a pending/unanalyzed DPR (ADMIN ACTION). Use this to retry failed analysis or analyze newly uploaded DPRs. This may take 1-2 minutes.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dpr_id": {
                        "type": "integer",
                        "description": "The ID of the DPR to analyze"
                    }
                },
                "required": ["dpr_id"]
            }
        ),
        Tool(
            name="approve_and_reject_others",
            description="Approve one DPR and automatically reject all others in the same project (ADMIN ACTION). This is the workflow automation for selecting the winning DPR. Optionally send feedback to rejected DPRs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "project_id": {
                        "type": "integer",
                        "description": "The project ID"
                    },
                    "approved_dpr_id": {
                        "type": "integer",
                        "description": "The DPR ID to approve"
                    },
                    "feedback": {
                        "type": "string",
                        "description": "Optional feedback message for rejected DPRs"
                    }
                },
                "required": ["project_id", "approved_dpr_id"]
            }
        ),
        Tool(
            name="batch_approve_dprs",
            description="Approve multiple DPRs at once (ADMIN ACTION). Sets status to 'accepted' for all specified DPRs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dpr_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of DPR IDs to approve"
                    }
                },
                "required": ["dpr_ids"]
            }
        ),
        Tool(
            name="send_bulk_feedback",
            description="Send the same feedback message to multiple DPRs at once (ADMIN ACTION). Useful for common review comments.",
            inputSchema={
                "type": "object",
                "properties": {
                    "dpr_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of DPR IDs to send feedback to"
                    },
                    "feedback": {
                        "type": "string",
                        "description": "Feedback message to send"
                    }
                },
                "required": ["dpr_ids", "feedback"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
    """
    Handle tool calls from MCP clients.
    
    Args:
        name: Name of the tool to call
        arguments: Tool arguments
        
    Returns:
        list[TextContent]: Tool response
    """
    try:
        if name == "list_projects":
            # Get all projects
            projects = db_client.get_projects()
            
            if projects is None:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Failed to retrieve projects from backend",
                            "projects": []
                        }, indent=2)
                    )
                ]
            
            # Enhance with summary info
            summary = []
            for p in projects:
                summary.append({
                    "id": p.get("id"),
                    "name": p.get("name"),
                    "state": p.get("state"),
                    "scheme": p.get("scheme"),
                    "sector": p.get("sector"),
                    "created_at": p.get("created_at")
                })
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "count": len(projects),
                        "projects": summary
                    }, indent=2, default=str)
                )
            ]
        
        elif name == "get_project_details":
            # Validate arguments
            if "project_id" not in arguments:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Missing required parameter: project_id"
                        }, indent=2)
                    )
                ]
            
            project_id = arguments["project_id"]
            
            # Validate project_id is an integer
            if not isinstance(project_id, int):
                try:
                    project_id = int(project_id)
                except ValueError:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "error": f"project_id must be an integer, got {type(arguments['project_id']).__name__}"
                            }, indent=2)
                        )
                    ]
            
            # Get project with DPRs
            project = db_client.get_project_with_dprs(project_id)
            
            if project is None:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Project {project_id} not found",
                            "project": None
                        }, indent=2)
                    )
                ]
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "project": project
                    }, indent=2, default=str)
                )
            ]
        
        elif name == "list_all_dprs":
            # Get all DPRs
            dprs = db_client.get_all_dprs()
            
            if dprs is None:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Failed to retrieve DPRs from backend",
                            "dprs": []
                        }, indent=2)
                    )
                ]
            
            # Create summary with key fields
            summary = []
            for d in dprs:
                summary.append({
                    "id": d.get("id"),
                    "original_filename": d.get("original_filename"),
                    "project_id": d.get("project_id"),
                    "status": d.get("status"),
                    "upload_ts": d.get("upload_ts"),
                    "has_analysis": d.get("summary_json") is not None,
                    "cloudinary_url": d.get("cloudinary_url")
                })
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "count": len(dprs),
                        "dprs": summary
                    }, indent=2, default=str)
                )
            ]
        
        elif name == "get_dpr_analysis":
            # Validate arguments
            if "dpr_id" not in arguments:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Missing required parameter: dpr_id"
                        }, indent=2)
                    )
                ]
            
            dpr_id = arguments["dpr_id"]
            
            # Validate dpr_id is an integer
            if not isinstance(dpr_id, int):
                try:
                    dpr_id = int(dpr_id)
                except ValueError:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "error": f"dpr_id must be an integer"
                            }, indent=2)
                        )
                    ]
            
            # Get DPR analysis
            dpr = db_client.get_dpr_analysis(dpr_id)
            
            if dpr is None:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"DPR {dpr_id} not found",
                            "dpr": None
                        }, indent=2)
                    )
                ]
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "dpr": dpr
                    }, indent=2, default=str)
                )
            ]
        
        elif name == "get_project_comparison":
            # Validate arguments
            if "project_id" not in arguments:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Missing required parameter: project_id"
                        }, indent=2)
                    )
                ]
            
            project_id = arguments["project_id"]
            
            if not isinstance(project_id, int):
                try:
                    project_id = int(project_id)
                except ValueError:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "error": f"project_id must be an integer"
                            }, indent=2)
                        )
                    ]
            
            # Get comparison
            comparison = db_client.get_project_comparison(project_id)
            
            if comparison is None:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"No comparison found for project {project_id}. A comparison may not have been generated yet.",
                            "comparison": None
                        }, indent=2)
                    )
                ]
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "comparison": comparison
                    }, indent=2, default=str)
                )
            ]
        
        elif name == "get_compliance_info":
            # Validate arguments  
            if "project_id" not in arguments:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Missing required parameter: project_id"
                        }, indent=2)
                    )
                ]
            
            project_id = arguments["project_id"]
            
            if not isinstance(project_id, int):
                try:
                    project_id = int(project_id)
                except ValueError:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "error": f"project_id must be an integer"
                            }, indent=2)
                        )
                    ]
            
            # Get compliance weights
            weights = db_client.get_compliance_weights(project_id)
            
            if weights is None:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Could not retrieve compliance info for project {project_id}",
                            "weights": None
                        }, indent=2)
                    )
                ]
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "project_id": project_id,
                        "compliance_info": weights
                    }, indent=2, default=str)
                )
            ]
        
        elif name == "approve_dpr":
            # Validate arguments
            if "dpr_id" not in arguments:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Missing required parameter: dpr_id"
                        }, indent=2)
                    )
                ]
            
            dpr_id = arguments["dpr_id"]
            
            if not isinstance(dpr_id, int):
                try:
                    dpr_id = int(dpr_id)
                except ValueError:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "error": f"dpr_id must be an integer"
                            }, indent=2)
                        )
                    ]
            
            # Update status to 'accepted'
            result = db_client.update_dpr_status(dpr_id, "accepted")
            
            if result is None:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Failed to approve DPR {dpr_id}. It may not exist."
                        }, indent=2)
                    )
                ]
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "message": f"DPR {dpr_id} has been approved (status set to 'accepted')",
                        "dpr_id": dpr_id,
                        "new_status": "accepted"
                    }, indent=2, default=str)
                )
            ]
        
        elif name == "reject_dpr":
            # Validate arguments
            if "dpr_id" not in arguments:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Missing required parameter: dpr_id"
                        }, indent=2)
                    )
                ]
            
            dpr_id = arguments["dpr_id"]
            feedback = arguments.get("feedback")  # Optional
            
            if not isinstance(dpr_id, int):
                try:
                    dpr_id = int(dpr_id)
                except ValueError:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "error": f"dpr_id must be an integer"
                            }, indent=2)
                        )
                    ]
            
            # Update status to 'rejected'
            result = db_client.update_dpr_status(dpr_id, "rejected")
            
            if result is None:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Failed to reject DPR {dpr_id}. It may not exist."
                        }, indent=2)
                    )
                ]
            
            # Send feedback if provided
            if feedback:
                feedback_result = db_client.send_dpr_feedback(dpr_id, feedback)
                if not feedback_result:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "success": True,
                                "message": f"DPR {dpr_id} rejected, but failed to send feedback",
                                "dpr_id": dpr_id,
                                "new_status": "rejected",
                                "feedback_sent": False
                            }, indent=2, default=str)
                        )
                    ]
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "message": f"DPR {dpr_id} has been rejected" + (" with feedback" if feedback else ""),
                        "dpr_id": dpr_id,
                        "new_status": "rejected",
                        "feedback_sent": bool(feedback)
                    }, indent=2, default=str)
                )
            ]
        
        elif name == "send_feedback_to_dpr":
            # Validate arguments
            if "dpr_id" not in arguments or "feedback" not in arguments:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Missing required parameters: dpr_id and feedback"
                        }, indent=2)
                    )
                ]
            
            dpr_id = arguments["dpr_id"]
            feedback = arguments["feedback"]
            
            if not isinstance(dpr_id, int):
                try:
                    dpr_id = int(dpr_id)
                except ValueError:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "error": f"dpr_id must be an integer"
                            }, indent=2)
                        )
                    ]
            
            # Send feedback
            result = db_client.send_dpr_feedback(dpr_id, feedback)
            
            if result is None:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Failed to send feedback to DPR {dpr_id}. It may not exist."
                        }, indent=2)
                    )
                ]
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "message": f"Feedback sent to DPR {dpr_id}",
                        "dpr_id": dpr_id,
                        "feedback": feedback
                    }, indent=2, default=str)
                )
            ]
        
        elif name == "trigger_comparison":
            # Validate arguments
            if "project_id" not in arguments:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Missing required parameter: project_id"
                        }, indent=2)
                    )
                ]
            
            project_id = arguments["project_id"]
            
            if not isinstance(project_id, int):
                try:
                    project_id = int(project_id)
                except ValueError:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "error": f"project_id must be an integer"
                            }, indent=2)
                        )
                    ]
            
            # Trigger comparison (this may take a while)
            result = db_client.trigger_project_comparison(project_id)
            
            if result is None:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Failed to trigger comparison for project {project_id}. May not have enough analyzed DPRs (need at least 2)."
                        }, indent=2)
                    )
                ]
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "message": f"Comparison triggered for project {project_id}",
                        "project_id": project_id,
                        "comparison": result.get("comparison")
                    }, indent=2, default=str)
                )
            ]
        
        elif name == "create_project":
            # Validate arguments
            required = ["name", "state", "scheme", "sector"]
            missing = [r for r in required if r not in arguments]
            if missing:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Missing required parameters: {', '.join(missing)}"
                        }, indent=2)
                    )
                ]
            
            result = db_client.create_project(
                name=arguments["name"],
                state=arguments["state"],
                scheme=arguments["scheme"],
                sector=arguments["sector"]
            )
            
            if result is None:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Failed to create project"
                        }, indent=2)
                    )
                ]
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "message": f"Project '{arguments['name']}' created successfully",
                        "project_id": result.get("id"),
                        "project": result
                    }, indent=2, default=str)
                )
            ]
        
        elif name == "delete_project":
            if "project_id" not in arguments:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Missing required parameter: project_id"
                        }, indent=2)
                    )
                ]
            
            project_id = arguments["project_id"]
            if not isinstance(project_id, int):
                try:
                    project_id = int(project_id)
                except ValueError:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "error": "project_id must be an integer"
                            }, indent=2)
                        )
                    ]
            
            result = db_client.delete_project(project_id)
            
            if result is None:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Failed to delete project {project_id}. It may not exist."
                        }, indent=2)
                    )
                ]
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "message": f"Project {project_id} and all its DPRs have been deleted"
                    }, indent=2, default=str)
                )
            ]
        
        elif name == "delete_dpr":
            if "dpr_id" not in arguments:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Missing required parameter: dpr_id"
                        }, indent=2)
                    )
                ]
            
            dpr_id = arguments["dpr_id"]
            if not isinstance(dpr_id, int):
                try:
                    dpr_id = int(dpr_id)
                except ValueError:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "error": "dpr_id must be an integer"
                            }, indent=2)
                        )
                    ]
            
            result = db_client.delete_dpr(dpr_id)
            
            if result is None:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Failed to delete DPR {dpr_id}. It may not exist."
                        }, indent=2)
                    )
                ]
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "message": f"DPR {dpr_id} has been permanently deleted"
                    }, indent=2, default=str)
                )
            ]
        
        elif name == "trigger_dpr_analysis":
            if "dpr_id" not in arguments:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Missing required parameter: dpr_id"
                        }, indent=2)
                    )
                ]
            
            dpr_id = arguments["dpr_id"]
            if not isinstance(dpr_id, int):
                try:
                    dpr_id = int(dpr_id)
                except ValueError:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps({
                                "error": "dpr_id must be an integer"
                            }, indent=2)
                        )
                    ]
            
            result = db_client.trigger_dpr_analysis(dpr_id)
            
            if result is None:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Failed to analyze DPR {dpr_id}. It may not exist or already be analyzed."
                        }, indent=2)
                    )
                ]
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": True,
                        "message": f"Analysis triggered for DPR {dpr_id}",
                        "dpr_id": dpr_id,
                        "result": result
                    }, indent=2, default=str)
                )
            ]
        
        elif name == "approve_and_reject_others":
            required = ["project_id", "approved_dpr_id"]
            missing = [r for r in required if r not in arguments]
            if missing:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Missing required parameters: {', '.join(missing)}"
                        }, indent=2)
                    )
                ]
            
            project_id = arguments["project_id"]
            approved_dpr_id = arguments["approved_dpr_id"]
            feedback = arguments.get("feedback")
            
            if not isinstance(project_id, int):
                try:
                    project_id = int(project_id)
                except ValueError:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps({"error": "project_id must be an integer"}, indent=2)
                        )
                    ]
            
            if not isinstance(approved_dpr_id, int):
                try:
                    approved_dpr_id = int(approved_dpr_id)
                except ValueError:
                    return [
                        TextContent(
                            type="text",
                            text=json.dumps({"error": "approved_dpr_id must be an integer"}, indent=2)
                        )
                    ]
            
            result = db_client.approve_and_reject_others(project_id, approved_dpr_id, feedback)
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": result.get("success", False),
                        "message": f"Approved DPR {result.get('approved_id')}, rejected {len(result.get('rejected_ids', []))} others",
                        "approved_id": result.get("approved_id"),
                        "rejected_ids": result.get("rejected_ids", []),
                        "errors": result.get("errors", [])
                    }, indent=2, default=str)
                )
            ]
        
        elif name == "batch_approve_dprs":
            if "dpr_ids" not in arguments:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "Missing required parameter: dpr_ids"
                        }, indent=2)
                    )
                ]
            
            dpr_ids = arguments["dpr_ids"]
            if not isinstance(dpr_ids, list):
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "dpr_ids must be a list of integers"
                        }, indent=2)
                    )
                ]
            
            # Convert to ints
            try:
                dpr_ids = [int(x) for x in dpr_ids]
            except (ValueError, TypeError):
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "All dpr_ids must be integers"
                        }, indent=2)
                    )
                ]
            
            result = db_client.batch_approve_dprs(dpr_ids)
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": result.get("success", False),
                        "message": f"Approved {len(result.get('approved_ids', []))} DPRs",
                        "approved_ids": result.get("approved_ids", []),
                        "failed_ids": result.get("failed_ids", [])
                    }, indent=2, default=str)
                )
            ]
        
        elif name == "send_bulk_feedback":
            required = ["dpr_ids", "feedback"]
            missing = [r for r in required if r not in arguments]
            if missing:
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": f"Missing required parameters: {', '.join(missing)}"
                        }, indent=2)
                    )
                ]
            
            dpr_ids = arguments["dpr_ids"]
            feedback = arguments["feedback"]
            
            if not isinstance(dpr_ids, list):
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "dpr_ids must be a list of integers"
                        }, indent=2)
                    )
                ]
            
            # Convert to ints
            try:
                dpr_ids = [int(x) for x in dpr_ids]
            except (ValueError, TypeError):
                return [
                    TextContent(
                        type="text",
                        text=json.dumps({
                            "error": "All dpr_ids must be integers"
                        }, indent=2)
                    )
                ]
            
            result = db_client.send_bulk_feedback(dpr_ids, feedback)
            
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "success": result.get("success", False),
                        "message": f"Sent feedback to {len(result.get('sent_ids', []))} DPRs",
                        "sent_ids": result.get("sent_ids", []),
                        "failed_ids": result.get("failed_ids", [])
                    }, indent=2, default=str)
                )
            ]
        
        else:
            return [
                TextContent(
                    type="text",
                    text=json.dumps({
                        "error": f"Unknown tool: {name}"
                    }, indent=2)
                )
            ]
            
    except Exception as e:
        import traceback
        traceback.print_exc(file=sys.stderr)
        return [
            TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Internal error: {str(e)}"
                }, indent=2)
            )
        ]


async def main():
    """
    Main entry point for the MCP server.
    Runs the server using stdio transport.
    """
    # Test backend API connection on startup
    backend_url = get_backend_url()
    print("Starting MCP Server for DPR Analyzer...", file=sys.stderr)
    print(f"Backend URL: {backend_url}", file=sys.stderr)
    
    if not db_client.test_connection():
        print("⚠ Warning: Could not connect to backend API. Make sure the backend is running!", file=sys.stderr)
        print(f"  Expected backend at: {backend_url}", file=sys.stderr)
    
    async with stdio_server() as (read_stream, write_stream):
        print("✓ MCP Server started successfully (v4.0.0)", file=sys.stderr)
        print("Available tools (17 total):", file=sys.stderr)
        print("  Read-only: list_projects, get_project_details, list_all_dprs, get_dpr_analysis, get_project_comparison, get_compliance_info", file=sys.stderr)
        print("  Admin Actions: approve_dpr, reject_dpr, send_feedback_to_dpr, trigger_comparison", file=sys.stderr)
        print("  Project Mgmt: create_project, delete_project, delete_dpr, trigger_dpr_analysis", file=sys.stderr)
        print("  Batch Ops: approve_and_reject_others, batch_approve_dprs, send_bulk_feedback", file=sys.stderr)
        print("Waiting for client connections...", file=sys.stderr)
        
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="dpr-analyzer-mcp",
                server_version="4.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                )
            )
        )


if __name__ == "__main__":
    asyncio.run(main())
