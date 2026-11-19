from pydantic import BaseModel


class EnrollmentCreate(BaseModel):
    student_id: int
    course_id: int


class CompletedCreate(BaseModel):
    course_id: int
