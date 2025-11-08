"""
Utilidades para serialización y conversión de modelos a diccionarios.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime


def to_dict_list(objects: List[Any]) -> List[Dict[str, Any]]:
    """
    Convierte una lista de objetos SQLAlchemy a lista de diccionarios.
    
    Args:
        objects: Lista de objetos con método to_dict()
        
    Returns:
        Lista de diccionarios
        
    Example:
        components = session.query(Component).all()
        components_dict = to_dict_list(components)
    """
    return [obj.to_dict() for obj in objects]


def model_to_dict(obj: Any) -> Optional[Dict[str, Any]]:
    """
    Convierte un objeto SQLAlchemy a diccionario con manejo de None.
    
    Args:
        obj: Objeto con método to_dict() o None
        
    Returns:
        Diccionario o None si el objeto es None
        
    Example:
        project = session.query(Project).first()
        project_dict = model_to_dict(project)  # None si no existe
    """
    if obj is None:
        return None
    if hasattr(obj, 'to_dict'):
        return obj.to_dict()
    # Fallback: crear diccionario manualmente si es posible
    if hasattr(obj, '__dict__'):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
    return None


def make_serializable(data: Any) -> Any:
    """
    Convierte valores no serializables (como datetime) a tipos básicos.
    Funciona recursivamente con dicts y listas.
    
    Args:
        data: Valor a serializar (dict, list, datetime, etc.)
        
    Returns:
        Valor serializable (datetime -> ISO string, etc.)
        
    Example:
        data = {'created_at': datetime.now(), 'name': 'Component'}
        serialized = make_serializable(data)
        # {'created_at': '2025-11-08T15:30:00', 'name': 'Component'}
    """
    if isinstance(data, datetime):
        return data.isoformat()
    elif isinstance(data, dict):
        return {key: make_serializable(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [make_serializable(item) for item in data]
    elif isinstance(data, (str, int, float, bool, type(None))):
        return data
    else:
        return str(data)

