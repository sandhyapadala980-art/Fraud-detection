@echo off
setlocal

set FRONTEND_DIR=%~dp0frontend
set PORT=5173

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%PORT% ^| findstr LISTENING') do (
  taskkill /PID %%a /F >nul 2>&1
)

pushd "%FRONTEND_DIR%"
python -m http.server %PORT%
popd
