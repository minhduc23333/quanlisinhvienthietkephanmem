from sqlalchemy import Boolean, Column, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    role = Column(String(20), nullable=False, default='student')
    username = Column(String(80), unique=True, nullable=False, index=True)
    email = Column(String(254), unique=True, nullable=True, index=True)
    password_hash = Column(String(255), nullable=False)
    is_locked = Column(Boolean, nullable=False, default=False, server_default='0')
    enrollments = relationship('Enrollment', back_populates='student')
