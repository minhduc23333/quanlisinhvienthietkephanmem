from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class Enrollment(Base):
    __tablename__ = 'enrollments'
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False, index=True)
    __table_args__ = (UniqueConstraint('student_id', 'course_id', name='uq_student_course'),)
    student = relationship('User', back_populates='enrollments')
    course = relationship('Course', back_populates='enrollments')
