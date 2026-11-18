from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from database import get_db
from models import Schedule,Course,User
from schemas import ScheduleCreate,ScheduleOut
from session_auth import current_user,admin_only
router=APIRouter(tags=['Schedule Service'])
@router.get('/schedules/{course_id}',response_model=list[ScheduleOut])
def get_schedules(course_id:int,db:Session=Depends(get_db),user:User=Depends(current_user)):
    if not db.get(Course,course_id):raise HTTPException(404,'Không tìm thấy học phần')
    return db.scalars(select(Schedule).where(Schedule.course_id==course_id).order_by(Schedule.day,Schedule.shift)).all()
@router.post('/schedules',response_model=ScheduleOut,status_code=201)
def create_schedule(body:ScheduleCreate,db:Session=Depends(get_db),admin:User=Depends(admin_only)):
    if not db.get(Course,body.course_id):raise HTTPException(404,'Không tìm thấy học phần')
    s=Schedule(**body.model_dump());db.add(s)
    try:db.commit()
    except IntegrityError:db.rollback();raise HTTPException(409,'Lịch học đã tồn tại')
    db.refresh(s);return s
