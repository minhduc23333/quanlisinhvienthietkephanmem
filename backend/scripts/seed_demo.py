import os
from sqlalchemy import select
from app.core.database import Base,engine,SessionLocal
from app.models import User,Course,Schedule,Enrollment,CompletedCourse
from app.core.security import hash_password
Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    # Admin được tạo qua setup_admin.py, không dùng .env.
    if not db.scalar(select(User.id).where(User.username=='sv001')):
        db.add(User(name='Nguyễn Văn An',username='sv001',role='student',password_hash=hash_password('12345678'),is_locked=False))
    specs=[('HP001','Lập trình Python',30,[(2,'sang'),(4,'sang')]),('HP002','Cơ sở dữ liệu',25,[(3,'chieu'),(5,'chieu')]),('HP003','Kiến trúc phần mềm',35,[(2,'chieu'),(6,'sang')]),('HP004','Mạng máy tính',30,[(4,'chieu')]),('HP005','Trí tuệ nhân tạo',25,[(3,'sang'),(5,'sang')]),('HP006','Phát triển phần mềm hướng dịch vụ',1,[(2,'sang')]),('HP007','Thiết kế Web',40,[(6,'chieu')]),('HP008','Toán rời rạc',40,[(7,'sang')]),('HP009','An toàn thông tin',35,[(5,'chieu')]),('HP010','Hệ quản trị cơ sở dữ liệu',25,[(7,'chieu')])]
    db.flush()
    for code,name,limit,slots in specs:
        course=db.scalar(select(Course).where(Course.code==code))
        if course is None:
            course=Course(code=code,name=name,max_students=limit,current_enrolled=0);db.add(course);db.flush()
        for day,shift in slots:
            if not db.scalar(select(Schedule.id).where(Schedule.course_id==course.id,Schedule.day==day,Schedule.shift==shift)):
                db.add(Schedule(course_id=course.id,day=day,shift=shift))
    # Bổ sung thông tin chi tiết học phần cho bản demo; không ghi đè dữ liệu đã thiết lập.
    metadata={
      'HP001':('ThS. Trần Minh Quân','P. A203'),'HP002':('ThS. Nguyễn Thị Hà','P. B105'),
      'HP003':('TS. Lê Anh Tuấn','P. A301'),'HP004':('ThS. Phạm Quốc Bảo','P. C204'),
      'HP005':('TS. Vũ Thu Trang','P. B302'),'HP006':('ThS. Đỗ Văn Nam','P. C101'),
      'HP007':('ThS. Mai Thanh Hương','P. A205'),'HP008':('ThS. Nguyễn Quang Huy','P. B201'),
      'HP009':('TS. Trịnh Hoài An','P. C303'),'HP010':('ThS. Lê Thị Lan','P. B108')}
    for c in db.scalars(select(Course)).all():
        if c.code not in metadata:continue
        teacher,room=metadata[c.code]
        if not c.lecturer:c.lecturer=teacher
        if not c.start_date:c.start_date='2027-01-11'
        if not c.end_date:c.end_date='2027-05-16'
        for slot in c.schedules:
            if not slot.start_time:slot.start_time='07:00' if slot.shift=='sang' else '13:00'
            if not slot.end_time:slot.end_time='11:00' if slot.shift=='sang' else '17:00'
            if not slot.room:slot.room=room
    db.flush()
    demo=db.scalar(select(User).where(User.username=='sv_full_demo'))
    if demo is None:demo=User(name='Sinh viên thử lớp đầy',username='sv_full_demo',role='student',password_hash=hash_password('12345678'));db.add(demo);db.flush()
    course=db.scalar(select(Course).where(Course.code=='HP006'))
    if not db.scalar(select(Enrollment.id).where(Enrollment.student_id==demo.id,Enrollment.course_id==course.id)):
        db.add(Enrollment(student_id=demo.id,course_id=course.id));course.current_enrolled+=1
    # Môn tiên quyết (demo): HP006 cố ý KHÔNG có tiên quyết để còn thử 'lớp đầy' + danh sách chờ.
    prerequisites={'HP003':['HP001'],'HP005':['HP001','HP008'],'HP009':['HP004'],'HP010':['HP002']}
    by_code={c.code:c for c in db.scalars(select(Course)).all()}
    for code,needs in prerequisites.items():
        course=by_code.get(code)
        if course is None:continue
        have={p.code for p in course.prerequisites}
        for need in needs:
            if need not in have and need in by_code:course.prerequisites.append(by_code[need])
    # sv001 đã học xong HP002 và HP004: đủ điều kiện HP010/HP009, còn thiếu HP001 nên bị chặn HP003/HP005.
    sv001=db.scalar(select(User).where(User.username=='sv001'))
    for code in ('HP002','HP004'):
        course=by_code.get(code)
        if sv001 and course and not db.scalar(select(CompletedCourse.id).where(CompletedCourse.student_id==sv001.id,CompletedCourse.course_id==course.id)):
            db.add(CompletedCourse(student_id=sv001.id,course_id=course.id))
    db.commit()
print('Tạo dữ liệu demo thành công. Chạy python -m scripts.setup_admin để tạo/cập nhật Admin.')
