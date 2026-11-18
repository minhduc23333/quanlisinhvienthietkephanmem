# ĐỐI CHIẾU 24 TASK V4

| ID | Nhiệm vụ | Vị trí / hướng dẫn |
|---|---|---|
| 1 | Repo và môi trường ảo | README (lệnh tạo venv, cài thư viện); repo Git cần nhóm tạo |
| 2 | main.py, database.py, CORS | backend/main.py, backend/database.py |
| 3 | Models User, Course và schema | backend/models.py, backend/schemas.py |
| 4 | Models Schedule, Enrollment | backend/models.py, backend/schemas.py |
| 5 | ERD & Use Case | docs/erd.puml, docs/use_case.puml |
| 6 | Sequence | docs/sequence.puml |
| 7 | POST /login | backend/routers/auth.py |
| 8 | GET /courses, is_full | backend/routers/courses.py |
| 9 | POST/GET schedules | backend/routers/schedules.py |
| 10 | check_conflict | backend/routers/enrollments.py |
| 11 | POST /enrollments | backend/routers/enrollments.py |
| 12 | GET /enrollments/{student_id}/schedule | backend/routers/enrollments.py |
| 13 | Đăng nhập fetch API | frontend/index.html, frontend/login.js |
| 14 | Dashboard + sidebar | frontend/dashboard.html, frontend/style.css |
| 15 | Bảng môn + nút đầy disabled | frontend/dashboard.js: renderCourses (nút đăng ký bên trong popup bị disable, nút xem chi tiết vẫn mở để xem lịch) |
| 16 | Tích hợp đăng ký và lỗi 400 | frontend/dashboard.js: enroll |
| 17 | Grid TKB | frontend/dashboard.js: renderCalendar |
| 18 | CORS / debug | backend/main.py, README mục kiểm thử |
| 19 | Báo cáo chương 1, 2 | docs/BAO_CAO_GOI_Y.md (dàn ý, chưa phải báo cáo chính thức) |
| 20 | Báo cáo chương 3 | docs/BAO_CAO_GOI_Y.md + sơ đồ PlantUML |
| 21 | Báo cáo chương 4, 5 | docs/BAO_CAO_GOI_Y.md (ảnh demo cần tự chụp) |
| 22 | 10 slide | docs/SLIDE_10_TRANG.md (dàn ý, chưa phải PPTX) |
| 23 | Demo MySQL, 1 user, 5+ môn, 1 môn đầy | backend/seed_demo.py |
| 24 | Video backup | docs/BAO_CAO_GOI_Y.md (quay bằng OBS/CapCut tại máy) |

**Lưu ý kiến trúc**: đề mô tả các service theo chức năng và một API Gateway. Bản chạy localhost là **monolith module hóa theo service routers** để nhóm dễ demo; không tự nhận là hệ thống microservices triển khai độc lập.
