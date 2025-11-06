# app/models/gupshup_log.py
from sqlalchemy import Column, Integer, Text, DateTime, String
from . import Base

class TblGupshupLog(Base):
    __tablename__ = 'tbl_gupshup_log'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_uid = Column(Text, nullable=True)
    event = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    message_id = Column(String(255), nullable=True)
    app_id = Column(Text, nullable=True)
    type = Column(Text, nullable=True)
    channel = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<TblGupshupLog(id={self.id}, event='{self.event}', message_id='{self.message_id}')>"