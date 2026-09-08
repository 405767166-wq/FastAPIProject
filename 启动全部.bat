@echo off
cd /d "%~dp0"

echo ============================================
echo   Meeting Minutes System - one-click start
echo   backend : http://127.0.0.1:8000
echo   nginx   : http://127.0.0.1:8080
echo   browser : http://127.0.0.1:8080
echo ============================================
echo.

echo [1/2] starting backend (port 8000)...
start "backend-8000" cmd /k ".\.venv\Scripts\python.exe backend\run.py"

echo [2/2] starting nginx (port 8080)...
start "nginx-8080" cmd /k ".\nginx\nginx.exe -p .\nginx\"

echo.
echo opening browser...
start "" "http://127.0.0.1:8080"

echo.
echo To stop: close the two popup windows (backend-8000 / nginx-8080),
echo        or run:  .\nginx\nginx.exe -p .\nginx\ -s stop
echo.
pause
