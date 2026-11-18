"""Safely extend existing v5 MySQL users table with an optional unique email."""
from sqlalchemy import inspect,text
from database import engine
inspector=inspect(engine)
if 'users' not in inspector.get_table_names():
    print('Chưa có users: tạo DB trước, rồi chạy py seed_demo.py');raise SystemExit(0)
cols={c['name'] for c in inspector.get_columns('users')}
if 'email' not in cols:
    with engine.begin() as conn:
        conn.execute(text('ALTER TABLE users ADD COLUMN email VARCHAR(254) NULL UNIQUE'))
    print('Đã thêm email (UNIQUE, NULL cho tài khoản cũ).')
else:print('Cột email đã tồn tại.')
