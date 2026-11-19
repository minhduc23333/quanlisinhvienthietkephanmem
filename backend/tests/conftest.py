"""Chạy: cd backend && python -m pytest -q   (dùng SQLite tạm, không đụng tới MySQL của bạn)."""
import os
import tempfile

# Mặc định dùng SQLite tạm. Muốn thử trên MySQL: đặt DATABASE_URL trỏ tới DB riêng có tên kết thúc bằng _test
# (test sẽ XÓA toàn bộ bảng của DB đó).
if 'DATABASE_URL' not in os.environ:
    _tmp = tempfile.mkdtemp(prefix='educourse_test_')
    os.environ['DATABASE_URL'] = f'sqlite:///{_tmp}/test.db'
_url = os.environ['DATABASE_URL']
if not (_url.startswith('sqlite') or _url.split('?')[0].rstrip('/').endswith('_test')):
    raise RuntimeError('DATABASE_URL của test phải là sqlite hoặc tên database kết thúc bằng _test.')
os.environ['SESSION_SECRET'] = 'test-secret-test-secret-test-secret-123456'

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.main import app  # noqa: E402
from app.models import User  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        db.add(User(name='Admin', username='admin', email='admin@x.vn', role='admin',
                    password_hash=hash_password('Admin@12345'), is_locked=False))
        db.commit()
    yield


class Client:
    def __init__(self):
        self.http = TestClient(app)
        self.user = None

    def login(self, email, password):
        r = self.http.post('/login', json={'username': email, 'password': password})
        assert r.status_code == 200, r.text
        self.user = r.json()
        return self

    def __getattr__(self, name):
        return getattr(self.http, name)


@pytest.fixture
def admin():
    return Client().login('admin@x.vn', 'Admin@12345')


@pytest.fixture
def make_student():
    count = {'n': 0}

    def _make(name=None):
        count['n'] += 1
        email = f'sv{count["n"]}@x.vn'
        c = Client()
        r = c.http.post('/register', json={'name': name or f'Sinh Vien {count["n"]}', 'email': email, 'password': 'Passw0rd!1'})
        assert r.status_code == 201, r.text
        return c.login(email, 'Passw0rd!1')

    return _make


@pytest.fixture
def make_course(admin):
    def _make(code, max_students=30, slots=(), prerequisites=(), **extra):
        r = admin.post('/admin/courses', json={'code': code, 'name': f'Mon {code}', 'max_students': max_students,
                                               'prerequisite_ids': list(prerequisites), **extra})
        assert r.status_code == 201, r.text
        course = r.json()
        for day, shift, *room in slots:
            body = {'course_id': course['id'], 'day': day, 'shift': shift}
            if room:
                body['room'] = room[0]
            rs = admin.post('/schedules', json=body)
            assert rs.status_code == 201, rs.text
        return course

    return _make


def enroll(student, course):
    return student.post('/enrollments', json={'student_id': student.user['id'], 'course_id': course['id']})


def join_waitlist(student, course):
    return student.post('/waitlist', json={'student_id': student.user['id'], 'course_id': course['id']})


def cancel(student, course):
    return student.delete(f"/enrollments/{student.user['id']}/{course['id']}")


def my_courses(student):
    return {c['code'] for c in student.get(f"/enrollments/{student.user['id']}").json()}
