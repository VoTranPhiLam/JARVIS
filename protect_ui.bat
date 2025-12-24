@echo off
echo ===== CÔNG CỤ BẢO VỆ GIAO DIỆN MT4/MT5 =====
echo.

REM Kiểm tra Python đã được cài đặt chưa
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Lỗi: Python chưa được cài đặt!
    echo Vui lòng cài đặt Python trước khi sử dụng công cụ này.
    goto :end
)

if "%1"=="" (
    echo HƯỚNG DẪN SỬ DỤNG:
    echo ------------------
    echo protect_ui.bat start   : Bắt đầu bảo vệ giao diện
    echo protect_ui.bat stop    : Tạm dừng bảo vệ giao diện
    echo protect_ui.bat status  : Kiểm tra trạng thái hiện tại
    echo protect_ui.bat protect : Bảo vệ tất cả cửa sổ MT4/MT5
    echo protect_ui.bat list    : Hiển thị danh sách cửa sổ được bảo vệ
    goto :end
)

if "%1"=="start" (
    echo Bắt đầu bảo vệ giao diện...
    echo.
    python ui_protection.py --disallow
    start /B pythonw ui_protection.py > nul 2>&1
    echo Đã bật chế độ bảo vệ giao diện!
    goto :end
)

if "%1"=="stop" (
    echo Dừng bảo vệ giao diện...
    echo.
    python ui_protection.py --allow
    taskkill /F /IM pythonw.exe > nul 2>&1
    echo Đã tắt chế độ bảo vệ giao diện!
    goto :end
)

if "%1"=="status" (
    echo Kiểm tra trạng thái bảo vệ giao diện...
    echo.
    python ui_protection.py --list
    goto :end
)

if "%1"=="protect" (
    echo Bảo vệ tất cả cửa sổ MT4/MT5...
    echo.
    python ui_protection.py --protect
    goto :end
)

if "%1"=="list" (
    echo Danh sách cửa sổ được bảo vệ:
    echo.
    python ui_protection.py --list
    goto :end
)

:end
echo.
echo Hoàn tất! 