# app/utils/gupshup_logger.py
import json
import logging
from datetime import datetime
from typing import Dict, Any

# Configurar logger para Gupshup
logger = logging.getLogger('gupshup_sender')
logger.setLevel(logging.INFO)

# Handler para archivo
file_handler = logging.FileHandler('gupshup_messages.log')
file_handler.setLevel(logging.INFO)

# Handler para consola
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)

# Formato
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

class GupshupLogger:
    @staticmethod
    def log_message_sent(to: str, message: str, result: Dict[str, Any], app_id: str = None):
        """Log de mensaje enviado exitosamente"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "action": "message_sent",
            "to": to,
            "message_length": len(message),
            "app_id": app_id,
            "gupshup_message_id": result.get("message_id"),
            "status": result.get("status"),
            "success": True
        }
        logger.info(f"MESSAGE_SENT: {json.dumps(log_data)}")
    
    @staticmethod
    def log_message_failed(to: str, message: str, error: str, error_code: str = None, app_id: str = None):
        """Log de mensaje que falló al enviar"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "action": "message_failed",
            "to": to,
            "message_length": len(message),
            "app_id": app_id,
            "error": error,
            "error_code": error_code,
            "success": False
        }
        logger.error(f"MESSAGE_FAILED: {json.dumps(log_data)}")
    
    @staticmethod
    def log_credentials_issue(display_phone_number: str, issue: str):
        """Log de problemas con credenciales"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "action": "credentials_issue",
            "display_phone_number": display_phone_number,
            "issue": issue
        }
        logger.warning(f"CREDENTIALS_ISSUE: {json.dumps(log_data)}")
    
    @staticmethod
    def log_api_response(url: str, status_code: int, response_data: Any, request_payload: Dict = None):
        """Log detallado de respuesta de API"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "action": "api_response",
            "url": url,
            "status_code": status_code,
            "response_data": response_data,
            "request_payload": request_payload
        }
        
        if status_code == 200:
            logger.info(f"API_SUCCESS: {json.dumps(log_data)}")
        else:
            logger.error(f"API_ERROR: {json.dumps(log_data)}")
    
    @staticmethod
    def log_webhook_processing(session_id: int, user_message: str, ai_response: str, sent_successfully: bool):
        """Log completo de procesamiento de webhook"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "action": "webhook_processing",
            "session_id": session_id,
            "user_message_length": len(user_message),
            "ai_response_length": len(ai_response),
            "sent_successfully": sent_successfully
        }
        logger.info(f"WEBHOOK_PROCESSING: {json.dumps(log_data)}")