# EduCourse V13 — Hệ thống đăng ký học phần (Đề tài 09, Nhóm 6)

Hướng dẫn cài đặt và chạy **từ đầu** trên **Windows, VS Code, Python FastAPI và MySQL Server**. Không cần XAMPP, Live Server hay React.

## 1. Chức năng

- **Sinh viên:** Đăng ký tài khoản bằng email, đăng nhập/đăng xuất, hiện/ẩn mật khẩu bằng nút con mắt; xem danh sách và chi tiết học phần (giảng viên, thời gian, phòng, sĩ số); đăng ký/hủy học phần; kiểm tra lớp đầy/trùng lịch; xem thời khóa biểu cá nhân.
- **Quản trị viên (Admin):** Đăng nhập tài khoản cố định được tạo qua Python Backend; xem, khóa/mở khóa, xóa tài khoản sinh viên và xem danh sách học phần.
- **Thông báo V13:** Thành công màu xanh, thất bại màu đỏ; tiêu đề nói rõ hành động, ví dụ **“Đăng ký học phần thành công”**, không hiện tiêu đề chung “Thao tác thành công”.

## 2. Chuẩn bị

1. Cài **Python** (khuyến nghị Python 3.11–3.13) và **VS Code**.
2. Cài và **khởi động MySQL Server**. **MySQL Workbench** chỉ dùng để kết nối/quản lý server, tự nó không thay thế MySQL Server.
3. Giải nén gói EduCourse V13, dùng **File → Open Folder** trong VS Code để mở thư mục dự án, thư mục có `backend`, `frontend`, `README.md`.

## 3. Tạo database trong MySQL Workbench

Mở Workbench, kết nối MySQL Server, mở SQL Editor, chạy:

```sql
CREATE DATABASE IF NOT EXISTS quanlihoc
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;
```

**Nếu đã có `quanlihoc`, không xóa database**: các tài khoản và lượt đăng ký cũ sẽ bị mất nếu xóa.

## 4. Tạo môi trường Python và cài thư viện

Trong VS Code, chọn **Terminal → New Terminal** tại thư mục gốc của dự án, chạy từng dòng:

```powershell
cd backend
py -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Dùng đường dẫn `venv\Scripts\python.exe` giúp tránh lỗi cài thư viện vào nhầm Python. File `requirements.txt` đã có `itsdangerous` cho chức năng phiên đăng nhập.

## 5. Cấu hình kết nối MySQL

Vẫn tại `backend`, tạo `.env` từ file mẫu (chỉ tạo lần đầu):

```powershell
Copy-Item .env.example .env
```

Mở `backend/.env` và sửa đúng thông tin trên máy:

```dotenv
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=MAT_KHAU_MYSQL_CUA_BAN
DB_NAME=quanlihoc
SESSION_SECRET=THAY_BANG_CHUOI_BI_MAT_NGAU_NHIEN
```

Tạo giá trị `SESSION_SECRET` bằng:

```powershell
.\venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Dán chuỗi vừa nhận được vào `SESSION_SECRET`. **Không đưa file `.env` lên GitHub** và không chia sẻ mật khẩu MySQL.

> Tài khoản Admin của bản này **không cấu hình trong `.env`**. Các thông số demo nằm trong `backend/admin_settings.py` và được đồng bộ vào database bằng `setup_admin.py`.

## 6. Khởi tạo dữ liệu và Admin — chỉ lần đầu

### Trường hợp A: Database mới hoàn toàn (trống)

Trong terminal **đang ở thư mục `backend`**, chạy lần lượt:

```powershell
.\venv\Scripts\python.exe seed_demo.py
.\venv\Scripts\python.exe setup_admin.py
```

`seed_demo.py` tạo các bảng và dữ liệu môn học mẫu; `setup_admin.py` tạo hoặc đồng bộ tài khoản quản trị và mở khóa nếu trước đó bị khóa.

### Trường hợp B: Nâng cấp từ EduCourse V4/V5/V6 (có dữ liệu cũ)

**Sao lưu database trước khi nâng cấp.** Chỉ chạy những migration chưa được áp dụng, theo đúng thứ tự:

```powershell
.\venv\Scripts\python.exe migrate_v5.py
.\venv\Scripts\python.exe migrate_v6.py
.\venv\Scripts\python.exe migrate_v7.py
.\venv\Scripts\python.exe seed_demo.py
.\venv\Scripts\python.exe setup_admin.py
```

Không chạy lại migration đã thành công nếu script không hỗ trợ chạy lặp. Với database đã dùng V7–V13, thông thường chỉ cần `setup_admin.py` nếu muốn đồng bộ lại Admin; **không cần migration lại**.

## 7. Chạy website trên localhost

Trong terminal `backend`, chạy:

```powershell
.\venv\Scripts\python.exe run.py
```

Khi hiển thị `Application startup complete` thì mở trình duyệt:

| Trang | Địa chỉ |
| --- | --- |
| Trang đăng nhập/đăng ký | http://127.0.0.1:8000/ |
| Dashboard sinh viên | http://127.0.0.1:8000/dashboard |
| Quản trị Admin | http://127.0.0.1:8000/admin |
| Tài liệu kiểm thử API | http://127.0.0.1:8000/docs |

Giữ terminal đang chạy; nhấn **Ctrl + C** để dừng server. Sau cập nhật Frontend, nhấn **Ctrl + F5** trên trình duyệt.

## 8. Tài khoản Admin và tài khoản sinh viên

Tài khoản **Admin demo** sau khi chạy `setup_admin.py`:

- **Email:** `admin@gmail.com`
- **Tên đăng nhập thay thế:** `admin`
- **Mật khẩu demo:** `Admin@2026Demo!`

Các giá trị ở `backend/admin_settings.py`. Nếu đổi mật khẩu trong file đó, chạy lại `setup_admin.py` để **cập nhật mật khẩu trong MySQL**. Không đặt mật khẩu Admin vào JavaScript Frontend. Mật khẩu demo cần thay trước khi đưa website lên Internet.

**Sinh viên:** Chọn tab **Đăng ký**, nhập họ tên, email, mật khẩu và xác nhận; tài khoản mới sẽ được lưu trong MySQL. Bản demo không gửi email xác minh hoặc OTP.

## 9. Kiểm tra dữ liệu bằng Workbench

```sql
USE quanlihoc;
SELECT id, name, username, email, role, is_locked FROM users;
SELECT * FROM courses;
SELECT * FROM schedules;
SELECT * FROM enrollments;
```

Dữ liệu lịch/giảng viên/phòng trong `seed_demo.py` là **mẫu phục vụ đồ án**, không phải thời khóa biểu chính thức.

## 10. Những lần chạy tiếp theo (rất ngắn)

Bảo đảm **MySQL Server đang chạy**. Mở VS Code tại thư mục dự án, mở Terminal:

```powershell
cd backend
.\venv\Scripts\python.exe run.py
```

**Không cần** cài lại thư viện, tạo lại database, chạy seed hay reset Admin mỗi lần.

## 11. Lỗi thường gặp

| Hiện tượng | Cách kiểm tra / xử lý |
| --- | --- |
| `ModuleNotFoundError: No module named 'itsdangerous'` | Chạy `.\venv\Scripts\python.exe -m pip install -r requirements.txt` khi ở `backend`. |
| `Access denied for user 'root'` | Kiểm tra `DB_USER`, `DB_PASSWORD` trong `.env` và xác nhận Workbench đăng nhập được cùng tài khoản. |
| `Can't connect to MySQL server` | Bật MySQL Server, kiểm tra `DB_HOST`, `DB_PORT` (thường là `127.0.0.1:3306`). |
| Admin đăng nhập lỗi **401** | Kiểm tra `backend/admin_settings.py`, chạy `.\venv\Scripts\python.exe setup_admin.py`, sau đó thử lại email/mật khẩu. |
| Trình duyệt vẫn hiện giao diện/thông báo cũ | Nhấn **Ctrl + F5** và bảo đảm bạn đang chạy đúng thư mục dự án mới. |
| Port 8000 đang được dùng | Dừng tiến trình Uvicorn đang chạy (`Ctrl + C` ở terminal cũ) rồi chạy lại. |
| Lỗi `Unknown column` khi dùng database từ bản cũ | Sao lưu DB; xác định migration V5/V6/V7 nào chưa chạy rồi áp dụng đúng thứ tự. |

## 12. Cấu trúc dự án chính

```text
EduCourse_V13_ThongBao_DungTen_MySQL/
├── backend/
│   ├── main.py                 # FastAPI, API router, trang web
│   ├── database.py             # Kết nối MySQL
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic schemas
│   ├── admin_settings.py       # Tài khoản Admin demo
│   ├── setup_admin.py          # Tạo/đồng bộ Admin trong MySQL
│   ├── seed_demo.py            # Dữ liệu mẫu
│   ├── migrate_v5.py
│   ├── migrate_v6.py
│   ├── migrate_v7.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── run.py
│   └── routers/
├── frontend/
│   ├── index.html
│   ├── dashboard.html
│   ├── admin.html
│   ├── login.js
│   ├── dashboard.js
│   ├── admin.js
│   ├── toast.js
│   ├── confirm-ui.js
│   └── style.css
├── docs/                      # UML, phân công, dàn ý báo cáo/slide
├── database.sql
└── README.md
```

### Ghi chú phạm vi

Đây là đồ án chạy trên máy cá nhân. Các Student/Course/Schedule/Enrollment API được chia theo **router FastAPI trong cùng một ứng dụng**, chưa triển khai thành các microservice độc lập. Trước khi đưa lên Internet cần thay mật khẩu demo và bổ sung cấu hình triển khai/bảo mật phù hợp.
