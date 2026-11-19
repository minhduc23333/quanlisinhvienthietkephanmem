-- EduCourse V14: các bảng mới cho môn tiên quyết, danh sách chờ, học phần đã hoàn thành.
-- KHÔNG bắt buộc: backend tự tạo các bảng này khi khởi động (Base.metadata.create_all).
-- Chỉ chạy file này nếu bạn muốn tạo thủ công trong MySQL Workbench. Chạy lại nhiều lần vẫn an toàn.
USE quanlihoc;

CREATE TABLE IF NOT EXISTS course_prerequisites (
	course_id INTEGER NOT NULL,
	prerequisite_id INTEGER NOT NULL,
	PRIMARY KEY (course_id, prerequisite_id),
	FOREIGN KEY(course_id) REFERENCES courses (id),
	FOREIGN KEY(prerequisite_id) REFERENCES courses (id)
);

CREATE TABLE IF NOT EXISTS waitlist (
	id INTEGER NOT NULL AUTO_INCREMENT,
	student_id INTEGER NOT NULL,
	course_id INTEGER NOT NULL,
	created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	INDEX ix_waitlist_course_id (course_id),
	INDEX ix_waitlist_student_id (student_id),
	CONSTRAINT uq_waitlist_student_course UNIQUE (student_id, course_id),
	FOREIGN KEY(student_id) REFERENCES users (id),
	FOREIGN KEY(course_id) REFERENCES courses (id)
);

CREATE TABLE IF NOT EXISTS completed_courses (
	id INTEGER NOT NULL AUTO_INCREMENT,
	student_id INTEGER NOT NULL,
	course_id INTEGER NOT NULL,
	completed_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY (id),
	INDEX ix_completed_courses_course_id (course_id),
	INDEX ix_completed_courses_student_id (student_id),
	CONSTRAINT uq_completed_student_course UNIQUE (student_id, course_id),
	FOREIGN KEY(student_id) REFERENCES users (id),
	FOREIGN KEY(course_id) REFERENCES courses (id)
);
