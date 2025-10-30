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

from src.models import Base, Project, Component, ProjectResponse, ComponentResponse, Hook

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
        """
        Guarda componentes en la base de datos.
        Separa y valida hooks:
        - native_hooks_used: Se guarda tal cual (ej: ["useState", "useEffect"])
        - custom_hooks_used: Se valida contra tabla de hooks y se guardan solo nombres existentes
        
        Args:
            components: Lista de componentes a guardar
            project_id: ID del proyecto
            
        Returns:
            Número de componentes guardados
        """
        if not components:
            return 0

        def _save():
            session = self._get_session()
            try:
                saved_count = 0
                
                # Obtener todos los custom hooks del proyecto para validación
                indexed_hooks = set(
                    session.query(Hook.name)
                    .filter(Hook.project_id == project_id)
                    .all()
                )
                indexed_hooks = {h[0] for h in indexed_hooks}  # Convertir a set de nombres

                for comp_data in components:
                    # Obtener hooks con los nombres correctos
                    native_hooks = comp_data.get('native_hooks_used', [])
                    potential_custom_hooks = comp_data.get('custom_hooks_used', [])
                    
                    # Validar: solo incluir custom hooks que realmente están indexados
                    valid_custom_hooks = [
                        hook for hook in potential_custom_hooks 
                        if hook in indexed_hooks
                    ]
                    
                    component_dict = {
                        'name': comp_data['name'],
                        'project_id': project_id,
                        'file_path': comp_data['file_path'],
                        'props': comp_data.get('props', []),
                        'native_hooks_used': native_hooks,
                        'custom_hooks_used': valid_custom_hooks,
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

    async def search_by_hook(
        self, hook_name: str, project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca componentes que usan un hook específico (búsqueda en la BD).
        Más eficiente que traer todos los componentes y filtrar en memoria.
        
        Args:
            hook_name: Nombre del hook (ej: useState, useEffect)
            project_id: Filtrar por proyecto (opcional)
            
        Returns:
            Lista de componentes que usan el hook
        """
        def _search():
            session = self._get_session()
            try:
                from sqlalchemy import text, cast, String
                
                q = session.query(Component)
                
                # Convertir JSON a texto y buscar el hook
                # Funciona con PostgreSQL, SQLite y MySQL
                q = q.filter(cast(Component.hooks, String).contains(f'"{hook_name}"'))
                
                if project_id:
                    q = q.filter(Component.project_id == project_id)
                
                components = q.all()
                return [c.to_dict() for c in components]
            finally:
                session.close()

        return await asyncio.to_thread(_search)

    async def search_by_prop(
        self, prop_name: str, project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca componentes que usan una prop específica.
        
        Args:
            prop_name: Nombre de la prop
            project_id: Filtrar por proyecto (opcional)
            
        Returns:
            Lista de componentes que usan la prop
        """
        def _search():
            session = self._get_session()
            try:
                from sqlalchemy import cast, String
                
                q = session.query(Component)
                
                # Convertir JSON a texto y buscar la prop
                q = q.filter(cast(Component.props, String).contains(f'"{prop_name}"'))
                
                if project_id:
                    q = q.filter(Component.project_id == project_id)
                
                components = q.all()
                return [c.to_dict() for c in components]
            finally:
                session.close()

        return await asyncio.to_thread(_search)

    # ============================================
    # HOOK OPERATIONS
    # ============================================

    async def save_hooks(self, hooks: List[Dict[str, Any]], project_id: str) -> int:
        """
        Guarda custom hooks en la base de datos.
        
        Args:
            hooks: Lista de custom hooks a guardar
            project_id: ID del proyecto
            
        Returns:
            Número de hooks guardados
        """
        if not hooks:
            return 0

        def _save():
            session = self._get_session()
            try:
                saved_count = 0

                for hook_data in hooks:
                    hook_dict = {
                        'name': hook_data['name'],
                        'project_id': project_id,
                        'file_path': hook_data['file_path'],
                        'hook_type': hook_data.get('hook_type', 'custom'),
                        'description': hook_data.get('description'),
                        'return_type': hook_data.get('return_type'),
                        'parameters': hook_data.get('parameters', []),
                        'imports': hook_data.get('imports', []),
                        'exports': hook_data.get('exports', []),
                        'native_hooks_used': hook_data.get('native_hooks_used', []),
                        'custom_hooks_used': hook_data.get('custom_hooks_used', []),
                        'jsdoc': hook_data.get('jsdoc'),
                    }

                    existing = (
                        session.query(Hook)
                        .filter(
                            Hook.name == hook_dict['name'],
                            Hook.project_id == project_id,
                            Hook.file_path == hook_dict['file_path'],
                        )
                        .first()
                    )

                    if existing:
                        for key, value in hook_dict.items():
                            setattr(existing, key, value)
                        existing.updated_at = datetime.utcnow()
                    else:
                        hook = Hook(**hook_dict)
                        session.add(hook)

                    saved_count += 1

                session.commit()
                print(f"✅ Saved {saved_count} hooks to database")
                return saved_count

            except Exception as e:
                session.rollback()
                print(f"❌ Error saving hooks: {e}")
                raise
            finally:
                session.close()

        return await asyncio.to_thread(_save)

    async def search_hooks(
        self, query: str, project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca custom hooks por nombre.
        
        Args:
            query: Término de búsqueda
            project_id: Filtrar por proyecto (opcional)
            
        Returns:
            Lista de hooks que coinciden
        """
        def _search():
            session = self._get_session()
            try:
                q = session.query(Hook)

                if query:
                    q = q.filter(Hook.name.ilike(f"%{query}%"))

                if project_id:
                    q = q.filter(Hook.project_id == project_id)

                hooks = q.limit(20).all()
                return [h.to_dict() for h in hooks]
            finally:
                session.close()

        return await asyncio.to_thread(_search)

    async def get_hooks_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los custom hooks de un proyecto.
        
        Args:
            project_id: ID del proyecto
            
        Returns:
            Lista de hooks del proyecto
        """
        def _get():
            session = self._get_session()
            try:
                hooks = session.query(Hook).filter(Hook.project_id == project_id).all()
                return [h.to_dict() for h in hooks]
            finally:
                session.close()

        return await asyncio.to_thread(_get)

    async def get_hook_by_name(
        self, hook_name: str, project_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene un custom hook por nombre y proyecto.
        
        Args:
            hook_name: Nombre del hook
            project_id: ID del proyecto
            
        Returns:
            Diccionario con información del hook o None
        """
        def _get():
            session = self._get_session()
            try:
                hook = session.query(Hook).filter(
                    Hook.name == hook_name,
                    Hook.project_id == project_id
                ).first()
                return hook.to_dict() if hook else None
            finally:
                session.close()

        return await asyncio.to_thread(_get)

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
