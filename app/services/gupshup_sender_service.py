# app/services/gupshup_sender_service.py
import requests
import os
import json
from typing import Dict, Any, Optional
from app.repositories.accounts_repository import AccountsRepository
from app.utils.gupshup_logger import GupshupLogger

class GupshupSenderService:
    def __init__(self, accounts_repository: AccountsRepository):
        self.accounts_repo = accounts_repository
        self.base_url = os.getenv('GUPSHUP_BASE_URL', 'https://partner.gupshup.io/partner/app')
        # URL base para autenticación (extraída de tu Java)
        self.api_base_url = "https://partner.gupshup.io/partner"  # Asumiendo esta URL base
    
    def get_login_partner(self, email: str, password: str) -> Dict[str, Any]:
        """Equivale a getLoginPatner en Java"""
        try:
            url = f"{self.api_base_url}/account/login"
            print(f"🔑 LOGIN: URL: {url}")
            print(f"🔑 LOGIN: Email: {email}")
            
            # Mostrar cURL exacto para debugging
            curl_cmd = f"""curl -X POST {url} \\
  -H "Content-Type: application/x-www-form-urlencoded" \\
  -d "email={email}&password={password}"""
            print(f"🔧 LOGIN CURL: {curl_cmd}")
            
            headers = {
                "Content-Type": "application/x-www-form-urlencoded"
            }
            data = {
                "email": email,
                "password": password
            }
            
            response = requests.post(url, headers=headers, data=data, timeout=10)
            print(f"🔑 LOGIN: Status Code: {response.status_code}")
            
            if response.status_code == 200:
                login_data = response.json()
                print(f"✅ LOGIN: Exitoso - Token obtenido: {login_data.get('token', 'NO TOKEN')[:20]}...")
                return {
                    "success": True,
                    "login_response": login_data
                }
            else:
                print(f"❌ LOGIN: Fallido - Status: {response.status_code}, Response: {response.text}")
                return {
                    "success": False,
                    "error": f"Login failed: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Login error: {str(e)}"
            }
    
    def get_token_app(self, login_token: str, app_id: str) -> Dict[str, Any]:
        """Equivale a getTokenApp en Java"""
        try:
            url = f"{self.api_base_url}/app/{app_id}/token"
            print(f"🎨 TOKEN_APP: URL: {url}")
            print(f"🎨 TOKEN_APP: App ID: {app_id}")
            print(f"🎨 TOKEN_APP: Login Token: {login_token[:20]}...")
            
            # Mostrar cURL exacto para debugging
            curl_cmd = f"""curl -X GET {url} \\
  -H "Content-Type: application/json" \\
  -H "Authorization: {login_token}"""
            print(f"🔧 TOKEN_APP CURL: {curl_cmd}")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": login_token
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            print(f"🎨 TOKEN_APP: Status Code: {response.status_code}")
            
            if response.status_code == 200:
                token_data = response.json()
                app_token = token_data.get('token', {}).get('token', 'NO TOKEN')
                print(f"✅ TOKEN_APP: Exitoso - App Token: {app_token[:20]}...")
                print(f"✅ TOKEN_APP: Response completa: {token_data}")
                return {
                    "success": True,
                    "token_response": token_data
                }
            else:
                print(f"❌ TOKEN_APP: Fallido - Status: {response.status_code}, Response: {response.text}")
                return {
                    "success": False,
                    "error": f"Token app failed: {response.status_code}",
                    "details": response.text
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Token app error: {str(e)}"
            }
        
    def send_text_message(self, to: str, message: str, display_phone_number: str) -> Dict[str, Any]:
        """
        Envía mensaje de texto via Gupshup API V3 con flujo de autenticación de 3 pasos
        Equivale al flujo Java: getLoginPatner -> getTokenApp -> enviarMensaje
        
        Args:
            to: Número del destinatario (ej: '51987654321')
            message: Contenido del mensaje
            display_phone_number: Número de la cuenta de WhatsApp Business
            
        Returns:
            Dict con resultado del envío
        """
        try:
            # 1. Obtener credenciales de la cuenta (equivale a findByFromUid)
            account = self.accounts_repo.find_by_from_uid(display_phone_number)
            
            if not account:
                GupshupLogger.log_credentials_issue(
                    display_phone_number, 
                    f"Cuenta no encontrada para {display_phone_number}"
                )
                return {
                    "success": False,
                    "error": f"No se encontró cuenta para {display_phone_number}",
                    "error_code": "ACCOUNT_NOT_FOUND"
                }
            
            if not account.appid or not account.gs_user or not account.gs_password:
                GupshupLogger.log_credentials_issue(
                    display_phone_number,
                    "Credenciales incompletas: falta appid, gs_user o gs_password"
                )
                return {
                    "success": False,
                    "error": "Credenciales incompletas en la cuenta",
                    "error_code": "MISSING_CREDENTIALS"
                }
            
            # 2. PASO 1: Login Partner (equivale a getLoginPatner)
            login_result = self.get_login_partner(account.gs_user, account.gs_password)
            
            if not login_result["success"]:
                GupshupLogger.log_credentials_issue(
                    display_phone_number,
                    f"Login fallido: {login_result['error']}"
                )
                return {
                    "success": False,
                    "error": f"Login fallido: {login_result['error']}",
                    "error_code": "LOGIN_FAILED"
                }
            
            login_token = login_result["login_response"].get("token")
            if not login_token:
                return {
                    "success": False,
                    "error": "No se obtuvo token de login",
                    "error_code": "NO_LOGIN_TOKEN"
                }
            
            # 3. PASO 2: Get Token App (equivale a getTokenApp)
            token_result = self.get_token_app(login_token, account.appid)
            
            if not token_result["success"]:
                return {
                    "success": False,
                    "error": f"Token app fallido: {token_result['error']}",
                    "error_code": "TOKEN_APP_FAILED"
                }
            
            app_token_data = token_result["token_response"].get("token")
            if not app_token_data or not app_token_data.get("token"):
                return {
                    "success": False,
                    "error": "No se obtuvo token de app",
                    "error_code": "NO_APP_TOKEN"
                }
            
            app_token = app_token_data["token"]
            
            # 4. PASO 3: Enviar Mensaje (equivale a enviarMensaje)
            url = f"{self.api_base_url}/app/{account.appid}/v3/message"
            print(f"📤 SEND_MSG: URL: {url}")
            print(f"📤 SEND_MSG: To: {to}")
            print(f"📤 SEND_MSG: App Token: {app_token[:20]}...")
            
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": app_token
            }
            
            # Payload equivale a WhatsAppMessageRequest
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            print(f"📤 SEND_MSG: Payload: {payload}")
            
            # Mostrar cURL exacto para debugging
            import json
            payload_json = json.dumps(payload, ensure_ascii=False)
            curl_cmd = f"""curl -X POST {url} \\
  -H "Content-Type: application/json" \\
  -H "Accept: application/json" \\
  -H "Authorization: {app_token}" \\
  -d '{payload_json}'"""
            print(f"🔧 SEND_MSG CURL: {curl_cmd}")
            
            # Enviar request
            response = requests.post(
                url=url, 
                headers=headers, 
                json=payload,
                timeout=10
            )
            print(f"📤 SEND_MSG: Response Status: {response.status_code}")
            
            # 5. Procesar respuesta
            if response.status_code == 200:
                response_data = response.json()
                print(f"✅ SEND_MSG: EXITOSO - Response completa: {response_data}")
                
                # Log exitoso
                GupshupLogger.log_message_sent(
                    to=to,
                    message=message,
                    result=response_data,
                    app_id=account.appid
                )
                
                return {
                    "success": True,
                    "message_id": response_data.get("id"),
                    "status": response_data.get("status"),
                    "gupshup_response": response_data,
                    "app_id": account.appid
                }
            else:
                error_data = response.json() if 'application/json' in response.headers.get('content-type', '') else response.text
                print(f"❌ SEND_MSG: ERROR - Status: {response.status_code}, Response: {error_data}")
                
                # Log error HTTP
                GupshupLogger.log_message_failed(
                    to=to,
                    message=message,
                    error=f"HTTP {response.status_code}: {error_data}",
                    error_code="HTTP_ERROR",
                    app_id=account.appid
                )
                
                return {
                    "success": False,
                    "error": f"Error HTTP {response.status_code}",
                    "error_details": error_data,
                    "error_code": "HTTP_ERROR"
                }
                
        except requests.exceptions.Timeout:
            GupshupLogger.log_message_failed(
                to=to, message=message, error="Timeout", error_code="TIMEOUT"
            )
            return {
                "success": False,
                "error": "Timeout al enviar mensaje",
                "error_code": "TIMEOUT"
            }
        except requests.exceptions.RequestException as e:
            GupshupLogger.log_message_failed(
                to=to, message=message, error=str(e), error_code="CONNECTION_ERROR"
            )
            return {
                "success": False,
                "error": f"Error de conexión: {str(e)}",
                "error_code": "CONNECTION_ERROR"
            }
        except Exception as e:
            GupshupLogger.log_message_failed(
                to=to, message=message, error=str(e), error_code="UNEXPECTED_ERROR"
            )
            return {
                "success": False,
                "error": f"Error inesperado: {str(e)}",
                "error_code": "UNEXPECTED_ERROR"
            }
    
    def send_media_message(self, to: str, media_url: str, caption: str, 
                          media_type: str, display_phone_number: str) -> Dict[str, Any]:
        """
        Envía mensaje con media (imagen, video, documento) via Gupshup API V3
        
        Args:
            to: Número del destinatario
            media_url: URL del archivo multimedia
            caption: Texto que acompaña al archivo
            media_type: 'image', 'video', 'document'
            display_phone_number: Número de la cuenta WhatsApp Business
        """
        try:
            account = self.accounts_repo.find_by_from_uid(display_phone_number)
            
            if not account or not account.appid or not account.gs_user:
                return {
                    "success": False,
                    "error": "Credenciales no encontradas",
                    "error_code": "MISSING_CREDENTIALS"
                }
            
            url = f"{self.base_url}/{account.appid}/v3/message"
            headers = {
                "Authorization": f"Bearer {account.gs_user}",
                "Content-Type": "application/json"
            }
            
            # Payload para media según tipo
            if media_type == "image":
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to,
                    "type": "image",
                    "image": {
                        "link": media_url,
                        "caption": caption
                    }
                }
            elif media_type == "document":
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": to,
                    "type": "document",
                    "document": {
                        "link": media_url,
                        "caption": caption
                    }
                }
            else:
                return {
                    "success": False,
                    "error": f"Tipo de media no soportado: {media_type}",
                    "error_code": "UNSUPPORTED_MEDIA_TYPE"
                }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    "success": True,
                    "message_id": response_data.get("id"),
                    "status": response_data.get("status"),
                    "gupshup_response": response_data
                }
            else:
                return {
                    "success": False,
                    "error": f"Error HTTP {response.status_code}",
                    "error_details": response.text,
                    "error_code": "HTTP_ERROR"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error enviando media: {str(e)}",
                "error_code": "UNEXPECTED_ERROR"
            }
    
    def send_template_message(self, to: str, template_name: str, 
                            template_params: list, display_phone_number: str) -> Dict[str, Any]:
        """
        Envía mensaje de plantilla (para notificaciones fuera del horario de 24h)
        
        Args:
            to: Número del destinatario
            template_name: Nombre de la plantilla aprobada
            template_params: Parámetros para la plantilla
            display_phone_number: Número de la cuenta WhatsApp Business
        """
        try:
            account = self.accounts_repo.find_by_from_uid(display_phone_number)
            
            if not account or not account.appid or not account.gs_user:
                return {
                    "success": False,
                    "error": "Credenciales no encontradas"
                }
            
            url = f"{self.base_url}/{account.appid}/v3/message"
            headers = {
                "Authorization": f"Bearer {account.gs_user}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": "es"  # Español
                    },
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                                {"type": "text", "text": param} for param in template_params
                            ]
                        }
                    ]
                }
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                return {
                    "success": True,
                    "message_id": response_data.get("id"),
                    "template_name": template_name,
                    "gupshup_response": response_data
                }
            else:
                return {
                    "success": False,
                    "error": f"Error enviando template: {response.status_code}",
                    "error_details": response.text
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Error con template: {str(e)}"
            }
    
    def send_template_message_v3(self, to: str, template_name: str, language_code: str,
                                template_components: list, display_phone_number: str) -> Dict[str, Any]:
        """
        Envía mensaje de template usando la API oficial de Gupshup V3.
        Basado en: https://partner-docs.gupshup.io/reference/post_partner-app-appid-v3-message-14
        
        Args:
            to: Número del destinatario (ej: '51987654321')
            template_name: Nombre de la plantilla aprobada
            language_code: Código de idioma (ej: 'es', 'en_US')
            template_components: Componentes del template (parámetros)
            display_phone_number: Número de la cuenta WhatsApp Business
        
        Returns:
            Dict con resultado del envío
        """
        try:
            # 1. Obtener credenciales y tokens (mismo flujo que send_text_message)
            account = self.accounts_repo.find_by_from_uid(display_phone_number)
            
            if not account or not account.appid or not account.gs_user or not account.gs_password:
                return {
                    "success": False,
                    "error": "Credenciales incompletas para template",
                    "error_code": "MISSING_CREDENTIALS"
                }
            
            # 2. Login y obtener tokens (reutilizando lógica existente)
            login_result = self.get_login_partner(account.gs_user, account.gs_password)
            if not login_result["success"]:
                return {
                    "success": False,
                    "error": f"Login fallido para template: {login_result['error']}",
                    "error_code": "LOGIN_FAILED"
                }
            
            login_token = login_result["login_response"].get("token")
            token_result = self.get_token_app(login_token, account.appid)
            if not token_result["success"]:
                return {
                    "success": False,
                    "error": f"Token app fallido para template: {token_result['error']}",
                    "error_code": "TOKEN_APP_FAILED"
                }
            
            app_token = token_result["token_response"]["token"]["token"]
            
            # 3. Construir URL y headers según documentación oficial
            url = f"https://partner.gupshup.io/partner/app/{account.appid}/v3/message"
            headers = {
                "accept": "application/json",
                "Authorization": app_token,
                "Content-Type": "application/json"
            }
            
            # 4. Payload según documentación oficial
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": language_code
                    },
                    "components": template_components
                }
            }
            
            print(f"📋 TEMPLATE: Enviando template '{template_name}' a {to}")
            print(f"📋 TEMPLATE: Payload: {payload}")
            
            # 5. Enviar request
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"✅ TEMPLATE: Enviado exitosamente - Response: {response_data}")
                
                return {
                    "success": True,
                    "message_id": response_data.get("messages", [{}])[0].get("id"),
                    "template_name": template_name,
                    "messaging_product": response_data.get("messaging_product"),
                    "contacts": response_data.get("contacts", []),
                    "gupshup_response": response_data
                }
            else:
                error_data = response.json() if 'application/json' in response.headers.get('content-type', '') else response.text
                print(f"❌ TEMPLATE: Error - Status: {response.status_code}, Response: {error_data}")
                
                return {
                    "success": False,
                    "error": f"Error enviando template: HTTP {response.status_code}",
                    "error_details": error_data,
                    "error_code": "HTTP_ERROR"
                }
                
        except Exception as e:
            print(f"❌ TEMPLATE: Excepción - {str(e)}")
            return {
                "success": False,
                "error": f"Error con template V3: {str(e)}",
                "error_code": "UNEXPECTED_ERROR"
            }
    
    def send_flow_message(self, to: str, flow_data: dict, display_phone_number: str) -> Dict[str, Any]:
        """
        Envía mensaje con Flow usando la API oficial de Gupshup V3.
        Basado en: https://partner-docs.gupshup.io/reference/post_partner-app-appid-v3-flow-message-6
        
        Args:
            to: Número del destinatario (ej: '51987654321')
            flow_data: Datos del flow (JSON parseado)
            display_phone_number: Número de la cuenta WhatsApp Business
        
        Returns:
            Dict con resultado del envío
        
        Ejemplo de flow_data:
        {
            "id": "1449142816146253",
            "token": "1449142816146253", 
            "text": "Validación de Cuenta de Cliente",
            "button": "Registrar",
            "description": "Registrar",
            "screen": "RECOMMEND"
        }
        """
        try:
            # 1. Obtener credenciales y tokens (mismo flujo que otras funciones)
            account = self.accounts_repo.find_by_from_uid(display_phone_number)
            
            if not account or not account.appid or not account.gs_user or not account.gs_password:
                return {
                    "success": False,
                    "error": "Credenciales incompletas para flow",
                    "error_code": "MISSING_CREDENTIALS"
                }
            
            # 2. Login y obtener tokens
            login_result = self.get_login_partner(account.gs_user, account.gs_password)
            if not login_result["success"]:
                return {
                    "success": False,
                    "error": f"Login fallido para flow: {login_result['error']}",
                    "error_code": "LOGIN_FAILED"
                }
            
            login_token = login_result["login_response"].get("token")
            token_result = self.get_token_app(login_token, account.appid)
            if not token_result["success"]:
                return {
                    "success": False,
                    "error": f"Token app fallido para flow: {token_result['error']}",
                    "error_code": "TOKEN_APP_FAILED"
                }
            
            app_token = token_result["token_response"]["token"]["token"]
            
            # 3. Construir URL y headers según documentación oficial
            url = f"https://partner.gupshup.io/partner/app/{account.appid}/v3/message"
            headers = {
                "Authorization": app_token,
                "Content-Type": "application/json"
            }
            
            # 4. Construir payload para Flow según documentación
            payload = {
                "recipient_type": "individual",
                "messaging_product": "whatsapp",
                "to": to,
                "type": "interactive",
                "interactive": {
                    "type": "flow",
                    "header": {
                        "type": "text",
                        "text": flow_data.get("text", "Flow Message")
                    },
                    "body": {
                        "text": flow_data.get("description", "Complete the form below")
                    },
                    "footer": {
                        "text": "Powered by Gupshup"
                    },
                    "action": {
                        "name": "flow",
                        "parameters": {
                            "flow_message_version": "3",
                            "flow_token": flow_data.get("token", ""),
                            "flow_id": flow_data.get("id", ""),
                            "flow_cta": flow_data.get("button", "Continue"),
                            "flow_action": "navigate",
                            "flow_action_payload": {
                                "screen": flow_data.get("screen", "MAIN"),
                                "data": {
                                    "flow_data": flow_data
                                }
                            }
                        }
                    }
                }
            }
            
            print(f"🌊 FLOW: Enviando flow ID '{flow_data.get('id')}' a {to}")
            print(f"🌊 FLOW: Payload: {payload}")
            
            # 5. Enviar request
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            
            if response.status_code == 200:
                response_data = response.json()
                print(f"✅ FLOW: Enviado exitosamente - Response: {response_data}")
                
                return {
                    "success": True,
                    "message_id": response_data.get("messages", [{}])[0].get("id"),
                    "flow_id": flow_data.get("id"),
                    "messaging_product": response_data.get("messaging_product"),
                    "contacts": response_data.get("contacts", []),
                    "gupshup_response": response_data
                }
            else:
                error_data = response.json() if 'application/json' in response.headers.get('content-type', '') else response.text
                print(f"❌ FLOW: Error - Status: {response.status_code}, Response: {error_data}")
                
                return {
                    "success": False,
                    "error": f"Error enviando flow: HTTP {response.status_code}",
                    "error_details": error_data,
                    "error_code": "HTTP_ERROR"
                }
                
        except Exception as e:
            print(f"❌ FLOW: Excepción - {str(e)}")
            return {
                "success": False,
                "error": f"Error con flow: {str(e)}",
                "error_code": "UNEXPECTED_ERROR"
            }
