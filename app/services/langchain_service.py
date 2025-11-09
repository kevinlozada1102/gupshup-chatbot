# app/services/langchain_service.py
import os
import json
from typing import Dict, Any, List
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain.memory import ConversationBufferWindowMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from app.repositories.message_repository import MessageRepository
from app.repositories.products_repository import ProductsRepository
from app.repositories.accounts_repository import AccountsRepository
from app.repositories.account_prompts_repository import AccountPromptsRepository
from app.services.prompt_service import PromptService
from app.tools.productos_tools import create_producto_tools
import logging
import httpx

class AdvancedLangChainService:
    def __init__(self, message_repository: MessageRepository, products_repository: ProductsRepository, 
                 accounts_repository: AccountsRepository, account_prompts_repository: AccountPromptsRepository):
        self.message_repo = message_repository
        self.products_repo = products_repository
        self.prompt_service = PromptService(accounts_repository, account_prompts_repository)
        
        # 1. Inicializar LLM (ChatOpenAI)
        self.llm = ChatOpenAI(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            model="gpt-4o",
            temperature=0.3
        )
        
        # 2. Crear Tools avanzadas para el Agent
        self.tools = create_producto_tools(products_repository)
        
        # 3. Configurar Memory para mantener contexto
        self.memory = ConversationBufferWindowMemory(
            k=10,  # Mantener últimos 10 intercambios
            memory_key="chat_history",
            return_messages=True
        )
        
        # 4. System prompt del .env
        self.system_prompt = os.getenv('SYSTEM_PROMPT', '')
        
        # 5. Crear Agent con Tools
        self.agent_executor = self._create_agent()
    
    def _create_agent(self) -> AgentExecutor:
        """Crea el Agent con Tools y Memory"""
        # Prompt con instrucciones DIRECTAS y ESTRICTAS
        system_instructions = """
Soy AVI de Coolbox! 😊 Soy super amigable y conversacional.

🚨 REGLAS ESTRICTAS QUE DEBES SEGUIR:
- MÁXIMO 3 productos en cualquier lista
- Para listados: SOLO nombres cortos + precio (ej: "Galaxy S21 - S/3,299")
- Para DETALLES/CARACTERÍSTICAS: Usa el campo 'caracteristicas' y sé más descriptivo
- Para COMPARACIONES: Compara 2-3 productos lado a lado incluyendo características principales
- USA emojis naturalmente 😎🔥💪
- SIEMPRE termina preguntando algo para continuar conversación
- Mantén respuestas conversacionales

✅ FORMATO OBLIGATORIO:
"¡Estos Samsung están geniales! 🔥
• Galaxy Z Fold3 - S/7,699 (el más top)
• Galaxy S21 Plus - S/4,299 (súper cámara) 
• Galaxy S20 FE - S/2,499 (buena opción)

¿Cuál te llama más la atención? 😊"

❌ PROHIBIDO:
- Listas largas con especificaciones
- Más de 3 opciones
- Texto robótico sin emojis
- Respuestas que no inviten a seguir hablando
"""
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_instructions),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Crear Agent con Tools
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Agent Executor con Memory
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )
    
    def _create_agent_with_prompt(self, custom_prompt: str) -> AgentExecutor:
        """Crea el Agent con un prompt personalizado desde base de datos"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", custom_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Crear Agent con Tools y prompt personalizado
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Agent Executor con Memory
        return AgentExecutor(
            agent=agent,
            tools=self.tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=3
        )
    
    def process_message(self, session_id: int, user_message: str, from_uid: str = None) -> Dict[str, Any]:
        """
        Procesa mensaje con Agent avanzado:
        - Agent decide automáticamente qué Tools usar
        - Memory mantiene contexto automáticamente  
        - Tools se ejecutan automáticamente
        - Usa prompt dinámico basado en from_uid
        """
        try:
            print(f"🤖 AGENT: Procesando mensaje para sesión {session_id}")
            # 1. Cargar historial de BD a Memory (solo la primera vez)
            self._load_session_history(session_id)
            
            # 2. Obtener prompt dinámico por from_uid si está disponible
            dynamic_prompt = None
            if from_uid:
                dynamic_prompt = self.prompt_service.get_prompt_by_from_uid(from_uid)
                if dynamic_prompt:
                    print(f"✅ Usando prompt dinámico para from_uid: {from_uid}")
                    # Recrear agent con nuevo prompt
                    self.agent_executor = self._create_agent_with_prompt(dynamic_prompt)
                else:
                    print(f"❌ No se encontró prompt para from_uid: {from_uid}, usando prompt estático")
            
            print(f"💬 AGENT: Enviando mensaje a Agent: '{user_message}'")
            print(f"📝 SYSTEM PROMPT: {dynamic_prompt[:100] if dynamic_prompt else self.system_prompt}...")
            
            # 3. Agent procesa mensaje (decide Tools automáticamente)
            response = self.agent_executor.invoke({
                "input": user_message
            })
            
            print(f"✅ AGENT: Respuesta recibida - output: '{response.get('output', 'NO OUTPUT')}'")
            
            return {
                "type": "agent_response",
                "message": response["output"],
                "tools_used": self._extract_tools_used(response),
                "success": True
            }
            
        except Exception as e:
            return {
                "type": "error",
                "message": f"Error procesando con Agent: {str(e)}",
                "success": False
            }
    
    def _load_session_history(self, session_id: int):
        """Carga historial de la BD al Memory de LangChain"""
        try:
            # Obtener historial de mensajes de la sesión
            messages = self.message_repo.find_by_session_id(session_id, limit=10)
            
            # Solo cargar si Memory está vacía (evita duplicados)
            if not hasattr(self, '_loaded_session') or self._loaded_session != session_id:
                self.memory.clear()  # Limpiar memory anterior
                
                # Cargar mensajes al Memory
                for msg in reversed(messages):  # Orden cronológico
                    if msg.message_direction == 0:  # Usuario
                        self.memory.chat_memory.add_user_message(msg.message)
                    else:  # Bot
                        self.memory.chat_memory.add_ai_message(msg.message)
                
                # Marcar como cargado en self, no en memory
                self._loaded_session = session_id
                
        except Exception as e:
            print(f"Error cargando historial: {e}")
    
    def _extract_tools_used(self, response: Dict[str, Any]) -> List[str]:
        """Extrae qué tools usó el Agent (para debugging)"""
        tools_used = []
        if "intermediate_steps" in response:
            for step in response["intermediate_steps"]:
                if hasattr(step[0], 'tool'):
                    tools_used.append(step[0].tool)
        return tools_used
    
    def clear_memory(self):
        """Limpia la memoria del Agent"""
        self.memory.clear()
        if hasattr(self, '_loaded_session'):
            delattr(self, '_loaded_session')

