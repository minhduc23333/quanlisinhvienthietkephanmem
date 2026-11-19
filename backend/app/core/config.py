"""Đọc cấu hình từ backend/.env. Mọi module khác lấy cấu hình qua file này."""
import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[2]
ROOT_DIR = BACKEND_DIR.parent
FRONTEND_DIR = ROOT_DIR / 'frontend'

load_dotenv(BACKEND_DIR / '.env')

DB_HOST = os.getenv('DB_HOST', '127.0.0.1')
DB_PORT = os.getenv('DB_PORT', '3306')
DB_USER = quote_plus(os.getenv('DB_USER', 'root'))
DB_PASSWORD = quote_plus(os.getenv('DB_PASSWORD', ''))
DB_NAME = os.getenv('DB_NAME', 'quanlihoc')

# DATABASE_URL (tùy chọn) ghi đè cấu hình MySQL, chủ yếu dùng cho kiểm thử tự động.
DATABASE_URL = os.getenv('DATABASE_URL') or (
    f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4'
)

SESSION_SECRET = os.getenv('SESSION_SECRET', '')
