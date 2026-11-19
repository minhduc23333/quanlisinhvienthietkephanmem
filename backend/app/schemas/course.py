from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator


class PrerequisiteOut(BaseModel):
    id: int
    code: str
    name: str
    met: bool | None = None  # None: người xem không phải sinh viên


class CourseOut(BaseModel):
    id: int
    code: str
    name: str
    max_students: int
    current_enrolled: int
    is_full: bool
    lecturer: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    waitlist_count: int = 0
    waitlist_position: int | None = None   # vị trí của chính sinh viên đang xem
    prerequisites: list[PrerequisiteOut] = []
    prerequisites_met: bool | None = None
    completed: bool | None = None          # sinh viên đã hoàn thành học phần này


def _check_date(value: str | None) -> str | None:
    if value in (None, ''):
        return None
    try:
        date.fromisoformat(value)
    except ValueError:
        raise ValueError('Ngày phải có dạng YYYY-MM-DD')
    return value


class CourseBase(BaseModel):
    lecturer: str | None = Field(default=None, max_length=140)
    start_date: str | None = None
    end_date: str | None = None

    @field_validator('start_date', 'end_date')
    @classmethod
    def _dates(cls, v):
        return _check_date(v)

    @model_validator(mode='after')
    def _order(self):
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValueError('Ngày kết thúc phải sau ngày bắt đầu')
        return self


class CourseCreate(CourseBase):
    code: str = Field(min_length=1, max_length=20)
    name: str = Field(min_length=1, max_length=160)
    max_students: int = Field(gt=0, le=10000)
    prerequisite_ids: list[int] = []


class CourseUpdate(CourseBase):
    code: str | None = Field(default=None, min_length=1, max_length=20)
    name: str | None = Field(default=None, min_length=1, max_length=160)
    max_students: int | None = Field(default=None, gt=0, le=10000)
    prerequisite_ids: list[int] | None = None
