# app/tools/productos_tools.py
from langchain.tools import tool
from typing import List
from app.repositories.products_repository import ProductsRepository
import json

# Variable global para el repository
_products_repo = None

def init_products_repo(products_repository: ProductsRepository):
    global _products_repo
    _products_repo = products_repository

@tool
def buscar_productos(termino: str, palabras_clave: str = None) -> str:
    """
    Busca productos en Coolbox. ChatGPT interpreta y puede agregar palabras clave.
    
    Args:
        termino: Lo que busca el usuario (ej: 'samsung', 'celular', 'audifonos')
        palabras_clave: Palabras adicionales para buscar en características (ej: 'gaming gpu rendimiento')
    
    Ejemplos:
    - Usuario: "celular gamer" → termino="celular", palabras_clave="gaming gpu rendimiento fps"
    - Usuario: "productos seguridad" → termino="seguridad", palabras_clave="vigilancia alarma camara sensor"
    """
    try:
        # Búsqueda inteligente con palabras clave adicionales
        products = _products_repo.buscar_con_palabras_clave(termino, palabras_clave)
        
        # Datos crudos para ChatGPT
        productos_data = []
        for product in products:
            productos_data.append({
                "nombre": product.nombre,
                "marca": product.marca,
                "precio": float(product.precio_con_impuesto) if product.precio_con_impuesto else 0,
                "stock": product.stock_web,
                "categoria": product.categoria,
                "modelo": product.modelo,
                "caracteristicas": product.caracteristicas  # Agregar características
            })
        
        return json.dumps(productos_data, ensure_ascii=False)
        
    except Exception as e:
        return f"Error: {str(e)}"

def create_producto_tools(products_repository: ProductsRepository) -> List:
    init_products_repo(products_repository)
    return [buscar_productos]
