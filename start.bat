@echo off
REM ─── HR Multi-Agent Platform – Local Development Startup ─────────────────────
REM This script is for running WITHOUT Docker (local Python + Node.js)

echo.
echo [92m HR Intelligence Platform – Starting Local Dev Server [0m
echo ─────────────────────────────────────────────────────────────────

REM Check if .env exists, copy from example if not
if not exist ".env" (
    echo [93m Creating .env from .env.example...[0m
    copy .env.example .env
    echo [93m ⚠  Please edit .env with your API keys before production use[0m
)

REM Create upload dir
if not exist "uploaded_cvs" mkdir uploaded_cvs
if not exist "logs" mkdir logs

echo.
echo [96m Starting Backend (FastAPI) on http://localhost:8001 ...[0m
start "HR Backend" cmd /k ".\venv\Scripts\python.exe -m uvicorn backend.gateway.main:app --host 0.0.0.0 --port 8001 --reload"

echo.
echo [96m Starting Frontend (React) on http://localhost:5173 ...[0m
start "HR Frontend" cmd /k "cd frontend && npm install && npm run dev"

echo.
echo [92m ✅ Platform starting up... [0m
echo [92m   Backend:  http://localhost:8001  [0m
echo [92m   Frontend: http://localhost:5173  [0m
echo [92m   API Docs: http://localhost:8001/docs [0m
echo.
pause
