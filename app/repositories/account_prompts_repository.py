# app/repositories/account_prompts_repository.py
from sqlalchemy.orm import Session
from app.models.account_prompts import TblAccountPrompts
from typing import Optional

class AccountPromptsRepository:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def find_active_prompt_by_account_id(self, account_id: str) -> Optional[TblAccountPrompts]:
        """Busca el prompt activo para una cuenta específica"""
        return self.db.query(TblAccountPrompts).filter(
            TblAccountPrompts.account_id == account_id,
            TblAccountPrompts.is_active == True
        ).first()
    
    def find_all_prompts_by_account_id(self, account_id: str) -> list[TblAccountPrompts]:
        """Obtiene todos los prompts de una cuenta"""
        return self.db.query(TblAccountPrompts).filter(
            TblAccountPrompts.account_id == account_id
        ).all()
    
    def create_prompt(self, account_id: str, prompt_content: str, is_active: bool = True) -> TblAccountPrompts:
        """Crea un nuevo prompt"""
        new_prompt = TblAccountPrompts(
            account_id=account_id,
            prompt_content=prompt_content,
            is_active=is_active
        )
        self.db.add(new_prompt)
        self.db.commit()
        self.db.refresh(new_prompt)
        return new_prompt
    
    def update_prompt_status(self, prompt_id: int, is_active: bool) -> Optional[TblAccountPrompts]:
        """Actualiza el estado de un prompt"""
        prompt = self.db.query(TblAccountPrompts).filter(
            TblAccountPrompts.id == prompt_id
        ).first()
        
        if prompt:
            prompt.is_active = is_active
            self.db.commit()
            self.db.refresh(prompt)
        
        return prompt
    
    def deactivate_all_prompts_for_account(self, account_id: str):
        """Desactiva todos los prompts de una cuenta"""
        self.db.query(TblAccountPrompts).filter(
            TblAccountPrompts.account_id == account_id
        ).update({TblAccountPrompts.is_active: False})
        self.db.commit()