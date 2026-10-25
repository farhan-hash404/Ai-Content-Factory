# Running the Project

## 1. Backend (FastAPI + LangGraph)

Using the project virtual environment (`.venv`):

```powershell
cd Agents_backend
# On Windows, use --reload-dir to avoid Click wildcard expansion issues with data/*:
..\.venv\Scripts\python.exe -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload --reload-dir api --reload-dir Graph
```

The backend API will be available at:
- **API URL:** `http://localhost:8000`
- **Interactive Swagger Docs:** `http://localhost:8000/docs`

---

## 2. Frontend (React + Vite)

```powershell
cd frontend
npm run dev
```

The frontend application will be accessible at:
- **Web App:** `http://localhost:3000`
