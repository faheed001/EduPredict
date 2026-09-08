@echo off
setlocal
cd /d "%~dp0"
title EduPredict 3.0 - Final Setup

echo ==============================================
echo        EduPredict 3.0 - FINAL SETUP
 echo ==============================================
echo.

where py >nul 2>&1
if errorlevel 1 (
  echo ERROR: Python Launcher was not found.
  echo Install Python 3.14 from python.org and enable "Add Python to PATH".
  pause
  exit /b 1
)

py -3.14 --version
if errorlevel 1 (
  echo.
  echo ERROR: Python 3.14 is required.
  echo Python 3.14 is the supported Python version for this project.
  echo Install Python 3.14, then run this setup again.
  pause
  exit /b 1
)

echo.
if exist ".venv\Scripts\python.exe" (
  for /f "tokens=2" %%V in ('".venv\Scripts\python.exe" --version 2^>^&1') do set VENVVER=%%V
  echo Existing virtual environment Python: %VENVVER%
  echo.
  echo The project requires Python 3.14. Recreating the environment is safest.
  rmdir /s /q ".venv"
)

echo Creating a clean Python 3.14 virtual environment...
py -3.14 -m venv .venv
if errorlevel 1 goto :fail

call ".venv\Scripts\activate.bat"
python --version
python -m pip install --upgrade pip
if errorlevel 1 goto :fail

echo.
echo Installing exact ML-compatible dependencies...
pip install -r requirements.txt
if errorlevel 1 goto :fail

echo.
echo Rebuilding ML artifacts with the SAME scikit-learn version used by the app...
python model\train_model.py
if errorlevel 1 goto :fail

echo.
echo Running project audit...
python tools\audit_project.py
if errorlevel 1 goto :fail

echo.
echo ==============================================
echo SETUP COMPLETE - READY TO RUN
 echo ==============================================
echo.
echo Start the application with RUN_WINDOWS.bat
pause
exit /b 0

:fail
echo.
echo SETUP FAILED. Read the error shown above.
pause
exit /b 1
