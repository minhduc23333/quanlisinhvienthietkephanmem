from tests.conftest import cancel, enroll, join_waitlist, my_courses


def test_cannot_join_waitlist_when_seats_available(make_course, make_student):
    c = make_course('A', 2, slots=[(2, 'sang')])
    r = join_waitlist(make_student(), c)
    assert r.status_code == 400 and 'còn chỗ' in r.json()['detail']


def test_waitlist_fifo_and_auto_promotion(make_course, make_student):
    c = make_course('A', 1, slots=[(2, 'sang')])
    a, b, d = make_student(), make_student(), make_student()
    assert enroll(a, c).status_code == 201
    r = join_waitlist(b, c)
    assert r.status_code == 201 and r.json()['position'] == 1
    assert join_waitlist(d, c).json()['position'] == 2
    assert join_waitlist(b, c).status_code == 400  # đã trong hàng chờ
    assert join_waitlist(a, c).status_code == 400  # đã đăng ký
    info = next(x for x in d.get('/courses').json() if x['code'] == 'A')
    assert info['waitlist_count'] == 2 and info['waitlist_position'] == 2
    assert [w['position'] for w in b.get(f"/waitlist/{b.user['id']}").json()] == [1]

    assert cancel(a, c).json()['promoted_from_waitlist'] == 1
    assert my_courses(b) == {'A'} and my_courses(d) == set()
    assert d.get(f"/waitlist/{d.user['id']}").json()[0]['position'] == 1
    course = b.get('/courses').json()[0]
    assert course['current_enrolled'] == 1 and course['waitlist_count'] == 1
    # lớp lại đầy nên người sau không chen được
    assert enroll(d, c).status_code == 400
    cancel(b, c)
    assert my_courses(d) == {'A'} and d.get('/courses').json()[0]['waitlist_count'] == 0


def test_leave_waitlist_keeps_order(make_course, make_student):
    c = make_course('A', 1, slots=[(2, 'sang')])
    a, b, d, e = (make_student() for _ in range(4))
    enroll(a, c)
    for s in (b, d, e):
        join_waitlist(s, c)
    assert b.delete(f"/waitlist/{b.user['id']}/{c['id']}").status_code == 200
    assert b.delete(f"/waitlist/{b.user['id']}/{c['id']}").status_code == 404
    assert d.get(f"/waitlist/{d.user['id']}").json()[0]['position'] == 1
    assert e.get(f"/waitlist/{e.user['id']}").json()[0]['position'] == 2
    cancel(a, c)
    assert my_courses(d) == {'A'} and my_courses(e) == set() and my_courses(b) == set()


def test_waitlist_requires_eligibility(admin, make_course, make_student):
    other = make_course('OTHER', slots=[(2, 'sang')])
    full = make_course('FULL', 1, slots=[(2, 'sang')])
    gated = make_course('GATED', 1, slots=[(3, 'sang')], prerequisites=[other['id']])
    holder, s = make_student(), make_student()
    enroll(holder, full)
    # trùng lịch -> không được vào hàng chờ
    enroll(s, other)
    r = join_waitlist(s, full)
    assert r.status_code == 400 and 'Trùng lịch' in r.json()['detail']
    # thiếu tiên quyết -> không được vào hàng chờ của môn đã đầy
    h2 = make_student()
    admin.post(f"/admin/users/{h2.user['id']}/completed", json={'course_id': other['id']})
    assert enroll(h2, gated).status_code == 201
    r = join_waitlist(make_student(), gated)
    assert r.status_code == 400 and 'tiên quyết' in r.json()['detail']


def test_promotion_skips_ineligible_but_keeps_them(make_course, make_student):
    full = make_course('FULL', 1, slots=[(2, 'sang')])
    clash = make_course('CLASH', slots=[(5, 'chieu')])
    holder, b, d = make_student(), make_student(), make_student()
    enroll(holder, full)
    assert join_waitlist(b, full).status_code == 201
    assert join_waitlist(d, full).status_code == 201
    # b đăng ký CLASH (lúc đó chưa trùng), sau đó CLASH bị thêm lịch trùng ca với FULL.
    # API Admin chặn việc này, nên mô phỏng bằng cách ghi thẳng DB để kiểm tra nhánh 'bỏ qua người không đủ điều kiện'.
    from app.core.database import SessionLocal
    from app.models import Schedule
    with SessionLocal() as db:
        db.add(Schedule(course_id=clash['id'], day=2, shift='sang'))
        db.commit()
    assert enroll(b, clash).status_code == 201
    cancel(holder, full)
    assert my_courses(b) == {'CLASH'} and my_courses(d) == {'FULL'}  # b bị bỏ qua, d được xếp
    assert b.get(f"/waitlist/{b.user['id']}").json()[0]['code'] == 'FULL'  # b vẫn trong hàng chờ


def test_locked_student_not_promoted(admin, make_course, make_student):
    c = make_course('A', 1, slots=[(2, 'sang')])
    a, b, d = make_student(), make_student(), make_student()
    enroll(a, c)
    join_waitlist(b, c)
    join_waitlist(d, c)
    assert admin.patch(f"/admin/users/{b.user['id']}/lock").status_code == 200
    cancel(a, c)
    assert my_courses(d) == {'A'}


def test_increasing_capacity_promotes(admin, make_course, make_student):
    c = make_course('A', 1, slots=[(2, 'sang')])
    a, b, d = make_student(), make_student(), make_student()
    enroll(a, c)
    join_waitlist(b, c)
    join_waitlist(d, c)
    r = admin.patch(f"/admin/courses/{c['id']}", json={'max_students': 3})
    assert r.status_code == 200
    assert my_courses(b) == {'A'} and my_courses(d) == {'A'}
    assert r.json()['current_enrolled'] == 3 and r.json()['waitlist_count'] == 0


def test_deleting_student_promotes_waiters_and_cleans_up(admin, make_course, make_student):
    c = make_course('A', 1, slots=[(2, 'sang')])
    done = make_course('DONE')
    a, b = make_student(), make_student()
    admin.post(f"/admin/users/{a.user['id']}/completed", json={'course_id': done['id']})
    enroll(a, c)
    join_waitlist(b, c)
    assert admin.delete(f"/admin/users/{a.user['id']}").status_code == 200
    assert my_courses(b) == {'A'}
    assert admin.get('/courses').json()[0]['current_enrolled'] == 1
    # xóa người đang chờ cũng dọn sạch bảng waitlist
    enroll(make_student(), c)  # lớp đầy lại
    d = make_student()
    join_waitlist(d, c)
    assert admin.delete(f"/admin/users/{d.user['id']}").status_code == 200
    assert admin.get(f"/admin/courses/{c['id']}/waitlist").json() == []


def test_admin_waitlist_view(admin, make_course, make_student):
    c = make_course('A', 1, slots=[(2, 'sang')])
    a, b, d = make_student('An'), make_student('Binh'), make_student('Dung')
    enroll(a, c)
    join_waitlist(b, c)
    join_waitlist(d, c)
    rows = admin.get(f"/admin/courses/{c['id']}/waitlist").json()
    assert [(r['position'], r['name']) for r in rows] == [(1, 'Binh'), (2, 'Dung')]
    assert b.get(f"/admin/courses/{c['id']}/waitlist").status_code == 403
    assert admin.get('/admin/stats').json()['waitlist'] == 2
