@echo off
setlocal

set BACKEND_DIR=%~dp0backend
set PORT=8001

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%PORT% ^| findstr LISTENING') do (
  taskkill /PID %%a /F >nul 2>&1
)

pushd "%BACKEND_DIR%"
if not exist ".venv\Scripts\python.exe" (
  echo Virtual environment not found at backend\.venv
  popd
  exit /b 1
)

".venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port %PORT%
popd
