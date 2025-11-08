"""
Utilidades para operaciones CRUD comunes.
"""

from typing import Callable, Dict, Any
from datetime import datetime
from functools import wraps

from sqlalchemy.orm import Session


def safe_upsert(
    session: Session,
    model_class,
    unique_fields: Dict[str, Any],
    data: Dict[str, Any],
    update_timestamp: bool = True
) -> Any:
    """
    Realiza un upsert (insert or update) seguro de un modelo.
    
    Args:
        session: Sesión de SQLAlchemy
        model_class: Clase del modelo (ej: Component, Hook, Project)
        unique_fields: Diccionario con campos únicos para buscar
                       (ej: {'name': 'Button', 'project_id': 'proj1'})
        data: Datos a insertar/actualizar
        update_timestamp: Si True, actualiza updated_at automáticamente
        
    Returns:
        Instancia del modelo (nueva o actualizada)
        
    Example:
        component = safe_upsert(
            session=session,
            model_class=Component,
            unique_fields={'name': 'Button', 'project_id': 'proj1', 'file_path': 'src/Button.js'},
            data={'props': ['onClick'], 'description': 'A button'}
        )
    """
    # Buscar registro existente
    query = session.query(model_class)
    for key, value in unique_fields.items():
        query = query.filter(getattr(model_class, key) == value)
    existing = query.first()
    
    if existing:
        # Actualizar registro existente
        for key, value in data.items():
            if hasattr(existing, key):
                setattr(existing, key, value)
        if update_timestamp and hasattr(existing, 'updated_at'):
            existing.updated_at = datetime.utcnow()
        return existing
    else:
        # Crear nuevo registro
        # Combinar unique_fields y data para crear el objeto completo
        # data puede sobrescribir unique_fields si hay overlap
        instance_data = {**unique_fields, **data}
        instance = model_class(**instance_data)
        session.add(instance)
        return instance


def update_field(
    session: Session,
    model_class,
    filter_fields: Dict[str, Any],
    field_name: str,
    field_value: Any,
    commit: bool = True
) -> bool:
    """
    Actualiza un campo específico de un modelo.
    
    Args:
        session: Sesión de SQLAlchemy
        model_class: Clase del modelo
        filter_fields: Campos para filtrar (ej: {'id': 'proj1'})
        field_name: Nombre del campo a actualizar
        field_value: Nuevo valor del campo
        commit: Si True, hace commit automáticamente
        
    Returns:
        True si se actualizó, False si no se encontró el registro
        
    Example:
        updated = update_field(
            session=session,
            model_class=Project,
            filter_fields={'id': 'proj1'},
            field_name='last_sync',
            field_value=datetime.utcnow()
        )
    """
    query = session.query(model_class)
    for key, value in filter_fields.items():
        query = query.filter(getattr(model_class, key) == value)
    instance = query.first()
    
    if instance and hasattr(instance, field_name):
        setattr(instance, field_name, field_value)
        if commit:
            session.commit()
        return True
    return False


def handle_db_error(operation_name: str):
    """
    Decorador para manejar errores de base de datos de forma consistente.
    
    Args:
        operation_name: Nombre de la operación para mensajes de error
        
    Returns:
        Decorador que maneja errores y rollback
        
    Example:
        @handle_db_error("saving components")
        def _save():
            session = self._get_session()
            # código que puede fallar
            session.commit()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            session = None
            # Intentar obtener session del primer argumento si es un método
            if args and hasattr(args[0], '_get_session'):
                session = args[0]._get_session()
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if session:
                    session.rollback()
                print(f"❌ Error {operation_name}: {e}")
                raise
        return wrapper
    return decorator

