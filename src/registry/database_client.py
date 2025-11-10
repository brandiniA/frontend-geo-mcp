"""
Cliente de base de datos con SQLAlchemy ORM.
Versión refactorizada usando repositorios para mejor organización.
"""

import os
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from src.models import Base
from .repositories import (
    ProjectRepository,
    ComponentRepository,
    HookRepository,
    DependencyRepository,
    FeatureFlagRepository,
)

load_dotenv()


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

        # Inicializar repositorios
        self.projects = ProjectRepository(self.SessionLocal)
        self.components = ComponentRepository(self.SessionLocal)
        self.hooks = HookRepository(self.SessionLocal)
        self.dependencies = DependencyRepository(self.SessionLocal)
        self.feature_flags = FeatureFlagRepository(self.SessionLocal)

        print("✅ Connected to database with SQLAlchemy")

    def _get_session(self):
        """Retorna una nueva sesión (sincrónico)."""
        return self.SessionLocal()

    # ============================================
    # PROJECT OPERATIONS (delegadas a ProjectRepository)
    # ============================================

    async def upsert_project(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea o actualiza un proyecto."""
        return await self.projects.upsert(project_id, data)

    async def get_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un proyecto por ID."""
        return await self.projects.get(project_id)

    async def list_projects(self) -> List[Dict[str, Any]]:
        """Lista todos los proyectos."""
        return await self.projects.list_all()

    async def update_project_sync(self, project_id: str):
        """Actualiza la fecha de último sync."""
        return await self.projects.update_sync(project_id)

    # ============================================
    # COMPONENT OPERATIONS (delegadas a ComponentRepository)
    # ============================================

    async def save_components(self, components: List[Dict[str, Any]], project_id: str) -> int:
        """Guarda componentes en la base de datos."""
        return await self.components.save(components, project_id)

    async def search_components(
        self, query: str, project_id: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Busca componentes por nombre, descripción y ruta."""
        return await self.components.search(query, project_id, limit)

    async def get_all_components(self) -> List[Dict[str, Any]]:
        """Obtiene todos los componentes indexados."""
        return await self.components.get_all()

    async def get_components_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Obtiene todos los componentes de un proyecto."""
        return await self.components.get_by_project(project_id)

    async def list_components_in_path(
        self, path: str, project_id: str
    ) -> List[Dict[str, Any]]:
        """Lista todos los componentes en una ruta específica."""
        return await self.components.list_in_path(path, project_id)

    async def search_components_semantic(
        self,
        query: Optional[str] = None,
        project_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Búsqueda semántica en múltiples campos con filtros avanzados."""
        return await self.components.search_semantic(query, project_id, filters)

    async def get_component_count(self, project_id: Optional[str] = None) -> int:
        """Obtiene el conteo de componentes."""
        return await self.components.count(project_id)

    async def get_component_index_stats(
        self, 
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Obtiene estadísticas detalladas del índice de componentes."""
        return await self.components.get_index_stats(project_id)

    async def search_by_hook(
        self, hook_name: str, project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Busca componentes que usan un hook específico."""
        return await self.components.search_by_hook(hook_name, project_id)
    
    async def update_component_container_file_path(
        self, component_name: str, project_id: str, container_file_path: str
    ) -> bool:
        """Actualiza el container_file_path de un componente."""
        return await self.components.update_container_file_path(
            component_name, project_id, container_file_path
        )

    async def search_by_prop(
        self, prop_name: str, project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Busca componentes que usan una prop específica."""
        return await self.components.search_by_prop(prop_name, project_id)

    # ============================================
    # HOOK OPERATIONS (delegadas a HookRepository)
    # ============================================

    async def save_hooks(self, hooks: List[Dict[str, Any]], project_id: str) -> int:
        """Guarda custom hooks en la base de datos."""
        return await self.hooks.save(hooks, project_id)

    async def search_hooks(
        self, query: str, project_id: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Busca custom hooks por nombre."""
        return await self.hooks.search(query, project_id, limit)

    async def get_hooks_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Obtiene todos los custom hooks de un proyecto."""
        return await self.hooks.get_by_project(project_id)

    async def get_hook_by_name(
        self, hook_name: str, project_id: str
    ) -> Optional[Dict[str, Any]]:
        """Obtiene un custom hook por nombre y proyecto."""
        return await self.hooks.get_by_name(hook_name, project_id)

    # ============================================
    # FEATURE FLAG OPERATIONS (delegadas a FeatureFlagRepository)
    # ============================================

    async def save_feature_flags(self, flags: List[Dict[str, Any]], project_id: str) -> int:
        """Guarda feature flags en la base de datos."""
        return await self.feature_flags.save(flags, project_id)

    async def get_feature_flags_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Obtiene todos los feature flags de un proyecto."""
        return await self.feature_flags.get_by_project(project_id)

    async def get_feature_flag_by_name(
        self, flag_name: str, project_id: str
    ) -> Optional[Dict[str, Any]]:
        """Obtiene un feature flag por nombre y proyecto."""
        return await self.feature_flags.get_by_name(flag_name, project_id)

    async def search_feature_flags(
        self, query: str, project_id: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Busca feature flags por nombre."""
        return await self.feature_flags.search(query, project_id, limit)

    async def get_components_using_flag(
        self, flag_name: str, project_id: str
    ) -> List[Dict[str, Any]]:
        """Obtiene todos los componentes que usan un flag específico."""
        return await self.feature_flags.get_components_using_flag(flag_name, project_id)

    async def get_unused_feature_flags(self, project_id: str) -> List[Dict[str, Any]]:
        """Obtiene flags definidos que NO se usan en ningún componente."""
        return await self.feature_flags.get_unused_flags(project_id)

    async def save_component_feature_flag_usage(
        self,
        component_id: int,
        feature_flag_id: int,
        usage_pattern: Optional[str] = None,
        usage_location: str = 'component',
        usage_context: Optional[str] = None,
        container_file_path: Optional[str] = None,
        usage_type: Optional[str] = None,
        combined_with: Optional[List[str]] = None,
        logic: Optional[str] = None
    ) -> None:
        """Guarda la relación entre un componente y un feature flag."""
        return await self.feature_flags.save_component_flag_usage(
            component_id, feature_flag_id, usage_pattern,
            usage_location, usage_context, container_file_path,
            usage_type, combined_with, logic
        )

    async def get_flags_for_component(
        self, component_id: int, project_id: str
    ) -> List[Dict[str, Any]]:
        """Obtiene todos los feature flags que usa un componente específico."""
        return await self.feature_flags.get_flags_for_component(component_id, project_id)
    
    async def get_flags_for_component_by_location(
        self, component_id: int, project_id: str, usage_location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Obtiene feature flags usados por un componente, filtrados por ubicación."""
        return await self.feature_flags.get_flags_for_component_by_location(
            component_id, project_id, usage_location
        )

    async def get_flags_for_hook(
        self, hook_id: int, project_id: str
    ) -> List[Dict[str, Any]]:
        """Obtiene todos los feature flags que usa un hook específico."""
        return await self.feature_flags.get_flags_for_hook(hook_id, project_id)

    async def save_hook_feature_flag_usage(
        self,
        hook_id: int,
        feature_flag_id: int,
        usage_pattern: Optional[str] = None
    ) -> None:
        """Guarda la relación entre un hook y un feature flag."""
        return await self.feature_flags.save_hook_flag_usage(
            hook_id, feature_flag_id, usage_pattern
        )

    async def get_hooks_using_flag(
        self, flag_name: str, project_id: str
    ) -> List[Dict[str, Any]]:
        """Obtiene todos los hooks que usan un flag específico."""
        return await self.feature_flags.get_hooks_using_flag(flag_name, project_id)

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
