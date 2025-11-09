# app/repositories/simple_answer_repository.py
from sqlalchemy.orm import Session
from app.models.simple_answer import TblSimpleAnswer
from typing import Optional, List

class SimpleAnswerRepository:
    def __init__(self, db_session: Session):
        self.db = db_session
    
    def find_by_handler_path(self, handler_path: str, account_id: str = None) -> Optional[TblSimpleAnswer]:
        """
        Busca respuesta por handler_path específico
        Si se proporciona account_id, filtra también por cuenta
        """
        query = self.db.query(TblSimpleAnswer).filter(
            TblSimpleAnswer.handler_path == handler_path
        )
        
        if account_id:
            query = query.filter(TblSimpleAnswer.account_id == account_id)
        
        return query.first()
    
    def find_by_handler_path_like(self, handler_path_pattern: str, account_id: str = None) -> List[TblSimpleAnswer]:
        """
        Busca respuestas que empiecen con un patrón específico
        Útil para encontrar opciones de un menú (ej: /menu/1, /menu/2, etc.)
        """
        query = self.db.query(TblSimpleAnswer).filter(
            TblSimpleAnswer.handler_path.like(f"{handler_path_pattern}%")
        )
        
        if account_id:
            query = query.filter(TblSimpleAnswer.account_id == account_id)
        
        return query.order_by(TblSimpleAnswer.handler_path).all()
    
    def find_children_paths(self, parent_path: str, account_id: str = None) -> List[TblSimpleAnswer]:
        """
        Encuentra rutas hijas directas de un path padre
        Ej: parent_path="/menu" encuentra "/menu/1", "/menu/2" pero no "/menu/1/a"
        """
        # Buscar rutas que empiecen con parent_path/ y no tengan más niveles
        pattern = f"{parent_path}/"
        
        query = self.db.query(TblSimpleAnswer).filter(
            TblSimpleAnswer.handler_path.like(f"{pattern}%")
        )
        
        if account_id:
            query = query.filter(TblSimpleAnswer.account_id == account_id)
        
        # Filtrar solo hijos directos (no nietos)
        results = []
        for result in query.all():
            # Quitar el prefijo del parent_path
            remaining = result.handler_path.replace(pattern, "", 1)
            # Si no hay más "/" significa que es hijo directo
            if "/" not in remaining:
                results.append(result)
        
        return sorted(results, key=lambda x: x.handler_path)
    
    def find_by_account_id(self, account_id: str) -> List[TblSimpleAnswer]:
        """Obtiene todas las respuestas de una cuenta específica"""
        return self.db.query(TblSimpleAnswer).filter(
            TblSimpleAnswer.account_id == account_id
        ).order_by(TblSimpleAnswer.handler_path).all()
    
    def create_simple_answer(
        self, 
        handler_path: str, 
        handler_path_to: str, 
        message: str,
        account_id: str = None,
        invalid_error: str = None,
        redirect_on_error: str = None,
        handler_path_to_description: str = None,
        description: str = None
    ) -> TblSimpleAnswer:
        """Crea una nueva respuesta simple"""
        new_answer = TblSimpleAnswer(
            handler_path=handler_path,
            handler_path_to=handler_path_to,
            message=message,
            account_id=account_id,
            invalid_error=invalid_error,
            redirect_on_error=redirect_on_error,
            handler_path_to_description=handler_path_to_description,
            description=description
        )
        
        self.db.add(new_answer)
        self.db.commit()
        self.db.refresh(new_answer)
        return new_answer
    
    def update_message(self, handler_path: str, new_message: str, account_id: str = None) -> bool:
        """Actualiza el mensaje de una ruta específica"""
        try:
            query = self.db.query(TblSimpleAnswer).filter(
                TblSimpleAnswer.handler_path == handler_path
            )
            
            if account_id:
                query = query.filter(TblSimpleAnswer.account_id == account_id)
            
            answer = query.first()
            if answer:
                answer.message = new_message
                self.db.commit()
                return True
            return False
        except Exception as e:
            print(f"❌ Error actualizando mensaje: {e}")
            return False
    
    def delete_by_handler_path(self, handler_path: str, account_id: str = None) -> bool:
        """Elimina una respuesta por handler_path"""
        try:
            query = self.db.query(TblSimpleAnswer).filter(
                TblSimpleAnswer.handler_path == handler_path
            )
            
            if account_id:
                query = query.filter(TblSimpleAnswer.account_id == account_id)
            
            answer = query.first()
            if answer:
                self.db.delete(answer)
                self.db.commit()
                return True
            return False
        except Exception as e:
            print(f"❌ Error eliminando respuesta: {e}")
            return False
    
    def get_menu_options(self, base_path: str, account_id: str = None) -> List[dict]:
        """
        Obtiene opciones de menú formateadas para mostrar al usuario
        Retorna lista de diccionarios con la información necesaria
        """
        children = self.find_children_paths(base_path, account_id)
        
        options = []
        for child in children:
            # Extraer la opción del path (último segmento)
            option = child.handler_path.split("/")[-1]
            options.append({
                "option": option,
                "path": child.handler_path,
                "path_to": child.handler_path_to,
                "message": child.message,
                "description": child.description
            })
        
        return options