# app/repositories/accounts_repository.py
from sqlalchemy.orm import Session
from app.models.accounts import TblAccounts
from typing import Optional

class AccountsRepository:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def find_by_from_uid(self, from_uid: str) -> Optional[TblAccounts]:
        """Busca cuenta por from_uid - equivale a findByFromUid en Java"""
        return self.db.query(TblAccounts).filter(
            TblAccounts.from_uid == from_uid
        ).first()
    
    def find_by_account_id(self, account_id: str) -> Optional[TblAccounts]:
        """Busca cuenta por account_id"""
        return self.db.query(TblAccounts).filter(
            TblAccounts.account_id == account_id
        ).first()
    
    def find_by_appid(self, appid: str) -> Optional[TblAccounts]:
        """Busca cuenta por appid"""
        return self.db.query(TblAccounts).filter(
            TblAccounts.appid == appid
        ).first()