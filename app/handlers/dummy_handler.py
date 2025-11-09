# app/handlers/dummy_handler.py
from typing import Dict, Any
from app.handlers.base_handler import BaseHandler
from app.repositories.simple_answer_repository import SimpleAnswerRepository
from app.repositories.transfered_chat_repository import TransferedChatRepository
from app.models.transfered_chat import TblTransferedChats
from datetime import datetime

class DummyHandler(BaseHandler):
    """
    Handler para transferencia a agentes humanos.
    Equivale al DummyHandler en mazz-chatbot.
    
    Funciona como "modo pausa" - registra la transferencia en tbl_transfered_chats
    y permite que los agentes humanos respondan manualmente.
    Una vez que entra aquí, el chat se queda esperando intervención humana.
    """
    
    def __init__(self, simple_answer_repository: SimpleAnswerRepository, transfered_chat_repository: TransferedChatRepository = None):
        super().__init__("DummyHandler")
        self.simple_answer_repo = simple_answer_repository
        self.transfered_chat_repo = transfered_chat_repository
    
    def request_action(self, message_channel: int, from_uid: str, client_uid: str, 
                      session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """RequestAction para DummyHandler - igual al original"""
        current_path = session_data.get("current_path", "")
        account_id = context.get("account_id")
        session_id = context.get("session_id")
        
        print(f"🎪 DummyHandler: RequestAction para {client_uid}")
        print(f"🎪 DummyHandler: Path actual: {current_path}")
        
        # Buscar respuesta en tbl_simple_answer (igual que el original)
        answer = self.simple_answer_repo.find_by_handler_path(current_path, account_id)
        
        if not answer:
            # Si no hay respuesta, quedarse en el mismo handler (igual al original)
            print(f"❌ DummyHandler: No se encontró configuración para: {current_path}")
            last_handler = session_data.get("handlerHistory", {}).get("lastHandler")
            if last_handler and last_handler.get("key") == self.name:
                session_data["current_path"] = last_handler.get("value", current_path)
            return {
                "success": True,
                "message": "",  # Sin mensaje si no hay configuración
                "next_path": session_data.get("current_path"),
                "next_handler": self.name,
                "session_data": session_data
            }
        
        # Actualizar historial (igual al original)
        session_data["handlerHistory"] = {
            "lastHandler": {
                "key": self.name,
                "value": current_path
            }
        }
        
        # REGISTRAR TRANSFERENCIA (esta es la parte clave del DummyHandler)
        if self.transfered_chat_repo:
            try:
                transfer = TblTransferedChats(
                    handler=current_path,
                    client_uid=client_uid,
                    session_id=session_id,
                    account_id=account_id,
                    started_at=datetime.now(),
                    from_uid=from_uid
                )
                saved_transfer = self.transfered_chat_repo.save(transfer)
                print(f"✅ DummyHandler: Transferencia registrada - ID: {saved_transfer.id}")
            except Exception as e:
                print(f"❌ DummyHandler: Error guardando transferencia: {str(e)}")
        
        # Enviar mensaje si existe (igual al original)
        message_to_send = ""
        if answer.message:
            message_to_send = answer.message.replace("\\n", "\n")
        
        # Determinar próximo handler (lógica igual al original)
        if not answer.handler_path_to or current_path == answer.handler_path_to:
            # Quedarse en el mismo handler
            next_path = current_path
            next_handler = self.name
            updated_session_data = session_data.copy()
            updated_session_data["current_path"] = current_path
            
            print(f"🎪 DummyHandler: Permanecer en {self.name} - MODO PAUSA ACTIVADO")
            return {
                "success": True,
                "message": message_to_send,
                "next_path": next_path,
                "next_handler": next_handler,
                "session_data": updated_session_data
            }
        
        # Cambiar a otro handler si pathTo está configurado
        next_path = answer.handler_path_to
        updated_session_data = session_data.copy()
        updated_session_data["current_path"] = next_path
        
        # Si pathTo es del mismo handler, ejecutar recursivamente
        if answer.handler_path_to.startswith(f"/{self.name}"):
            next_handler = self.name
            print(f"🎪 DummyHandler: Ejecutar recursivamente")
        else:
            # Cambiar a otro handler
            next_handler = self._extract_handler_name(answer.handler_path_to)
            print(f"🎪 DummyHandler: Cambiar a {next_handler}")
        
        return {
            "success": True,
            "message": message_to_send,
            "next_path": next_path,
            "next_handler": next_handler,
            "session_data": updated_session_data
        }
    
    def process_message(self, message: str, session_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """ProcessMessage para DummyHandler - igual al original"""
        current_path = session_data.get("current_path", "")
        
        print(f"🎪 DummyHandler: Procesando mensaje '{message}' para {context.get('client_uid')}")
        
        # Concatenar mensaje al path actual (igual al original)
        if message.strip():
            new_path = f"{current_path}/{message.strip()}"
            session_data["current_path"] = new_path
            print(f"🎪 DummyHandler: Nuevo path: {new_path}")
        
        # Ejecutar requestAction con el nuevo path (igual al original)
        return self.request_action(
            message_channel=0,
            from_uid=context.get("from_uid"),
            client_uid=context.get("client_uid"),
            session_data=session_data,
            context=context
        )
