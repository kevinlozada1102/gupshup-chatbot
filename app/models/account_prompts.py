# app/models/account_prompts.py
from sqlalchemy import Column, Integer, Text, Boolean, DateTime
from sqlalchemy.sql import func
from . import Base

class TblAccountPrompts(Base):
    __tablename__ = 'tbl_account_prompts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Text, nullable=False)
    prompt_content = Column(Text, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=True, default=func.now())
    updated_at = Column(DateTime, nullable=True, default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<TblAccountPrompts(id={self.id}, account_id='{self.account_id}', is_active={self.is_active})>"