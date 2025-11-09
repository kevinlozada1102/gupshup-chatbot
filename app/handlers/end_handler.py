# app/handlers/end_handler.py
from typing import Dict, Any
from app.handlers.base_handler import BaseHandler

class EndHandler(BaseHandler):
    """
    Handler que finaliza conversaciones.
    Equivale al EndHandler o finalización de conversación en tenet.
    """
    
    def __init__(self):
        super().__init__("EndHandler")
    
    def process_message(self, message: str, session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa finalización de conversación.
        """
        print(f"🏁 EndHandler: Finalizando conversación para {context.get('client_uid')}")
        
        # Limpiar session_data
        updated_session_data = session_data.copy()
        updated_session_data["conversation_ended"] = True
        updated_session_data["current_path"] = ""
        
        return {
            "success": True,
            "message": "¡Gracias por contactarnos! La conversación ha finalizado. Puedes escribir nuevamente cuando lo necesites.",
            "next_path": None,
            "next_handler": None,
            "session_data": updated_session_data,
            "conversation_ended": True
        }
    
    def request_action(self, message_channel: int, from_uid: str, client_uid: str, 
                      session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """RequestAction para EndHandler es igual a process_message"""
        return self.process_message("", session_data, context)