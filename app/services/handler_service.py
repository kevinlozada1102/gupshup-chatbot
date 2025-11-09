# app/services/handler_service.py
from typing import Dict, Any, Optional
from app.handlers.handler_registry import HandlerRegistry
from app.handlers.db_answer_handler import DbAnswerHandler
from app.handlers.end_handler import EndHandler
from app.handlers.dummy_handler import DummyHandler
from app.repositories.simple_answer_repository import SimpleAnswerRepository
from app.repositories.text_chatbot_repository import TextChatbotRepository
from app.repositories.session_data_repository import SessionDataRepository

class HandlerService:
    """
    Servicio principal que coordina el sistema de handlers.
    Equivale al flujo principal de HelloHandler + DbAnswerHandler en mazz-chatbot.
    """
    
    def __init__(self, 
                 simple_answer_repository: SimpleAnswerRepository,
                 text_chatbot_repository: TextChatbotRepository, 
                 session_data_repository: SessionDataRepository,
                 gupshup_sender_service=None,
                 message_repository=None):
        
        self.simple_answer_repo = simple_answer_repository
        self.text_chatbot_repo = text_chatbot_repository
        self.session_data_repo = session_data_repository
        self.gupshup_sender = gupshup_sender_service
        self.message_repo = message_repository
        
        # Inicializar registry y registrar handlers
        self.handler_registry = HandlerRegistry()
        self._register_handlers()
    
    def _register_handlers(self):
        """Registra todos los handlers disponibles"""
        # Importar todos los handlers
        from app.handlers.db_interactive_template_handler import DbInteractiveTemplateHandler
        from app.handlers.db_flow_handler import DbFlowHandler
        from app.handlers.chatgpt_handler import ChatGptHandler
        from app.handlers.db_ask_handler import DbAskHandler
        
        # Registrar DbAnswerHandler (principal)
        db_answer_handler = DbAnswerHandler(self.simple_answer_repo)
        self.handler_registry.register(db_answer_handler)
        
        # Registrar DbInteractiveTemplateHandler (templates interactivos)
        template_handler = DbInteractiveTemplateHandler(self.simple_answer_repo)
        self.handler_registry.register(template_handler)
        
        # Registrar DbFlowHandler (flujos automatizados)
        flow_handler = DbFlowHandler(self.simple_answer_repo)
        self.handler_registry.register(flow_handler)
        
        # Registrar DbAskHandler (preguntas libres)
        ask_handler = DbAskHandler(self.simple_answer_repo)
        self.handler_registry.register(ask_handler)
        
        # Registrar ChatGptHandler (IA integrada) - REQUIERE LangChain service
        try:
            from app.services.langchain_service import AdvancedLangChainService
            from app.repositories.message_repository import MessageRepository
            from app.repositories.products_repository import ProductsRepository
            from app.repositories.accounts_repository import AccountsRepository
            from app.repositories.account_prompts_repository import AccountPromptsRepository
            from app.config.database import SessionLocal
            
            # Crear dependencias para LangChain (temporal)
            db_session = SessionLocal()
            try:
                message_repo = MessageRepository(db_session)
                products_repo = ProductsRepository(db_session)
                accounts_repo = AccountsRepository(db_session)
                prompts_repo = AccountPromptsRepository(db_session)
                
                langchain_service = AdvancedLangChainService(
                    message_repo, products_repo, accounts_repo, prompts_repo
                )
                
                chatgpt_handler = ChatGptHandler(self.simple_answer_repo, langchain_service)
                self.handler_registry.register(chatgpt_handler)
                
            finally:
                db_session.close()
                
        except Exception as e:
            print(f"⚠️ No se pudo registrar ChatGptHandler: {e}")
        
        # Registrar EndHandler (finalización)
        end_handler = EndHandler()
        self.handler_registry.register(end_handler)
        
        # Registrar DummyHandler (transferencias a agentes)
        try:
            from app.repositories.transfered_chat_repository import TransferedChatRepository
            from app.config.database import SessionLocal
            
            # Crear repositorio temporal para transferencias
            db_session = SessionLocal()
            try:
                transfered_chat_repo = TransferedChatRepository(db_session)
                dummy_handler = DummyHandler(self.simple_answer_repo, transfered_chat_repo)
                self.handler_registry.register(dummy_handler)
                print(f"✅ Handler registrado: DummyHandler (con transferencias)")
            finally:
                db_session.close()
                
        except Exception as e:
            print(f"⚠️ DummyHandler sin transferencias: {e}")
            # Fallback sin transferencias
            dummy_handler = DummyHandler(self.simple_answer_repo)
            self.handler_registry.register(dummy_handler)
        
        print(f"📋 Handlers registrados: {self.handler_registry.list_handlers()}")
    
    def process_message(self, from_uid: str, client_uid: str, message: str, 
                       account_id: str, session_id: int) -> Dict[str, Any]:
        """
        Procesa un mensaje usando el sistema de handlers.
        Equivale al flujo completo de HelloHandler.doRequest() en tenet.
        """
        try:
            print(f"🚀 HandlerService: Procesando mensaje de {client_uid} para account {account_id}")
            
            # 1. Verificar si existe session_data
            existing_session_data = self.session_data_repo.get_session_data_as_dict(str(session_id))
            
            # Variable para determinar si es nueva conversación
            is_restarted_conversation = False
            
            if existing_session_data:
                # CONVERSACIÓN EXISTENTE
                print(f"🔄 CONVERSACIÓN EXISTENTE - Session data encontrada")
                session_data = existing_session_data
                current_path = session_data.get("current_path", "")
                print(f"🔄 Path actual: {current_path}")
                
                # Verificar si la conversación ha terminado
                if current_path == "/EndHandler":
                    print(f"🔄 Conversación terminada, reiniciando como nueva")
                    # Tratar como nueva conversación
                    initial_path = self._get_initial_path(from_uid)
                    if not initial_path:
                        return {
                            "success": False,
                            "message": "Configuración de chatbot no encontrada."
                        }
                    session_data["current_path"] = initial_path
                    current_path = initial_path
                    is_restarted_conversation = True  # Marcar como reiniciada
                    print(f"🎯 REINICIANDO - Nuevo path inicial: {initial_path}")
            else:
                # NUEVA CONVERSACIÓN
                print(f"🎯 NUEVA CONVERSACIÓN - No hay session data")
                initial_path = self._get_initial_path(from_uid)
                if not initial_path:
                    return {
                        "success": False,
                        "message": "Configuración de chatbot no encontrada."
                    }
                
                # Crear nueva session_data
                session_data = {
                    "current_path": initial_path,
                    "history": []
                }
                current_path = initial_path
                print(f"🎯 Path inicial desde tbl_text_chatbot: {initial_path}")
            
            # 3. Preparar contexto
            context = {
                "from_uid": from_uid,
                "client_uid": client_uid,
                "account_id": account_id,
                "session_id": str(session_id)
            }
            
            # 3. Determinar handler a ejecutar
            handler_name = self._extract_handler_name_from_path(current_path)
            
            if not handler_name:
                return {
                    "success": False,
                    "message": "Error determinando handler."
                }
            
            print(f"🎭 Handler determinado: {handler_name} para path: {current_path}")
            
            # 4. Lógica de ejecución basada en existencia de session_data
            if existing_session_data and current_path != "/EndHandler" and not is_restarted_conversation:
                # CONVERSACIÓN EXISTENTE: siempre procesar mensaje del usuario si hay mensaje
                if message.strip():
                    print(f"📝 CONVERSACIÓN EXISTENTE - Procesando mensaje: '{message.strip()}'")
                    result = self.handler_registry.execute_handler(handler_name, message, session_data, context)
                else:
                    print(f"🔄 CONVERSACIÓN EXISTENTE - Sin mensaje, mostrando estado actual")
                    result = self.handler_registry.execute_request_action(
                        handler_name, 0, from_uid, client_uid, session_data, context
                    )
            else:
                # NUEVA CONVERSACIÓN O REINICIADA: mostrar mensaje inicial (ignorar mensaje del usuario)
                conversation_type = "REINICIADA" if is_restarted_conversation else "NUEVA"
                print(f"🎬 CONVERSACIÓN {conversation_type} - Mostrando mensaje inicial (ignorando: '{message.strip()}')")
                result = self.handler_registry.execute_request_action(
                    handler_name, 0, from_uid, client_uid, session_data, context
                )
            
            if not result.get("success"):
                return result
            
            # 6. EJECUCIÓN RECURSIVA CON ENVÍO INMEDIATO DE MENSAJES
            
            # ENVIAR EL PRIMER MENSAJE INMEDIATAMENTE
            first_message = result.get("message", "")
            if first_message.strip() and self.gupshup_sender:
                print(f"📤 ENVIANDO MENSAJE 1: '{first_message[:50]}...'")
                self._send_message_immediately(first_message, client_uid, from_uid, context)
            elif first_message.strip():
                print(f"⚠️ MENSAJE 1 sin enviar (no hay sender service): '{first_message[:50]}...'")
            
            messages_sent_count = 1 if first_message.strip() else 0
            final_result = result.copy()
            
            # Ejecutar recursivamente la cadena de handlers
            current_result = result
            iteration = 1
            max_iterations = 10  # Prevenir bucles infinitos
            
            while iteration <= max_iterations:
                next_handler = current_result.get("next_handler")
                next_path = current_result.get("next_path")
                
                # Si no hay siguiente handler o es EndHandler, parar
                if not next_handler or next_handler == "EndHandler":
                    print(f"🏁 Cadena de handlers terminada: {next_handler or 'Sin handler'}")
                    break
                
                # Si el path no cambia y el mensaje está vacío, romper el bucle
                current_message = current_result.get("message", "")
                current_path_in_session = updated_session_data.get("current_path") if iteration > 1 else session_data.get("current_path")
                if (next_path == current_path_in_session and 
                    not current_message.strip()):
                    print(f"🛑 Rompiendo bucle: Path no cambia ({next_path}) y mensaje vacío")
                    break
                    
                print(f"🔄 ITERACIÓN {iteration}: Ejecutando {next_handler} con path {next_path}")
                
                # Ejecutar el siguiente handler
                updated_session_data = current_result.get("session_data", session_data)
                
                print(f"🔍 DEBUG ITERACIÓN {iteration}:")
                print(f"  → updated_session_data recibida desde handler anterior: {updated_session_data}")
                print(f"  → current_path en session_data: '{updated_session_data.get('current_path')}'")
                
                next_result = self.handler_registry.execute_request_action(
                    next_handler, 0, from_uid, client_uid, updated_session_data, context
                )
                
                print(f"🔍 RESULTADO DE {next_handler}:")
                print(f"  → Success: {next_result.get('success')}")
                print(f"  → session_data devuelta por handler: {next_result.get('session_data')}")
                print(f"  → current_path en session_data devuelta: '{next_result.get('session_data', {}).get('current_path')}'")
                
                if not next_result.get("success"):
                    print(f"❌ Error ejecutando {next_handler}, parando cadena")
                    break
                
                # ENVIAR MENSAJE INMEDIATAMENTE si no está vacío
                next_message = next_result.get("message", "")
                if next_message.strip() and self.gupshup_sender:
                    messages_sent_count += 1
                    print(f"📤 ENVIANDO MENSAJE {messages_sent_count}: '{next_message[:50]}...'")
                    self._send_message_immediately(next_message, client_uid, from_uid, context)
                elif next_message.strip():
                    print(f"⚠️ MENSAJE {messages_sent_count + 1} sin enviar: '{next_message[:50]}...'")
                    
                # Actualizar resultado final con la última iteración
                final_result.update({
                    "next_handler": next_result.get("next_handler"),
                    "next_path": next_result.get("next_path"),
                    "session_data": next_result.get("session_data"),
                    "last_message": next_message  # Guardar último mensaje para debugging
                })
                
                # Actualizar current_path para la siguiente iteración
                updated_session_data["current_path"] = next_result.get("next_path")
                
                # GUARDAR SESSION_DATA DESPUÉS DE CADA ITERACIÓN
                print(f"💾 ACTUALIZANDO tbl_session_data - Iteración {iteration}")
                print(f"  → Session ID: {context['session_id']}")
                print(f"  → updated_session_data completa ANTES de guardar: {updated_session_data}")
                print(f"  → current_path que se va a guardar: '{updated_session_data.get('current_path')}'")
                
                # Guardar en BD
                self.session_data_repo.save_session_data(context["session_id"], updated_session_data)
                
                # Verificar que se guardó correctamente
                verification_data = self.session_data_repo.get_session_data_as_dict(context["session_id"])
                print(f"  → VERIFICACIÓN - session_data guardada en BD: {verification_data}")
                print(f"  → VERIFICACIÓN - current_path en BD: '{verification_data.get('current_path') if verification_data else 'NO DATA'}'")
                
                current_result = next_result
                iteration += 1
            
            if iteration > max_iterations:
                print(f"⚠️ Máximo de iteraciones alcanzado ({max_iterations}), posible bucle infinito")
            
            # Para el sistema actual, devolvemos solo el primer mensaje
            # Los demás se "enviaron" durante la ejecución recursiva
            final_result["message"] = first_message  # Solo el primer mensaje para el flujo principal
            final_result["messages_sent"] = messages_sent_count
            
            print(f"🎆 CADENA COMPLETA: {messages_sent_count} mensajes enviados por separado")
            
            result = final_result
            
            # 7. Session_data ya se guardó durante cada iteración
            # Solo guardar si no hubo iteraciones (caso de mensaje único)
            if messages_sent_count <= 1:
                updated_session_data = result.get("session_data", session_data)
                print(f"💾 GUARDADO FINAL de session_data (mensaje único)")
                print(f"  → Session ID: {context['session_id']}")
                print(f"  → updated_session_data completa ANTES de guardar: {updated_session_data}")
                print(f"  → current_path que se va a guardar: '{updated_session_data.get('current_path')}'")
                
                # Guardar en BD
                self.session_data_repo.save_session_data(context["session_id"], updated_session_data)
                
                # Verificar que se guardó correctamente
                verification_data = self.session_data_repo.get_session_data_as_dict(context["session_id"])
                print(f"  → VERIFICACIÓN - session_data guardada en BD: {verification_data}")
                print(f"  → VERIFICACIÓN - current_path en BD: '{verification_data.get('current_path') if verification_data else 'NO DATA'}'")
            else:
                print(f"💾 Session_data ya actualizada durante {messages_sent_count} iteraciones")
            
            # 8. Manejar EndHandler (finalización)
            if result.get("next_handler") == "EndHandler" or result.get("next_path") == "/EndHandler":
                print("🏁 Conversación finalizada - EndHandler")
                self._handle_end_conversation(str(session_id))
                
            final_result = {
                "success": True,
                "message": result.get("message", ""),
                "handler_used": next_handler or handler_name,
                "next_path": result.get("next_path")
            }
            
            print(f"✅ RESULTADO FINAL HANDLER SERVICE:")
            print(f"  - Handler usado: {final_result['handler_used']}")
            print(f"  - Next path: {final_result['next_path']}")
            print(f"  - Mensaje: '{final_result['message'][:100]}{'...' if len(final_result['message']) > 100 else ''}'")
            
            return final_result
            
        except Exception as e:
            print(f"❌ Error en HandlerService: {str(e)}")
            return {
                "success": False,
                "message": "Ocurrió un error inesperado. Por favor intenta nuevamente.",
                "error": str(e)
            }
    
    
    def _get_initial_path(self, from_uid: str) -> Optional[str]:
        """
        Obtiene el path inicial desde tbl_text_chatbot.
        Busca por from_uid sin importar el canal.
        """
        # Buscar cualquier configuración para este from_uid (sin filtrar por canal)
        configs = self.text_chatbot_repo.find_by_from_uid(from_uid)
        if configs:
            initial_path = configs[0].initial_path  # Tomar el primero
            print(f"🔍 Path inicial para {from_uid}: {initial_path}")
            return initial_path
        
        print(f"🔍 Path inicial para {from_uid}: None (no encontrado)")
        return None
    
    def _extract_handler_name_from_path(self, path: str) -> Optional[str]:
        """Extrae nombre del handler de un path"""
        if not path:
            return None
        
        parts = path.strip('/').split('/')
        return parts[0] if parts else None
    
    def _handle_end_conversation(self, session_id: str):
        """Maneja el final de conversación"""
        # Marcar conversación como terminada pero mantener current_path = /EndHandler
        self.session_data_repo.update_session_data(session_id, "conversation_ended", True)
        # NO limpiar current_path - debe mantenerse como /EndHandler para lógica de nueva conversación
        
        # Verificar estado final
        final_session_data = self.session_data_repo.get_session_data_as_dict(session_id)
        print(f"🧹 Conversación finalizada para session: {session_id}")
        print(f"  → Estado final en BD: {final_session_data}")
        print(f"  → current_path mantenido: '{final_session_data.get('current_path') if final_session_data else 'NO DATA'}'")
    
    def get_registered_handlers(self) -> list[str]:
        """Obtiene lista de handlers registrados"""
        return self.handler_registry.list_handlers()
    
    def _send_message_immediately(self, message: str, client_uid: str, from_uid: str, context: dict = None):
        """Envía mensaje inmediatamente usando GupshupSenderService y lo guarda en tbl_message"""
        try:
            if self.gupshup_sender:
                # Detectar si el mensaje es un JSON de template interactivo
                send_result = self._send_smart_message(message, client_uid, from_uid)
                
                if send_result.get("success"):
                    print(f"✅ Mensaje enviado exitosamente")
                    
                    # GUARDAR EN TBL_MESSAGE cada mensaje enviado durante recursion
                    if context:
                        self._save_bot_message_to_db(message, client_uid, from_uid, context, send_result)
                        
                else:
                    print(f"❌ Error enviando mensaje: {send_result.get('error')}")
            else:
                print(f"⚠️ No se puede enviar: GupshupSender no disponible")
        except Exception as e:
            print(f"❌ Excepción enviando mensaje: {str(e)}")
    
    def _save_bot_message_to_db(self, message: str, client_uid: str, from_uid: str, context: dict, send_result: dict):
        """Guarda mensaje del bot en tbl_message usando repositorio existente"""
        try:
            if self.message_repo:
                # Usar repositorio existente
                bot_message = self.message_repo.save_message(
                    from_uid=from_uid,
                    client_uid=client_uid,
                    message_body=message,
                    account_id=context.get("account_id"),
                    session_id=int(context.get("session_id")),
                    message_id=send_result.get("message_id", f"bot_recursive_{hash(message) % 10000}"),
                    message_channel=0,
                    message_direction=1,  # Respuesta del bot
                    message_type=1
                )
                print(f"💾 MENSAJE RECURSIVO GUARDADO EN BD: ID {bot_message.id}")
            else:
                print(f"⚠️ No se pudo guardar: message_repo no disponible")
                
        except Exception as e:
            print(f"❌ Error guardando mensaje recursivo en BD: {str(e)}")
    
    def _send_smart_message(self, message: str, client_uid: str, from_uid: str):
        """Detecta el tipo de mensaje y usa el método apropiado para enviarlo"""
        import json
        
        # Intentar parsear como JSON para detectar templates interactivos
        try:
            message_data = json.loads(message)
            
            # Detectar si es un template con botones
            if isinstance(message_data, dict) and "buttons" in message_data:
                print(f"🎁 Detectado template con BOTONES")
                return self._send_interactive_button_message(message_data, client_uid, from_uid)
            
            # Detectar si es un template con lista
            elif isinstance(message_data, dict) and "list" in message_data:
                print(f"📝 Detectado template con LISTA")
                return self._send_interactive_list_message(message_data, client_uid, from_uid)
            
            # Detectar si es un flow
            elif isinstance(message_data, dict) and "id" in message_data and "token" in message_data:
                print(f"🌊 Detectado FLOW interactivo")
                return self.gupshup_sender.send_flow_message(
                    to=client_uid,
                    flow_data=message_data,
                    display_phone_number=from_uid
                )
            
            # Si es JSON pero no es ningún template conocido, enviar como texto
            else:
                print(f"📝 JSON sin formato conocido, enviando como texto")
                return self.gupshup_sender.send_text_message(
                    to=client_uid,
                    message=message,
                    display_phone_number=from_uid
                )
                
        except json.JSONDecodeError:
            # No es JSON, es texto plano
            print(f"💬 Enviando como mensaje de TEXTO")
            return self.gupshup_sender.send_text_message(
                to=client_uid,
                message=message,
                display_phone_number=from_uid
            )
    
    def _send_interactive_button_message(self, button_data: dict, client_uid: str, from_uid: str):
        """Envía mensaje interactivo con botones usando la API de Gupshup"""
        try:
            # Construir payload para mensaje interactivo con botones
            # Basado en la documentación de WhatsApp Business API
            
            # Obtener credenciales y token (similar a otros métodos)
            account = self.gupshup_sender.accounts_repo.find_by_from_uid(from_uid)
            if not account:
                return {"success": False, "error": "Account not found"}
            
            # Login y token (reutilizar lógica existente)
            login_result = self.gupshup_sender.get_login_partner(account.gs_user, account.gs_password)
            if not login_result["success"]:
                return login_result
            
            token_result = self.gupshup_sender.get_token_app(login_result["login_response"]["token"], account.appid)
            if not token_result["success"]:
                return token_result
            
            app_token = token_result["token_response"]["token"]["token"]
            
            # Construir payload para botones interactivos
            import requests
            
            url = f"https://partner.gupshup.io/partner/app/{account.appid}/v3/message"
            headers = {
                "Authorization": app_token,
                "Content-Type": "application/json"
            }
            
            # Convertir botones a formato de WhatsApp
            interactive_buttons = []
            buttons = button_data.get("buttons", [])
            
            for i, button_text in enumerate(buttons[:3]):  # Máximo 3 botones
                interactive_buttons.append({
                    "type": "reply",
                    "reply": {
                        "id": f"btn_{i}_{button_text.lower().replace(' ', '_')}",
                        "title": button_text[:20]  # Máximo 20 caracteres
                    }
                })
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": client_uid,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "header": {
                        "type": "text",
                        "text": button_data.get("header", "Menú")
                    },
                    "body": {
                        "text": button_data.get("text", "Selecciona una opción:")
                    },
                    "action": {
                        "buttons": interactive_buttons
                    }
                }
            }
            
            print(f"🎁 BUTTONS: Payload: {payload}")
            
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"✅ BUTTONS: Enviado exitosamente")
                return {
                    "success": True,
                    "message_id": response_data.get("messages", [{}])[0].get("id"),
                    "gupshup_response": response_data
                }
            else:
                error_data = response.json() if 'application/json' in response.headers.get('content-type', '') else response.text
                print(f"❌ BUTTONS: Error - Status: {response.status_code}, Response: {error_data}")
                return {
                    "success": False,
                    "error": f"Error enviando botones: HTTP {response.status_code}",
                    "error_details": error_data
                }
                
        except Exception as e:
            print(f"❌ BUTTONS: Excepción - {str(e)}")
            return {
                "success": False,
                "error": f"Error con botones: {str(e)}"
            }
    
    def _send_interactive_list_message(self, list_data: dict, client_uid: str, from_uid: str):
        """Envía mensaje interactivo con lista usando la API de Gupshup"""
        # Por ahora, enviar como texto hasta implementar completamente
        print(f"⚠️ LISTA: Aún no implementado, enviando como texto")
        return self.gupshup_sender.send_text_message(
            to=client_uid,
            message=str(list_data),
            display_phone_number=from_uid
        )
