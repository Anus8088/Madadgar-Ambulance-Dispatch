@echo off
title Madadgar Emergency Ambulance Dispatch System
color 0A
echo =========================================================================
echo    MADADGAR (MADADGAR EMERGENCY AMBULANCE DISPATCH SYSTEM)
echo    Powered by 100%% Python Flask ^& PostgreSQL ('emergency_db')
echo    Team: Muhammad Anus ^| Sufyan Akhter ^| Rana Faraz Ahmed
echo =========================================================================
echo.
echo [1/2] Installing / Checking Python dependencies...
pip install -r requirements.txt
echo.
echo [2/2] Starting Python Flask Server...
echo -------------------------------------------------------------------------
echo Opening server at http://127.0.0.1:5000 ...
echo Press Ctrl+C to stop the server anytime.
echo -------------------------------------------------------------------------
echo.
python app.py
pause
