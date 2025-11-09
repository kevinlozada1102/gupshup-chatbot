# app/handlers/db_interactive_template_handler.py
from typing import Dict, Any
from app.handlers.base_handler import BaseHandler
from app.repositories.simple_answer_repository import SimpleAnswerRepository

class DbInteractiveTemplateHandler(BaseHandler):
    """
    Handler para templates interactivos.
    Por ahora funciona igual que DbAnswerHandler pero podría extenderse 
    para enviar templates específicos de WhatsApp.
    """
    
    def __init__(self, simple_answer_repository: SimpleAnswerRepository):
        super().__init__("DbInteractiveTemplateHandler")
        self.simple_answer_repo = simple_answer_repository
    
    def process_message(self, message: str, session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa mensaje del usuario navegando por templates.
        """
        current_path = session_data.get("current_path", "")
        account_id = context.get("account_id")
        
        # Si usuario respondió algo, construir nueva ruta
        if message.strip():
            current_path = f"{current_path}/{message.strip()}"
        
        print(f"🔍 DbInteractiveTemplate buscando: {current_path}")
        
        # Buscar respuesta en tbl_simple_answer
        answer = self.simple_answer_repo.find_by_handler_path(current_path, account_id)
        
        if not answer:
            print(f"❌ No se encontró template para: {current_path}")
            return self._handle_invalid_option_with_fallback(current_path, session_data, context)
        
        # LOG DETALLADO DEL HANDLER ENCONTRADO
        print(f"✅ TEMPLATE ENCONTRADO:")
        print(f"  - ID: {answer.id}")
        print(f"  - Path: {current_path}")
        print(f"  - PathTo: '{answer.handler_path_to}' {'(vacío)' if not answer.handler_path_to else ''}")
        print(f"  - Mensaje: '{answer.message[:50]}{'...' if len(answer.message) > 50 else ''}'")
        
        # Actualizar session_data y determinar próximo handler
        updated_session_data = session_data.copy()
        
        # Lógica de pathTo igual a mazz-chatbot
        if not answer.handler_path_to or current_path == answer.handler_path_to:
            next_path = current_path
            next_handler = self.name
            print(f"🔄 Template: Permanecer en {self.name}")
        elif answer.handler_path_to.startswith(f"/{self.name}"):
            next_path = answer.handler_path_to
            next_handler = self.name
            print(f"🔄 Template: Ejecutar recursivamente en {self.name}")
        else:
            next_path = answer.handler_path_to
            next_handler = self._extract_handler_name(answer.handler_path_to)
            print(f"🔄 Template: Cambiar a handler {next_handler}")
        
        updated_session_data["current_path"] = next_path
        updated_session_data["last_message"] = answer.message
        
        return {
            "success": True,
            "message": answer.message.replace("\\n", "\n"),
            "next_path": next_path,
            "next_handler": next_handler,
            "session_data": updated_session_data
        }
    
    def request_action(self, message_channel: int, from_uid: str, client_uid: str, 
                      session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Equivale a requestAction() en tenet.
        Muestra el template inicial.
        """
        current_path = session_data.get("current_path", "")
        account_id = context.get("account_id")
        
        print(f"🎬 Template RequestAction para path: {current_path}")
        
        # Buscar template para el path actual
        answer = self.simple_answer_repo.find_by_handler_path(current_path, account_id)
        
        if not answer:
            print(f"❌ No se encontró template inicial para: {current_path}")
            return {
                "success": False,
                "message": "Template no encontrado.",
                "session_data": session_data
            }
        
        # LOG DETALLADO
        print(f"✅ TEMPLATE INICIAL ENCONTRADO:")
        print(f"  - ID: {answer.id}")
        print(f"  - Path: {current_path}")
        print(f"  - PathTo: '{answer.handler_path_to}' {'(vacío)' if not answer.handler_path_to else ''}")
        print(f"  - Mensaje: '{answer.message[:100]}{'...' if len(answer.message) > 100 else ''}'")
        
        # Lógica de pathTo igual a mazz-chatbot
        if not answer.handler_path_to or current_path == answer.handler_path_to:
            next_path = current_path
            next_handler = self.name
            print(f"🔄 Template RequestAction: Permanecer en {self.name}")
        elif answer.handler_path_to.startswith(f"/{self.name}"):
            next_path = answer.handler_path_to
            next_handler = self.name
            print(f"🔄 Template RequestAction: Ejecutar recursivamente")
        else:
            next_path = answer.handler_path_to
            next_handler = self._extract_handler_name(answer.handler_path_to)
            print(f"🔄 Template RequestAction: Cambiar a {next_handler}")
        
        # Actualizar session_data
        updated_session_data = session_data.copy()
        updated_session_data["current_path"] = next_path
        
        return {
            "success": True,
            "message": answer.message.replace("\\n", "\n"),
            "next_path": next_path,
            "next_handler": next_handler,
            "session_data": updated_session_data
        }
    
    def _handle_invalid_option_with_fallback(self, failed_path: str, session_data: Dict[str, Any], 
                                           context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manejo de opción inválida con fallback.
        """
        account_id = context.get("account_id")
        
        # Obtener path padre
        path_parts = failed_path.split("/")
        if len(path_parts) > 1:
            path_parts.pop()
            parent_path = "/".join(path_parts)
        else:
            parent_path = failed_path
        
        print(f"🔙 Template fallback a path padre: {parent_path}")
        
        # Buscar respuesta del path padre
        parent_answer = self.simple_answer_repo.find_by_handler_path(parent_path, account_id)
        
        # Mensaje de error
        error_message = "Opción inválida para template, intenta nuevamente."
        if parent_answer and parent_answer.invalid_error:
            error_message = parent_answer.invalid_error
        
        # Actualizar session_data al path padre
        updated_session_data = session_data.copy()
        updated_session_data["current_path"] = parent_path
        
        return {
            "success": False,
            "message": error_message,
            "next_path": parent_path,
            "next_handler": self.name,
            "session_data": updated_session_data
        }