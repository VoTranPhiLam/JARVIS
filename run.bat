@echo off
cd /d "%~dp0"
start "" python mt_login_sheets.py
timeout /t 2 /nobreak >nul
pause
