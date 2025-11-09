# app/models/session_data.py
from sqlalchemy import Column, Text
from . import Base

class TblSessionData(Base):
    __tablename__ = 'tbl_session_data'
    
    id = Column(Text, primary_key=True)  # varchar(255)
    data = Column(Text, nullable=True)   # varchar(2000) - JSON serialized data
    
    def __repr__(self):
        return f"<TblSessionData(id='{self.id}', data_length={len(self.data) if self.data else 0})>"