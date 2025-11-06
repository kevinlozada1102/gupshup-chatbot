# app/models/chat_session.py
from sqlalchemy import Column, Integer, Text, DateTime, Boolean
from . import Base

class TblChatSession(Base):
    __tablename__ = 'tbl_chat_session'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    ended_at = Column(DateTime, nullable=True)
    started_at = Column(DateTime, nullable=True)
    client_uid = Column(Text, nullable=True)
    from_uid = Column(Text, nullable=True)
    account_id = Column(Text, nullable=True)
    message_channel = Column(Integer, nullable=True)
    attended_by = Column(Text, nullable=True)
    message_direction = Column(Integer, nullable=True)
    isclosed = Column(Boolean, default=False)
    
    def __repr__(self):
        return f"<TblChatSession(id={self.id}, client_uid='{self.client_uid}', isclosed={self.isclosed})>"