# app/repositories/gupshup_repository.py
from sqlalchemy.orm import Session
from app.models.gupshup_log import TblGupshupLog
from datetime import datetime

class GupshupRepository:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def save_log(self, event: str, message_id: str = None, from_uid: str = None, 
                 type: str = None, app_id: str = None, channel: str = None) -> TblGupshupLog:
        """Guarda un registro en tbl_gupshup_log"""
        gupshup_log = TblGupshupLog(
            event=event,
            message_id=message_id,
            from_uid=from_uid,
            type=type,
            app_id=app_id,
            channel=channel,
            created_at=datetime.now()
        )
        
        self.db.add(gupshup_log)
        self.db.commit()
        self.db.refresh(gupshup_log)
        
        return gupshup_log
    
    def get_log_by_message_id(self, message_id: str) -> TblGupshupLog:
        """Busca un log por message_id"""
        return self.db.query(TblGupshupLog).filter(
            TblGupshupLog.message_id == message_id
        ).first()