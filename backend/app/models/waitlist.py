from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint, text

from app.core.database import Base


class WaitlistEntry(Base):
    """Sinh viên xếp hàng chờ một học phần đã đầy. Thứ tự hàng chờ = thứ tự `id` tăng dần (FIFO)."""
    __tablename__ = 'waitlist'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    __table_args__ = (UniqueConstraint('student_id', 'course_id', name='uq_waitlist_student_course'),)
