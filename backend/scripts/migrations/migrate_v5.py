"""Run once for users table created by v4; safe to rerun."""
from sqlalchemy import text,inspect
from app.core.database import engine
if 'users' not in inspect(engine).get_table_names():
    print('Chưa có bảng users. Chạy python -m scripts.seed_demo để tạo dữ liệu.');raise SystemExit
cols={c['name'] for c in inspect(engine).get_columns('users')}
if 'is_locked' not in cols:
    with engine.begin() as conn:conn.execute(text('ALTER TABLE users ADD COLUMN is_locked BOOLEAN NOT NULL DEFAULT 0'))
    print('Đã bổ sung cột is_locked')
else:print('Cột is_locked đã tồn tại')
