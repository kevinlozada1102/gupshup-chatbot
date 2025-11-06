# app/repositories/message_repository.py
from sqlalchemy.orm import Session
from app.models.message import TblMessage
from datetime import datetime
from typing import Optional

class MessageRepository:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def save_message(self, from_uid: str, client_uid: str, message_body: str, 
                    account_id: str, session_id: int, message_id: str, 
                    message_channel: int = 0, message_direction: int = 0, 
                    message_type: int = 0) -> TblMessage:
        """Guarda un mensaje - equivale a messageRepository.save() en Java"""
        
        message = TblMessage(
            from_uid=from_uid,
            client_uid=client_uid,
            created_at=datetime.now(),
            message=message_body,
            message_channel=message_channel,
            message_direction=message_direction,
            message_type=message_type,
            account_id=account_id,
            session_id=session_id,
            message_id=message_id
        )
        
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        
        return message
    
    def find_by_message_id(self, message_id: str) -> Optional[TblMessage]:
        """Busca mensaje por message_id"""
        return self.db.query(TblMessage).filter(
            TblMessage.message_id == message_id
        ).first()
    
    def find_by_session_id(self, session_id: int, limit: int = 50) -> list[TblMessage]:
        """Obtiene mensajes de una sesión (para historial)"""
        return self.db.query(TblMessage).filter(
            TblMessage.session_id == session_id
        ).order_by(TblMessage.created_at.desc()).limit(limit).all()