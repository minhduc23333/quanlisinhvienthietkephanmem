from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, CheckConstraint, Boolean
from sqlalchemy.orm import relationship
from database import Base
class User(Base):
    __tablename__='users'
    id=Column(Integer,primary_key=True)
    name=Column(String(120),nullable=False)
    role=Column(String(20),nullable=False,default='student')
    username=Column(String(80),unique=True,nullable=False,index=True)
    email=Column(String(254),unique=True,nullable=True,index=True)
    password_hash=Column(String(255),nullable=False)
    is_locked=Column(Boolean,nullable=False,default=False,server_default='0')
    enrollments=relationship('Enrollment',back_populates='student')
class Course(Base):
    __tablename__='courses'
    id=Column(Integer,primary_key=True)
    code=Column(String(20),nullable=False,unique=True)
    name=Column(String(160),nullable=False)
    lecturer=Column(String(140),nullable=True)
    start_date=Column(String(10),nullable=True)
    end_date=Column(String(10),nullable=True)
    max_students=Column(Integer,nullable=False)
    current_enrolled=Column(Integer,nullable=False,default=0)
    __table_args__=(CheckConstraint('max_students > 0'),CheckConstraint('current_enrolled >= 0'))
    schedules=relationship('Schedule',back_populates='course',cascade='all,delete-orphan')
    enrollments=relationship('Enrollment',back_populates='course')
class Schedule(Base):
    __tablename__='schedules'
    id=Column(Integer,primary_key=True)
    course_id=Column(Integer,ForeignKey('courses.id'),nullable=False,index=True)
    day=Column(Integer,nullable=False)
    shift=Column(String(20),nullable=False)
    start_time=Column(String(5),nullable=True)
    end_time=Column(String(5),nullable=True)
    room=Column(String(50),nullable=True)
    __table_args__=(UniqueConstraint('course_id','day','shift',name='uq_schedule'),CheckConstraint('day BETWEEN 2 AND 7'))
    course=relationship('Course',back_populates='schedules')
class Enrollment(Base):
    __tablename__='enrollments'
    id=Column(Integer,primary_key=True)
    student_id=Column(Integer,ForeignKey('users.id'),nullable=False,index=True)
    course_id=Column(Integer,ForeignKey('courses.id'),nullable=False,index=True)
    __table_args__=(UniqueConstraint('student_id','course_id',name='uq_student_course'),)
    student=relationship('User',back_populates='enrollments')
    course=relationship('Course',back_populates='enrollments')
