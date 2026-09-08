@echo off
cd /d "%~dp0"
echo ============================================
echo   Meeting Minutes System - backend only
echo   backend : http://127.0.0.1:8000
echo   docs    : http://127.0.0.1:8000/docs
echo   Stop with Ctrl+C
echo ============================================
.\.venv\Scripts\python.exe backend\run.py
echo.
echo Server exited. (If it failed, see the message above.)
pause
