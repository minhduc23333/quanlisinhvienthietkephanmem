from tests.conftest import enroll


def test_course_crud(admin, make_course):
    c = make_course('hp100', 40, lecturer='  ThS. A ', start_date='2027-01-11', end_date='2027-05-16')
    assert c['code'] == 'HP100' and c['lecturer'] == 'ThS. A' and c['max_students'] == 40
    assert admin.post('/admin/courses', json={'code': 'HP100', 'name': 'x', 'max_students': 5}).status_code == 409
    r = admin.patch(f"/admin/courses/{c['id']}", json={'name': 'Moi', 'max_students': 50})
    assert r.status_code == 200 and r.json()['name'] == 'Moi' and r.json()['max_students'] == 50
    assert admin.delete(f"/admin/courses/{c['id']}").status_code == 200
    assert admin.get('/courses').json() == []


def test_course_validation(admin):
    bad = [{'code': 'A', 'name': 'x', 'max_students': 0},
           {'code': 'A', 'name': 'x', 'max_students': 5, 'start_date': '2027-13-40'},
           {'code': 'A', 'name': 'x', 'max_students': 5, 'start_date': '2027-05-01', 'end_date': '2027-01-01'}]
    for body in bad:
        assert admin.post('/admin/courses', json=body).status_code == 422


def test_student_cannot_manage(make_student, make_course):
    c = make_course('HP1')
    s = make_student()
    assert s.post('/admin/courses', json={'code': 'X', 'name': 'x', 'max_students': 5}).status_code == 403
    assert s.patch(f"/admin/courses/{c['id']}", json={'name': 'h'}).status_code == 403
    assert s.delete(f"/admin/courses/{c['id']}").status_code == 403
    assert s.post('/schedules', json={'course_id': c['id'], 'day': 2, 'shift': 'sang'}).status_code == 403


def test_schedule_crud_and_validation(admin, make_course):
    c = make_course('HP1')
    r = admin.post('/schedules', json={'course_id': c['id'], 'day': 2, 'shift': 'sang', 'start_time': '07:00',
                                       'end_time': '11:00', 'room': 'A1'})
    assert r.status_code == 201
    sid = r.json()['id']
    assert admin.post('/schedules', json={'course_id': c['id'], 'day': 2, 'shift': 'sang'}).status_code == 409
    assert admin.post('/schedules', json={'course_id': c['id'], 'day': 3, 'shift': 'sang', 'start_time': '11:00',
                                          'end_time': '07:00'}).status_code == 422
    assert admin.post('/schedules', json={'course_id': c['id'], 'day': 3, 'shift': 'sang', 'start_time': '7h'}).status_code == 422
    assert admin.post('/schedules', json={'course_id': c['id'], 'day': 8, 'shift': 'sang'}).status_code == 422
    r = admin.patch(f'/schedules/{sid}', json={'day': 4, 'room': 'B2'})
    assert r.status_code == 200 and r.json()['day'] == 4 and r.json()['room'] == 'B2'
    assert admin.patch(f'/schedules/{sid}', json={'start_time': '12:00'}).status_code == 422  # 12:00 >= 11:00
    assert admin.delete(f'/schedules/{sid}').status_code == 200
    assert admin.get(f"/schedules/{c['id']}").json() == []
    assert admin.delete(f'/schedules/{sid}').status_code == 404


def test_room_clash(admin, make_course):
    a = make_course('A', slots=[(2, 'sang', 'P.101')])
    b = make_course('B')
    r = admin.post('/schedules', json={'course_id': b['id'], 'day': 2, 'shift': 'sang', 'room': 'p.101'})
    assert r.status_code == 409 and 'P.101'.lower() in r.json()['detail'].lower()
    assert admin.post('/schedules', json={'course_id': b['id'], 'day': 2, 'shift': 'chieu', 'room': 'P.101'}).status_code == 201
    assert a['id'] != b['id']


def test_schedule_change_that_breaks_students_is_rejected(admin, make_course, make_student):
    a = make_course('A', slots=[(2, 'sang')])
    b = make_course('B', slots=[(3, 'sang')])
    s = make_student()
    assert enroll(s, a).status_code == 201 and enroll(s, b).status_code == 201
    sched_b = admin.get(f"/schedules/{b['id']}").json()[0]
    r = admin.patch(f"/schedules/{sched_b['id']}", json={'day': 2})  # trùng ca với A
    assert r.status_code == 409 and '1 sinh viên' in r.json()['detail']
    assert admin.post('/schedules', json={'course_id': b['id'], 'day': 2, 'shift': 'sang'}).status_code == 409
    assert admin.post('/schedules', json={'course_id': b['id'], 'day': 5, 'shift': 'chieu'}).status_code == 201


def test_max_students_rules(admin, make_course, make_student):
    c = make_course('A', 2, slots=[(2, 'sang')])
    for _ in range(2):
        assert enroll(make_student(), c).status_code == 201
    r = admin.patch(f"/admin/courses/{c['id']}", json={'max_students': 1})
    assert r.status_code == 400
    assert admin.patch(f"/admin/courses/{c['id']}", json={'max_students': 2}).status_code == 200


def test_delete_course_guards(admin, make_course, make_student):
    base = make_course('BASE', slots=[(2, 'sang')])
    nxt = make_course('NEXT', prerequisites=[base['id']])
    assert admin.delete(f"/admin/courses/{base['id']}").status_code == 409  # là tiên quyết của NEXT
    s = make_student()
    assert enroll(s, base).status_code == 201
    assert admin.delete(f"/admin/courses/{nxt['id']}").status_code == 200
    assert admin.delete(f"/admin/courses/{base['id']}").status_code == 409  # có sinh viên đăng ký
