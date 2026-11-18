import os
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv(Path(__file__).with_name('.env'))
HOST = os.getenv('DB_HOST', '127.0.0.1')
PORT = os.getenv('DB_PORT', '3306')
USER = quote_plus(os.getenv('DB_USER', 'root'))
PASSWORD = quote_plus(os.getenv('DB_PASSWORD', ''))
DB_NAME = os.getenv('DB_NAME', 'quanlihoc')
URL = f'mysql+pymysql://{USER}:{PASSWORD}@{HOST}:{PORT}/{DB_NAME}?charset=utf8mb4'
engine = create_engine(URL, pool_pre_ping=True, pool_recycle=1800)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
class Base(DeclarativeBase):
    pass

def get_db():
    with SessionLocal() as db:
        yield db
