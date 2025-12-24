# ⚡ JARVIS Quick Start Guide

Hướng dẫn nhanh để chạy JARVIS trong 5 phút!

---

## 🚀 Bước 1: Cài Đặt Dependencies

```bash
# Mở Command Prompt hoặc PowerShell
cd /path/to/JARVIS

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

**Lưu ý**: Nếu bạn muốn sử dụng AI thật (OpenAI/Anthropic), cài thêm:

```bash
# Cho OpenAI
pip install openai>=1.0.0

# Hoặc cho Anthropic Claude
pip install anthropic>=0.8.0
```

---

## 🎮 Bước 2: Chạy Ứng Dụng

### Chế Độ Mock (Không Cần API Key)

```bash
python mt_login_gui.py
```

**Mock mode** sử dụng AI giả lập (rule-based), hoàn toàn miễn phí, phù hợp để:
- Học cách sử dụng
- Demo
- Testing

### Chế Độ AI Thật (OpenAI/Anthropic)

**Bước 2.1**: Chỉnh sửa `config/ai_config.json`:

```json
{
  "ai_provider": "openai",  // hoặc "anthropic"

  "openai": {
    "api_key": "sk-YOUR-REAL-API-KEY-HERE",
    "model": "gpt-3.5-turbo"
  }
}
```

**Bước 2.2**: Chạy ứng dụng:

```bash
python mt_login_gui.py
```

---

## 💬 Bước 3: Thử Nghiệm Chat AI

Sau khi ứng dụng mở, bạn sẽ thấy:
- **Bên trái**: Bảng quản lý tài khoản
- **Bên phải**: Chat box AI

### Ví Dụ Lệnh:

**Lệnh 1: Xem danh sách tài khoản**
```
Cho tôi xem danh sách tài khoản
```

**Lệnh 2: Quét terminal đang chạy**
```
Quét các terminal MT4/MT5 đang chạy
```

**Lệnh 3: Đăng nhập tài khoản (ví dụ đầy đủ)**
```
Đăng nhập tài khoản Exness MT5 login 12345678 pass Abc123 server Exness-MT5Live
```

**Lệnh 4: Đăng nhập (từng bước)**
```
User: Đăng nhập tài khoản Exness MT5 login 12345678
AI: Vui lòng cung cấp thêm: password và server
User: Pass là Abc123, server Exness-MT5Live
AI: [Trả về command để thực thi]
```

---

## 📋 Bước 4: Xem Command Preview

Sau khi AI phân tích xong, bạn sẽ thấy:

1. **Chat Display**: AI response
2. **Command Preview Panel**: JSON command
3. **Execute Button**: Nút thực thi (sáng lên nếu command hợp lệ)

Ví dụ JSON command:

```json
{
  "action": "LOGIN_ACCOUNT",
  "platform": "MT5",
  "broker": "Exness",
  "login": "12345678",
  "password": "Abc123",
  "server": "Exness-MT5Live",
  "confidence": 0.98,
  "reason": "User provided complete info",
  "requires_confirmation": true
}
```

---

## ✅ Bước 5: Thực Thi Command

1. Kiểm tra JSON command trong preview panel
2. Nhấn nút **"▶ Execute Command"**
3. Xác nhận trong popup (nếu command yêu cầu)
4. Xem kết quả trong chat

---

## 🔧 Troubleshooting

### Lỗi 1: "Module not found"

```bash
pip install -r requirements.txt
```

### Lỗi 2: "API key not configured"

Kiểm tra file `config/ai_config.json`, đảm bảo API key đúng.

### Lỗi 3: "Không tìm thấy cửa sổ MT4/MT5"

- Mở MT4/MT5 terminal trước
- Đảm bảo tên broker trong lệnh khớp với tiêu đề cửa sổ
- Ví dụ: Nếu cửa sổ là "Exness-Live", dùng "Exness" trong lệnh

### Lỗi 4: PyQt5 không chạy được

Trên một số hệ thống Windows, cần cài Visual C++ Redistributable:
https://aka.ms/vs/17/release/vc_redist.x64.exe

---

## 📚 Tài Liệu Đầy Đủ

- **README_AI_INTEGRATION.md**: Hướng dẫn chi tiết
- **DEVELOPER_GUIDE.md**: Dành cho developers
- **config/ai_config.json**: Cấu hình AI và automation

---

## 🎯 Tips & Tricks

### Tip 1: Sử dụng Mock Mode để học

Mock mode không cần API key, phù hợp để:
- Hiểu cách hệ thống hoạt động
- Test giao diện
- Demo cho người khác

### Tip 2: Lưu tài khoản thường dùng

Sau khi đăng nhập thành công 1 lần, tài khoản tự động lưu vào `config/accounts.json`. Lần sau chỉ cần gõ:
```
Đăng nhập tài khoản Exness
```

AI sẽ nhớ thông tin (trừ password vì bảo mật).

### Tip 3: Dùng tiếng Việt hoặc English đều được

```
User: Login Exness MT5 12345678
AI: [Works!]

User: Đăng nhập Exness MT5 12345678
AI: [Cũng works!]
```

### Tip 4: Kiểm tra Command Preview trước khi Execute

Luôn xem JSON command trong preview panel để đảm bảo AI hiểu đúng ý bạn.

---

## 🚧 Giới Hạn Hiện Tại

1. **Chỉ chạy trên Windows**: Do sử dụng pywinauto cho UI automation
2. **Cần MT4/MT5 đang mở**: Không thể tự động mở terminal
3. **Mock mode giới hạn**: Chỉ nhận diện các pattern cơ bản

---

## 🎉 Xong!

Bây giờ bạn đã sẵn sàng sử dụng JARVIS!

Nếu có vấn đề, xem:
- **README_AI_INTEGRATION.md** để biết thêm chi tiết
- **DEVELOPER_GUIDE.md** nếu muốn customize

**Enjoy! 🚀**
