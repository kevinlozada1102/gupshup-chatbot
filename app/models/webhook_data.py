# app/models/webhook_data.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class WebhookData:
    """
    Clase para optimizar el manejo de datos del payload de Gupshup
    Evita pasar múltiples parámetros entre funciones
    """
    # Datos principales del mensaje
    from_uid: Optional[str] = None
    message_id: Optional[str] = None
    message_type: Optional[str] = None
    message_body: Optional[str] = None
    display_phone_number: Optional[str] = None
    app_id: Optional[str] = None
    
    # Flags de control
    is_user_message: bool = False
    is_status_update: bool = False
    
    # Payload original
    raw_payload: Optional[dict] = None
    
    def is_text_message(self) -> bool:
        """Verifica si es un mensaje de texto o interactivo del usuario"""
        return self.is_user_message and self.message_type in ["text", "interactive"]
    
    def has_required_fields(self) -> bool:
        """Verifica si tiene los campos mínimos requeridos"""
        return all([
            self.from_uid,
            self.message_id,
            self.message_type
        ])
    
    def get_session_key(self) -> str:
        """Genera clave para buscar/crear sesión"""
        return f"{self.from_uid}_{self.display_phone_number}"