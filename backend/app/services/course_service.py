from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import CompletedCourse, Course, Enrollment, User, WaitlistEntry
from app.schemas import CourseOut, PrerequisiteOut


def get_course_or_404(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if not course:
        raise HTTPException(404, 'Không tìm thấy học phần')
    return course


def lock_course(db: Session, course_id: int) -> Course:
    """Khóa dòng học phần (SELECT ... FOR UPDATE) để các thao tác đăng ký/hủy xếp hàng tuần tự."""
    course = db.scalar(select(Course).where(Course.id == course_id).with_for_update()
                       .execution_options(populate_existing=True))
    if not course:
        raise HTTPException(404, 'Không tìm thấy học phần')
    return course


def completed_course_ids(db: Session, student_id: int) -> set[int]:
    return set(db.scalars(select(CompletedCourse.course_id).where(CompletedCourse.student_id == student_id)).all())


def waitlist_positions(db: Session, student_id: int) -> dict[int, int]:
    """{course_id: vị trí (bắt đầu từ 1)} của sinh viên trong các danh sách chờ."""
    result = {}
    for entry_id, course_id in db.execute(
            select(WaitlistEntry.id, WaitlistEntry.course_id).where(WaitlistEntry.student_id == student_id)).all():
        result[course_id] = db.scalar(
            select(func.count()).select_from(WaitlistEntry)
            .where(WaitlistEntry.course_id == course_id, WaitlistEntry.id <= entry_id))
    return result


def build_course_out(db: Session, courses: list[Course], viewer: User) -> list[CourseOut]:
    counts = dict(db.execute(select(WaitlistEntry.course_id, func.count()).group_by(WaitlistEntry.course_id)).all())
    is_student = viewer.role == 'student'
    done = completed_course_ids(db, viewer.id) if is_student else set()
    positions = waitlist_positions(db, viewer.id) if is_student else {}
    result = []
    for c in courses:
        prereqs = [PrerequisiteOut(id=p.id, code=p.code, name=p.name, met=(p.id in done) if is_student else None)
                   for p in sorted(c.prerequisites, key=lambda p: p.code)]
        result.append(CourseOut(
            id=c.id, code=c.code, name=c.name, max_students=c.max_students, current_enrolled=c.current_enrolled,
            is_full=c.current_enrolled >= c.max_students, lecturer=c.lecturer, start_date=c.start_date,
            end_date=c.end_date, waitlist_count=counts.get(c.id, 0), waitlist_position=positions.get(c.id),
            prerequisites=prereqs,
            prerequisites_met=all(p.met for p in prereqs) if is_student else None,
            completed=(c.id in done) if is_student else None))
    return result


def _reaches(start: Course, target_id: int | None) -> bool:
    """True nếu từ `start` đi theo chuỗi môn tiên quyết sẽ gặp `target_id`."""
    seen, stack = set(), [start]
    while stack:
        node = stack.pop()
        if node.id == target_id:
            return True
        if node.id in seen:
            continue
        seen.add(node.id)
        stack.extend(node.prerequisites)
    return False


def set_prerequisites(db: Session, course: Course, prerequisite_ids: list[int]) -> None:
    ids = list(dict.fromkeys(prerequisite_ids))
    if course.id is not None and course.id in ids:
        raise HTTPException(400, 'Học phần không thể là môn tiên quyết của chính nó')
    found = db.scalars(select(Course).where(Course.id.in_(ids))).all() if ids else []
    if len(found) != len(ids):
        raise HTTPException(400, 'Có môn tiên quyết không tồn tại')
    for p in found:
        if course.id is not None and _reaches(p, course.id):
            raise HTTPException(400, f'Tiên quyết bị vòng lặp: {p.code} đã yêu cầu {course.code} (trực tiếp hoặc gián tiếp)')
    course.prerequisites = list(found)


def delete_course(db: Session, course: Course) -> None:
    if db.scalar(select(func.count()).select_from(Enrollment).where(Enrollment.course_id == course.id)):
        raise HTTPException(409, 'Học phần đã có sinh viên đăng ký, không thể xóa')
    if db.scalar(select(func.count()).select_from(CompletedCourse).where(CompletedCourse.course_id == course.id)):
        raise HTTPException(409, 'Đã có sinh viên hoàn thành học phần này, không thể xóa')
    if course.required_by:
        codes = ', '.join(sorted(c.code for c in course.required_by))
        raise HTTPException(409, f'Học phần đang là môn tiên quyết của: {codes}')
    for entry in db.scalars(select(WaitlistEntry).where(WaitlistEntry.course_id == course.id)).all():
        db.delete(entry)
    course.prerequisites = []
    db.flush()
    db.delete(course)
