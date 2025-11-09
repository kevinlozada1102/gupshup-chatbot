# app/handlers/db_flow_handler.py
from typing import Dict, Any
from app.handlers.base_handler import BaseHandler
from app.repositories.simple_answer_repository import SimpleAnswerRepository

class DbFlowHandler(BaseHandler):
    """
    Handler para flujos automatizados.
    Maneja secuencias de mensajes automáticos y formularios.
    Equivale a flujos en mazz-chatbot.
    """
    
    def __init__(self, simple_answer_repository: SimpleAnswerRepository):
        super().__init__("DbFlowHandler")
        self.simple_answer_repo = simple_answer_repository
    
    def process_message(self, message: str, session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa mensaje del usuario en un flujo.
        En flows, generalmente captura datos del usuario.
        """
        current_path = session_data.get("current_path", "")
        account_id = context.get("account_id")
        
        # En flows, el mensaje del usuario puede ser una respuesta a un formulario
        # Por ahora seguimos la lógica similar pero con logs específicos de flow
        if message.strip():
            current_path = f"{current_path}/{message.strip()}"
        
        print(f"🌊 DbFlow procesando: {current_path}")
        
        # Buscar configuración de flow
        answer = self.simple_answer_repo.find_by_handler_path(current_path, account_id)
        
        if not answer:
            print(f"❌ No se encontró configuración de flow para: {current_path}")
            return self._handle_invalid_flow(current_path, session_data, context)
        
        # LOG ESPECÍFICO PARA FLOWS
        print(f"🌊 FLOW ENCONTRADO:")
        print(f"  - ID: {answer.id}")
        print(f"  - Path: {current_path}")
        print(f"  - PathTo: '{answer.handler_path_to}' {'(vacío)' if not answer.handler_path_to else ''}")
        print(f"  - Mensaje: '{answer.message[:50]}{'...' if len(answer.message) > 50 else ''}'")
        
        # Capturar respuesta del usuario en el flow
        updated_session_data = session_data.copy()
        
        # Guardar datos del flow si es necesario
        if not updated_session_data.get("flow_data"):
            updated_session_data["flow_data"] = {}
        
        # Lógica de navegación de flow
        if not answer.handler_path_to or current_path == answer.handler_path_to:
            next_path = current_path
            next_handler = self.name
            print(f"🌊 Flow: Permanecer en {self.name}")
        elif answer.handler_path_to.startswith(f"/{self.name}"):
            next_path = answer.handler_path_to
            next_handler = self.name
            print(f"🌊 Flow: Continuar flow a {next_path}")
        else:
            next_path = answer.handler_path_to
            next_handler = self._extract_handler_name(answer.handler_path_to)
            print(f"🌊 Flow: Completar flow, ir a {next_handler}")
        
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
        Inicia un flujo automatizado.
        """
        current_path = session_data.get("current_path", "")
        account_id = context.get("account_id")
        
        print(f"🌊 Flow RequestAction para path: {current_path}")
        
        # Buscar configuración inicial del flow
        answer = self.simple_answer_repo.find_by_handler_path(current_path, account_id)
        
        if not answer:
            print(f"❌ No se encontró configuración inicial de flow para: {current_path}")
            return {
                "success": False,
                "message": "Flow no configurado.",
                "session_data": session_data
            }
        
        # LOG DETALLADO PARA FLOW INICIAL
        print(f"🌊 FLOW INICIAL:")
        print(f"  - ID: {answer.id}")
        print(f"  - Path: {current_path}")
        print(f"  - PathTo: '{answer.handler_path_to}' {'(vacío)' if not answer.handler_path_to else ''}")
        print(f"  - Mensaje: '{answer.message[:100]}{'...' if len(answer.message) > 100 else ''}'")
        
        # Inicializar datos del flow
        updated_session_data = session_data.copy()
        if not updated_session_data.get("flow_data"):
            updated_session_data["flow_data"] = {
                "started_at": current_path,
                "step": 1
            }
        
        # Lógica de navegación de flow inicial
        if not answer.handler_path_to or current_path == answer.handler_path_to:
            next_path = current_path
            next_handler = self.name
            print(f"🌊 Flow RequestAction: Permanecer en {self.name}")
        elif answer.handler_path_to.startswith(f"/{self.name}"):
            next_path = answer.handler_path_to
            next_handler = self.name
            print(f"🌊 Flow RequestAction: Continuar a paso siguiente")
        else:
            next_path = answer.handler_path_to
            next_handler = self._extract_handler_name(answer.handler_path_to)
            print(f"🌊 Flow RequestAction: Flow completo, ir a {next_handler}")
        
        updated_session_data["current_path"] = next_path
        
        return {
            "success": True,
            "message": answer.message.replace("\\n", "\n"),
            "next_path": next_path,
            "next_handler": next_handler,
            "session_data": updated_session_data
        }
    
    def _handle_invalid_flow(self, failed_path: str, session_data: Dict[str, Any], 
                            context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Manejo de error en flow.
        """
        account_id = context.get("account_id")
        
        # Obtener path padre
        path_parts = failed_path.split("/")
        if len(path_parts) > 1:
            path_parts.pop()
            parent_path = "/".join(path_parts)
        else:
            parent_path = failed_path
        
        print(f"🌊 Flow error, fallback a: {parent_path}")
        
        # Buscar configuración del paso anterior
        parent_answer = self.simple_answer_repo.find_by_handler_path(parent_path, account_id)
        
        # Mensaje de error específico para flows
        error_message = "Error en el flujo. Volvamos al paso anterior."
        if parent_answer and parent_answer.invalid_error:
            error_message = parent_answer.invalid_error
        
        # Actualizar session_data
        updated_session_data = session_data.copy()
        updated_session_data["current_path"] = parent_path
        
        # Marcar error en flow_data
        if updated_session_data.get("flow_data"):
            updated_session_data["flow_data"]["last_error"] = failed_path
        
        return {
            "success": False,
            "message": error_message,
            "next_path": parent_path,
            "next_handler": self.name,
            "session_data": updated_session_data
        }