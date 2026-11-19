from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship

from app.core.database import Base

# Môn tiên quyết: (course_id) chỉ được đăng ký khi sinh viên đã hoàn thành (prerequisite_id).
# Không đặt CHECK/ON DELETE trên bảng này: MySQL cấm dùng chung hai thứ trên cùng một cột FK.
# Việc chặn tự tham chiếu và vòng lặp được kiểm tra ở services/course_service.py.
course_prerequisites = Table(
    'course_prerequisites', Base.metadata,
    Column('course_id', Integer, ForeignKey('courses.id'), primary_key=True),
    Column('prerequisite_id', Integer, ForeignKey('courses.id'), primary_key=True),
)


class Course(Base):
    __tablename__ = 'courses'
    id = Column(Integer, primary_key=True)
    code = Column(String(20), nullable=False, unique=True)
    name = Column(String(160), nullable=False)
    lecturer = Column(String(140), nullable=True)
    start_date = Column(String(10), nullable=True)
    end_date = Column(String(10), nullable=True)
    max_students = Column(Integer, nullable=False)
    current_enrolled = Column(Integer, nullable=False, default=0)
    __table_args__ = (CheckConstraint('max_students > 0'), CheckConstraint('current_enrolled >= 0'))
    schedules = relationship('Schedule', back_populates='course', cascade='all,delete-orphan')
    enrollments = relationship('Enrollment', back_populates='course')
    prerequisites = relationship(
        'Course', secondary=course_prerequisites,
        primaryjoin=id == course_prerequisites.c.course_id,
        secondaryjoin=id == course_prerequisites.c.prerequisite_id,
        backref='required_by',
    )
