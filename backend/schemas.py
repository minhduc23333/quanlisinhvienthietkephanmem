from pydantic import BaseModel, Field, ConfigDict
from typing import Literal
class LoginIn(BaseModel):
    username: str = Field(min_length=3,max_length=254)  # email, or admin/legacy username
    password: str = Field(min_length=1)
class RegisterIn(BaseModel):
    name: str = Field(min_length=2,max_length=120)
    email: str = Field(min_length=5,max_length=254)
    password: str = Field(min_length=8,max_length=128)
class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id:int
    name:str
    role:str
    username:str
    email:str|None=None
class CourseOut(BaseModel):
    id:int
    code:str
    name:str
    max_students:int
    current_enrolled:int
    is_full:bool
    lecturer:str|None=None
    start_date:str|None=None
    end_date:str|None=None
class ScheduleCreate(BaseModel):
    course_id:int
    day:int=Field(ge=2,le=7)
    shift:Literal['sang','chieu']
    start_time:str|None=None
    end_time:str|None=None
    room:str|None=None
class ScheduleOut(ScheduleCreate):
    id:int
    model_config=ConfigDict(from_attributes=True)
class EnrollmentCreate(BaseModel):
    student_id:int
    course_id:int
