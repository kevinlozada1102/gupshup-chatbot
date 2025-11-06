# app/repositories/chat_session_repository.py
from sqlalchemy.orm import Session
from app.models.chat_session import TblChatSession
from datetime import datetime, timedelta
from typing import Optional

class ChatSessionRepository:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def find_active_session(self, client_uid: str, from_uid: str, current_time: datetime) -> Optional[TblChatSession]:
        """
        Busca sesión activa - equivale a findActiveSession en Java
        Una sesión está activa si no está cerrada y está dentro del rango de tiempo
        """
        return self.db.query(TblChatSession).filter(
            TblChatSession.client_uid == client_uid,
            TblChatSession.from_uid == from_uid,
            TblChatSession.isclosed == False,
            TblChatSession.started_at <= current_time,
            TblChatSession.ended_at >= current_time
        ).first()
    
    def create_session(self, client_uid: str, from_uid: str, account_id: str = None) -> TblChatSession:
        """Crea nueva sesión de chat"""
        current_time = datetime.now()
        
        chat_session = TblChatSession(
            started_at=current_time,
            ended_at=current_time + timedelta(days=1),  # Expira en 24 horas
            client_uid=client_uid,
            from_uid=from_uid,
            account_id=account_id,
            message_channel=0,  # WhatsApp por defecto
            message_direction=0,  # Incoming
            isclosed=False
        )
        
        self.db.add(chat_session)
        self.db.commit()
        self.db.refresh(chat_session)
        
        return chat_session
    
    def close_session(self, session_id: int) -> bool:
        """Cierra una sesión"""
        session = self.db.query(TblChatSession).filter(
            TblChatSession.id == session_id
        ).first()
        
        if session:
            session.isclosed = True
            session.ended_at = datetime.now()
            self.db.commit()
            return True
        
        return False