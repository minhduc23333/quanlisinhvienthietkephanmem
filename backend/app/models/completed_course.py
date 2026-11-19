from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, text

from app.core.database import Base


class CompletedCourse(Base):
    """Học phần sinh viên đã hoàn thành (do Admin ghi nhận). Dùng để xét môn tiên quyết."""
    __tablename__ = 'completed_courses'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False, index=True)
    completed_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    __table_args__ = (UniqueConstraint('student_id', 'course_id', name='uq_completed_student_course'),)
