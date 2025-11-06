# app/models/message.py
from sqlalchemy import Column, Integer, Text, DateTime, BigInteger, String
from . import Base

class TblMessage(Base):
    __tablename__ = 'tbl_message'
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    from_uid = Column(Text, nullable=True)
    client_uid = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    message = Column(Text, nullable=True)
    message_channel = Column(Integer, nullable=True)
    message_direction = Column(Integer, nullable=True)
    message_type = Column(Integer, nullable=True)
    account_id = Column(String(255), nullable=True)
    session_id = Column(BigInteger, nullable=True)
    attended_by = Column(String(255), nullable=True)
    attended_status = Column(String(10), nullable=True)
    message_id = Column(String(255), nullable=True)
    nodo_id = Column(BigInteger, nullable=True)
    
    def __repr__(self):
        return f"<TblMessage(id={self.id}, message_id='{self.message_id}', session_id={self.session_id})>"