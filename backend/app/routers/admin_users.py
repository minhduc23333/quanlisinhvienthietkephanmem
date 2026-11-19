from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy import select,func
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models import User,Course,Enrollment,CompletedCourse,WaitlistEntry
from app.schemas import CompletedCreate
from app.core.session_auth import admin_only
from app.services import enrollment_service as svc
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
    return {'users':db.scalar(select(func.count()).select_from(User).where(User.role=='student')),'locked':db.scalar(select(func.count()).select_from(User).where(User.role=='student',User.is_locked==True)),'courses':db.scalar(select(func.count()).select_from(Course)),'enrollments':db.scalar(select(func.count()).select_from(Enrollment)),'waitlist':db.scalar(select(func.count()).select_from(WaitlistEntry))}
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
    user=db.scalar(select(User).where(User.id==user_id).with_for_update())
    if not user or user.role!='student':raise HTTPException(404,'Không tìm thấy tài khoản sinh viên')
    # Trả chỗ các học phần, xóa hàng chờ + lịch sử hoàn thành, rồi xếp người đang chờ vào chỗ trống.
    svc.remove_student(db,user)
    return {'message':'Đã xóa tài khoản và các học phần đã đăng ký'}
def _student_or_404(db:Session,user_id:int)->User:
    user=db.get(User,user_id)
    if not user or user.role!='student':raise HTTPException(404,'Không tìm thấy tài khoản sinh viên')
    return user
@router.get('/users/{user_id}/completed')
def list_completed(user_id:int,db:Session=Depends(get_db),admin:User=Depends(admin_only)):
    _student_or_404(db,user_id)
    rows=db.execute(select(Course.id,Course.code,Course.name,CompletedCourse.completed_at).join(CompletedCourse,CompletedCourse.course_id==Course.id).where(CompletedCourse.student_id==user_id).order_by(Course.code)).all()
    return [{'course_id':cid,'code':code,'name':name,'completed_at':at.isoformat() if at else None} for cid,code,name,at in rows]
@router.post('/users/{user_id}/completed',status_code=201)
def add_completed(user_id:int,body:CompletedCreate,db:Session=Depends(get_db),admin:User=Depends(admin_only)):
    svc.mark_completed(db,user_id,body.course_id)
    return {'message':'Đã ghi nhận học phần hoàn thành'}
@router.delete('/users/{user_id}/completed/{course_id}')
def remove_completed(user_id:int,course_id:int,db:Session=Depends(get_db),admin:User=Depends(admin_only)):
    _student_or_404(db,user_id)
    row=db.scalar(select(CompletedCourse).where(CompletedCourse.student_id==user_id,CompletedCourse.course_id==course_id))
    if not row:raise HTTPException(404,'Sinh viên chưa có học phần này trong danh sách hoàn thành')
    db.delete(row);db.commit()
    return {'message':'Đã bỏ ghi nhận hoàn thành học phần'}
