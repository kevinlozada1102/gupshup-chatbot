# app/models/transfered_chat.py
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Numeric, Text
from sqlalchemy.sql import func
from app.config.database import Base

class TblTransferedChats(Base):
    __tablename__ = "tbl_transfered_chats"
    
    id = Column(Integer, primary_key=True, index=True)
    client_uid = Column(String(255))
    started_at = Column(DateTime, server_default=func.now())
    closed_at = Column(DateTime)
    attended_by = Column(String(255))
    attended_status = Column(String(10))
    account_id = Column(String(255))
    comment = Column(String(255))
    master_account = Column(String(255))
    client_name = Column(String(800))
    client_query = Column(String(500))
    dni = Column(String(512))
    motivo = Column(String(255))
    submotivo = Column(String(255))
    handler = Column(String(255))
    session_id = Column(String(255))
    chat_started_at = Column(DateTime)
    assign = Column(Boolean)
    duracion = Column(Numeric(12, 4))
    flag1 = Column(String(50))
    rating_text = Column(String(20))
    rating_number = Column(Integer)
    user_channel_icon = Column(String(255))
    tramite = Column(String(255))
    message_channel = Column(Integer)
    channel_code = Column(String(20))
    user_area = Column(Text)
    transfer = Column(Boolean)
    from_uid = Column(Text)
    appid = Column(Text)
    qualification = Column(Text)
    sentiment_analysis = Column(Text)
    language_id = Column(Text)
    ai_chat_rate = Column(Integer)
    fechalocal = Column(DateTime(timezone=True), server_default=func.timezone('America/Lima', func.current_timestamp()))
    survey_result = Column(Text)
    token_account = Column(Integer)
    token_chat_account = Column(Integer)
    motivo_encuesta = Column(Text)
    transfer_date = Column(DateTime, server_default=func.now())
    
    def __repr__(self):
        return f"<TblTransferedChats(id={self.id}, client_uid={self.client_uid}, handler={self.handler})>"