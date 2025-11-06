# app/models/session_segment.py
from sqlalchemy import Column, Integer, BigInteger, DateTime
from . import Base

class TblChatSessionSegment(Base):
    __tablename__ = 'tbl_chat_session_segment'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, nullable=True)
    ended_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    correlative = Column(Integer, nullable=True)
    
    def __repr__(self):
        return f"<TblChatSessionSegment(id={self.id}, session_id={self.session_id}, correlative={self.correlative})>"