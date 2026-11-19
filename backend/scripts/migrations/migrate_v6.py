"""Safely extend existing v5 MySQL users table with an optional unique email."""
from sqlalchemy import inspect,text
from app.core.database import engine
inspector=inspect(engine)
if 'users' not in inspector.get_table_names():
    print('Chưa có users: tạo DB trước, rồi chạy python -m scripts.seed_demo');raise SystemExit(0)
cols={c['name'] for c in inspector.get_columns('users')}
if 'email' not in cols:
    with engine.begin() as conn:
        conn.execute(text('ALTER TABLE users ADD COLUMN email VARCHAR(254) NULL UNIQUE'))
    print('Đã thêm email (UNIQUE, NULL cho tài khoản cũ).')
else:print('Cột email đã tồn tại.')
