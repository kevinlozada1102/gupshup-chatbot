# app/webhook.py
from flask import Flask, request, jsonify
from typing import Dict, Any
from config.database import get_db_session
from app.repositories.gupshup_repository import GupshupRepository
from app.repositories.accounts_repository import AccountsRepository
from app.repositories.chat_session_repository import ChatSessionRepository
from app.repositories.message_repository import MessageRepository
from app.repositories.products_repository import ProductsRepository
from app.services.gupshup_service import GupshupService

app = Flask(__name__)

@app.route('/webhook/gupshup', methods=['POST'])
def gupshup_webhook():
    """
    Endpoint POST para recibir webhooks de Gupshup
    Equivale a @RequestBody Map<String, Object> payload en Java
    """
    try:
        # Obtener payload JSON del request (equivale a @RequestBody en Java)
        payload: Dict[str, Any] = request.get_json()
        
        if not payload:
            return jsonify({"error": "No payload received"}), 400
        
        # Obtener sesión de BD
        db_session = get_db_session()
        
        # Inicializar repositories
        gupshup_repo = GupshupRepository(db_session)
        accounts_repo = AccountsRepository(db_session)
        session_repo = ChatSessionRepository(db_session)
        message_repo = MessageRepository(db_session)
        products_repo = ProductsRepository(db_session)
        
        # Inicializar service con todos los repositories
        gupshup_service = GupshupService(
            gupshup_repo, accounts_repo, session_repo, message_repo, products_repo
        )
        
        # Procesar webhook y guardar en gupshup_log
        result = gupshup_service.process_webhook(payload)
        
        # Cerrar sesión
        db_session.close()
        
        if result["success"]:
            # Respuesta base
            response_data = {
                "status": "success",
                "message": "Webhook processed successfully",
                "log_id": result["log_id"],
                "is_user_message": result["is_user_message"]
            }
            
            # Si es mensaje de usuario procesado
            if result["is_user_message"] and "send_result" in result:
                response_data.update({
                    "ai_processing": {
                        "success": result.get("ai_response", {}).get("success", False),
                        "type": result.get("ai_response", {}).get("type"),
                        "tools_used": result.get("ai_response", {}).get("tools_used", [])
                    },
                    "message_sending": {
                        "sent_to_user": result.get("sent_to_user", False),
                        "gupshup_message_id": result.get("send_result", {}).get("message_id"),
                        "error": result.get("send_result", {}).get("error") if not result.get("sent_to_user") else None
                    },
                    "session_data": {
                        "session_id": result.get("session_id"),
                        "account_id": result.get("account_id")
                    }
                })
            
            return jsonify(response_data), 200
        else:
            return jsonify({
                "status": "error",
                "message": "Error processing webhook",
                "error": result["error"],
                "log_id": result["log_id"]
            }), 500
            
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "gupshup-webhook"}), 200

@app.route('/status', methods=['GET'])
def status_check():
    """Simple status endpoint for testing"""
    return "activo", 200

if __name__ == '__main__':
    app.run(debug=True)