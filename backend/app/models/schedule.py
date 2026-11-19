from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class Schedule(Base):
    __tablename__ = 'schedules'
    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey('courses.id'), nullable=False, index=True)
    day = Column(Integer, nullable=False)
    shift = Column(String(20), nullable=False)
    start_time = Column(String(5), nullable=True)
    end_time = Column(String(5), nullable=True)
    room = Column(String(50), nullable=True)
    __table_args__ = (UniqueConstraint('course_id', 'day', 'shift', name='uq_schedule'), CheckConstraint('day BETWEEN 2 AND 7'))
    course = relationship('Course', back_populates='schedules')
