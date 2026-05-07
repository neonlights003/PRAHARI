# Team Setup Guide - PostgreSQL Migration

Welcome! This guide will help you set up the DPR Analyzer project with PostgreSQL on your local machine.

## Prerequisites
- ✅ PostgreSQL installed (any version 12+)
- ✅ Python 3.9+ installed
- ✅ Node.js and npm installed
- ✅ Project pulled from Git

---

## 🚀 Quick Setup (5 Steps)

### Step 1: Create PostgreSQL Database

Open PowerShell or Command Prompt and run:

```powershell
# Connect to PostgreSQL (enter your password when prompted)
psql -U postgres

# Inside psql, create the database
CREATE DATABASE "dpr-analyzer";

# Verify it was created
\l

# Exit psql
\q
```

**Note:** The database name MUST be `dpr-analyzer` (with quotes because of the hyphen).

---

### Step 2: Configure Environment Variables

1. **Create a `.env` file** in the project root (same folder as `backend/` and `frontend/`)

2. **Copy this template** and fill in YOUR details:

```env
# PostgreSQL Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dpr-analyzer
DB_USER=postgres
DB_PASSWORD=YOUR_POSTGRES_PASSWORD_HERE

# Gemini API Key (get from Google AI Studio)
GEMINI_API_KEY=YOUR_GEMINI_API_KEY_HERE
```

3. **Replace:**
   - `YOUR_POSTGRES_PASSWORD_HERE` → Your PostgreSQL password
   - `YOUR_GEMINI_API_KEY_HERE` → Get from [Google AI Studio](https://aistudio.google.com/app/apikey)

---

### Step 3: Install Python Dependencies

```powershell
# Navigate to project root
cd path\to\AI-For-Bharat

# Create virtual environment (if not exists)
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

**Key dependency:** This will install `psycopg2-binary` (PostgreSQL adapter for Python)

---

### Step 4: Initialize Database Tables

The database tables will be **automatically created** when you first run the backend server!

Just run:

```powershell
# Make sure venv is activated
.\.venv\Scripts\activate

# Start backend server
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

You should see:
```
✓ PostgreSQL connection pool initialized
✓ PostgreSQL database initialized successfully
```

This means all 8 tables were created automatically! 🎉

---

### Step 5: Install Frontend Dependencies & Run

Open a **NEW terminal** window:

```powershell
# Navigate to frontend folder
cd path\to\AI-For-Bharat\frontend

# Install dependencies (first time only)
npm install

# Start frontend dev server
npm run dev -- --host 127.0.0.1 --port 5000
```

---

## 🌐 Access the Application

Once both servers are running:
- **Frontend:** http://127.0.0.1:5000
- **Backend API:** http://127.0.0.1:8000
- **API Documentation:** http://127.0.0.1:8000/docs

---

## 🔧 Troubleshooting

### ❌ "password authentication failed"
**Solution:** Check your `.env` file - make sure `DB_PASSWORD` matches your PostgreSQL password

### ❌ "database 'dpr-analyzer' does not exist"
**Solution:** Run: `psql -U postgres -c "CREATE DATABASE \"dpr-analyzer\""`

### ❌ "ModuleNotFoundError: No module named 'psycopg2'"
**Solution:** 
```powershell
.\.venv\Scripts\activate
pip install psycopg2-binary
```

### ❌ "Connection refused" or "could not connect to server"
**Solution:** Make sure PostgreSQL service is running:
- Windows: Check Services → PostgreSQL should be "Running"
- Or restart it: `net start postgresql-x64-XX` (replace XX with your version)

### ❌ Frontend shows "Network Error" or API calls fail
**Solution:** Make sure backend is running on port 8000 first, then start frontend

---

## 📋 Complete Checklist

- [ ] PostgreSQL installed
- [ ] Database `dpr-analyzer` created
- [ ] `.env` file created with correct credentials
- [ ] Python virtual environment created
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Backend server running (port 8000)
- [ ] Frontend dependencies installed (`npm install`)
- [ ] Frontend server running (port 5000)
- [ ] Can access http://127.0.0.1:5000 in browser

---

## 🎯 Quick Start Commands

**Every time you want to run the project:**

**Terminal 1 (Backend):**
```powershell
cd path\to\AI-For-Bharat
.\.venv\Scripts\activate
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 (Frontend):**
```powershell
cd path\to\AI-For-Bharat\frontend
npm run dev -- --host 127.0.0.1 --port 5000
```

---

## 💡 Important Notes

1. **Each teammate has their own local database** - Data is NOT shared between team members
2. **Fresh database** - Everyone starts with empty tables (this is expected)
3. **`.env` file is NOT in Git** - Each person must create their own
4. **Different passwords are OK** - Each teammate can use their own PostgreSQL password

---

## 🆘 Need Help?

If you encounter any issues:
1. Check the troubleshooting section above
2. Make sure PostgreSQL service is running
3. Verify your `.env` file has correct credentials
4. Check that both backend and frontend servers are running
5. Ask the team for help!

---

## ✅ Success Confirmation

You'll know everything is working when:
- ✓ Backend shows: `✓ PostgreSQL database initialized successfully`
- ✓ Frontend shows: `VITE ready in XXX ms`
- ✓ You can open http://127.0.0.1:5000 and see the app
- ✓ You can create a project and upload a DPR

Happy coding! 🚀
