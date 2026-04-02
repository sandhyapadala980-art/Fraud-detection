@echo off
start "Fraud Backend" "%~dp0start-backend.bat"
timeout /t 2 >nul
start "Fraud Frontend" "%~dp0start-frontend.bat"
