import os
import sys
import shutil
from pathlib import Path

def fix_resources():
    """
    Script để sửa vấn đề với đường dẫn tài nguyên trong file EXE.
    Khi chạy file EXE, có thể xảy ra vấn đề về đường dẫn đến credentials.json.
    Script này tạo ra cấu trúc thư mục cần thiết và sao chép các file quan trọng.
    """
    print("=============================================")
    print("  Sửa lỗi đường dẫn tài nguyên cho file EXE")
    print("=============================================")
    
    # Kiểm tra xem file EXE đã được tạo chưa
    exe_path = Path("dist/MT4_MT5_Login.exe")
    if not exe_path.exists():
        print("❌ Không tìm thấy file EXE! Hãy chạy build_exe.py trước.")
        input("\nNhấn Enter để thoát...")
        sys.exit(1)
    
    # Tạo thư mục chứa file EXE và tài nguyên
    release_dir = Path("MT4_MT5_Login")
    if not release_dir.exists():
        release_dir.mkdir()
        print(f"✅ Đã tạo thư mục {release_dir}")
    
    # Sao chép file EXE
    print("📋 Đang sao chép file EXE...")
    shutil.copy(exe_path, release_dir)
    print(f"✅ Đã sao chép EXE vào {release_dir}")
    
    # Sao chép credentials.json nếu có
    creds_path = Path("credentials.json")
    if creds_path.exists():
        print("📋 Đang sao chép credentials.json...")
        shutil.copy(creds_path, release_dir)
        print("✅ Đã sao chép credentials.json")
    else:
        print("⚠️ Không tìm thấy file credentials.json")
        # Tạo file credentials.json mẫu
        placeholder = Path(release_dir, "credentials.json")
        with open(placeholder, "w") as f:
            f.write("{\n  \"YOUR CREDENTIALS HERE\": \"Download from Google Cloud Console\"\n}")
        print("✅ Đã tạo file credentials.json mẫu - Bạn cần thay thế bằng file thật")
    
    # Sao chép config.json nếu có
    config_path = Path("config.json")
    if config_path.exists():
        print("📋 Đang sao chép config.json...")
        shutil.copy(config_path, release_dir)
        print("✅ Đã sao chép config.json")
    
    # Tạo file README.txt
    readme_path = Path(release_dir, "README.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("""MT4/MT5 Login - Công cụ đăng nhập tự động

HƯỚNG DẪN SỬ DỤNG:
1. Đảm bảo file credentials.json nằm trong cùng thư mục với file EXE
2. Khởi động file MT4_MT5_Login.exe
3. Ứng dụng sẽ tự động tải cấu hình từ config.json nếu có

LƯU Ý:
- Nếu gặp cảnh báo bảo mật, hãy nhấn "Thêm thông tin" và "Vẫn chạy"
- MT4/MT5 phải được mở trước khi sử dụng chức năng đăng nhập
- Nếu gặp lỗi, hãy thử chạy với quyền Admin
        
Phát triển bởi: Cursor AI
""")
    print("✅ Đã tạo file README.txt")
    
    # Tạo file ZIP nếu có thư viện zipfile
    try:
        import zipfile
        zip_path = Path("MT4_MT5_Login.zip")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file in release_dir.glob('*'):
                zipf.write(file, arcname=file.name)
        print(f"\n✅ Đã tạo file ZIP: {zip_path}")
    except:
        print("\n⚠️ Không thể tạo file ZIP")
    
    print("\n🎉 Hoàn tất! Thư mục cài đặt được tạo tại:", release_dir.absolute())
    print("📝 Bạn có thể sao chép toàn bộ thư mục này đến nơi muốn sử dụng")
    
    input("\nNhấn Enter để thoát...")

if __name__ == "__main__":
    fix_resources() 