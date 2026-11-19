from app.models.user import User
from app.models.course import Course, course_prerequisites
from app.models.schedule import Schedule
from app.models.enrollment import Enrollment
from app.models.waitlist import WaitlistEntry
from app.models.completed_course import CompletedCourse

__all__ = ['User', 'Course', 'Schedule', 'Enrollment', 'WaitlistEntry', 'CompletedCourse', 'course_prerequisites']
