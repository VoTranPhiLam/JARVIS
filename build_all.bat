@echo off
title MT4/MT5 Login - Build Process
echo ========================================================
echo     Quy trinh dong goi MT4/MT5 Login Sheets
echo ========================================================
echo.

echo [1/3] Dang kiem tra Python...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python khong duoc cai dat! Hay cai dat Python 3.6 tro len.
    pause
    exit /b 1
)
echo Python da duoc cai dat.

echo.
echo [2/3] Dang dong goi thanh file EXE...
python build_exe.py

echo.
echo [3/3] Dang sua loi duong dan tai nguyen...
python fix_resources.py

echo.
echo ========================================================
echo     Qua trinh dong goi hoan tat!
echo     Ban co the tim thay file MT4_MT5_Login.zip hoac
echo     thu muc MT4_MT5_Login trong thu muc hien tai.
echo ========================================================
echo.

pause 