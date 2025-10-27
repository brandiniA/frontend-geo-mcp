"""
Cliente de base de datos con SQLAlchemy ORM.
Versión con métodos async para compatibilidad con FastMCP.
"""

import os
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from functools import wraps

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from dotenv import load_dotenv

from src.models import Base, Project, Component, ProjectResponse, ComponentResponse

load_dotenv()


def async_wrapper(func):
    """Decorador para hacer funciones síncronas compatible con async."""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)
    return wrapper


class DatabaseClient:
    """Cliente de base de datos con SQLAlchemy ORM - async compatible."""

    def __init__(self):
        """Inicializa la conexión a la base de datos."""
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")

        # Crear engine (sincrónico)
        self.engine = create_engine(
            self.database_url,
            echo=False,
            pool_pre_ping=True,
        )

        # Crear tablas si no existen
        Base.metadata.create_all(self.engine)

        # Session factory
        self.SessionLocal = sessionmaker(bind=self.engine, expire_on_commit=False)

        print("✅ Connected to database with SQLAlchemy")

    def _get_session(self) -> Session:
        """Retorna una nueva sesión (sincrónico)."""
        return self.SessionLocal()

    # ============================================
    # PROJECT OPERATIONS
    # ============================================

    async def upsert_project(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea o actualiza un proyecto."""
        def _upsert():
            session = self._get_session()
            try:
                project = session.query(Project).filter(Project.id == project_id).first()

                if project:
                    for key, value in data.items():
                        if hasattr(project, key):
                            setattr(project, key, value)
                else:
                    project = Project(id=project_id, **data)
                    session.add(project)

                session.commit()
                return project.to_dict()
            finally:
                session.close()

        return await asyncio.to_thread(_upsert)

    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un proyecto por ID."""
        def _get():
            session = self._get_session()
            try:
                project = session.query(Project).filter(Project.id == project_id).first()
                return project.to_dict() if project else None
            finally:
                session.close()

        return await asyncio.to_thread(_get)

    async def list_projects(self) -> List[Dict[str, Any]]:
        """Lista todos los proyectos."""
        def _list():
            session = self._get_session()
            try:
                projects = session.query(Project).all()
                return [p.to_dict() for p in projects]
            finally:
                session.close()

        return await asyncio.to_thread(_list)

    async def update_project_sync(self, project_id: str):
        """Actualiza la fecha de último sync."""
        def _update():
            session = self._get_session()
            try:
                project = session.query(Project).filter(Project.id == project_id).first()
                if project:
                    project.last_sync = datetime.utcnow()
                    session.commit()
            finally:
                session.close()

        return await asyncio.to_thread(_update)

    # ============================================
    # COMPONENT OPERATIONS
    # ============================================

    async def save_components(self, components: List[Dict[str, Any]], project_id: str) -> int:
        """Guarda componentes en la base de datos."""
        if not components:
            return 0

        def _save():
            session = self._get_session()
            try:
                saved_count = 0

                for comp_data in components:
                    component_dict = {
                        'name': comp_data['name'],
                        'project_id': project_id,
                        'file_path': comp_data['file_path'],
                        'props': comp_data.get('props', []),
                        'hooks': comp_data.get('hooks', []),
                        'imports': comp_data.get('imports', []),
                        'exports': comp_data.get('exports', []),
                        'component_type': comp_data.get('component_type', 'component'),
                        'description': comp_data.get('description'),
                        'jsdoc': comp_data.get('jsdoc'),
                    }

                    existing = (
                        session.query(Component)
                        .filter(
                            Component.name == component_dict['name'],
                            Component.project_id == project_id,
                            Component.file_path == component_dict['file_path'],
                        )
                        .first()
                    )

                    if existing:
                        for key, value in component_dict.items():
                            setattr(existing, key, value)
                        existing.updated_at = datetime.utcnow()
                    else:
                        component = Component(**component_dict)
                        session.add(component)

                    saved_count += 1

                session.commit()
                print(f"✅ Saved {saved_count} components to database")
                return saved_count

            except Exception as e:
                session.rollback()
                print(f"❌ Error saving components: {e}")
                raise
            finally:
                session.close()

        return await asyncio.to_thread(_save)

    async def search_components(
        self, query: str, project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Busca componentes por nombre."""
        def _search():
            session = self._get_session()
            try:
                q = session.query(Component)

                if query:
                    q = q.filter(Component.name.ilike(f"%{query}%"))

                if project_id:
                    q = q.filter(Component.project_id == project_id)

                components = q.limit(20).all()
                return [c.to_dict() for c in components]
            finally:
                session.close()

        return await asyncio.to_thread(_search)

    async def get_all_components(self) -> List[Dict[str, Any]]:
        """Obtiene todos los componentes indexados."""
        def _get_all():
            session = self._get_session()
            try:
                components = session.query(Component).all()
                return [c.to_dict() for c in components]
            finally:
                session.close()

        return await asyncio.to_thread(_get_all)

    async def get_components_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Obtiene todos los componentes de un proyecto."""
        def _get():
            session = self._get_session()
            try:
                components = session.query(Component).filter(Component.project_id == project_id).all()
                return [c.to_dict() for c in components]
            finally:
                session.close()

        return await asyncio.to_thread(_get)

    async def get_component_count(self, project_id: Optional[str] = None) -> int:
        """Obtiene el conteo de componentes."""
        def _count():
            session = self._get_session()
            try:
                q = session.query(Component)
                if project_id:
                    q = q.filter(Component.project_id == project_id)
                return q.count()
            finally:
                session.close()

        return await asyncio.to_thread(_count)

    # ============================================
    # CONTEXT MANAGER
    # ============================================

    def close(self):
        """Cierra la conexión."""
        self.engine.dispose()
        print("✅ Database connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
