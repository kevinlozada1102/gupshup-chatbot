# app/handlers/base_handler.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

class BaseHandler(ABC):
    """
    Clase base abstracta para todos los handlers del sistema.
    Inspirado en el sistema de mazz-chatbot de tenet.
    """
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def process_message(self, message: str, session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa un mensaje y retorna la respuesta.
        
        Args:
            message: Mensaje del usuario
            session_data: Datos de la sesión actual (equivale a SessionData en tenet)
            context: Contexto adicional (from_uid, account_id, etc.)
            
        Returns:
            Dict con: {
                "success": bool,
                "message": str,  # Mensaje a enviar al usuario
                "next_path": str,  # Próxima ruta (puede ser None)
                "next_handler": str,  # Próximo handler (puede ser None) 
                "session_data": dict  # Datos actualizados de sesión
            }
        """
        pass
    
    def request_action(self, message_channel: int, from_uid: str, client_uid: str, 
                      session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Método equivalente a requestAction() en tenet.
        Por defecto llama a process_message, pero puede ser sobrescrito.
        """
        return self.process_message("", session_data, context)
    
    def _extract_handler_name(self, path: str) -> Optional[str]:
        """
        Extrae el nombre del handler de un path.
        Ej: "/DbAnswerHandler/menu/1" → "DbAnswerHandler" 
        """
        if not path or path == "/EndHandler":
            return None
        
        parts = path.strip('/').split('/')
        return parts[0] if parts else None
    
    def _handle_invalid_option(self, session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Maneja opciones inválidas (equivale al manejo de error en DbAnswerHandler)
        """
        return {
            "success": False,
            "message": "Opción inválida, vuelve a intentarlo.",
            "next_path": session_data.get("current_path"),
            "next_handler": self.name,
            "session_data": session_data
        }
    
    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}')>"