from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

import app.models  # noqa: F401  (đăng ký các bảng với Base.metadata)
from app.core.config import FRONTEND_DIR
from app.core.database import Base, engine
from app.routers import admin_courses, admin_users, auth, courses, enrollments, schedules, waitlist

PAGES = FRONTEND_DIR / 'pages'
app = FastAPI(title='EduCourse SOA - De tai 09 - Nhom 6', version='6.0')
# Frontend and API run on the same origin. No wildcard CORS with auth cookies.
app.add_middleware(CORSMiddleware, allow_origins=['http://127.0.0.1:8000', 'http://localhost:8000'],
                   allow_credentials=True, allow_methods=['*'], allow_headers=['*'])
# Tạo bảng còn thiếu (kể cả các bảng mới: course_prerequisites, waitlist, completed_courses).
Base.metadata.create_all(bind=engine)
for module in [auth, courses, schedules, enrollments, waitlist, admin_users, admin_courses]:
    app.include_router(module.router)
app.mount('/static', StaticFiles(directory=str(FRONTEND_DIR)), name='static')


@app.get('/', include_in_schema=False)
def index():
    return FileResponse(PAGES / 'index.html')


@app.get('/dashboard', include_in_schema=False)
def dashboard():
    return FileResponse(PAGES / 'dashboard.html')


@app.get('/admin', include_in_schema=False)
def admin_page():
    return FileResponse(PAGES / 'admin.html', headers={'Cache-Control': 'no-store, max-age=0'})


@app.get('/api/health')
def health():
    return {'status': 'ok', 'database': 'MySQL', 'version': 6}
