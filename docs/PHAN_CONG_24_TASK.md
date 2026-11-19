# ĐỐI CHIẾU 24 TASK (cập nhật V14)

| ID | Nhiệm vụ | Vị trí / hướng dẫn |
|---|---|---|
| 1 | Repo và môi trường ảo | README (lệnh tạo venv, cài thư viện); repo Git cần nhóm tạo |
| 2 | main.py, database.py, CORS | backend/app/main.py, backend/app/core/database.py |
| 3 | Models User, Course và schema | backend/app/models/, backend/app/schemas/ |
| 4 | Models Schedule, Enrollment | backend/app/models/, backend/app/schemas/ |
| 5 | ERD & Use Case | docs/erd.puml, docs/use_case.puml |
| 6 | Sequence | docs/sequence.puml |
| 7 | POST /login | backend/app/routers/auth.py |
| 8 | GET /courses, is_full | backend/app/routers/courses.py |
| 9 | POST/GET schedules | backend/app/routers/schedules.py |
| 10 | check_conflict | backend/app/services/enrollment_service.py |
| 11 | POST /enrollments | backend/app/routers/enrollments.py, backend/app/services/enrollment_service.py |
| 12 | GET /enrollments/{student_id}/schedule | backend/app/routers/enrollments.py |
| 13 | Đăng nhập fetch API | frontend/pages/index.html, frontend/js/pages/login.js |
| 14 | Dashboard + sidebar | frontend/pages/dashboard.html, frontend/css/style.css |
| 15 | Bảng môn + nút đầy disabled | frontend/js/pages/dashboard.js: renderCourses, decideDialog (nút trong popup bị disable khi thiếu tiên quyết/trùng lịch; lớp đầy chuyển thành “Vào danh sách chờ”) |
| 16 | Tích hợp đăng ký và lỗi 400 | frontend/js/pages/dashboard.js: submitAction |
| 17 | Grid TKB | frontend/js/pages/dashboard.js: renderCalendar |
| 18 | CORS / debug | backend/app/main.py, README mục kiểm thử |
| 19 | Báo cáo chương 1, 2 | docs/BAO_CAO_GOI_Y.md (dàn ý, chưa phải báo cáo chính thức) |
| 20 | Báo cáo chương 3 | docs/BAO_CAO_GOI_Y.md + sơ đồ PlantUML |
| 21 | Báo cáo chương 4, 5 | docs/BAO_CAO_GOI_Y.md (ảnh demo cần tự chụp) |
| 22 | 10 slide | docs/SLIDE_10_TRANG.md (dàn ý, chưa phải PPTX) |
| 23 | Demo MySQL, 1 user, 5+ môn, 1 môn đầy | backend/scripts/seed_demo.py |
| 24 | Video backup | docs/BAO_CAO_GOI_Y.md (quay bằng OBS/CapCut tại máy) |

**Lưu ý kiến trúc**: đề mô tả các service theo chức năng và một API Gateway. Bản chạy localhost là **monolith module hóa theo service routers** để nhóm dễ demo; không tự nhận là hệ thống microservices triển khai độc lập.

## Chức năng nâng cao (V14)

| Chức năng | Vị trí |
|---|---|
| Quản lý học phần, sĩ số tối đa | backend/app/routers/admin_courses.py, backend/app/services/course_service.py, frontend/js/pages/admin.js |
| Quản lý lịch học, chặn trùng phòng / trùng TKB | backend/app/routers/schedules.py, backend/app/services/schedule_service.py |
| Môn tiên quyết (đa tiên quyết, chặn vòng lặp) | backend/app/models/course.py, course_service.set_prerequisites, enrollment_service.eligibility_problem |
| Học phần đã hoàn thành (Admin ghi nhận) | backend/app/models/completed_course.py, backend/app/routers/admin_users.py |
| Danh sách chờ + tự xếp lớp | backend/app/models/waitlist.py, backend/app/routers/waitlist.py, enrollment_service.promote_from_waitlist |
| Hủy học phần | backend/app/routers/enrollments.py (cancel), enrollment_service.cancel_enrollment |
| Kiểm thử tự động | backend/tests/ |
