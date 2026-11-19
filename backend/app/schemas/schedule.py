from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

TIME_PATTERN = r'^([01]\d|2[0-3]):[0-5]\d$'


class _TimeRange(BaseModel):
    @model_validator(mode='after')
    def _order(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValueError('Giờ kết thúc phải sau giờ bắt đầu')
        return self


class ScheduleCreate(_TimeRange):
    course_id: int
    day: int = Field(ge=2, le=7)
    shift: Literal['sang', 'chieu']
    start_time: str | None = Field(default=None, pattern=TIME_PATTERN)
    end_time: str | None = Field(default=None, pattern=TIME_PATTERN)
    room: str | None = Field(default=None, max_length=50)


class ScheduleUpdate(_TimeRange):
    day: int | None = Field(default=None, ge=2, le=7)
    shift: Literal['sang', 'chieu'] | None = None
    start_time: str | None = Field(default=None, pattern=TIME_PATTERN)
    end_time: str | None = Field(default=None, pattern=TIME_PATTERN)
    room: str | None = Field(default=None, max_length=50)


class ScheduleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    course_id: int
    day: int
    shift: str
    start_time: str | None = None
    end_time: str | None = None
    room: str | None = None
