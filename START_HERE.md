# Quick Start - DPR Analyzer

## Start Backend (Terminal 1)
```powershell
.\.venv\Scripts\activate
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

## Start Frontend (Terminal 2)
```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5000
```

## Access Application
- Frontend: http://127.0.0.1:5000
- Backend API: http://127.0.0.1:8000/docs

## What to Expect in Logs

### Backend Startup:
```
✓ Cloudinary configured with cloud: dwnigoa4b
✓ PostgreSQL connection pool initialized
✓ PostgreSQL database initialized successfully
INFO: Uvicorn running on http://127.0.0.1:8000
```

### When You Upload a PDF:
```
⏳ Saving client DPR: filename.pdf
✓ File saved: data/filename.pdf
⏳ Uploading to Cloudinary: data/filename.pdf
✓ Cloudinary upload successful: https://res.cloudinary.com/...
✓ DPR inserted with ID: 1
✓ Cleaned up local file
⏳ Auto-analyzing client DPR 1...
✓ Analysis complete for DPR 1
```

### When You View a PDF:
```
📄 PDF Request: DPR 1
✓ DPR 1 found: filename.pdf
Cloudinary URL: https://res.cloudinary.com/...
Fetching from Cloudinary...
✓ Returning PDF from Cloudinary (458443 bytes)
```

## ✅ Everything Working:
- Upload → Cloudinary ✅
- Analysis → Gemini AI ✅  
- Viewing → Cloudinary CDN ✅
- Download → Works ✅
