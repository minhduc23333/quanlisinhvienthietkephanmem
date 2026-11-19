from fastapi import Depends, HTTPException, Request
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy.orm import Session
from app.core.config import SESSION_SECRET as SECRET
from app.core.database import get_db
from app.models import User

COOKIE = 'educourse_session'
if not SECRET or SECRET == 'change-this-to-a-long-random-secret':
    raise RuntimeError('Hãy cấu hình SESSION_SECRET trong backend/.env (ít nhất 32 ký tự ngẫu nhiên).')
serializer = URLSafeTimedSerializer(SECRET, salt='educourse-v5')
def create_session(user):
    return serializer.dumps({'uid':user.id})
def current_user(request:Request, db:Session=Depends(get_db)):
    value=request.cookies.get(COOKIE)
    if not value: raise HTTPException(401,'Vui lòng đăng nhập')
    try: payload=serializer.loads(value,max_age=60*60*12)
    except (BadSignature,SignatureExpired): raise HTTPException(401,'Phiên đăng nhập hết hạn')
    user=db.get(User,payload.get('uid'))
    if not user: raise HTTPException(401,'Tài khoản không còn tồn tại')
    if user.is_locked: raise HTTPException(403,'Tài khoản của bạn đã bị khóa')
    return user
def student_only(user:User=Depends(current_user)):
    if user.role!='student': raise HTTPException(403,'Chỉ sinh viên được sử dụng chức năng này')
    return user
def admin_only(user:User=Depends(current_user)):
    if user.role!='admin': raise HTTPException(403,'Bạn không có quyền quản trị')
    return user
