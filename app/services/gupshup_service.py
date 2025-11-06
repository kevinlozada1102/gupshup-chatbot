# app/services/gupshup_service.py
from typing import Dict, Any, Optional
import json
from datetime import datetime
from app.models.webhook_data import WebhookData
from app.repositories.gupshup_repository import GupshupRepository
from app.repositories.accounts_repository import AccountsRepository
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.products_repository import ProductsRepository
from app.services.langchain_service import AdvancedLangChainService
from app.services.gupshup_sender_service import GupshupSenderService

class GupshupService:
    def __init__(self, gupshup_repository: GupshupRepository, 
                 accounts_repository: AccountsRepository,
                 chat_session_repository: ChatSessionRepository,
                 message_repository: MessageRepository,
                 products_repository: ProductsRepository):
        self.gupshup_repo = gupshup_repository
        self.accounts_repo = accounts_repository
        self.session_repo = chat_session_repository
        self.message_repo = message_repository
        self.products_repo = products_repository
        
        # Inicializar LangChain Service avanzado
        self.langchain_service = AdvancedLangChainService(
            message_repository, products_repository
        )
        
        # Inicializar servicio de envío Gupshup
        self.gupshup_sender = GupshupSenderService(accounts_repository)
    
    def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa el webhook de Gupshup con lógica completa de mensaje y sesión"""
        try:
            # 1. Extraer datos del payload
            webhook_data = self._extract_payload_data(payload)
            
            # 2. Guardar en gupshup_log siempre
            log_result = self.gupshup_repo.save_log(
                event=json.dumps(payload),
                message_id=webhook_data.message_id,
                from_uid=webhook_data.display_phone_number or webhook_data.from_uid,
                type=webhook_data.message_type,
                app_id=webhook_data.app_id,
                channel="whatsapp"
            )
            
            # 3. Si es mensaje de texto del usuario, procesar mensaje
            if webhook_data.is_text_message():
                session_result = self._process_user_message(webhook_data)
                return {
                    "success": True,
                    "log_id": log_result.id,
                    "message_id": session_result.get("message_id"),
                    "session_id": session_result.get("session_id"),
                    "is_user_message": True,
                    "webhook_data": webhook_data
                }
            
            # 4. Para otros tipos (status, etc.) solo retornar log
            return {
                "success": True,
                "log_id": log_result.id,
                "is_user_message": webhook_data.is_user_message,
                "webhook_data": webhook_data
            }
            
        except Exception as e:
            # En caso de error, guardar el payload completo
            error_log = self.gupshup_repo.save_log(
                event=json.dumps(payload),
                type="error",
                channel="webhook_error"
            )
            
            return {
                "success": False,
                "error": str(e),
                "log_id": error_log.id
            }
    
    def _extract_payload_data(self, payload: Dict[str, Any]) -> WebhookData:
        """Extrae datos del payload y los organiza en WebhookData"""
        webhook_data = WebhookData(raw_payload=payload)
        
        try:
            # Navegar por la estructura del payload como en Java
            entry = payload.get("entry", [])
            
            if entry and len(entry) > 0:
                first_entry = entry[0]
                changes = first_entry.get("changes", [])
                
                if changes and len(changes) > 0:
                    first_change = changes[0]
                    value = first_change.get("value", {})
                    
                    if value:
                        messages = value.get("messages", [])
                        statuses = value.get("statuses", [])
                        
                        # Extraer metadata
                        metadata = value.get("metadata", {})
                        if metadata:
                            webhook_data.display_phone_number = metadata.get("display_phone_number")
                            webhook_data.app_id = metadata.get("phone_number_id")
                        
                        # Procesar mensajes de usuario
                        if messages and len(messages) > 0 and not statuses:
                            webhook_data.is_user_message = True
                            first_message = messages[0]
                            
                            webhook_data.from_uid = first_message.get("from")
                            webhook_data.message_id = first_message.get("id")
                            webhook_data.message_type = first_message.get("type")
                            
                            # Extraer contenido del mensaje
                            if webhook_data.message_type == "text":
                                text_content = first_message.get("text", {})
                                webhook_data.message_body = text_content.get("body")
                        
                        # Procesar status updates
                        elif statuses and len(statuses) > 0:
                            webhook_data.is_status_update = True
                            first_status = statuses[0]
                            
                            webhook_data.message_id = first_status.get("id")
                            webhook_data.from_uid = first_status.get("recipient_id")
                            webhook_data.message_type = "status"
                            
        except Exception as e:
            print(f"Error extracting payload data: {e}")
            
        return webhook_data
    
    def _process_user_message(self, webhook_data: WebhookData) -> Dict[str, Any]:
        """Procesa mensaje de usuario: obtiene/crea sesión y guarda mensaje"""
        try:
            # 1. Obtener o crear session_id - equivale a obtenerOCrearSessionId
            session_id = self._get_or_create_session_id(
                webhook_data.from_uid, 
                webhook_data.display_phone_number
            )
            
            # 2. Buscar cuenta por display_phone_number
            account = self.accounts_repo.find_by_from_uid(webhook_data.display_phone_number)
            account_id = account.account_id if account else None
            
            # 3. Guardar mensaje - equivale a messageRepository.save()
            message = self.message_repo.save_message(
                from_uid=webhook_data.display_phone_number,
                client_uid=webhook_data.from_uid,
                message_body=webhook_data.message_body,
                account_id=account_id,
                session_id=session_id,
                message_id=webhook_data.message_id,
                message_channel=0,
                message_direction=0,
                message_type=0
            )
            
            # 4. PROCESAR CON LANGCHAIN AVANZADO ✅
            ai_response = self.langchain_service.process_message(
                session_id=session_id,
                user_message=webhook_data.message_body
            )
            
            # 5. ENVIAR RESPUESTA VIA GUPSHUP API V3 ✅
            if ai_response["success"]:
                print(f"📤 GUPSHUP: Enviando mensaje: '{ai_response['message'][:100]}...'")
                send_result = self.gupshup_sender.send_text_message(
                    to=webhook_data.from_uid,
                    message=ai_response["message"],
                    display_phone_number=webhook_data.display_phone_number
                )
                print(f"🔄 GUPSHUP: Resultado envío - success: {send_result['success']}")
                
                # 6. Solo guardar en BD si se envió exitosamente
                bot_message = None
                if send_result["success"]:
                    bot_message = self.message_repo.save_message(
                        from_uid=webhook_data.display_phone_number,
                        client_uid=webhook_data.from_uid,
                        message_body=ai_response["message"],
                        account_id=account_id,
                        session_id=session_id,
                        message_id=send_result.get("message_id", f"bot_{message.id}"),
                        message_channel=0,
                        message_direction=1,  # Respuesta del bot
                        message_type=1
                    )
                
                return {
                    "success": True,
                    "session_id": session_id,
                    "message_id": message.id,
                    "account_id": account_id,
                    "ai_response": ai_response,
                    "send_result": send_result,
                    "bot_message_id": bot_message.id if bot_message else None,
                    "sent_to_user": send_result["success"]
                }
            else:
                # Si LangChain falló, retornar error sin enviar
                return {
                    "success": False,
                    "error": "Error procesando con LangChain",
                    "ai_response": ai_response
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _get_or_create_session_id(self, client_uid: str, from_uid: str) -> int:
        """Obtiene o crea session_id - equivale a obtenerOCrearSessionId en Java"""
        try:
            current_time = datetime.now()
            
            # Buscar sesión activa
            existing_session = self.session_repo.find_active_session(
                client_uid, from_uid, current_time
            )
            
            if existing_session:
                print(f"Sesión existente encontrada: {existing_session.id}")
                return existing_session.id
            else:
                # Crear nueva sesión
                new_session = self.session_repo.create_session(
                    client_uid=client_uid,
                    from_uid=from_uid
                )
                print(f"Nueva sesión creada: {new_session.id}")
                return new_session.id
                
        except Exception as e:
            print(f"Error obteniendo sessionId: {e}")
            # Fallback: generar ID temporal (esto podría necesitar ajuste)
            return hash(f"{client_uid}_{from_uid}") % 1000000
