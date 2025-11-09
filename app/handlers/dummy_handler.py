# app/handlers/dummy_handler.py
from typing import Dict, Any
from app.handlers.base_handler import BaseHandler

class DummyHandler(BaseHandler):
    """
    Handler dummy/simple para testing y casos básicos.
    Equivale al DummyHandler en tenet.
    """
    
    def __init__(self):
        super().__init__("DummyHandler")
    
    def process_message(self, message: str, session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa mensaje de forma simple - principalmente para testing.
        """
        print(f"🎪 DummyHandler: Procesando mensaje '{message}' para {context.get('client_uid')}")
        
        # Por defecto, finaliza la conversación
        updated_session_data = session_data.copy()
        updated_session_data["dummy_processed"] = True
        
        return {
            "success": True,
            "message": "Mensaje procesado por DummyHandler. Finalizando conversación.",
            "next_path": "/EndHandler",
            "next_handler": "EndHandler",
            "session_data": updated_session_data
        }
    
    def request_action(self, message_channel: int, from_uid: str, client_uid: str, 
                      session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """RequestAction para DummyHandler"""
        print(f"🎪 DummyHandler: RequestAction para {client_uid}")
        
        return {
            "success": True,
            "message": "DummyHandler activado. Escribe cualquier cosa para continuar.",
            "next_path": session_data.get("current_path"),
            "next_handler": self.name,
            "session_data": session_data
        }