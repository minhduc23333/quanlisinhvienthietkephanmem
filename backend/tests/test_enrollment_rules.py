from tests.conftest import cancel, enroll, my_courses


def test_enroll_view_timetable_cancel(make_course, make_student):
    c = make_course('A', slots=[(2, 'sang', 'P1'), (4, 'sang', 'P1')], lecturer='GV')
    s = make_student()
    assert enroll(s, c).status_code == 201
    assert enroll(s, c).status_code == 400  # đã đăng ký
    tt = s.get(f"/enrollments/{s.user['id']}/schedule").json()
    assert {(r['day'], r['shift']) for r in tt} == {(2, 'sang'), (4, 'sang')}
    assert s.get('/courses').json()[0]['current_enrolled'] == 1
    assert cancel(s, c).status_code == 200
    assert s.get('/courses').json()[0]['current_enrolled'] == 0
    assert cancel(s, c).status_code == 404


def test_schedule_conflict(make_course, make_student):
    a = make_course('A', slots=[(2, 'sang')])
    b = make_course('B', slots=[(2, 'sang'), (5, 'chieu')])
    s = make_student()
    assert enroll(s, a).status_code == 201
    r = enroll(s, b)
    assert r.status_code == 400 and 'Trùng lịch' in r.json()['detail'] and 'Mon A' in r.json()['detail']


def test_full_class(make_course, make_student):
    c = make_course('A', 1, slots=[(2, 'sang')])
    assert enroll(make_student(), c).status_code == 201
    r = enroll(make_student(), c)
    assert r.status_code == 400 and 'đủ sĩ số' in r.json()['detail']
    out = make_student().get('/courses').json()[0]
    assert out['is_full'] and out['current_enrolled'] == 1


def test_cannot_act_for_other_student(make_course, make_student):
    c = make_course('A', slots=[(2, 'sang')])
    s1, s2 = make_student(), make_student()
    assert s1.post('/enrollments', json={'student_id': s2.user['id'], 'course_id': c['id']}).status_code == 403
    assert s1.get(f"/enrollments/{s2.user['id']}").status_code == 403
    assert s1.get(f"/enrollments/{s2.user['id']}/schedule").status_code == 403
    assert s1.delete(f"/enrollments/{s2.user['id']}/{c['id']}").status_code == 403
    assert s1.post('/waitlist', json={'student_id': s2.user['id'], 'course_id': c['id']}).status_code == 403
    assert s1.get(f"/waitlist/{s2.user['id']}").status_code == 403


def test_prerequisite_blocks_until_completed(admin, make_course, make_student):
    base = make_course('BASE', slots=[(2, 'sang')])
    adv = make_course('ADV', slots=[(3, 'sang')], prerequisites=[base['id']])
    s = make_student()
    r = enroll(s, adv)
    assert r.status_code == 400 and 'BASE' in r.json()['detail'] and 'tiên quyết' in r.json()['detail']
    info = next(c for c in s.get('/courses').json() if c['code'] == 'ADV')
    assert info['prerequisites_met'] is False and info['prerequisites'][0]['met'] is False
    # đăng ký (chưa hoàn thành) môn tiên quyết vẫn chưa đủ điều kiện
    assert enroll(s, base).status_code == 201
    assert enroll(s, adv).status_code == 400
    # Admin ghi nhận hoàn thành -> mở khóa
    assert admin.post(f"/admin/users/{s.user['id']}/completed", json={'course_id': base['id']}).status_code == 201
    info = next(c for c in s.get('/courses').json() if c['code'] == 'ADV')
    assert info['prerequisites_met'] is True
    assert enroll(s, adv).status_code == 201
    # không đăng ký lại môn đã hoàn thành
    r = enroll(s, base)
    assert r.status_code == 400 and 'hoàn thành' in r.json()['detail']


def test_multiple_prerequisites_all_required(admin, make_course, make_student):
    a, b = make_course('A'), make_course('B')
    c = make_course('C', slots=[(2, 'sang')], prerequisites=[a['id'], b['id']])
    s = make_student()
    admin.post(f"/admin/users/{s.user['id']}/completed", json={'course_id': a['id']})
    r = enroll(s, c)
    assert r.status_code == 400 and 'B -' in r.json()['detail'] and 'A -' not in r.json()['detail']
    admin.post(f"/admin/users/{s.user['id']}/completed", json={'course_id': b['id']})
    assert enroll(s, c).status_code == 201


def test_prerequisite_cycle_and_self_rejected(admin, make_course):
    a = make_course('A')
    b = make_course('B', prerequisites=[a['id']])
    c = make_course('C', prerequisites=[b['id']])
    assert admin.patch(f"/admin/courses/{a['id']}", json={'prerequisite_ids': [a['id']]}).status_code == 400
    assert admin.patch(f"/admin/courses/{a['id']}", json={'prerequisite_ids': [b['id']]}).status_code == 400
    r = admin.patch(f"/admin/courses/{a['id']}", json={'prerequisite_ids': [c['id']]})
    assert r.status_code == 400 and 'vòng lặp' in r.json()['detail']
    assert admin.patch(f"/admin/courses/{c['id']}", json={'prerequisite_ids': [a['id']]}).status_code == 200
    assert admin.patch(f"/admin/courses/{c['id']}", json={'prerequisite_ids': [999]}).status_code == 400
    assert admin.patch(f"/admin/courses/{c['id']}", json={'prerequisite_ids': []}).json()['prerequisites'] == []


def test_completed_admin_api(admin, make_course, make_student):
    c = make_course('A', slots=[(2, 'sang')])
    s = make_student()
    url = f"/admin/users/{s.user['id']}/completed"
    assert admin.post(url, json={'course_id': c['id']}).status_code == 201
    assert admin.post(url, json={'course_id': c['id']}).status_code == 409
    assert admin.post(url, json={'course_id': 999}).status_code == 404
    assert admin.post('/admin/users/9999/completed', json={'course_id': c['id']}).status_code == 404
    assert [x['code'] for x in admin.get(url).json()] == ['A']
    assert [x['code'] for x in s.get(f"/students/{s.user['id']}/completed").json()] == ['A']
    assert s.post(url, json={'course_id': c['id']}).status_code == 403
    assert admin.delete(f"{url}/{c['id']}").status_code == 200
    assert admin.delete(f"{url}/{c['id']}").status_code == 404


def test_marking_completed_converts_active_enrollment_and_frees_seat(admin, make_course, make_student):
    c = make_course('A', 1, slots=[(2, 'sang')])
    s1, s2 = make_student(), make_student()
    assert enroll(s1, c).status_code == 201
    from tests.conftest import join_waitlist
    assert join_waitlist(s2, c).status_code == 201
    assert admin.post(f"/admin/users/{s1.user['id']}/completed", json={'course_id': c['id']}).status_code == 201
    assert my_courses(s1) == set() and my_courses(s2) == {'A'}
