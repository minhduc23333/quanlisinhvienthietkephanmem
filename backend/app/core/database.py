from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import DATABASE_URL

_engine_options = {'pool_pre_ping': True}
if DATABASE_URL.startswith('sqlite'):
    _engine_options['connect_args'] = {'check_same_thread': False}
else:
    _engine_options['pool_recycle'] = 1800
    # Mặc định MySQL là REPEATABLE READ: sau khi khóa dòng học phần, các lần đọc tiếp theo vẫn thấy "ảnh chụp" cũ,
    # nên hai thao tác hủy/đăng ký đồng thời có thể cùng xếp một sinh viên chờ vào lớp. READ COMMITTED tránh việc đó.
    _engine_options['isolation_level'] = 'READ COMMITTED'

engine = create_engine(DATABASE_URL, **_engine_options)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    with SessionLocal() as db:
        yield db
