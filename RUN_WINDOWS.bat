@echo off
setlocal
cd /d "%~dp0"
title EduPredict 3.0 - Run
if not exist ".venv\Scripts\python.exe" (
  echo ERROR: .venv not found. Run SETUP_WINDOWS.bat first.
  pause
  exit /b 1
)
call ".venv\Scripts\activate.bat"
set FLASK_DEBUG=0
set PORT=5000
echo Starting EduPredict 3.0...
echo Open http://127.0.0.1:5000 in your browser.
echo Press CTRL+C to stop the server.
echo.
python app.py
pause
