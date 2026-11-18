"""Tạo hoặc đồng bộ tài khoản admin vào MySQL. Chạy: py setup_admin.py"""
from sqlalchemy import select, func
from database import Base, engine, SessionLocal
from models import User
from security import hash_password
from admin_settings import ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_NAME


def sync_admin():
    if len(ADMIN_PASSWORD) < 10:
        raise RuntimeError('Mật khẩu admin phải dài ít nhất 10 ký tự')
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        # Ưu tiên tài khoản admin đã tồn tại để không tạo trùng.
        by_username = db.scalar(select(User).where(func.lower(User.username) == ADMIN_USERNAME.lower()))
        by_email = db.scalar(select(User).where(func.lower(User.email) == ADMIN_EMAIL.lower()))
        if by_username and by_email and by_username.id != by_email.id:
            raise RuntimeError('Username và email Admin đang thuộc hai tài khoản khác nhau. Kiểm tra bảng users.')
        admin = by_username or by_email
        if admin is not None and admin.role != 'admin':
            raise RuntimeError('Tên đăng nhập hoặc email Admin đang thuộc sinh viên. Không tự nâng quyền!')
        if admin is None:
            admin = User(name=ADMIN_NAME, username=ADMIN_USERNAME, email=ADMIN_EMAIL,
                         role='admin', password_hash=hash_password(ADMIN_PASSWORD), is_locked=False)
            db.add(admin)
            result = 'Đã tạo tài khoản Admin'
        else:
            admin.name = ADMIN_NAME
            admin.username = ADMIN_USERNAME
            admin.email = ADMIN_EMAIL
            admin.role = 'admin'
            admin.password_hash = hash_password(ADMIN_PASSWORD)
            admin.is_locked = False
            result = 'Đã cập nhật và mở khóa tài khoản Admin'
        db.commit()
        print(f'{result}. Email: {ADMIN_EMAIL}; username: {ADMIN_USERNAME}')


if __name__ == '__main__':
    sync_admin()
