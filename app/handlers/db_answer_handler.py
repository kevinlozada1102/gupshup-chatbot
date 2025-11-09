# app/handlers/db_answer_handler.py
from typing import Dict, Any
from app.handlers.base_handler import BaseHandler
from app.repositories.simple_answer_repository import SimpleAnswerRepository

class DbAnswerHandler(BaseHandler):
    """
    Handler principal del sistema de menús.
    Equivale al DbAnswerHandler de mazz-chatbot en tenet.
    
    Maneja el flujo de conversación usando tbl_simple_answer con rutas jerárquicas.
    """
    
    def __init__(self, simple_answer_repository: SimpleAnswerRepository):
        super().__init__("DbAnswerHandler")
        self.simple_answer_repo = simple_answer_repository
    
    def process_message(self, message: str, session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa mensaje del usuario y navega por el árbol de respuestas.
        Lógica equivale a DbAnswerHandler.processMessage() en tenet.
        """
        current_path = session_data.get("current_path", "")
        account_id = context.get("account_id")
        
        print(f"📍 PROCESS_MESSAGE - Path inicial: '{current_path}'")
        print(f"📍 PROCESS_MESSAGE - Mensaje del usuario: '{message}'")
        print(f"📍 PROCESS_MESSAGE - Account ID: '{account_id}'")
        
        # Si usuario respondió algo, construir nueva ruta
        if message.strip():
            path_before = current_path
            current_path = f"{current_path}/{message.strip()}"
            print(f"🔗 CONCATENACIÓN REALIZADA:")
            print(f"  → Path anterior: '{path_before}'")
            print(f"  → Mensaje usuario: '{message.strip()}'")
            print(f"  → Path resultante: '{current_path}'")
        else:
            print(f"⚠️ MENSAJE VACÍO - No se concatena nada al path")
        
        print(f"🔍 Buscando respuesta para path: {current_path}")
        
        # DEBUGGING: Mostrar todos los registros disponibles para este account
        all_answers = self.simple_answer_repo.find_by_account_id(account_id)
        print(f"📋 REGISTROS DISPONIBLES en tbl_simple_answer para account {account_id}:")
        for ans in all_answers:
            print(f"  - Path: {ans.handler_path} -> To: {ans.handler_path_to}")
        
        # Buscar respuesta en tbl_simple_answer
        answer = self.simple_answer_repo.find_by_handler_path(current_path, account_id)
        
        if not answer:
            # Manejo de error como en tenet
            print(f"❌ No se encontró respuesta para: {current_path}")
            return self._handle_invalid_option_with_fallback(current_path, session_data, context)
        
        # LOG DETALLADO DEL HANDLER ENCONTRADO EN PROCESS_MESSAGE
        print(f"✅ HANDLER ENCONTRADO EN PROCESS_MESSAGE:")
        print(f"  - ID: {answer.id}")
        print(f"  - Path procesado: {current_path}")
        print(f"  - PathTo: '{answer.handler_path_to}' {'(vacío)' if not answer.handler_path_to else ''}")
        print(f"  - Mensaje: '{answer.message[:50]}{'...' if len(answer.message) > 50 else ''}'")
        
        # Actualizar session_data - Lógica: si handler_path_to está vacío usa handler_path, sino usa handler_path_to
        updated_session_data = session_data.copy()
        final_current_path = answer.handler_path_to if answer.handler_path_to else current_path
        updated_session_data["current_path"] = final_current_path
        updated_session_data["last_message"] = answer.message
        
        print(f"💾 SESSION_DATA actualizada:")
        print(f"  → handler_path: '{current_path}'")
        print(f"  → handler_path_to: '{answer.handler_path_to}' {'(vacío)' if not answer.handler_path_to else ''}")
        print(f"  → current_path guardado: '{final_current_path}' (lógica: path_to si no vacío, sino path)")
        
        # Determinar próximo handler
        next_handler = self._extract_handler_name(answer.handler_path_to) if answer.handler_path_to else None
        
        print(f"✅ Respuesta encontrada - next_path: {answer.handler_path_to}, next_handler: {next_handler}")
        
        return {
            "success": True,
            "message": answer.message.replace("\\n", "\n"),  # Procesar saltos de línea como en tenet
            "next_path": answer.handler_path_to,
            "next_handler": next_handler,
            "session_data": updated_session_data
        }
    
    def request_action(self, message_channel: int, from_uid: str, client_uid: str, 
                      session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Equivale a requestAction() en tenet.
        Muestra el mensaje inicial para un path sin requerir input del usuario.
        """
        current_path = session_data.get("current_path", "")
        account_id = context.get("account_id")
        
        print(f"🎬 RequestAction para path: {current_path}")
        
        # Buscar respuesta para el path actual
        answer = self.simple_answer_repo.find_by_handler_path(current_path, account_id)
        
        if not answer:
            print(f"❌ No se encontró configuración inicial para: {current_path}")
            return {
                "success": False,
                "message": "Configuración no encontrada.",
                "session_data": session_data
            }
        
        # LOG DETALLADO DEL HANDLER ENCONTRADO
        print(f"✅ HANDLER ENCONTRADO:")
        print(f"  - ID: {answer.id}")
        print(f"  - Path actual: {current_path}")
        print(f"  - PathTo: '{answer.handler_path_to}' {'(vacío)' if not answer.handler_path_to else ''}")
        print(f"  - Mensaje: '{answer.message[:100]}{'...' if len(answer.message) > 100 else ''}'")
        print(f"  - Account: {answer.account_id}")
        
        # IMPORTANTE: PRIMERO actualizar session_data con pathTo para próximo handler
        # PERO el mensaje se envía del path actual (como mazz-chatbot)
        updated_session_data = session_data.copy()
        
        # Lógica de pathTo igual a mazz-chatbot
        if not answer.handler_path_to or current_path == answer.handler_path_to:
            # Si pathTo está vacío o es igual al path actual, quedarse en el mismo handler
            next_path = current_path
            next_handler = self.name
            print(f"🔄 DECISIÓN: PathTo vacío o igual - PERMANECER en DbAnswerHandler")
            print(f"  → next_path: {next_path}")
            print(f"  → next_handler: {next_handler}")
        elif answer.handler_path_to.startswith(f"/{self.name}"):
            # Si pathTo empieza con /DbAnswerHandler, ejecutar recursivamente
            next_path = answer.handler_path_to
            next_handler = self.name
            print(f"🔄 DECISIÓN: PathTo es del mismo handler - EJECUTAR RECURSIVAMENTE")
            print(f"  → next_path: {next_path}")
            print(f"  → next_handler: {next_handler}")
        else:
            # PathTo es de otro handler - cambiar handler
            next_path = answer.handler_path_to
            next_handler = self._extract_handler_name(answer.handler_path_to)
            print(f"🔄 DECISIÓN: PathTo es de OTRO HANDLER - CAMBIAR HANDLER")
            print(f"  → Este mensaje se envía: '{answer.message[:50]}...'")
            print(f"  → Después cambiar a: {next_handler}")
            print(f"  → next_path: {next_path}")
        
        # Actualizar session_data - Lógica: si handler_path_to está vacío usa handler_path, sino usa handler_path_to
        final_current_path = answer.handler_path_to if answer.handler_path_to else current_path
        updated_session_data["current_path"] = final_current_path
        
        print(f"💾 REQUEST_ACTION - SESSION_DATA actualizada:")
        print(f"  → handler_path: '{current_path}'")
        print(f"  → handler_path_to: '{answer.handler_path_to}' {'(vacío)' if not answer.handler_path_to else ''}")
        print(f"  → current_path guardado: '{final_current_path}' (lógica: path_to si no vacío, sino path)")
        
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
        Manejo de opción inválida con fallback como en tenet.
        Vuelve al path padre y muestra error personalizado.
        """
        account_id = context.get("account_id")
        
        # Obtener path padre (quitar último segmento)
        path_parts = failed_path.split("/")
        if len(path_parts) > 1:
            path_parts.pop()  # Quitar último elemento
            parent_path = "/".join(path_parts)
        else:
            parent_path = failed_path
        
        print(f"🔙 Fallback a path padre: {parent_path}")
        
        # Buscar respuesta del path padre para obtener error personalizado
        parent_answer = self.simple_answer_repo.find_by_handler_path(parent_path, account_id)
        
        if parent_answer:
            print(f"✅ Respuesta fallback encontrada para path padre: {parent_path}")
        else:
            print(f"❌ Tampoco se encontró respuesta fallback para path padre: {parent_path}")
        
        # Mensaje de error (personalizado o genérico)
        error_message = "Opción inválida, vuelve a intentarlo."
        if parent_answer and parent_answer.invalid_error:
            error_message = parent_answer.invalid_error
            print(f"📋 Usando mensaje de error personalizado: {error_message}")
        else:
            print(f"📋 Usando mensaje de error genérico: {error_message}")
        
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
    
    def _should_stay_in_same_handler(self, path_to: str) -> bool:
        """
        Determina si debe quedarse en el mismo handler.
        Lógica equivale a answer.pathTo.startsWith("/DbAnswerHandler") en tenet.
        """
        if not path_to:
            return True
        return path_to.startswith(f"/{self.name}")