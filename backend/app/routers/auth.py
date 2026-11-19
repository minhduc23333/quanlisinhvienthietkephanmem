import re
import uuid
from fastapi import APIRouter,Depends,HTTPException,Response
from sqlalchemy.orm import Session
from sqlalchemy import select,func,or_
from sqlalchemy.exc import IntegrityError
from app.core.database import get_db
from app.models import User
from app.schemas import LoginIn,RegisterIn,UserOut
from app.core.security import hash_password,verify_password
from app.core.session_auth import current_user,create_session,COOKIE
router=APIRouter(tags=['Authentication'])
EMAIL_RE=re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?(?:\.[A-Za-z0-9](?:[A-Za-z0-9-]*[A-Za-z0-9])?)+$")
@router.post('/login')
def login(body:LoginIn,response:Response,db:Session=Depends(get_db)):
    identity=body.username.strip().lower()
    user=db.scalar(select(User).where(or_(func.lower(User.email)==identity,func.lower(User.username)==identity)))
    if user is None or not verify_password(body.password,user.password_hash):raise HTTPException(401,'Email hoặc mật khẩu không đúng. Nếu là Admin, hãy chạy python -m scripts.setup_admin một lần.')
    if user.is_locked:raise HTTPException(403,'Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.')
    response.set_cookie(COOKIE,create_session(user),httponly=True,samesite='lax',secure=False,max_age=43200,path='/')
    return {'id':user.id,'student_id':user.id if user.role=='student' else None,'name':user.name,'role':user.role}
@router.post('/logout')
def logout(response:Response):
    response.delete_cookie(COOKIE,path='/')
    return {'message':'Đã đăng xuất'}
@router.get('/me',response_model=UserOut)
def me(user:User=Depends(current_user)):return user
@router.post('/register',response_model=UserOut,status_code=201)
def register(body:RegisterIn,db:Session=Depends(get_db)):
    name=body.name.strip()
    email=body.email.strip().lower()
    if len(name)<2:raise HTTPException(400,'Vui lòng nhập họ và tên')
    if not EMAIL_RE.fullmatch(email):raise HTTPException(400,'Email không hợp lệ')
    if len(body.password)<8:raise HTTPException(400,'Mật khẩu cần ít nhất 8 ký tự')
    if db.scalar(select(User.id).where(func.lower(User.email)==email)):raise HTTPException(409,'Email này đã được đăng ký')
    # Preserve old username column and allow admin/legacy accounts to keep their usernames.
    user=User(name=name,email=email,username='sv_'+uuid.uuid4().hex[:20],password_hash=hash_password(body.password),role='student',is_locked=False)
    db.add(user)
    try:db.commit()
    except IntegrityError:
        db.rollback();raise HTTPException(409,'Email này đã được đăng ký')
    db.refresh(user)
    return user
