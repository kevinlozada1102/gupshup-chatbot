# app/repositories/text_chatbot_repository.py
from sqlalchemy.orm import Session
from app.models.text_chatbot import TblTextChatbot
from typing import Optional, List

class TextChatbotRepository:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def find_by_from_uid_and_channel(self, from_uid: str, channel: int) -> Optional[TblTextChatbot]:
        """
        Busca configuración por from_uid y canal específico
        Esta es la función principal para obtener el handler inicial
        """
        return self.db.query(TblTextChatbot).filter(
            TblTextChatbot.from_uid == from_uid,
            TblTextChatbot.channel == channel
        ).first()
    
    def find_by_from_uid(self, from_uid: str) -> List[TblTextChatbot]:
        """
        Obtiene todas las configuraciones de un from_uid en todos los canales
        """
        return self.db.query(TblTextChatbot).filter(
            TblTextChatbot.from_uid == from_uid
        ).order_by(TblTextChatbot.channel).all()
    
    def find_by_channel(self, channel: int) -> List[TblTextChatbot]:
        """
        Obtiene todas las configuraciones de un canal específico
        """
        return self.db.query(TblTextChatbot).filter(
            TblTextChatbot.channel == channel
        ).order_by(TblTextChatbot.from_uid).all()
    
    def find_by_initial_path(self, initial_path: str) -> List[TblTextChatbot]:
        """
        Encuentra todos los números que usan un handler inicial específico
        """
        return self.db.query(TblTextChatbot).filter(
            TblTextChatbot.initial_path == initial_path
        ).order_by(TblTextChatbot.from_uid, TblTextChatbot.channel).all()
    
    def create_text_chatbot_config(
        self, 
        from_uid: str, 
        channel: int, 
        initial_path: str
    ) -> TblTextChatbot:
        """
        Crea una nueva configuración de chatbot
        """
        new_config = TblTextChatbot(
            from_uid=from_uid,
            channel=channel,
            initial_path=initial_path
        )
        
        self.db.add(new_config)
        self.db.commit()
        self.db.refresh(new_config)
        return new_config
    
    def update_initial_path(self, from_uid: str, channel: int, new_initial_path: str) -> bool:
        """
        Actualiza el handler inicial para un número y canal específicos
        """
        try:
            config = self.find_by_from_uid_and_channel(from_uid, channel)
            if config:
                config.initial_path = new_initial_path
                self.db.commit()
                return True
            return False
        except Exception as e:
            print(f"❌ Error actualizando initial_path: {e}")
            return False
    
    def delete_config(self, from_uid: str, channel: int) -> bool:
        """
        Elimina configuración para un número y canal específicos
        """
        try:
            config = self.find_by_from_uid_and_channel(from_uid, channel)
            if config:
                self.db.delete(config)
                self.db.commit()
                return True
            return False
        except Exception as e:
            print(f"❌ Error eliminando configuración: {e}")
            return False
    
    def get_initial_path_for_whatsapp(self, from_uid: str) -> Optional[str]:
        """
        Método de conveniencia para obtener el handler inicial de WhatsApp (canal 0)
        """
        config = self.find_by_from_uid_and_channel(from_uid, 0)  # 0 = WhatsApp
        return config.initial_path if config else None
    
    def setup_whatsapp_chatbot(self, from_uid: str, initial_path: str) -> TblTextChatbot:
        """
        Método de conveniencia para configurar un chatbot de WhatsApp
        """
        return self.create_text_chatbot_config(from_uid, 0, initial_path)  # 0 = WhatsApp
    
    def get_all_configured_numbers(self) -> List[str]:
        """
        Obtiene lista de todos los números configurados (sin duplicados)
        """
        result = self.db.query(TblTextChatbot.from_uid).distinct().all()
        return [row.from_uid for row in result]
    
    def get_channel_stats(self) -> List[dict]:
        """
        Obtiene estadísticas de configuraciones por canal
        """
        from sqlalchemy import func
        
        result = self.db.query(
            TblTextChatbot.channel,
            func.count(TblTextChatbot.id).label('count')
        ).group_by(TblTextChatbot.channel).all()
        
        channel_names = {
            0: "WhatsApp",
            1: "Telegram", 
            2: "Facebook",
            3: "Instagram"
        }
        
        stats = []
        for channel, count in result:
            stats.append({
                "channel": channel,
                "channel_name": channel_names.get(channel, f"Canal {channel}"),
                "count": count
            })
        
        return sorted(stats, key=lambda x: x['channel'])