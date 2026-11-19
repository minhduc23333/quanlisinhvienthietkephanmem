from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from app.models import Course, Enrollment, Schedule

DAY_NAME = {2: 'Thứ 2', 3: 'Thứ 3', 4: 'Thứ 4', 5: 'Thứ 5', 6: 'Thứ 6', 7: 'Thứ 7'}
SHIFT_NAME = {'sang': 'Sáng', 'chieu': 'Chiều'}


def slot_label(day: int, shift: str) -> str:
    return f'{DAY_NAME.get(day, day)} - ca {SHIFT_NAME.get(shift, shift).lower()}'


def validate_slot(db: Session, course: Course, day: int, shift: str, room: str | None,
                  schedule_id: int | None = None) -> None:
    """Chặn lịch mới/sửa nếu: trùng ca của chính học phần, trùng phòng, hoặc làm sinh viên bị trùng lịch."""
    dup = select(Schedule.id).where(Schedule.course_id == course.id, Schedule.day == day, Schedule.shift == shift)
    if schedule_id is not None:
        dup = dup.where(Schedule.id != schedule_id)
    if db.scalar(dup):
        raise HTTPException(409, 'Lịch học đã tồn tại')

    if room:
        clash = db.execute(
            select(Course.code).join(Schedule, Schedule.course_id == Course.id)
            .where(func.lower(Schedule.room) == room.lower(), Schedule.day == day, Schedule.shift == shift,
                   Schedule.course_id != course.id)).first()
        if clash:
            raise HTTPException(409, f'Phòng {room} đã được học phần {clash[0]} sử dụng vào {slot_label(day, shift)}')

    other = aliased(Enrollment)
    other_slot = aliased(Schedule)
    affected = db.scalar(
        select(func.count(func.distinct(Enrollment.student_id)))
        .join(other, other.student_id == Enrollment.student_id)
        .join(other_slot, other_slot.course_id == other.course_id)
        .where(Enrollment.course_id == course.id, other.course_id != course.id,
               other_slot.day == day, other_slot.shift == shift))
    if affected:
        raise HTTPException(409, f'Lịch này gây trùng thời khóa biểu của {affected} sinh viên đã đăng ký học phần')
