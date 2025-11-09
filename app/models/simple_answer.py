# app/models/simple_answer.py
from sqlalchemy import Column, Integer, Text
from . import Base

class TblSimpleAnswer(Base):
    __tablename__ = 'tbl_simple_answer'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    message = Column(Text, nullable=False)                               # text - Mensaje a mostrar
    handler_path = Column(Text, nullable=False)                         # varchar(255) - Ruta actual del handler
    handler_path_to = Column(Text, nullable=False)                      # varchar(255) - Ruta destino del handler
    account_id = Column(Text, nullable=True)                            # varchar(35) - ID de cuenta para multitenancy
    invalid_error = Column(Text, nullable=True)                         # varchar(800) - Mensaje de error personalizado
    redirect_on_error = Column(Text, nullable=True)                     # varchar(255) - Ruta de redirección en error
    handler_path_to_description = Column(Text, nullable=True)           # text - Descripción del destino
    description = Column(Text, nullable=True)                           # varchar(400) - Descripción general
    
    def __repr__(self):
        return f"<TblSimpleAnswer(id={self.id}, handler_path='{self.handler_path}', handler_path_to='{self.handler_path_to}')>"