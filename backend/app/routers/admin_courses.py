from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.session_auth import admin_only
from app.models import Course, User, WaitlistEntry
from app.schemas import CourseCreate, CourseOut, CourseUpdate
from app.services import enrollment_service as svc
from app.services.course_service import (build_course_out, delete_course, get_course_or_404, lock_course,
                                         set_prerequisites)

router = APIRouter(prefix='/admin', tags=['Admin Service - Courses'])


def _normalize_code(code: str) -> str:
    code = code.strip().upper()
    if not code:
        raise HTTPException(400, 'Mã học phần không được để trống')
    return code


def _one(db: Session, course: Course, admin: User) -> CourseOut:
    return build_course_out(db, [course], admin)[0]


@router.post('/courses', response_model=CourseOut, status_code=201)
def create_course(body: CourseCreate, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    code = _normalize_code(body.code)
    if db.scalar(select(Course.id).where(Course.code == code)):
        raise HTTPException(409, f'Mã học phần {code} đã tồn tại')
    course = Course(code=code, name=body.name.strip(), lecturer=(body.lecturer or '').strip() or None,
                    start_date=body.start_date, end_date=body.end_date, max_students=body.max_students,
                    current_enrolled=0)
    set_prerequisites(db, course, body.prerequisite_ids)
    db.add(course)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, f'Mã học phần {code} đã tồn tại')
    db.refresh(course)
    return _one(db, course, admin)


@router.patch('/courses/{course_id}', response_model=CourseOut)
def update_course(course_id: int, body: CourseUpdate, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    course = lock_course(db, course_id)
    data = body.model_dump(exclude_unset=True)
    if data.get('code') is not None:
        code = _normalize_code(data['code'])
        if db.scalar(select(Course.id).where(Course.code == code, Course.id != course.id)):
            raise HTTPException(409, f'Mã học phần {code} đã tồn tại')
        course.code = code
    if data.get('name') is not None:
        course.name = data['name'].strip()
    if 'lecturer' in data:
        course.lecturer = (data['lecturer'] or '').strip() or None
    new_start = data.get('start_date', course.start_date)
    new_end = data.get('end_date', course.end_date)
    if new_start and new_end and new_start > new_end:
        raise HTTPException(422, 'Ngày kết thúc phải sau ngày bắt đầu')
    course.start_date, course.end_date = new_start, new_end
    capacity_grew = False
    if data.get('max_students') is not None:
        if data['max_students'] < course.current_enrolled:
            raise HTTPException(400, f'Sĩ số tối đa không thể nhỏ hơn số sinh viên đã đăng ký ({course.current_enrolled})')
        capacity_grew = data['max_students'] > course.max_students
        course.max_students = data['max_students']
    if data.get('prerequisite_ids') is not None:
        set_prerequisites(db, course, data['prerequisite_ids'])
    db.flush()
    if capacity_grew:
        svc.promote_from_waitlist(db, course)  # tăng sĩ số thì xếp người đang chờ vào chỗ mới
    db.commit()
    db.refresh(course)
    return _one(db, course, admin)


@router.delete('/courses/{course_id}')
def remove_course(course_id: int, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    course = lock_course(db, course_id)
    delete_course(db, course)
    db.commit()
    return {'message': 'Đã xóa học phần'}


@router.get('/courses/{course_id}/waitlist')
def course_waitlist(course_id: int, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    get_course_or_404(db, course_id)
    rows = db.execute(select(WaitlistEntry.id, User.id, User.name, User.email, WaitlistEntry.created_at)
                      .join(User, User.id == WaitlistEntry.student_id)
                      .where(WaitlistEntry.course_id == course_id).order_by(WaitlistEntry.id)).all()
    return [{'position': i, 'student_id': uid, 'name': name, 'email': email,
             'joined_at': at.isoformat() if at else None} for i, (_, uid, name, email, at) in enumerate(rows, start=1)]
