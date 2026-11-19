@echo off
title InfraSphere AI - Frontend Command Center
cd /d "%~dp0frontend"
echo ========================================================
echo   InfraSphere AI - Frontend Command Center
echo   Current Directory: %CD%
echo ========================================================
echo.
echo Starting Vite dev server on http://localhost:5173...
npm run dev
pause
