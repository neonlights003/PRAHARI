# Quick Setup Checklist for Teammates

## ✅ One-Time Setup

1. **Install PostgreSQL** ✓ (you already did this)

2. **Create Database:**
   ```powershell
   psql -U postgres -c "CREATE DATABASE \"dpr-analyzer\""
   ```

3. **Create `.env` file:**
   - Copy `.env.template` → rename to `.env`
   - Edit it with YOUR password and API key

4. **Install Python Dependencies:**
   ```powershell
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

5. **Install Frontend Dependencies:**
   ```powershell
   cd frontend
   npm install
   ```

## 🚀 Running the App (Every Time)

**Terminal 1 - Backend:**
```powershell
.\.venv\Scripts\activate
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 - Frontend:**
```powershell
cd frontend
npm run dev -- --host 127.0.0.1 --port 5000
```

**Open:** http://127.0.0.1:5000

---

For detailed setup instructions, see **TEAM_SETUP.md**
