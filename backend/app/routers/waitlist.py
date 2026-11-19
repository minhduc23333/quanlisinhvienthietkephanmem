from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.session_auth import student_only
from app.models import Course, User, WaitlistEntry
from app.schemas import EnrollmentCreate
from app.services import enrollment_service as svc
from app.services.course_service import waitlist_positions

router = APIRouter(tags=['Waitlist Service'])


@router.post('/waitlist', status_code=201)
def join(body: EnrollmentCreate, db: Session = Depends(get_db), student: User = Depends(student_only)):
    if body.student_id != student.id:
        raise HTTPException(403, 'Không thể xếp hàng chờ hộ tài khoản khác')
    position = svc.join_waitlist(db, student, body.course_id)
    return {'message': f'Đã vào danh sách chờ, vị trí số {position}', 'position': position, 'course_id': body.course_id}


@router.get('/waitlist/{student_id}')
def own(student_id: int, db: Session = Depends(get_db), student: User = Depends(student_only)):
    if student.id != student_id:
        raise HTTPException(403, 'Không có quyền xem dữ liệu của tài khoản khác')
    positions = waitlist_positions(db, student.id)
    rows = db.execute(select(WaitlistEntry.id, Course.id, Course.code, Course.name, WaitlistEntry.created_at)
                      .join(Course, Course.id == WaitlistEntry.course_id)
                      .where(WaitlistEntry.student_id == student.id).order_by(WaitlistEntry.id)).all()
    return [{'id': eid, 'course_id': cid, 'code': code, 'name': name, 'position': positions.get(cid),
             'joined_at': at.isoformat() if at else None} for eid, cid, code, name, at in rows]


@router.delete('/waitlist/{student_id}/{course_id}')
def leave(student_id: int, course_id: int, db: Session = Depends(get_db), student: User = Depends(student_only)):
    if student.id != student_id:
        raise HTTPException(403, 'Không thể hủy hàng chờ của tài khoản khác')
    svc.leave_waitlist(db, student.id, course_id)
    return {'message': 'Đã rời danh sách chờ'}
