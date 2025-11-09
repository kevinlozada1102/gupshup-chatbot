# app/repositories/session_data_repository.py
from sqlalchemy.orm import Session
from app.models.session_data import TblSessionData
from typing import Optional
import json

class SessionDataRepository:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def find_by_id(self, session_id: str) -> Optional[TblSessionData]:
        """Busca datos de sesión por ID"""
        return self.db.query(TblSessionData).filter(
            TblSessionData.id == session_id
        ).first()
    
    def save_session_data(self, session_id: str, data: dict) -> TblSessionData:
        """Guarda o actualiza datos de sesión"""
        existing_session = self.find_by_id(session_id)
        
        if existing_session:
            # Actualizar sesión existente
            existing_session.data = json.dumps(data, ensure_ascii=False)
            self.db.commit()
            self.db.refresh(existing_session)
            return existing_session
        else:
            # Crear nueva sesión
            new_session = TblSessionData(
                id=session_id,
                data=json.dumps(data, ensure_ascii=False)
            )
            self.db.add(new_session)
            self.db.commit()
            self.db.refresh(new_session)
            return new_session
    
    def get_session_data_as_dict(self, session_id: str) -> Optional[dict]:
        """Obtiene datos de sesión como diccionario Python"""
        session = self.find_by_id(session_id)
        if session and session.data:
            try:
                return json.loads(session.data)
            except json.JSONDecodeError:
                print(f"❌ Error decodificando JSON para session_id: {session_id}")
                return None
        return None
    
    def update_session_data(self, session_id: str, key: str, value) -> bool:
        """Actualiza un campo específico en los datos de sesión"""
        try:
            current_data = self.get_session_data_as_dict(session_id) or {}
            current_data[key] = value
            self.save_session_data(session_id, current_data)
            return True
        except Exception as e:
            print(f"❌ Error actualizando session_data: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """Elimina una sesión por ID"""
        try:
            session = self.find_by_id(session_id)
            if session:
                self.db.delete(session)
                self.db.commit()
                return True
            return False
        except Exception as e:
            print(f"❌ Error eliminando session: {e}")
            return False
    
    def clear_session_data(self, session_id: str) -> bool:
        """Limpia los datos de una sesión (mantiene el ID pero borra data)"""
        try:
            session = self.find_by_id(session_id)
            if session:
                session.data = None
                self.db.commit()
                return True
            return False
        except Exception as e:
            print(f"❌ Error limpiando session_data: {e}")
            return False