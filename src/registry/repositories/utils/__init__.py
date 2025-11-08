"""
Utilidades para repositorios.
Exporta todas las utilidades organizadas por propósito.
"""

from .db_session import db_session, async_db_operation
from .serialization import to_dict_list, model_to_dict, make_serializable
from .crud import safe_upsert, update_field, handle_db_error

__all__ = [
    # Sesiones
    'db_session',
    'async_db_operation',
    # Serialización
    'to_dict_list',
    'model_to_dict',
    'make_serializable',
    # CRUD
    'safe_upsert',
    'update_field',
    'handle_db_error',
]

