from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from database import Base,engine
import models
from routers import auth,courses,schedules,enrollments,admin
from session_auth import SECRET
ROOT=Path(__file__).resolve().parent.parent
FRONTEND=ROOT/'frontend'
app=FastAPI(title='EduCourse SOA - De tai 09 - Nhom 6',version='5.0')
# Frontend and API run on the same origin. No wildcard CORS with auth cookies.
app.add_middleware(CORSMiddleware,allow_origins=['http://127.0.0.1:8000','http://localhost:8000'],allow_credentials=True,allow_methods=['*'],allow_headers=['*'])
Base.metadata.create_all(bind=engine)
for module in [auth,courses,schedules,enrollments,admin]:app.include_router(module.router)
app.mount('/static',StaticFiles(directory=str(FRONTEND)),name='static')
@app.get('/',include_in_schema=False)
def index():return FileResponse(FRONTEND/'index.html')
@app.get('/dashboard',include_in_schema=False)
def dashboard():return FileResponse(FRONTEND/'dashboard.html')
@app.get('/admin',include_in_schema=False)
def admin_page():return FileResponse(FRONTEND/'admin.html', headers={'Cache-Control':'no-store, max-age=0'})
@app.get('/api/health')
def health():return {'status':'ok','database':'MySQL','version':5}
