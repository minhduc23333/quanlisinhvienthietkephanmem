# GỢI Ý NỘI DUNG BÁO CÁO (TASK 19–21)

## Chương 1. Giới thiệu và cơ sở lý thuyết
- Nhu cầu đăng ký học phần, tránh trùng thời khóa biểu và quản lý sĩ số.
- Kiến trúc SOA: phân chia chức năng theo service và giao tiếp bằng API.
- Microservices: mô hình triển khai độc lập, có thể áp dụng khi phát triển dự án rộng hơn.

## Chương 2. Công nghệ
- FastAPI (Python): xây dựng REST API; Uvicorn: web server.
- SQLAlchemy: ORM; MySQL: lưu dữ liệu quan hệ; MySQL Workbench: quản trị DB.
- HTML/CSS/JavaScript thuần: frontend; fetch để gọi API.
- *Nếu giảng viên bắt buộc React*: đề phân công có nhắc React ở phần báo cáo nhưng prompt lập trình UI yêu cầu HTML/JS; bản này triển khai HTML/CSS/JS thuần. Không trình bày React như công nghệ đã dùng.

## Chương 3. Phân tích và thiết kế
- Vẽ `erd.puml`, `use_case.puml`, `sequence.puml` bằng PlantUML, chụp hoặc xuất PNG và chèn vào báo cáo.
- Bảy bảng: User, Course, Schedule, Enrollment (lõi) và CoursePrerequisite, WaitlistEntry, CompletedCourse (nâng cao V14); xem `docs/erd.puml`.
- API: POST /login, POST /register, GET /courses, POST /schedules, GET /schedules/{course_id}, POST /enrollments, GET /enrollments/{student_id}/schedule.
- Kiểm tra trùng lịch dựa trên cặp (day, shift); lớp đầy nếu current_enrolled >= max_students.
- Điều kiện đăng ký (theo thứ tự): chưa đăng ký, chưa hoàn thành, đã hoàn thành mọi môn tiên quyết, không trùng (day, shift), còn chỗ. Lớp đầy → vào danh sách chờ; có chỗ trống → tự xếp người chờ đủ điều kiện (FIFO). Dùng khóa dòng học phần (SELECT ... FOR UPDATE) và mức cô lập READ COMMITTED để tránh vượt sĩ số khi đăng ký/hủy đồng thời.
- API bổ sung V14: xem README mục “API bổ sung ở V14”.

## Chương 4. Kết quả và kiểm thử
1. Chụp giao diện Login sau khi mở localhost.
2. Chụp Dashboard và bảng môn học.
3. Chụp popup xem lịch môn và lịch theo tuần.
4. Đăng ký môn HP001, sau đó thử HP006: phải lỗi trùng lịch nếu đã học HP001; thử HP006 ngay từ tài khoản mới sẽ báo lớp đầy.
4b. Kiểm thử nâng cao: kịch bản demo tiên quyết / danh sách chờ trong README mục 10b; `python -m pytest -q` chạy 26 test tự động.
5. Kiểm tra MySQL Workbench: `SELECT * FROM users;`, `SELECT * FROM courses;`, `SELECT * FROM enrollments;`.
6. Chụp Developer Tools (F12) hoặc Swagger khi cần minh họa HTTP 400.

## Chương 5. Kết luận
- Hoàn thành quản lý học phần, đăng ký, kiểm tra sĩ số, trùng lịch và xem thời khóa biểu.
- Giới hạn bản demo: login đơn giản không JWT/session xác thực phía server, gateway là FastAPI ứng dụng đơn chứ chưa phải gateway/service deploy độc lập.
- Hướng phát triển: phân quyền, xác thực JWT, giảng viên, quản trị, lịch theo tiết/giờ, triển khai các service riêng.

## Task 24: Quay dự phòng
- Mở OBS hoặc CapCut, quay theo thứ tự: đăng nhập → danh sách môn → xem lịch → đăng ký → lịch cá nhân → thử môn đầy/trùng lịch.
- Đây là đầu việc nhóm phải thao tác tại máy thật, không thể thay bằng file code.
