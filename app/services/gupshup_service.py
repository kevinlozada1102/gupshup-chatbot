# app/services/gupshup_service.py
from typing import Dict, Any, Optional
import json
from datetime import datetime
from app.models.webhook_data import WebhookData
from app.repositories.gupshup_repository import GupshupRepository
from app.repositories.accounts_repository import AccountsRepository
from app.repositories.account_prompts_repository import AccountPromptsRepository
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.products_repository import ProductsRepository
from app.repositories.simple_answer_repository import SimpleAnswerRepository
from app.repositories.text_chatbot_repository import TextChatbotRepository
from app.repositories.session_data_repository import SessionDataRepository
from app.services.langchain_service import AdvancedLangChainService
from app.services.handler_service import HandlerService
from app.services.gupshup_sender_service import GupshupSenderService

class GupshupService:
    def __init__(self, gupshup_repository: GupshupRepository, 
                 accounts_repository: AccountsRepository,
                 chat_session_repository: ChatSessionRepository,
                 message_repository: MessageRepository,
                 products_repository: ProductsRepository,
                 account_prompts_repository: AccountPromptsRepository,
                 simple_answer_repository: SimpleAnswerRepository,
                 text_chatbot_repository: TextChatbotRepository,
                 session_data_repository: SessionDataRepository):
        self.gupshup_repo = gupshup_repository
        self.accounts_repo = accounts_repository
        self.session_repo = chat_session_repository
        self.message_repo = message_repository
        self.products_repo = products_repository
        self.account_prompts_repo = account_prompts_repository
        self.simple_answer_repo = simple_answer_repository
        self.text_chatbot_repo = text_chatbot_repository
        self.session_data_repo = session_data_repository
        
        # Inicializar servicio de envío Gupshup PRIMERO
        self.gupshup_sender = GupshupSenderService(accounts_repository)
        
        # Inicializar LangChain Service avanzado con repositorios
        self.langchain_service = AdvancedLangChainService(
            message_repository, products_repository, accounts_repository, account_prompts_repository
        )
        
        # Inicializar Handler Service para el sistema de menús
        self.handler_service = HandlerService(
            simple_answer_repository, text_chatbot_repository, session_data_repository,
            self.gupshup_sender,  # Pasar sender para envío inmediato
            message_repository    # Pasar message_repo para guardar mensajes recursivos
        )
    
    def process_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa el webhook de Gupshup con lógica completa de mensaje y sesión"""
        try:
            print(f"🎯 WEBHOOK: Payload completo recibido: {payload}")
            
            # 1. Extraer datos del payload
            webhook_data = self._extract_payload_data(payload)
            
            print(f"📋 WEBHOOK: Datos extraídos:")
            print(f"  - from_uid: {webhook_data.from_uid}")
            print(f"  - display_phone_number: {webhook_data.display_phone_number}")
            print(f"  - message_body: {webhook_data.message_body}")
            print(f"  - message_type: {webhook_data.message_type}")
            print(f"  - is_user_message: {webhook_data.is_user_message}")
            print(f"  - is_text_message: {webhook_data.is_text_message()}")
            
            # 2. Guardar en gupshup_log siempre
            log_result = self.gupshup_repo.save_log(
                event=json.dumps(payload),
                message_id=webhook_data.message_id,
                from_uid=webhook_data.display_phone_number or webhook_data.from_uid,
                type=webhook_data.message_type,
                app_id=webhook_data.app_id,
                channel="whatsapp"
            )
            
            # 3. Si es mensaje de texto o interactivo del usuario, procesar mensaje
            if webhook_data.is_text_message():
                print(f"✅ WEBHOOK: Es mensaje de tipo '{webhook_data.message_type}' - procesando...")
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
            print(f"⚠️ WEBHOOK: NO es mensaje procesable - tipo: {webhook_data.message_type}, is_user: {webhook_data.is_user_message}")
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
                            elif webhook_data.message_type == "interactive":
                                # Extraer contenido de mensaje interactivo (botones)
                                interactive_content = first_message.get("interactive", {})
                                if interactive_content.get("type") == "button_reply":
                                    button_reply = interactive_content.get("button_reply", {})
                                    webhook_data.message_body = button_reply.get("title", "")
                                elif interactive_content.get("type") == "list_reply":
                                    list_reply = interactive_content.get("list_reply", {})
                                    webhook_data.message_body = list_reply.get("title", "")
                        
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
            
            # 2. Buscar cuenta y estrategia de procesamiento
            account = self.accounts_repo.find_by_from_uid(webhook_data.display_phone_number)
            if not account:
                return {
                    "success": False,
                    "error": "Account not configured for this number"
                }
            
            account_id = account.account_id
            processing_strategy = account.processing_strategy
            
            print(f"🎯 ESTRATEGIA DE PROCESAMIENTO: {processing_strategy} para account: {account_id}")
            print(f"📱 FROM_UID: {webhook_data.display_phone_number}")
            print(f"👤 CLIENT_UID: {webhook_data.from_uid}")
            print(f"💬 MENSAJE: '{webhook_data.message_body}'")
            
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
            
            # 4. DECISIÓN POR ESTRATEGIA DE PROCESAMIENTO 🎯
            if processing_strategy == "langchain":
                # 🔴 SISTEMA LANGCHAIN (Coolbox y cuentas con IA)
                print("🤖 Usando LANGCHAIN para procesamiento con IA")
                ai_response = self.langchain_service.process_message(
                    session_id=session_id,
                    user_message=webhook_data.message_body,
                    from_uid=webhook_data.display_phone_number
                )
                print(f"🤖 LANGCHAIN: Resultado - success: {ai_response.get('success')}, message: '{ai_response.get('message', '')[:100]}...'")
                
            elif processing_strategy == "handlers":
                # 🟡 SISTEMA HANDLERS PURO (Sin IA - Lógica determinista)
                print("🎭 Usando HANDLERS puros (lógica determinista)")
                
                ai_response = self.handler_service.process_message(
                    from_uid=webhook_data.display_phone_number,
                    client_uid=webhook_data.from_uid,
                    message=webhook_data.message_body,
                    account_id=account_id,
                    session_id=session_id
                )
                
            else:
                # ❌ ESTRATEGIA NO SOPORTADA
                print(f"❌ Estrategia no soportada: {processing_strategy}")
                return {
                    "success": False,
                    "error": f"Processing strategy '{processing_strategy}' not supported"
                }
            
            # 5. LOS MENSAJES YA SE ENVIARON DURANTE LA RECURSION ✅
            if ai_response["success"]:
                messages_sent = ai_response.get("messages_sent", 0)
                print(f"🎆 MENSAJES YA ENVIADOS DURANTE RECURSION: {messages_sent}")
                
                # Los mensajes ya se enviaron durante la recursion
                send_result = {"success": True, "message_id": "sent_during_recursion"}
                
                print(f"🔄 GUPSHUP: Resultado envío - success: {send_result['success']}")
                if not send_result['success']:
                    print(f"❌ GUPSHUP: Error detallado: {send_result.get('error', 'No error info')}")
                    print(f"❌ GUPSHUP: Error code: {send_result.get('error_code', 'No error code')}")
                else:
                    print(f"✅ GUPSHUP: Mensaje enviado exitosamente - ID: {send_result.get('message_id')}")
                
                # 6. LOS MENSAJES YA SE GUARDARON DURANTE LA RECURSION EN HandlerService
                # No duplicar guardado aquí
                bot_message = None
                print(f"💾 MENSAJES YA GUARDADOS DURANTE RECURSION - No duplicar")
                
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
            print(f"❌ ERROR en _process_user_message: {e}")
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
    
    def _send_smart_message(self, to: str, message_content: str, display_phone_number: str) -> Dict[str, Any]:
        """
        Envía mensaje detectando automáticamente si es texto, template o flow.
        
        Detecta:
        - JSON con "id", "token" → Flow
        - JSON con estructura de template → Template  
        - Texto plano → Mensaje normal
        """
        try:
            # Intentar parsear como JSON
            import json
            flow_data = json.loads(message_content)
            
            # 🌊 DETECTAR FLOW (tiene id y token)
            if isinstance(flow_data, dict) and flow_data.get("id") and flow_data.get("token"):
                print(f"🌊 SMART: Detectado FLOW - ID: {flow_data.get('id')}")
                return self.gupshup_sender.send_flow_message(
                    to=to,
                    flow_data=flow_data,
                    display_phone_number=display_phone_number
                )
            
            # 📋 DETECTAR TEMPLATE (tiene name, language)
            elif isinstance(flow_data, dict) and flow_data.get("name") and flow_data.get("language"):
                print(f"📋 SMART: Detectado TEMPLATE - Name: {flow_data.get('name')}")
                return self.gupshup_sender.send_template_message_v3(
                    to=to,
                    template_name=flow_data["name"],
                    language_code=flow_data["language"]["code"],
                    template_components=flow_data.get("components", []),
                    display_phone_number=display_phone_number
                )
            
            else:
                # JSON pero no reconocido - enviar como texto
                print("📝 SMART: JSON no reconocido - enviando como texto")
                return self.gupshup_sender.send_text_message(
                    to=to,
                    message=message_content,
                    display_phone_number=display_phone_number
                )
                
        except (json.JSONDecodeError, TypeError, ValueError):
            # 📝 NO ES JSON - TEXTO NORMAL
            print("📝 SMART: Texto normal detectado")
            return self.gupshup_sender.send_text_message(
                to=to,
                message=message_content,
                display_phone_number=display_phone_number
            )
        
        except Exception as e:
            print(f"❌ SMART: Error en detección: {str(e)}")
            # Fallback a texto en caso de error
            return self.gupshup_sender.send_text_message(
                to=to,
                message=message_content,
                display_phone_number=display_phone_number
            )
