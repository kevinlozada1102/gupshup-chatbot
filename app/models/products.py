# app/models/products.py
from sqlalchemy import Column, Integer, Text, Numeric, Boolean, DateTime
from . import Base

class TblProducts(Base):
    __tablename__ = 'tbl_products'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo_ecomm = Column(Integer, nullable=True)
    codigo_punto_venta = Column(Text, nullable=True)
    nombre = Column(Text, nullable=True)
    descripcion_larga = Column(Text, nullable=True)
    caracteristicas = Column(Text, nullable=True)
    marca = Column(Text, nullable=True)
    precio_regular = Column(Numeric(10, 2), nullable=True)
    precio_con_impuesto = Column(Numeric(10, 2), nullable=True)
    stock_web = Column(Integer, default=0)
    categoria = Column(Text, nullable=True)
    rubro = Column(Text, nullable=True)
    sub_familia = Column(Text, nullable=True)
    modelo = Column(Text, nullable=True)
    garantia = Column(Text, nullable=True)
    color = Column(Text, nullable=True)
    activo = Column(Boolean, default=True)
    empresa = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<TblProducts(id={self.id}, nombre='{self.nombre}', marca='{self.marca}', precio={self.precio_con_impuesto})>"