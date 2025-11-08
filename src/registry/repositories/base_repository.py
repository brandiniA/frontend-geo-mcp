"""
Repositorio base con funcionalidad común para todos los repositorios.
"""

from typing import Optional
from sqlalchemy.orm import Session, sessionmaker


class BaseRepository:
    """Repositorio base con funcionalidad común."""
    
    def __init__(self, session_factory: sessionmaker):
        """
        Inicializa el repositorio base.
        
        Args:
            session_factory: Factory de sesiones SQLAlchemy
        """
        self.SessionLocal = session_factory
    
    def _get_session(self) -> Session:
        """Retorna una nueva sesión (sincrónico)."""
        return self.SessionLocal()

