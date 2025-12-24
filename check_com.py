
# Script để kiểm tra COM initialization
import sys
try:
    import pythoncom
    pythoncom.CoInitialize()
    print("COM initialization OK")
    # Không gọi CoUninitialize() để đảm bảo COM được khởi tạo
except Exception as e:
    print(f"COM initialization failed: {e}")
    sys.exit(1)

try:
    from pywinauto import Desktop, Application
    print("Pywinauto import OK")
except Exception as e:
    print(f"Pywinauto import failed: {e}")
    sys.exit(1)

try:
    import psutil
    print(f"Psutil version: {psutil.__version__}")
except Exception as e:
    print(f"Psutil import failed: {e}")
    sys.exit(1)
