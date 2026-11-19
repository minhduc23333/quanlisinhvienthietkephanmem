from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.session_auth import admin_only, current_user
from app.models import Schedule, User
from app.schemas import ScheduleCreate, ScheduleOut, ScheduleUpdate
from app.services.course_service import get_course_or_404
from app.services.schedule_service import validate_slot

router = APIRouter(tags=['Schedule Service'])


@router.get('/schedules/{course_id}', response_model=list[ScheduleOut])
def get_schedules(course_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    get_course_or_404(db, course_id)
    return db.scalars(select(Schedule).where(Schedule.course_id == course_id).order_by(Schedule.day, Schedule.shift)).all()


@router.post('/schedules', response_model=ScheduleOut, status_code=201)
def create_schedule(body: ScheduleCreate, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    course = get_course_or_404(db, body.course_id)
    room = (body.room or '').strip() or None
    validate_slot(db, course, body.day, body.shift, room)
    s = Schedule(**{**body.model_dump(), 'room': room})
    db.add(s)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Lịch học đã tồn tại')
    db.refresh(s)
    return s


@router.patch('/schedules/{schedule_id}', response_model=ScheduleOut)
def update_schedule(schedule_id: int, body: ScheduleUpdate, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    s = db.get(Schedule, schedule_id)
    if not s:
        raise HTTPException(404, 'Không tìm thấy lịch học')
    data = body.model_dump(exclude_unset=True)
    if 'room' in data:
        data['room'] = (data['room'] or '').strip() or None
    day, shift = data.get('day', s.day), data.get('shift', s.shift)
    room = data['room'] if 'room' in data else s.room
    start, end = data.get('start_time', s.start_time), data.get('end_time', s.end_time)
    if start and end and start >= end:
        raise HTTPException(422, 'Giờ kết thúc phải sau giờ bắt đầu')
    if (day, shift) != (s.day, s.shift) or room != s.room:
        validate_slot(db, get_course_or_404(db, s.course_id), day, shift, room, schedule_id=s.id)
    for key, value in data.items():
        setattr(s, key, value)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, 'Lịch học đã tồn tại')
    db.refresh(s)
    return s


@router.delete('/schedules/{schedule_id}')
def delete_schedule(schedule_id: int, db: Session = Depends(get_db), admin: User = Depends(admin_only)):
    s = db.get(Schedule, schedule_id)
    if not s:
        raise HTTPException(404, 'Không tìm thấy lịch học')
    db.delete(s)
    db.commit()
    return {'message': 'Đã xóa lịch học'}
