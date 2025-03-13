#app/models/exam.py
from sqlalchemy import Column, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime
import pytz
import ulid
from app.database import Base
timezone = pytz.timezone('UTC')

class Exam(Base):
    __tablename__ = 'exams'
    id = Column(String(26), primary_key=True, default=lambda: str(ulid.new()))
    title = Column(String(100), nullable=False)
    description = Column(String(500))
    user_id = Column(String(26), ForeignKey('users.id'))

    company_id = Column(String(26), ForeignKey('companies.id'))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    user = relationship("User", back_populates="exams")
    company = relationship("Company", back_populates="exams")

