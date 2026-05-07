# MCP Server Setup Guide

This guide helps teammates set up the MCP (Model Context Protocol) server for Claude Desktop integration.

---

## 📋 Prerequisites

1. **Python 3.9+** installed
2. **Claude Desktop** installed ([Download](https://claude.ai/download))
3. **Backend server** running at `http://127.0.0.1:8000`
4. **PostgreSQL** configured (get `.env` file from team lead)

---

## 🚀 Quick Setup

### Step 1: Install MCP Server Dependencies

```bash
cd mcp-server/mcp-server/mcp-server
pip install -r requirements.txt
```

### Step 2: Verify MCP Server Works

```bash
# Make sure backend is running first!
python db_client.py
```

You should see:
```
Testing backend API connection...
✓ Backend API connection successful. Found X projects.
```

### Step 3: Configure Claude Desktop

Find your Claude Desktop config file:

**Windows:**
```
%APPDATA%\Claude\claude_desktop_config.json
```

**macOS:**
```
~/Library/Application Support/Claude/claude_desktop_config.json
```

---

## ⚠️ PATHS YOU MUST CHANGE

The following paths in `claude_desktop_config.json` are **user-specific** and must be updated:

### Config File Template

```json
{
  "mcpServers": {
    "dpr-analyzer": {
      "command": "YOUR_PYTHON_PATH_HERE",
      "args": ["YOUR_SERVER_PATH_HERE"],
      "cwd": "YOUR_MCP_DIR_HERE"
    }
  }
}
```

### Paths to Update:

| Field | What to Put | Example (Windows) |
|-------|-------------|-------------------|
| `command` | Full path to `python.exe` in your venv | `C:\\Users\\YOUR_USERNAME\\...\\AI-For-Bharat\\.venv\\Scripts\\python.exe` |
| `args` | Full path to `server.py` | `C:\\Users\\YOUR_USERNAME\\...\\AI-For-Bharat\\mcp-server\\mcp-server\\mcp-server\\server.py` |
| `cwd` | MCP server directory | `C:\\Users\\YOUR_USERNAME\\...\\AI-For-Bharat\\mcp-server\\mcp-server\\mcp-server` |

### Finding Your Paths (Windows)

```powershell
# Find Python path
where python
# OR for venv
.venv\Scripts\python.exe

# Get full path to server.py
cd mcp-server\mcp-server\mcp-server
echo %cd%\server.py
```

### Finding Your Paths (macOS/Linux)

```bash
# Find Python path
which python3
# OR for venv
source .venv/bin/activate && which python

# Get full path to server.py
cd mcp-server/mcp-server/mcp-server
echo "$(pwd)/server.py"
```

---

## 📝 Example Configurations

### Windows Example

```json
{
  "mcpServers": {
    "dpr-analyzer": {
      "command": "C:\\Users\\JohnDoe\\Projects\\AI-For-Bharat\\.venv\\Scripts\\python.exe",
      "args": [
        "C:\\Users\\JohnDoe\\Projects\\AI-For-Bharat\\mcp-server\\mcp-server\\mcp-server\\server.py"
      ],
      "cwd": "C:\\Users\\JohnDoe\\Projects\\AI-For-Bharat\\mcp-server\\mcp-server\\mcp-server"
    }
  }
}
```

### macOS Example

```json
{
  "mcpServers": {
    "dpr-analyzer": {
      "command": "/Users/johndoe/Projects/AI-For-Bharat/.venv/bin/python",
      "args": [
        "/Users/johndoe/Projects/AI-For-Bharat/mcp-server/mcp-server/mcp-server/server.py"
      ],
      "cwd": "/Users/johndoe/Projects/AI-For-Bharat/mcp-server/mcp-server/mcp-server"
    }
  }
}
```

---

## ✅ Verification

1. **Restart Claude Desktop** after editing config
2. Look for the **hammer icon** 🔨 in Claude Desktop
3. Click it to see available tools (should show 17 tools)

### Test Commands in Claude:

- *"List all projects in the DPR system"*
- *"Get details for project 1"*
- *"Show all DPRs"*

---

## 🔧 Troubleshooting

### "Could not connect to MCP server"

1. **Check backend is running:**
   ```bash
   python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
   ```

2. **Verify paths in config** - Use absolute paths with escaped backslashes on Windows

3. **Check Python path** - Must point to Python with MCP packages installed

### "No tools showing"

1. Restart Claude Desktop completely
2. Check `%APPDATA%\Claude\logs` for errors (Windows)

### "Connection refused"

1. Backend server not running
2. Check `BACKEND_URL` in `config.py` (default: `http://127.0.0.1:8000`)

---

## 🛠️ Available MCP Tools (17 Total)

### Read-Only (6)
- `list_projects` - All projects overview
- `get_project_details` - Project + DPRs with analysis
- `list_all_dprs` - All DPRs across projects
- `get_dpr_analysis` - Full AI analysis for DPR
- `get_project_comparison` - Saved comparison results
- `get_compliance_info` - Compliance weights

### Admin Actions (4)
- `approve_dpr` - Accept a DPR
- `reject_dpr` - Reject with optional feedback
- `send_feedback_to_dpr` - Send review comments
- `trigger_comparison` - Start AI comparison

### Project Management (4)
- `create_project` - Create new project
- `delete_project` - Delete project + all DPRs
- `delete_dpr` - Delete single DPR
- `trigger_dpr_analysis` - Trigger AI analysis

### Batch Operations (3)
- `approve_and_reject_others` - Approve one, reject rest
- `batch_approve_dprs` - Approve multiple DPRs
- `send_bulk_feedback` - Feedback to multiple DPRs

---

## 📞 Need Help?

If MCP server still doesn't work after following this guide, share:
1. Your `claude_desktop_config.json` (hide sensitive paths if needed)
2. Output of `python db_client.py`
3. Any error messages from Claude Desktop logs
