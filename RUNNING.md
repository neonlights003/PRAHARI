# How to Run Your DPR Analyzer Application

## Step 1: Activate Virtual Environment & Install Dependencies

```powershell
# In the project root directory (AI-For-Bharat)
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## Step 2: Start Backend Server

```powershell
# Make sure you're in the project root with venv activated
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

**Backend will run on:** http://127.0.0.1:8000

## Step 3: Start Frontend (In a NEW Terminal)

```powershell
# Navigate to frontend folder
cd frontend
npm run dev -- --host 127.0.0.1 --port 5000
```

**Frontend will run on:** http://127.0.0.1:5000

## Quick Start Commands

### Terminal 1 (Backend):
```powershell
.\.venv\Scripts\activate
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

### Terminal 2 (Frontend):
```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5000
```

## Troubleshooting

### "ModuleNotFoundError: No module named 'psycopg2'"
**Solution:** Install dependencies
```powershell
.\.venv\Scripts\activate
pip install psycopg2-binary
```

### "uvicorn: The term is not recognized"
**Solution:** Activate virtual environment first
```powershell
.\.venv\Scripts\activate
```

### Backend starts but can't connect to database
**Solution:** Check PostgreSQL is running and .env file has correct credentials
```powershell
# Check .env file has:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=dpr-analyzer
DB_USER=postgres
DB_PASSWORD=<your-password>
```

## What Changed with PostgreSQL Migration

- ✅ Database is now PostgreSQL (not SQLite)
- ✅ No more `data/dpr.db` file
- ✅ Data stored in PostgreSQL server
- ✅ Better performance and scalability
- ✅ Connection pooling enabled

## Access Points

- **Frontend:** http://127.0.0.1:5000
- **Backend API:** http://127.0.0.1:8000
- **API Docs:** http://127.0.0.1:8000/docs (Swagger UI)
- **ReDoc:** http://127.0.0.1:8000/redoc
