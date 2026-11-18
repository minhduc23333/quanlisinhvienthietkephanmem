from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db
from models import Course,User,Schedule
from schemas import CourseOut
from session_auth import current_user
router=APIRouter(tags=['Course Service'])
@router.get('/courses',response_model=list[CourseOut])
def courses(db:Session=Depends(get_db),user:User=Depends(current_user)):
    return [CourseOut(id=c.id,code=c.code,name=c.name,max_students=c.max_students,current_enrolled=c.current_enrolled,lecturer=c.lecturer,start_date=c.start_date,end_date=c.end_date,is_full=c.current_enrolled>=c.max_students) for c in db.scalars(select(Course).order_by(Course.id)).all()]

@router.get('/courses/{course_id}/details')
def course_details(course_id:int,db:Session=Depends(get_db),user:User=Depends(current_user)):
    c=db.get(Course,course_id)
    if not c:raise HTTPException(404,'Không tìm thấy học phần')
    slots=db.scalars(select(Schedule).where(Schedule.course_id==course_id).order_by(Schedule.day,Schedule.start_time)).all()
    return {'id':c.id,'code':c.code,'name':c.name,'lecturer':c.lecturer or 'Chưa phân công',
        'start_date':c.start_date,'end_date':c.end_date,'max_students':c.max_students,
        'current_enrolled':c.current_enrolled,'is_full':c.current_enrolled>=c.max_students,
        'schedules':[{'id':s.id,'day':s.day,'shift':s.shift,'start_time':s.start_time or ('07:00' if s.shift=='sang' else '13:00'),
                      'end_time':s.end_time or ('11:00' if s.shift=='sang' else '17:00'),'room':s.room or 'Đang cập nhật'} for s in slots]}
