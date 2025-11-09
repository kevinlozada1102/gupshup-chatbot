# app/services/prompt_service.py
from typing import Optional
from app.repositories.accounts_repository import AccountsRepository
from app.repositories.account_prompts_repository import AccountPromptsRepository

class PromptService:
    def __init__(self, accounts_repository: AccountsRepository, account_prompts_repository: AccountPromptsRepository):
        self.accounts_repo = accounts_repository
        self.prompts_repo = account_prompts_repository
    
    def get_prompt_by_from_uid(self, from_uid: str) -> Optional[str]:
        """
        Obtiene el prompt activo para un from_uid específico:
        1. Busca la cuenta por from_uid en tbl_accounts
        2. Con el account_id obtenido, busca el prompt activo en tbl_account_prompts
        3. Retorna el prompt_content o None si no se encuentra
        """
        try:
            # 1. Buscar cuenta por from_uid
            account = self.accounts_repo.find_by_from_uid(from_uid)
            if not account:
                print(f"❌ No se encontró cuenta para from_uid: {from_uid}")
                return None
            
            # 2. Buscar prompt activo por account_id
            prompt_record = self.prompts_repo.find_active_prompt_by_account_id(account.account_id)
            if not prompt_record:
                print(f"❌ No se encontró prompt activo para account_id: {account.account_id}")
                return None
            
            print(f"✅ Prompt encontrado para from_uid {from_uid} -> account_id {account.account_id}")
            return prompt_record.prompt_content
            
        except Exception as e:
            print(f"❌ Error obteniendo prompt para from_uid {from_uid}: {str(e)}")
            return None
    
    def get_prompt_by_account_id(self, account_id: str) -> Optional[str]:
        """
        Obtiene el prompt activo directamente por account_id
        """
        try:
            prompt_record = self.prompts_repo.find_active_prompt_by_account_id(account_id)
            if not prompt_record:
                print(f"❌ No se encontró prompt activo para account_id: {account_id}")
                return None
            
            return prompt_record.prompt_content
            
        except Exception as e:
            print(f"❌ Error obteniendo prompt para account_id {account_id}: {str(e)}")
            return None