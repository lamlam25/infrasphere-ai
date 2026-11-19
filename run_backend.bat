@echo off
title InfraSphere AI - Backend Server
cd /d "%~dp0backend"
echo ========================================================
echo   InfraSphere AI - Backend Server
echo   Current Directory: %CD%
echo ========================================================
echo.
echo [1/2] Initializing and verifying database...
python test_init.py
echo.
echo [2/2] Starting FastAPI server on http://localhost:8000...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
pause
