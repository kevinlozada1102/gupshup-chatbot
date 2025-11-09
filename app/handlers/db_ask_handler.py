# app/handlers/db_ask_handler.py
from typing import Dict, Any
from app.handlers.base_handler import BaseHandler
from app.repositories.simple_answer_repository import SimpleAnswerRepository

class DbAskHandler(BaseHandler):
    """
    Handler para capturar respuestas libres del usuario.
    Equivale al DbAskHandler de mazz-chatbot.
    
    Permite hacer preguntas abiertas al usuario y capturar sus respuestas
    para procesamiento posterior o guardarlas en base de datos.
    """
    
    def __init__(self, simple_answer_repository: SimpleAnswerRepository):
        super().__init__("DbAskHandler")
        self.simple_answer_repo = simple_answer_repository
        # En una implementación completa, aquí tendríamos un repository
        # para guardar las respuestas del usuario (AskHandlerAnswerRepository)
    
    def process_message(self, message: str, session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Captura la respuesta libre del usuario y procede al siguiente step.
        En mazz-chatbot esto guarda la respuesta en AskHandlerAnswer.
        """
        current_path = session_data.get("current_path", "")
        account_id = context.get("account_id")
        client_uid = context.get("client_uid", "")
        session_id = context.get("session_id", "")
        
        print(f"❓ DbAsk capturando respuesta: '{message}' para path: {current_path}")
        
        # Buscar configuración de la pregunta
        ask_config = self.simple_answer_repo.find_by_handler_path(current_path, account_id)
        
        if not ask_config:
            print(f"❌ No se encontró configuración DbAsk para: {current_path}")
            return {
                "success": False,
                "message": "Configuración de pregunta no encontrada.",
                "session_data": session_data
            }
        
        # LOG DETALLADO
        print(f"❓ DBASK CONFIG:")
        print(f"  - ID: {ask_config.id}")
        print(f"  - Path: {current_path}")
        print(f"  - PathTo: '{ask_config.handler_path_to}' {'(vacío)' if not ask_config.handler_path_to else ''}")
        print(f"  - Pregunta: '{ask_config.message[:50]}{'...' if len(ask_config.message) > 50 else ''}'")
        
        # GUARDAR RESPUESTA DEL USUARIO
        # En una implementación completa, aquí guardaríamos en una tabla específica
        # Por ahora lo guardamos en session_data
        updated_session_data = session_data.copy()
        
        if not updated_session_data.get("user_answers"):
            updated_session_data["user_answers"] = {}
        
        # Guardar la respuesta del usuario asociada al path
        updated_session_data["user_answers"][current_path] = {
            "question": ask_config.message,
            "answer": message,
            "client_uid": client_uid,
            "timestamp": str(session_id)  # En implementación real sería timestamp actual
        }
        
        print(f"💾 DbAsk guardó respuesta: '{message}' para pregunta: '{ask_config.message[:30]}...'")
        
        # Determinar próximo paso
        if not ask_config.handler_path_to:
            print(f"❌ DbAsk: No hay pathTo definido, esto es un error")
            return {
                "success": False,
                "message": "Error en configuración de pregunta.",
                "session_data": updated_session_data
            }
        
        # En DbAskHandler siempre debe haber un pathTo porque después de capturar
        # la respuesta debe ir a algún lugar
        next_path = ask_config.handler_path_to
        next_handler = self._extract_handler_name(ask_config.handler_path_to)
        
        print(f"❓ DbAsk: Respuesta capturada, ir a {next_handler} con path {next_path}")
        
        updated_session_data["current_path"] = next_path
        updated_session_data["last_question"] = ask_config.message
        updated_session_data["last_answer"] = message
        
        return {
            "success": True,
            "message": f"Gracias por tu respuesta: '{message}'. Procesando...",
            "next_path": next_path,
            "next_handler": next_handler,
            "session_data": updated_session_data
        }
    
    def request_action(self, message_channel: int, from_uid: str, client_uid: str, 
                      session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Equivale a requestAction() en tenet.
        Muestra la pregunta al usuario y espera su respuesta libre.
        """
        current_path = session_data.get("current_path", "")
        account_id = context.get("account_id")
        
        print(f"❓ DbAsk RequestAction para path: {current_path}")
        
        # Buscar configuración de la pregunta
        ask_config = self.simple_answer_repo.find_by_handler_path(current_path, account_id)
        
        if not ask_config:
            print(f"❌ No se encontró pregunta para: {current_path}")
            return {
                "success": False,
                "message": "Pregunta no configurada.",
                "session_data": session_data
            }
        
        # LOG DETALLADO
        print(f"❓ DBASK PREGUNTA:")
        print(f"  - ID: {ask_config.id}")
        print(f"  - Path: {current_path}")
        print(f"  - PathTo: '{ask_config.handler_path_to}' {'(vacío)' if not ask_config.handler_path_to else ''}")
        print(f"  - Pregunta: '{ask_config.message[:100]}{'...' if len(ask_config.message) > 100 else ''}'")
        
        if not ask_config.handler_path_to:
            print(f"⚠️ DbAsk: Pregunta sin pathTo definido, quedará esperando respuesta")
        
        # Preparar session_data para capturar respuesta
        updated_session_data = session_data.copy()
        updated_session_data["awaiting_answer"] = True
        updated_session_data["current_question"] = ask_config.message
        
        # En DbAskHandler, después de mostrar la pregunta, nos quedamos esperando
        # la respuesta del usuario (no cambiamos de handler todavía)
        return {
            "success": True,
            "message": ask_config.message.replace("\\n", "\n"),
            "next_path": current_path,  # Nos quedamos en el mismo path
            "next_handler": self.name,  # Nos quedamos en DbAskHandler esperando respuesta
            "session_data": updated_session_data
        }
    
    def get_user_answer(self, session_data: Dict[str, Any], question_path: str) -> str:
        """
        Método de utilidad para obtener la respuesta del usuario a una pregunta específica.
        """
        user_answers = session_data.get("user_answers", {})
        answer_data = user_answers.get(question_path, {})
        return answer_data.get("answer", "")
    
    def get_all_user_answers(self, session_data: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Método de utilidad para obtener todas las respuestas del usuario.
        """
        return session_data.get("user_answers", {})