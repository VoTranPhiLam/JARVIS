# Cải Tiến Ứng Dụng Đăng Nhập Tài Khoản MT4/MT5

## Các tính năng mới

Phiên bản mới này bao gồm những cải tiến quan trọng sau:

### 1. Tăng tốc độ đăng nhập

- **Tối ưu hóa thời gian chờ**: Giảm thời gian chờ giữa các thao tác để đăng nhập nhanh hơn
- **Cấu hình tùy chỉnh**: Có thể điều chỉnh các thông số tốc độ qua tập tin `mt_login_config.json`
- **Các thông số tốc độ**:
  - `focus_delay`: Thời gian chờ sau khi focus cửa sổ (mặc định: 0.5 giây)
  - `key_delay`: Thời gian chờ giữa các phím (mặc định: 0.1 giây)
  - `form_open_delay`: Thời gian chờ form đăng nhập mở (mặc định: 1.0 giây)
  - `field_delay`: Thời gian chờ giữa các trường (mặc định: 0.2 giây)

### 2. Tự động chọn tài khoản thay thế

- **Tự động tích**: Checkbox "Chọn tất cả tài khoản có tài khoản thay thế" giờ đây sẽ tự động được chọn mặc định trong giao diện kiểm tra nhánh
- **Tiết kiệm thời gian**: Không cần phải thủ công tích chọn từng tài khoản

### 3. Bảo vệ giao diện

- **Ngăn thay đổi giao diện**: Bảo vệ các cửa sổ MT4/MT5 khỏi sự thay đổi không mong muốn
- **Khóa vị trí và kích thước**: Ngăn chặn việc di chuyển hoặc thay đổi kích thước cửa sổ
- **Quản lý qua tập lệnh**: Sử dụng `protect_ui.bat` để dễ dàng bật/tắt tính năng bảo vệ

## Hướng dẫn sử dụng

### Cấu hình tốc độ đăng nhập

Tệp cấu hình `mt_login_config.json` sẽ tự động được tạo trong thư mục của ứng dụng khi chạy lần đầu. Bạn có thể chỉnh sửa trực tiếp các thông số trong tệp này để thay đổi tốc độ đăng nhập:

```json
{
    "allow_ui_changes": false,
    "protected_windows": [],
    "speed_settings": {
        "focus_delay": 0.5,
        "key_delay": 0.1,
        "form_open_delay": 1.0,
        "field_delay": 0.2
    }
}
```

**Chú ý**: Giảm thời gian chờ sẽ giúp tăng tốc độ đăng nhập, nhưng quá ngắn có thể gây lỗi nếu máy tính chạy chậm. Hãy điều chỉnh sao cho phù hợp với hiệu năng máy tính của bạn.

### Bảo vệ giao diện

Sử dụng tập lệnh `protect_ui.bat` để quản lý tính năng bảo vệ giao diện:

```
protect_ui.bat start   : Bắt đầu bảo vệ giao diện
protect_ui.bat stop    : Tạm dừng bảo vệ giao diện
protect_ui.bat status  : Kiểm tra trạng thái hiện tại
protect_ui.bat protect : Bảo vệ tất cả cửa sổ MT4/MT5
protect_ui.bat list    : Hiển thị danh sách cửa sổ được bảo vệ
```

Hoặc bạn có thể sử dụng trực tiếp mô-đun `ui_protection.py` với các tham số tương ứng:

```
python ui_protection.py --allow      : Cho phép thay đổi giao diện
python ui_protection.py --disallow   : Cấm thay đổi giao diện
python ui_protection.py --protect    : Bảo vệ tất cả cửa sổ MT4/MT5
python ui_protection.py --unprotect  : Hủy bảo vệ tất cả cửa sổ
python ui_protection.py --list       : Hiển thị danh sách cửa sổ được bảo vệ
```

## Cách hoạt động của bảo vệ giao diện

Tính năng bảo vệ giao diện hoạt động bằng cách giám sát tất cả các cửa sổ MT4/MT5 đang chạy và ngăn chặn các thay đổi không mong muốn:

1. Khi kích hoạt, hệ thống sẽ liên tục kiểm tra các cửa sổ MT4/MT5 trong danh sách bảo vệ
2. Các thay đổi về style của cửa sổ được áp dụng để ngăn chặn việc:
   - Thay đổi kích thước (loại bỏ flag WS_THICKFRAME)
   - Di chuyển cửa sổ (thêm flag WS_EX_TOOLWINDOW)
3. Danh sách các cửa sổ được bảo vệ được lưu trong tệp cấu hình `mt_login_config.json`
4. Tính năng này chạy trong nền với `pythonw.exe` để không hiển thị cửa sổ console

## Lưu ý

- Khi sử dụng tính năng bảo vệ giao diện, có thể cần quyền quản trị để điều khiển các cửa sổ ứng dụng
- Nếu bạn cần tạm thời thay đổi giao diện, hãy sử dụng lệnh `protect_ui.bat stop` để tắt tính năng bảo vệ
- Sau khi hoàn tất thay đổi, bạn có thể bật lại bảo vệ bằng lệnh `protect_ui.bat start` 