from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.database import get_db
from app.core.session_auth import current_user
from app.models import Course, Schedule, User
from app.schemas import CourseOut
from app.services.course_service import build_course_out, get_course_or_404

router = APIRouter(tags=['Course Service'])


@router.get('/courses', response_model=list[CourseOut])
def courses(db: Session = Depends(get_db), user: User = Depends(current_user)):
    rows = db.scalars(select(Course).options(selectinload(Course.prerequisites)).order_by(Course.id)).all()
    return build_course_out(db, rows, user)


@router.get('/courses/{course_id}/details')
def course_details(course_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    c = get_course_or_404(db, course_id)
    info = build_course_out(db, [c], user)[0]
    slots = db.scalars(select(Schedule).where(Schedule.course_id == course_id).order_by(Schedule.day, Schedule.start_time)).all()
    return {'id': c.id, 'code': c.code, 'name': c.name, 'lecturer': c.lecturer or 'Chưa phân công',
            'start_date': c.start_date, 'end_date': c.end_date, 'max_students': c.max_students,
            'current_enrolled': c.current_enrolled, 'is_full': info.is_full,
            'waitlist_count': info.waitlist_count, 'waitlist_position': info.waitlist_position,
            'prerequisites': [p.model_dump() for p in info.prerequisites],
            'prerequisites_met': info.prerequisites_met, 'completed': info.completed,
            'schedules': [{'id': s.id, 'day': s.day, 'shift': s.shift,
                           'start_time': s.start_time or ('07:00' if s.shift == 'sang' else '13:00'),
                           'end_time': s.end_time or ('11:00' if s.shift == 'sang' else '17:00'),
                           'room': s.room or 'Đang cập nhật'} for s in slots]}
