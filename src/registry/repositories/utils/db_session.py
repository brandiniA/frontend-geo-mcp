"""
Utilidades para manejo de sesiones de base de datos.
"""

import asyncio
from typing import Callable, TypeVar
from contextlib import contextmanager
from functools import wraps

from sqlalchemy.orm import Session, sessionmaker

T = TypeVar('T')


@contextmanager
def db_session(session_factory: sessionmaker):
    """
    Context manager para manejar sesiones de base de datos.
    Asegura que la sesión se cierre correctamente.
    
    Usage:
        with db_session(self.SessionLocal) as session:
            result = session.query(Model).all()
            session.commit()
    """
    session = session_factory()
    try:
        yield session
    finally:
        session.close()


def async_db_operation(func: Callable[[], T]) -> Callable[[], T]:
    """
    Decorador para convertir operaciones de base de datos síncronas a async.
    
    Usage:
        @async_db_operation
        def _search():
            session = self._get_session()
            # ... código sincrónico
            return result
        
        result = await _search()
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper

