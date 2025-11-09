# app/handlers/handler_registry.py
from typing import Dict, Any, Optional
from app.handlers.base_handler import BaseHandler

class HandlerRegistry:
    """
    Registry para manejar y ejecutar handlers.
    Equivale al sistema de inyección de handlers en mazz-chatbot.
    """
    
    def __init__(self):
        self.handlers: Dict[str, BaseHandler] = {}
    
    def register(self, handler: BaseHandler) -> None:
        """Registra un handler en el registry"""
        self.handlers[handler.name] = handler
        print(f"✅ Handler registrado: {handler.name}")
    
    def get_handler(self, name: str) -> Optional[BaseHandler]:
        """Obtiene un handler por nombre"""
        return self.handlers.get(name)
    
    def execute_handler(self, handler_name: str, message: str, session_data: Dict[str, Any], 
                       context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta un handler específico.
        Equivale a la lógica de HelloHandler.doRequest() en tenet.
        """
        handler = self.get_handler(handler_name)
        if not handler:
            return {
                "success": False,
                "error": f"Handler '{handler_name}' not found",
                "message": "Error interno del sistema."
            }
        
        try:
            print(f"🔄 Ejecutando handler: {handler_name}")
            result = handler.process_message(message, session_data, context)
            
            # Asegurar que session_data se actualice
            if "session_data" not in result:
                result["session_data"] = session_data
            
            return result
        except Exception as e:
            print(f"❌ Error ejecutando handler {handler_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Ocurrió un error inesperado. Por favor intenta nuevamente."
            }
    
    def execute_request_action(self, handler_name: str, message_channel: int, from_uid: str, 
                             client_uid: str, session_data: Dict[str, Any], 
                             context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta requestAction de un handler específico.
        Equivale a handler.requestAction() en tenet.
        """
        handler = self.get_handler(handler_name)
        if not handler:
            return {
                "success": False,
                "error": f"Handler '{handler_name}' not found"
            }
        
        try:
            return handler.request_action(message_channel, from_uid, client_uid, session_data, context)
        except Exception as e:
            print(f"❌ Error en requestAction {handler_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "message": "Error interno del sistema."
            }
    
    def list_handlers(self) -> list[str]:
        """Lista todos los handlers registrados"""
        return list(self.handlers.keys())
    
    def is_registered(self, handler_name: str) -> bool:
        """Verifica si un handler está registrado"""
        return handler_name in self.handlers
    
    def __repr__(self):
        return f"<HandlerRegistry(handlers={list(self.handlers.keys())})>"