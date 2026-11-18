from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from database import get_db
from models import User,Course,Enrollment
from session_auth import admin_only
router=APIRouter(prefix='/admin',tags=['Admin Service'])
@router.get('/users')
def list_users(q:str='',db:Session=Depends(get_db),admin:User=Depends(admin_only)):
    statement=select(User).where(User.role=='student').order_by(User.id.desc())
    if q.strip():statement=statement.where(User.username.like(f'%{q.strip()}%') | User.name.like(f'%{q.strip()}%') | User.email.like(f'%{q.strip()}%'))
    users=db.scalars(statement.limit(300)).all()
    counts=dict(db.execute(select(Enrollment.student_id,func.count(Enrollment.id)).group_by(Enrollment.student_id)).all())
    return [{'id':u.id,'name':u.name,'username':u.username,'email':u.email,'role':u.role,'is_locked':u.is_locked,'enrollment_count':counts.get(u.id,0)} for u in users]
@router.get('/stats')
def stats(db:Session=Depends(get_db),admin:User=Depends(admin_only)):
    return {'users':db.scalar(select(func.count()).select_from(User).where(User.role=='student')),'locked':db.scalar(select(func.count()).select_from(User).where(User.role=='student',User.is_locked==True)),'courses':db.scalar(select(func.count()).select_from(Course)),'enrollments':db.scalar(select(func.count()).select_from(Enrollment))}
@router.patch('/users/{user_id}/lock')
def lock(user_id:int,db:Session=Depends(get_db),admin:User=Depends(admin_only)):
    if True:
        user=db.scalar(select(User).where(User.id==user_id).with_for_update())
        if not user or user.role!='student':raise HTTPException(404,'Không tìm thấy tài khoản sinh viên')
        user.is_locked=True
        db.commit()
    return {'message':'Đã khóa tài khoản'}
@router.patch('/users/{user_id}/unlock')
def unlock(user_id:int,db:Session=Depends(get_db),admin:User=Depends(admin_only)):
    if True:
        user=db.scalar(select(User).where(User.id==user_id).with_for_update())
        if not user or user.role!='student':raise HTTPException(404,'Không tìm thấy tài khoản sinh viên')
        user.is_locked=False
        db.commit()
    return {'message':'Đã mở khóa tài khoản'}
@router.delete('/users/{user_id}')
def delete_user(user_id:int,db:Session=Depends(get_db),admin:User=Depends(admin_only)):
    # Lock course rows before decrementing enrollment counters to avoid lost updates.
    if True:
        user=db.scalar(select(User).where(User.id==user_id).with_for_update())
        if not user or user.role!='student':raise HTTPException(404,'Không tìm thấy tài khoản sinh viên')
        enrollments=db.scalars(select(Enrollment).where(Enrollment.student_id==user.id)).all()
        for eid in sorted({e.course_id for e in enrollments}):
            course=db.scalar(select(Course).where(Course.id==eid).with_for_update())
            if course:course.current_enrolled=max(0,course.current_enrolled-sum(e.course_id==eid for e in enrollments))
        for e in enrollments:db.delete(e)
        db.flush();db.delete(user)
        db.commit()
    return {'message':'Đã xóa tài khoản và các học phần đã đăng ký'}
