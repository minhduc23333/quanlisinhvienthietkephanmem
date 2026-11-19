from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CompletedCourse, Course, Enrollment, Schedule, User, WaitlistEntry
from app.services.course_service import completed_course_ids, lock_course
from app.services.schedule_service import slot_label


# ---------------------------------------------------------------- kiểm tra điều kiện

def conflicting_slots(db: Session, student_id: int, course_id: int) -> list[str]:
    """Các ca học của `course_id` trùng với học phần sinh viên đã đăng ký (ca = thứ + sáng/chiều)."""
    mine = {}
    for day, shift, name in db.execute(
            select(Schedule.day, Schedule.shift, Course.name)
            .join(Enrollment, Enrollment.course_id == Schedule.course_id)
            .join(Course, Course.id == Schedule.course_id)
            .where(Enrollment.student_id == student_id)).all():
        mine[(day, shift)] = name
    new = db.execute(select(Schedule.day, Schedule.shift).where(Schedule.course_id == course_id)
                     .order_by(Schedule.day, Schedule.shift)).all()
    return [f'{mine[(d, s)]} ({slot_label(d, s)})' for d, s in new if (d, s) in mine]


def check_conflict(student_id: int, course_id: int, db: Session) -> bool:
    return bool(conflicting_slots(db, student_id, course_id))


def missing_prerequisites(db: Session, student_id: int, course: Course) -> list[Course]:
    done = completed_course_ids(db, student_id)
    return [p for p in sorted(course.prerequisites, key=lambda p: p.code) if p.id not in done]


def eligibility_problem(db: Session, student_id: int, course: Course) -> tuple[str, str] | None:
    """(mã lỗi, thông báo) nếu sinh viên chưa đủ điều kiện học học phần, ngược lại None. Chưa xét sĩ số."""
    if db.scalar(select(Enrollment.id).where(Enrollment.student_id == student_id, Enrollment.course_id == course.id)):
        return 'enrolled', 'Bạn đã đăng ký học phần này'
    if db.scalar(select(CompletedCourse.id).where(CompletedCourse.student_id == student_id,
                                                  CompletedCourse.course_id == course.id)):
        return 'completed', 'Bạn đã hoàn thành học phần này'
    missing = missing_prerequisites(db, student_id, course)
    if missing:
        names = ', '.join(f'{p.code} - {p.name}' for p in missing)
        return 'prerequisite', f'Chưa hoàn thành môn tiên quyết: {names}'
    clashes = conflicting_slots(db, student_id, course.id)
    if clashes:
        return 'conflict', 'Trùng lịch với học phần đã đăng ký: ' + '; '.join(clashes)
    return None


def _ensure_eligible(db: Session, student_id: int, course: Course) -> None:
    problem = eligibility_problem(db, student_id, course)
    if problem:
        raise HTTPException(400, problem[1])


# ---------------------------------------------------------------- đăng ký / hủy

def enroll(db: Session, student: User, course_id: int) -> Course:
    course = lock_course(db, course_id)
    _ensure_eligible(db, student.id, course)
    if course.current_enrolled >= course.max_students:
        raise HTTPException(400, 'Học phần đã đủ sĩ số. Bạn có thể vào danh sách chờ.')
    db.add(Enrollment(student_id=student.id, course_id=course.id))
    course.current_enrolled += 1
    stale = db.scalar(select(WaitlistEntry).where(WaitlistEntry.student_id == student.id,
                                                  WaitlistEntry.course_id == course.id))
    if stale:
        db.delete(stale)
    db.commit()
    return course


def cancel_enrollment(db: Session, student_id: int, course_id: int) -> list[int]:
    """Hủy đăng ký, trả chỗ và tự xếp người đầu danh sách chờ (đủ điều kiện) vào lớp. Trả về id sinh viên được xếp."""
    course = lock_course(db, course_id)
    row = db.scalar(select(Enrollment).where(Enrollment.student_id == student_id, Enrollment.course_id == course_id))
    if not row:
        raise HTTPException(404, 'Không tìm thấy đăng ký')
    db.delete(row)
    course.current_enrolled = max(0, course.current_enrolled - 1)
    db.flush()
    promoted = promote_from_waitlist(db, course)
    db.commit()
    return promoted


# ---------------------------------------------------------------- danh sách chờ

def waitlist_position(db: Session, entry: WaitlistEntry) -> int:
    return db.scalar(select(func.count()).select_from(WaitlistEntry)
                     .where(WaitlistEntry.course_id == entry.course_id, WaitlistEntry.id <= entry.id))


def join_waitlist(db: Session, student: User, course_id: int) -> int:
    course = lock_course(db, course_id)
    _ensure_eligible(db, student.id, course)
    if course.current_enrolled < course.max_students:
        raise HTTPException(400, 'Học phần còn chỗ, hãy đăng ký trực tiếp')
    if db.scalar(select(WaitlistEntry.id).where(WaitlistEntry.student_id == student.id,
                                                WaitlistEntry.course_id == course.id)):
        raise HTTPException(400, 'Bạn đã ở trong danh sách chờ của học phần này')
    entry = WaitlistEntry(student_id=student.id, course_id=course.id)
    db.add(entry)
    db.flush()
    position = waitlist_position(db, entry)
    db.commit()
    return position


def leave_waitlist(db: Session, student_id: int, course_id: int) -> None:
    lock_course(db, course_id)
    entry = db.scalar(select(WaitlistEntry).where(WaitlistEntry.student_id == student_id,
                                                  WaitlistEntry.course_id == course_id))
    if not entry:
        raise HTTPException(404, 'Bạn không có trong danh sách chờ của học phần này')
    db.delete(entry)
    db.commit()


def promote_from_waitlist(db: Session, course: Course) -> list[int]:
    """Xếp sinh viên trong danh sách chờ vào lớp theo thứ tự đến trước được trước, cho đến khi hết chỗ.

    Người chưa đủ điều kiện (trùng lịch, thiếu tiên quyết, tài khoản khóa) bị bỏ qua nhưng vẫn giữ trong hàng chờ,
    để không chặn những người phía sau. Gọi khi đã khóa dòng `course` và chưa commit.
    """
    promoted: list[int] = []
    if course.current_enrolled >= course.max_students:
        return promoted
    entries = db.scalars(select(WaitlistEntry).where(WaitlistEntry.course_id == course.id)
                         .order_by(WaitlistEntry.id)).all()
    for entry in entries:
        if course.current_enrolled >= course.max_students:
            break
        user = db.get(User, entry.student_id)
        if user is None or user.is_locked or user.role != 'student':
            continue
        problem = eligibility_problem(db, entry.student_id, course)
        if problem and problem[0] in ('enrolled', 'completed'):
            db.delete(entry)  # mục chờ cũ không còn ý nghĩa
            continue
        if problem:
            continue
        db.add(Enrollment(student_id=entry.student_id, course_id=course.id))
        course.current_enrolled += 1
        db.delete(entry)
        db.flush()
        promoted.append(entry.student_id)
    return promoted


# ---------------------------------------------------------------- nghiệp vụ của Admin

def mark_completed(db: Session, student_id: int, course_id: int) -> None:
    """Ghi nhận sinh viên đã hoàn thành học phần. Nếu đang đăng ký học phần đó thì chuyển sang 'đã hoàn thành'."""
    student = db.get(User, student_id)
    if not student or student.role != 'student':
        raise HTTPException(404, 'Không tìm thấy tài khoản sinh viên')
    course = lock_course(db, course_id)
    if db.scalar(select(CompletedCourse.id).where(CompletedCourse.student_id == student_id,
                                                  CompletedCourse.course_id == course_id)):
        raise HTTPException(409, 'Sinh viên đã được ghi nhận hoàn thành học phần này')
    row = db.scalar(select(Enrollment).where(Enrollment.student_id == student_id, Enrollment.course_id == course_id))
    if row:
        db.delete(row)
        course.current_enrolled = max(0, course.current_enrolled - 1)
    entry = db.scalar(select(WaitlistEntry).where(WaitlistEntry.student_id == student_id,
                                                  WaitlistEntry.course_id == course_id))
    if entry:
        db.delete(entry)
    db.add(CompletedCourse(student_id=student_id, course_id=course_id))
    db.flush()
    if row:
        promote_from_waitlist(db, course)
    db.commit()


def remove_student(db: Session, user: User) -> None:
    """Xóa sinh viên cùng toàn bộ đăng ký, hàng chờ, lịch sử hoàn thành; trả chỗ cho người đang chờ."""
    enrollments = db.scalars(select(Enrollment).where(Enrollment.student_id == user.id)).all()
    course_ids = sorted({e.course_id for e in enrollments})
    for cid in course_ids:
        course = db.scalar(select(Course).where(Course.id == cid).with_for_update())
        if course:
            course.current_enrolled = max(0, course.current_enrolled - sum(e.course_id == cid for e in enrollments))
    for e in enrollments:
        db.delete(e)
    for model in (WaitlistEntry, CompletedCourse):
        for row in db.scalars(select(model).where(model.student_id == user.id)).all():
            db.delete(row)
    db.flush()
    db.delete(user)
    db.flush()
    for cid in course_ids:
        course = db.get(Course, cid)
        if course:
            promote_from_waitlist(db, course)
    db.commit()
