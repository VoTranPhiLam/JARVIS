@echo off
echo ==================================================
echo   DONG GOI UNG DUNG MT4_MT5_LOGIN THANH FILE EXE
echo ==================================================
echo.

echo Dang kiem tra Python...
where python >nul 2>nul
if %ERRORLEVEL% NEQ 0 (
    echo Loi: Khong tim thay Python. Vui long cai dat Python truoc.
    pause
    exit /b 1
)

echo Dang cai dat cac thu vien can thiet...
python -m pip install --upgrade pip
python -m pip install pyinstaller pandas gspread oauth2client pyperclip pywinauto pyautogui psutil PyQt5

echo Dang kiem tra file requirements.txt...
if not exist requirements.txt (
    echo Dang tao file requirements.txt...
    echo pandas>=1.3.0 > requirements.txt
    echo gspread>=5.0.0 >> requirements.txt
    echo oauth2client>=4.1.3 >> requirements.txt
    echo PyQt5>=5.15.0 >> requirements.txt
    echo pyperclip>=1.8.2 >> requirements.txt
    echo pywinauto>=0.6.8 >> requirements.txt
    echo pyautogui>=0.9.53 >> requirements.txt
    echo psutil>=5.8.0 >> requirements.txt
)

echo Dang bat dau qua trinh dong goi...
python build_exe.py

echo.
echo Qua trinh hoan tat!
echo File EXE da duoc tao trong thu muc "dist"
echo.
pause 