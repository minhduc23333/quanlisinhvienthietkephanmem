from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.session_auth import student_only
from app.models import Course, CompletedCourse, Enrollment, Schedule, User
from app.schemas import EnrollmentCreate
from app.services import enrollment_service as svc

router = APIRouter(tags=['Enrollment Service'])


def _own_only(student: User, student_id: int, message: str) -> None:
    if student.id != student_id:
        raise HTTPException(403, message)


@router.post('/enrollments', status_code=201)
def enroll(body: EnrollmentCreate, db: Session = Depends(get_db), student: User = Depends(student_only)):
    _own_only(student, body.student_id, 'Không thể đăng ký hộ tài khoản khác')
    course = svc.enroll(db, student, body.course_id)
    return {'message': 'Đăng ký học phần thành công', 'student_id': student.id, 'course_id': course.id}


@router.get('/enrollments/{student_id}/schedule')
def timetable(student_id: int, db: Session = Depends(get_db), student: User = Depends(student_only)):
    _own_only(student, student_id, 'Không có quyền xem lịch của tài khoản khác')
    rows = db.execute(select(Enrollment.id, Course.id, Course.code, Course.name, Schedule.day, Schedule.shift,
                             Schedule.start_time, Schedule.end_time, Schedule.room, Course.lecturer)
                      .join(Course, Enrollment.course_id == Course.id).join(Schedule, Schedule.course_id == Course.id)
                      .where(Enrollment.student_id == student.id).order_by(Schedule.day, Schedule.shift)).all()
    return [{'enrollment_id': e, 'course_id': cid, 'code': code, 'course_name': name, 'day': day, 'shift': shift,
             'start_time': start_time or ('07:00' if shift == 'sang' else '13:00'),
             'end_time': end_time or ('11:00' if shift == 'sang' else '17:00'),
             'room': room or 'Đang cập nhật', 'lecturer': lecturer or 'Chưa phân công'}
            for e, cid, code, name, day, shift, start_time, end_time, room, lecturer in rows]


@router.get('/enrollments/{student_id}')
def own(student_id: int, db: Session = Depends(get_db), student: User = Depends(student_only)):
    _own_only(student, student_id, 'Không có quyền xem dữ liệu của tài khoản khác')
    rows = db.execute(select(Enrollment.id, Course.id, Course.code, Course.name).join(Course)
                      .where(Enrollment.student_id == student.id)).all()
    return [{'id': e, 'course_id': cid, 'code': code, 'name': name} for e, cid, code, name in rows]


@router.delete('/enrollments/{student_id}/{course_id}')
def cancel(student_id: int, course_id: int, db: Session = Depends(get_db), student: User = Depends(student_only)):
    _own_only(student, student_id, 'Không thể hủy đăng ký của tài khoản khác')
    promoted = svc.cancel_enrollment(db, student.id, course_id)
    return {'message': 'Đã hủy đăng ký học phần', 'promoted_from_waitlist': len(promoted)}


@router.get('/students/{student_id}/completed')
def completed(student_id: int, db: Session = Depends(get_db), student: User = Depends(student_only)):
    _own_only(student, student_id, 'Không có quyền xem dữ liệu của tài khoản khác')
    rows = db.execute(select(Course.id, Course.code, Course.name, CompletedCourse.completed_at)
                      .join(CompletedCourse, CompletedCourse.course_id == Course.id)
                      .where(CompletedCourse.student_id == student.id).order_by(Course.code)).all()
    return [{'course_id': cid, 'code': code, 'name': name,
             'completed_at': at.isoformat() if at else None} for cid, code, name, at in rows]
