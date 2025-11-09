# app/repositories/transfered_chat_repository.py
from sqlalchemy.orm import Session
from app.models.transfered_chat import TblTransferedChats
from typing import Optional, List

class TransferedChatRepository:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def save(self, transfered_chat: TblTransferedChats) -> TblTransferedChats:
        """Guarda una transferencia de chat"""
        self.db.add(transfered_chat)
        self.db.commit()
        self.db.refresh(transfered_chat)
        return transfered_chat
    
    def find_active_by_client_uid(self, client_uid: str) -> Optional[TblTransferedChats]:
        """Busca transferencia activa por client_uid (no cerrada)"""
        return self.db.query(TblTransferedChats).filter(
            TblTransferedChats.client_uid == client_uid,
            TblTransferedChats.closed_at.is_(None)
        ).first()
    
    def find_active_by_session_id(self, session_id: str) -> Optional[TblTransferedChats]:
        """Busca transferencia activa por session_id (no cerrada)"""
        return self.db.query(TblTransferedChats).filter(
            TblTransferedChats.session_id == session_id,
            TblTransferedChats.closed_at.is_(None)
        ).first()
    
    def list_pending(self) -> List[TblTransferedChats]:
        """Lista transferencias pendientes (sin asignar a agente)"""
        return self.db.query(TblTransferedChats).filter(
            TblTransferedChats.attended_by.is_(None),
            TblTransferedChats.closed_at.is_(None)
        ).all()
    
    def count_attended_by(self) -> List[tuple]:
        """Cuenta transferencias por agente (similar a AttendedByCount del original)"""
        return self.db.query(
            TblTransferedChats.attended_by,
            self.db.query().func.count(TblTransferedChats.id)
        ).filter(
            TblTransferedChats.attended_by.isnot(None),
            TblTransferedChats.closed_at.is_(None)
        ).group_by(TblTransferedChats.attended_by).all()
    
    def close_transfer(self, transfer_id: int) -> bool:
        """Cierra una transferencia"""
        transfer = self.db.query(TblTransferedChats).filter(
            TblTransferedChats.id == transfer_id
        ).first()
        
        if transfer:
            from datetime import datetime
            transfer.closed_at = datetime.now()
            self.db.commit()
            return True
        return False