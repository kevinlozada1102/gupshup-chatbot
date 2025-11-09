# app/models/text_chatbot.py
from sqlalchemy import Column, Integer, Text
from . import Base

class TblTextChatbot(Base):
    __tablename__ = 'tbl_text_chatbot'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    from_uid = Column(Text, nullable=False)                  # varchar(20) - Número del chatbot
    channel = Column(Integer, nullable=False)                # integer - Canal: 0=WhatsApp, 1=Telegram, etc.
    initial_path = Column(Text, nullable=False)              # varchar(255) - Handler inicial (ej: /DbAnswerHandler/menu)
    
    def __repr__(self):
        return f"<TblTextChatbot(id={self.id}, from_uid='{self.from_uid}', channel={self.channel}, initial_path='{self.initial_path}')>"