# app/repositories/products_repository.py
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from app.models.products import TblProducts
from typing import List, Optional

class ProductsRepository:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def consultar_productos(self, nombre: str = None, marca: str = None, 
                          tipo: str = 'info', rango_min: float = None, 
                          rango_max: float = None, orden_precio: str = None, limit: int = 10) -> List[TblProducts]:
        """
        Consulta dinámica de productos - equivale a tu función ConsultarProductos
        
        Args:
            nombre: Nombre del producto o categoría
            marca: Marca específica
            tipo: 'stock', 'precio' o 'info'
            rango_min: Precio mínimo
            rango_max: Precio máximo
            orden_precio: 'mas_caros' o 'mas_baratos' para ordenamiento
            limit: Límite de resultados
        """
        print(f"🔍 REPO: Consultando productos - nombre: {nombre}, tipo: {tipo}")
        try:
            query = self.db.query(TblProducts).filter(TblProducts.activo == True)
            print(f"📊 REPO: Query inicial creada")
            
            # Filtro por nombre/categoría mejorado
            if nombre:
                nombre_clean = nombre.lower().strip()
                
                # Mapeo de términos comunes a categorías específicas
                categoria_mapping = {
                    'celular': 'celulares y accesorios',
                    'celulares': 'celulares y accesorios', 
                    'telefono': 'celulares y accesorios',
                    'smartphone': 'celulares y accesorios',
                    'tv': 'tv y video',
                    'television': 'tv y video',
                    'televisor': 'tv y video',
                    'audio': 'audio',
                    'audifonos': 'audio',
                    'parlante': 'audio'
                }
                
                # Si hay mapeo directo a categoría, usar esa búsqueda más específica
                if nombre_clean in categoria_mapping:
                    categoria_especifica = categoria_mapping[nombre_clean]
                    print(f"📍 REPO: Mapeando '{nombre_clean}' a categoría '{categoria_especifica}'")
                    query = query.filter(
                        or_(
                            func.lower(TblProducts.categoria).contains(categoria_especifica),
                            func.lower(TblProducts.rubro).contains(categoria_especifica)
                        )
                    )
                else:
                    # Búsqueda general en todos los campos
                    query = query.filter(
                        or_(
                            func.lower(TblProducts.nombre).contains(nombre_clean),
                            func.lower(TblProducts.categoria).contains(nombre_clean),
                            func.lower(TblProducts.sub_familia).contains(nombre_clean),
                            func.lower(TblProducts.modelo).contains(nombre_clean),
                            func.lower(TblProducts.rubro).contains(nombre_clean)
                        )
                    )
            
            # Filtro por marca
            if marca:
                marca_clean = marca.lower().strip()
                query = query.filter(func.lower(TblProducts.marca).contains(marca_clean))
            
            # Filtros por rango de precio
            if rango_min is not None:
                query = query.filter(TblProducts.precio_con_impuesto >= rango_min)
            
            if rango_max is not None:
                query = query.filter(TblProducts.precio_con_impuesto <= rango_max)
            
            # Filtro específico por tipo
            if tipo == 'stock':
                # Solo productos con stock disponible
                query = query.filter(TblProducts.stock_web > 0)
            
            # Ordenamiento por precio si se especifica
            if orden_precio == 'mas_caros':
                query = query.order_by(TblProducts.precio_con_impuesto.desc())
            elif orden_precio == 'mas_baratos' or tipo == 'precio':
                query = query.order_by(TblProducts.precio_con_impuesto.asc())
            else:
                # Ordenamiento por defecto
                query = query.order_by(TblProducts.nombre.asc())
            
            # Debug: Mostrar la query SQL que se va a ejecutar
            print(f"🔍 REPO: SQL Query a ejecutar:")
            print(f"📋 REPO: {str(query.statement.compile(compile_kwargs={'literal_binds': True}))}")
            
            # Aplicar limit
            results = query.limit(limit).all()
            print(f"✅ REPO: Query ejecutada - {len(results)} productos encontrados")
            
            # Debug: Mostrar los primeros resultados para verificar
            if results:
                print(f"📊 REPO: Primeros resultados:")
                for i, product in enumerate(results[:3]):
                    print(f"   {i+1}. {product.nombre} - {product.marca} - S/{product.precio_con_impuesto} - {product.categoria}")
            
            return results
        except Exception as e:
            print(f"❌ REPO ERROR: {str(e)}")
            raise e
    
    def format_products_response(self, products: List[TblProducts], tipo: str = 'info') -> str:
        """Formatea la respuesta de productos para ChatGPT"""
        if not products:
            return "No se encontraron productos que coincidan con tu búsqueda 😔"
        
        response_parts = []
        
        if tipo == 'stock':
            response_parts.append(f"📦 **Stock disponible** ({len(products)} productos):\\n")
            for product in products:
                stock_status = f"✅ {product.stock_web} unidades" if product.stock_web > 0 else "❌ Sin stock"
                response_parts.append(f"• **{product.nombre}** - {product.marca} - {stock_status}")
                
        elif tipo == 'precio':
            response_parts.append(f"💰 **Precios encontrados** ({len(products)} productos):\\n")
            for product in products:
                precio = f"S/. {product.precio_con_impuesto}" if product.precio_con_impuesto else "Precio no disponible"
                response_parts.append(f"• **{product.nombre}** - {product.marca} - {precio}")
                
        else:  # tipo == 'info'
            response_parts.append(f"ℹ️ **Información de productos** ({len(products)} encontrados):\\n")
            for product in products[:5]:  # Limitar a 5 para info
                precio = f"S/. {product.precio_con_impuesto}" if product.precio_con_impuesto else "Consultar precio"
                stock = f"Stock: {product.stock_web}" if product.stock_web > 0 else "Sin stock"
                
                response_parts.append(f"**{product.nombre}**")
                response_parts.append(f"🏷️ Marca: {product.marca}")
                response_parts.append(f"💵 Precio: {precio}")
                response_parts.append(f"📦 {stock}")
                if product.descripcion_larga:
                    desc = product.descripcion_larga[:100] + "..." if len(product.descripcion_larga) > 100 else product.descripcion_larga
                    response_parts.append(f"📝 {desc}")
                response_parts.append("---")
        
        return "\\n".join(response_parts)
    
    def buscar_simple(self, termino: str) -> List[TblProducts]:
        """Búsqueda simple. ChatGPT interpreta el resto."""
        query = self.db.query(TblProducts).filter(TblProducts.activo == True)
        
        if termino:
            termino_clean = termino.lower().strip()
            query = query.filter(
                or_(
                    func.lower(TblProducts.nombre).contains(termino_clean),
                    func.lower(TblProducts.marca).contains(termino_clean),
                    func.lower(TblProducts.categoria).contains(termino_clean),
                    func.lower(TblProducts.modelo).contains(termino_clean),
                    func.lower(TblProducts.caracteristicas).contains(termino_clean)  # 🆕 Búsqueda en características
                )
            )
        
        # Ordenar por precio DESC (mejores primero) - SOLO 5 productos
        return query.order_by(TblProducts.precio_con_impuesto.desc()).limit(5).all()
    
    def buscar_con_palabras_clave(self, termino: str, palabras_clave: str = None) -> List[TblProducts]:
        """Búsqueda con palabras clave adicionales para características"""
        query = self.db.query(TblProducts).filter(TblProducts.activo == True)
        
        condiciones = []
        
        # Búsqueda principal por término
        if termino:
            termino_clean = termino.lower().strip()
            condiciones.extend([
                func.lower(TblProducts.nombre).contains(termino_clean),
                func.lower(TblProducts.marca).contains(termino_clean),
                func.lower(TblProducts.categoria).contains(termino_clean),
                func.lower(TblProducts.modelo).contains(termino_clean),
                func.lower(TblProducts.caracteristicas).contains(termino_clean)
            ])
        
        # Búsqueda adicional en características con palabras clave
        if palabras_clave:
            palabras = [p.strip().lower() for p in palabras_clave.split() if p.strip()]
            for palabra in palabras:
                condiciones.append(func.lower(TblProducts.caracteristicas).contains(palabra))
        
        if condiciones:
            query = query.filter(or_(*condiciones))
        
        return query.order_by(TblProducts.precio_con_impuesto.desc()).limit(5).all()
    
    def get_product_by_id(self, product_id: int) -> Optional[TblProducts]:
        """Obtiene un producto específico por ID"""
        return self.db.query(TblProducts).filter(TblProducts.id == product_id).first()
