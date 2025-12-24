# Hướng dẫn đóng gói MT4/MT5 Login thành file EXE

Tài liệu này hướng dẫn cách đóng gói ứng dụng MT4/MT5 Login thành file thực thi (EXE) độc lập, cho phép chạy trên máy tính Windows mà không cần cài đặt Python và các thư viện liên quan.

## Cách đóng gói

### Bước 1: Chuẩn bị môi trường

Đảm bảo bạn đã có:
- Python 3.6 trở lên
- Tất cả các file code (mt_login_sheets.py)
- File credentials.json (nếu có)
- File config.json (nếu đã lưu cấu hình trước đó)

### Bước 2: Chạy script đóng gói

1. Chạy file build_exe.py:
```
python build_exe.py
```

2. Script sẽ tự động:
   - Kiểm tra và cài đặt PyInstaller nếu chưa có
   - Kiểm tra và cài đặt các thư viện cần thiết
   - Đóng gói ứng dụng thành file EXE
   - Sao chép các file hỗ trợ (credentials.json, config.json) nếu có

3. Khi hoàn thành, bạn sẽ nhận được thông báo thành công và đường dẫn đến file EXE.

## Cách sử dụng file EXE

### Yêu cầu

- Windows 7/8/10/11
- Quyền Admin (cho lần chạy đầu tiên)
- File credentials.json (để kết nối với Google Sheets)

### Cài đặt

1. Sao chép thư mục `dist` sau khi đóng gói đến nơi bạn muốn sử dụng
2. Đảm bảo file `credentials.json` nằm trong cùng thư mục với file EXE
3. (Tùy chọn) Sao chép file `config.json` nếu bạn đã có cấu hình trước đó

### Chạy ứng dụng

1. Nhấp đúp vào file `MT4_MT5_Login.exe` để chạy
2. Lần đầu tiên chạy, Windows có thể hiển thị cảnh báo bảo mật - nhấn "Thêm thông tin" và "Vẫn chạy"
3. Ứng dụng sẽ tự động tải cấu hình từ config.json nếu có
4. Sử dụng ứng dụng như bình thường

## Xử lý sự cố

### Không thể khởi động file EXE
- Đảm bảo bạn có quyền Admin
- Thử chạy với quyền Admin (nhấp chuột phải > Chạy với quyền Admin)
- Kiểm tra Windows Defender hoặc phần mềm diệt virus có thể đang chặn

### Lỗi khi kết nối Google Sheets
- Đảm bảo file credentials.json đúng và nằm trong cùng thư mục với EXE
- Kiểm tra kết nối Internet
- Kiểm tra xem Google Sheet đã được chia sẻ với Service Account chưa

### Không thể đăng nhập MT4/MT5
- Đảm bảo MT4/MT5 đã được mở trước khi thử đăng nhập
- Kiểm tra cấu hình cột dữ liệu có chính xác không
- Thử chạy với quyền Admin

## Lưu ý quan trọng

- File EXE có thể bị phần mềm diệt virus cảnh báo (đây là cảnh báo sai)
- File credentials.json chứa thông tin nhạy cảm, không nên chia sẻ
- Nếu bạn cập nhật mã nguồn, cần đóng gói lại để tạo file EXE mới 