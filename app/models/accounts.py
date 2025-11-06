# app/models/accounts.py
from sqlalchemy import Column, Integer, Text
from . import Base

class TblAccounts(Base):
    __tablename__ = 'tbl_accounts'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Text, nullable=False)
    from_uid = Column(Text, nullable=True)
    gs_user = Column(Text, nullable=True)
    gs_password = Column(Text, nullable=True)
    appid = Column(Text, nullable=True)
    
    def __repr__(self):
        return f"<TblAccounts(id={self.id}, account_id='{self.account_id}', appid='{self.appid}')>"