# app/services/hybrid_orchestrator.py
from typing import Dict, Any, Optional
from app.services.langchain_service import AdvancedLangChainService
from app.services.handler_service import HandlerService
import json

class HybridOrchestrator:
    """
    Orquestador híbrido que combina LangChain con Handlers.
    
    LangChain actúa como "director de orquesta" analizando mensajes del usuario
    y decidiendo qué handler ejecutar y cómo (requestAction vs processMessage).
    """
    
    def __init__(self, langchain_service: AdvancedLangChainService, handler_service: HandlerService):
        self.langchain = langchain_service
        self.handlers = handler_service
    
    def process_message(self, from_uid: str, client_uid: str, message: str, 
                       account_id: str, session_id: int) -> Dict[str, Any]:
        """
        Proceso principal del orquestador híbrido.
        """
        try:
            print(f"🎼 HYBRID ORCHESTRATOR: Analizando mensaje para decidir estrategia")
            
            # 1. Obtener contexto de la sesión
            session_context = self._get_session_context(str(session_id))
            
            # 2. Crear prompt para LangChain Analyzer
            analyzer_prompt = self._build_analyzer_prompt(
                message, session_context, account_id
            )
            
            # 3. LangChain decide la estrategia
            strategy_response = self._get_strategy_from_langchain(analyzer_prompt, from_uid, session_id)
            
            if not strategy_response.get("success"):
                return {"success": False, "message": "Error en análisis de estrategia"}
            
            strategy = strategy_response.get("strategy", {})
            
            print(f"🎯 ESTRATEGIA DECIDIDA: {strategy}")
            
            # 4. Ejecutar la estrategia decidida
            return self._execute_strategy(strategy, from_uid, client_uid, message, 
                                        account_id, session_id, session_context)
            
        except Exception as e:
            print(f"❌ Error en HybridOrchestrator: {str(e)}")
            return {
                "success": False,
                "message": "Ocurrió un error inesperado. Por favor intenta nuevamente.",
                "error": str(e)
            }
    
    def _get_session_context(self, session_id: str) -> Dict[str, Any]:
        """Obtiene contexto de la sesión desde handlers"""
        # Usar el método existente del handler service
        return self.handlers._get_or_create_session_data(session_id)
    
    def _build_analyzer_prompt(self, message: str, session_context: Dict[str, Any], 
                              account_id: str) -> str:
        """
        Construye el prompt para que LangChain analice y decida la estrategia.
        """
        is_first_interaction = not session_context.get("initialized", False)
        current_path = session_context.get("current_path", "")
        
        # CASO ESPECIAL: Si no tiene current_path, es primera vez con handlers aunque tenga sesión
        is_first_time_with_handlers = not current_path
        
        return f"""
Eres un analizador inteligente de conversaciones para un sistema de chatbot híbrido.
Tu trabajo es decidir qué acción tomar basándote en el mensaje del usuario y el contexto.

CONTEXTO ACTUAL:
- Account: {account_id}
- Primera interacción: {is_first_interaction}
- Primera vez con handlers: {is_first_time_with_handlers}
- Path actual: {current_path}
- Mensaje del usuario: "{message}"

OPCIONES DISPONIBLES:
1. REQUEST_ACTION: Mostrar mensaje inicial/menú (primera vez o reinicio)
2. PROCESS_MESSAGE: Procesar respuesta del usuario (navegación en menú)
3. LANGCHAIN_RESPONSE: Responder con IA cuando no hay opción clara en menú

REGLAS DE DECISIÓN:
- Si es primera interacción O primera vez con handlers (current_path vacío) → REQUEST_ACTION
- Si el usuario dice una opción específica de menú (números, palabras clave) → PROCESS_MESSAGE  
- Si el usuario hace preguntas abiertas o mensajes confusos → LANGCHAIN_RESPONSE
- Si usuario dice "menú", "inicio", "empezar" → REQUEST_ACTION

⚠️ IMPORTANTE: Si Primera vez con handlers = True, SIEMPRE usar REQUEST_ACTION

Responde SOLO con un JSON válido con esta estructura:
{{
    "action": "REQUEST_ACTION|PROCESS_MESSAGE|LANGCHAIN_RESPONSE",
    "handler": "DbAnswerHandler|EndHandler|etc",
    "reasoning": "explicación breve de por qué elegiste esta acción",
    "confidence": 0.8
}}

RESPONDE SOLO EL JSON, SIN TEXTO ADICIONAL.
"""

    def _get_strategy_from_langchain(self, prompt: str, from_uid: str, session_id: int) -> Dict[str, Any]:
        """
        Usa LangChain para obtener la estrategia de procesamiento.
        """
        try:
            # Usar el servicio LangChain existente pero con prompt personalizado
            ai_response = self.langchain.llm.invoke(prompt)
            
            # Parsear la respuesta JSON (manejar markdown)
            try:
                content = ai_response.content.strip()
                
                # Si viene con markdown (```json), extraer solo el JSON
                if content.startswith("```json"):
                    # Extraer contenido entre ```json y ```
                    json_start = content.find("```json") + 7
                    json_end = content.rfind("```")
                    content = content[json_start:json_end].strip()
                elif content.startswith("```"):
                    # Si solo tiene ``` sin especificar json
                    json_start = content.find("```") + 3
                    json_end = content.rfind("```")
                    content = content[json_start:json_end].strip()
                
                print(f"✅ JSON extraído: {content}")
                
                strategy_json = json.loads(content)
                return {
                    "success": True,
                    "strategy": strategy_json
                }
            except json.JSONDecodeError as e:
                print(f"❌ Error parseando JSON de LangChain: {ai_response.content}")
                return {
                    "success": False,
                    "error": f"JSON parsing error: {str(e)}"
                }
                
        except Exception as e:
            print(f"❌ Error consultando LangChain para estrategia: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _execute_strategy(self, strategy: Dict[str, Any], from_uid: str, client_uid: str, 
                         message: str, account_id: str, session_id: int, 
                         session_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ejecuta la estrategia decidida por LangChain.
        """
        action = strategy.get("action")
        handler_name = strategy.get("handler", "DbAnswerHandler")
        reasoning = strategy.get("reasoning", "No reasoning provided")
        
        print(f"🚀 EJECUTANDO: {action} con {handler_name}")
        print(f"💭 RAZÓN: {reasoning}")
        
        if action == "REQUEST_ACTION":
            # Si es primera interacción, configurar current_path inicial
            if not session_context.get("current_path"):
                initial_path = self.handlers._get_initial_path(from_uid)
                if initial_path:
                    session_context["current_path"] = initial_path
                    print(f"🎯 Path inicial configurado en HybridOrchestrator: {initial_path}")
                else:
                    print(f"❌ No se pudo obtener path inicial para {from_uid}")
                    return {
                        "success": False,
                        "message": "Configuración de chatbot no encontrada."
                    }
            
            # Ejecutar requestAction del handler (mostrar menú/mensaje inicial)
            result = self.handlers.handler_registry.execute_request_action(
                handler_name, 0, from_uid, client_uid, session_context, 
                {"account_id": account_id, "session_id": str(session_id), "from_uid": from_uid, "client_uid": client_uid}
            )
            
            # Marcar como inicializado
            if result.get("success"):
                updated_session = result.get("session_data", session_context)
                updated_session["initialized"] = True
                self.handlers.session_data_repo.save_session_data(str(session_id), updated_session)
            
            return {
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "strategy_used": "REQUEST_ACTION",
                "handler_used": handler_name,
                "reasoning": reasoning
            }
            
        elif action == "PROCESS_MESSAGE":
            # Procesar respuesta del usuario con handlers
            context = {
                "account_id": account_id, 
                "session_id": str(session_id),
                "from_uid": from_uid, 
                "client_uid": client_uid
            }
            
            result = self.handlers.handler_registry.execute_handler(
                handler_name, message, session_context, context
            )
            
            if result.get("success"):
                updated_session = result.get("session_data", session_context)
                self.handlers.session_data_repo.save_session_data(str(session_id), updated_session)
            
            return {
                "success": result.get("success", False),
                "message": result.get("message", ""),
                "strategy_used": "PROCESS_MESSAGE", 
                "handler_used": handler_name,
                "next_handler": result.get("next_handler"),
                "reasoning": reasoning
            }
            
        elif action == "LANGCHAIN_RESPONSE":
            # Responder con LangChain cuando no hay opción clara
            ai_response = self.langchain.process_message(
                session_id=session_id,
                user_message=message,
                from_uid=from_uid
            )
            
            return {
                "success": ai_response.get("success", False),
                "message": ai_response.get("message", ""),
                "strategy_used": "LANGCHAIN_RESPONSE",
                "reasoning": reasoning
            }
            
        else:
            return {
                "success": False,
                "message": "Estrategia desconocida",
                "error": f"Unknown action: {action}"
            }