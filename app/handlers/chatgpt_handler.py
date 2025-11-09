# app/handlers/chatgpt_handler.py
from typing import Dict, Any
from app.handlers.base_handler import BaseHandler
from app.repositories.simple_answer_repository import SimpleAnswerRepository
from app.services.langchain_service import AdvancedLangChainService

class ChatGptHandler(BaseHandler):
    """
    Handler que integra IA (LangChain) con la estructura de handlers.
    Equivale al ChatGptHandler de mazz-chatbot pero usando LangChain.
    
    Permite respuestas inteligentes dentro del flujo de handlers estructurado.
    """
    
    def __init__(self, simple_answer_repository: SimpleAnswerRepository, langchain_service: AdvancedLangChainService):
        super().__init__("ChatGptHandler")
        self.simple_answer_repo = simple_answer_repository
        self.langchain_service = langchain_service
    
    def process_message(self, message: str, session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa mensaje usando IA para determinar respuesta y próximo paso.
        Combina la estructura de handlers con capacidades de LangChain.
        """
        current_path = session_data.get("current_path", "")
        account_id = context.get("account_id")
        session_id = int(context.get("session_id", "0"))
        from_uid = context.get("from_uid", "")
        
        print(f"🤖 ChatGPT procesando: {current_path}")
        print(f"🤖 Mensaje del usuario: '{message}'")
        
        # 1. Primero buscar si hay una respuesta exacta en la BD
        exact_path = f"{current_path}/{message.strip()}"
        exact_answer = self.simple_answer_repo.find_by_handler_path(exact_path, account_id)
        
        if exact_answer:
            print(f"✅ ChatGPT: Respuesta exacta encontrada en BD")
            return self._process_exact_answer(exact_answer, session_data)
        
        # 2. Si no hay respuesta exacta, usar IA para generar respuesta
        print(f"🤖 ChatGPT: No hay respuesta exacta, usando IA...")
        
        # Buscar configuración del ChatGPT para este path
        gpt_config = self.simple_answer_repo.find_by_handler_path(current_path, account_id)
        
        if not gpt_config:
            print(f"❌ No se encontró configuración ChatGPT para: {current_path}")
            return {
                "success": False,
                "message": "Configuración de ChatGPT no encontrada.",
                "session_data": session_data
            }
        
        # LOG DETALLADO
        print(f"🤖 CHATGPT CONFIG:")
        print(f"  - ID: {gpt_config.id}")
        print(f"  - Path: {current_path}")
        print(f"  - PathTo: '{gpt_config.handler_path_to}' {'(vacío)' if not gpt_config.handler_path_to else ''}")
        
        # 3. Generar respuesta con LangChain
        try:
            ai_response = self.langchain_service.process_message(
                session_id=session_id,
                user_message=message,
                from_uid=from_uid
            )
            
            if not ai_response.get("success"):
                print(f"❌ Error en LangChain: {ai_response}")
                return {
                    "success": False,
                    "message": "Error generando respuesta con IA.",
                    "session_data": session_data
                }
            
            ai_message = ai_response.get("message", "")
            print(f"🤖 LangChain generó: '{ai_message[:100]}...'")
            
        except Exception as e:
            print(f"❌ Excepción en LangChain: {str(e)}")
            return {
                "success": False,
                "message": "Error procesando con IA.",
                "session_data": session_data
            }
        
        # 4. Determinar próximo paso basado en configuración
        updated_session_data = session_data.copy()
        
        if not gpt_config.handler_path_to or current_path == gpt_config.handler_path_to:
            # Quedarse esperando más input del usuario
            next_path = current_path
            next_handler = self.name
            print(f"🤖 ChatGPT: Esperar más input del usuario")
        elif gpt_config.handler_path_to.startswith(f"/{self.name}"):
            # Continuar en ChatGPT pero cambiar path
            next_path = gpt_config.handler_path_to
            next_handler = self.name
            print(f"🤖 ChatGPT: Continuar en ChatGPT con path {next_path}")
        else:
            # Cambiar a otro handler
            next_path = gpt_config.handler_path_to
            next_handler = self._extract_handler_name(gpt_config.handler_path_to)
            print(f"🤖 ChatGPT: Cambiar a handler {next_handler}")
        
        updated_session_data["current_path"] = next_path
        updated_session_data["last_ai_response"] = ai_message
        
        return {
            "success": True,
            "message": ai_message,
            "next_path": next_path,
            "next_handler": next_handler,
            "session_data": updated_session_data
        }
    
    def request_action(self, message_channel: int, from_uid: str, client_uid: str, 
                      session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Equivale a requestAction() en tenet.
        Inicia interacción con ChatGPT mostrando mensaje inicial.
        """
        current_path = session_data.get("current_path", "")
        account_id = context.get("account_id")
        
        print(f"🤖 ChatGPT RequestAction para path: {current_path}")
        
        # Buscar configuración inicial de ChatGPT
        gpt_config = self.simple_answer_repo.find_by_handler_path(current_path, account_id)
        
        if not gpt_config:
            print(f"❌ No se encontró configuración inicial de ChatGPT para: {current_path}")
            return {
                "success": False,
                "message": "ChatGPT no configurado.",
                "session_data": session_data
            }
        
        # LOG DETALLADO
        print(f"🤖 CHATGPT INICIAL:")
        print(f"  - ID: {gpt_config.id}")
        print(f"  - Path: {current_path}")
        print(f"  - PathTo: '{gpt_config.handler_path_to}' {'(vacío)' if not gpt_config.handler_path_to else ''}")
        print(f"  - Mensaje: '{gpt_config.message[:100]}{'...' if len(gpt_config.message) > 100 else ''}'")
        
        # Determinar próximo paso
        if not gpt_config.handler_path_to or current_path == gpt_config.handler_path_to:
            next_path = current_path
            next_handler = self.name
            print(f"🤖 ChatGPT RequestAction: Esperar input usuario")
        elif gpt_config.handler_path_to.startswith(f"/{self.name}"):
            next_path = gpt_config.handler_path_to
            next_handler = self.name
            print(f"🤖 ChatGPT RequestAction: Continuar ChatGPT")
        else:
            next_path = gpt_config.handler_path_to
            next_handler = self._extract_handler_name(gpt_config.handler_path_to)
            print(f"🤖 ChatGPT RequestAction: Ir a {next_handler}")
        
        # Actualizar session_data
        updated_session_data = session_data.copy()
        updated_session_data["current_path"] = next_path
        updated_session_data["chatgpt_active"] = True
        
        return {
            "success": True,
            "message": gpt_config.message.replace("\\n", "\n"),
            "next_path": next_path,
            "next_handler": next_handler,
            "session_data": updated_session_data
        }
    
    def _process_exact_answer(self, answer, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Procesa una respuesta exacta encontrada en la BD.
        """
        updated_session_data = session_data.copy()
        
        # Lógica de navegación
        if not answer.handler_path_to:
            next_path = session_data.get("current_path", "")
            next_handler = self.name
            print(f"🤖 ChatGPT: Respuesta exacta, permanecer esperando")
        elif answer.handler_path_to.startswith(f"/{self.name}"):
            next_path = answer.handler_path_to
            next_handler = self.name
            print(f"🤖 ChatGPT: Respuesta exacta, continuar ChatGPT")
        else:
            next_path = answer.handler_path_to
            next_handler = self._extract_handler_name(answer.handler_path_to)
            print(f"🤖 ChatGPT: Respuesta exacta, ir a {next_handler}")
        
        updated_session_data["current_path"] = next_path
        updated_session_data["last_message"] = answer.message
        
        return {
            "success": True,
            "message": answer.message.replace("\\n", "\n"),
            "next_path": next_path,
            "next_handler": next_handler,
            "session_data": updated_session_data
        }