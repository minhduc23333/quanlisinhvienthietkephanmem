from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session
from database import get_db
from models import User,Course,Schedule,Enrollment
from schemas import EnrollmentCreate
from session_auth import student_only
router=APIRouter(tags=['Enrollment Service'])
def check_conflict(student_id:int,course_id:int,db:Session)->bool:
    old=set(db.execute(select(Schedule.day,Schedule.shift).join(Enrollment,Enrollment.course_id==Schedule.course_id).where(Enrollment.student_id==student_id)).all())
    new=set(db.execute(select(Schedule.day,Schedule.shift).where(Schedule.course_id==course_id)).all())
    return bool(old & new)
@router.post('/enrollments',status_code=201)
def enroll(body:EnrollmentCreate,db:Session=Depends(get_db),student:User=Depends(student_only)):
    if body.student_id!=student.id:raise HTTPException(403,'Không thể đăng ký hộ tài khoản khác')
    if True:
        course=db.scalar(select(Course).where(Course.id==body.course_id).with_for_update())
        if not course:raise HTTPException(404,'Không tìm thấy học phần')
        if db.scalar(select(Enrollment.id).where(Enrollment.student_id==student.id,Enrollment.course_id==course.id)):raise HTTPException(400,'Bạn đã đăng ký học phần này')
        if check_conflict(student.id,course.id,db):raise HTTPException(400,'Trùng lịch với học phần đã đăng ký')
        if course.current_enrolled>=course.max_students:raise HTTPException(400,'Học phần đã đủ sĩ số')
        db.add(Enrollment(student_id=student.id,course_id=course.id));course.current_enrolled+=1
        db.commit()
    return {'message':'Đăng ký học phần thành công','student_id':student.id,'course_id':course.id}
@router.get('/enrollments/{student_id}/schedule')
def timetable(student_id:int,db:Session=Depends(get_db),student:User=Depends(student_only)):
    if student.id!=student_id:raise HTTPException(403,'Không có quyền xem lịch của tài khoản khác')
    rows=db.execute(select(Enrollment.id,Course.id,Course.code,Course.name,Schedule.day,Schedule.shift,Schedule.start_time,Schedule.end_time,Schedule.room,Course.lecturer).join(Course,Enrollment.course_id==Course.id).join(Schedule,Schedule.course_id==Course.id).where(Enrollment.student_id==student.id).order_by(Schedule.day,Schedule.shift)).all()
    return [{'enrollment_id':e,'course_id':cid,'code':code,'course_name':name,'day':day,'shift':shift,'start_time':start_time or ('07:00' if shift=='sang' else '13:00'),'end_time':end_time or ('11:00' if shift=='sang' else '17:00'),'room':room or 'Đang cập nhật','lecturer':lecturer or 'Chưa phân công'} for e,cid,code,name,day,shift,start_time,end_time,room,lecturer in rows]
@router.get('/enrollments/{student_id}')
def own(student_id:int,db:Session=Depends(get_db),student:User=Depends(student_only)):
    if student.id!=student_id:raise HTTPException(403,'Không có quyền xem dữ liệu của tài khoản khác')
    rows=db.execute(select(Enrollment.id,Course.id,Course.code,Course.name).join(Course).where(Enrollment.student_id==student.id)).all()
    return [{'id':e,'course_id':cid,'code':code,'name':name} for e,cid,code,name in rows]
@router.delete('/enrollments/{student_id}/{course_id}')
def cancel(student_id:int,course_id:int,db:Session=Depends(get_db),student:User=Depends(student_only)):
    if student.id!=student_id:raise HTTPException(403,'Không thể hủy đăng ký của tài khoản khác')
    if True:
        course=db.scalar(select(Course).where(Course.id==course_id).with_for_update())
        row=db.scalar(select(Enrollment).where(Enrollment.student_id==student.id,Enrollment.course_id==course_id))
        if not row or not course:raise HTTPException(404,'Không tìm thấy đăng ký')
        db.delete(row);course.current_enrolled=max(0,course.current_enrolled-1)
        db.commit()
    return {'message':'Đã hủy đăng ký học phần'}
