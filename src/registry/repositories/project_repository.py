"""
Repositorio para operaciones de Project.
"""

import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime

from src.models import Project
from .base_repository import BaseRepository
from .utils import (
    db_session,
    to_dict_list,
    model_to_dict,
    safe_upsert,
    update_field,
)


class ProjectRepository(BaseRepository):
    """Repositorio para operaciones de Project."""
    
    async def upsert(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Crea o actualiza un proyecto."""
        def _upsert():
            with db_session(self.SessionLocal) as session:
                project = safe_upsert(
                    session=session,
                    model_class=Project,
                    unique_fields={'id': project_id},
                    data=data,
                    update_timestamp=False  # No actualizar updated_at en upsert de proyecto
                )
                session.commit()
                return project.to_dict()

        return await asyncio.to_thread(_upsert)

    async def get(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene un proyecto por ID."""
        def _get():
            with db_session(self.SessionLocal) as session:
                project = session.query(Project).filter(Project.id == project_id).first()
                return model_to_dict(project)

        return await asyncio.to_thread(_get)

    async def list_all(self) -> List[Dict[str, Any]]:
        """Lista todos los proyectos."""
        def _list():
            with db_session(self.SessionLocal) as session:
                projects = session.query(Project).all()
                return to_dict_list(projects)

        return await asyncio.to_thread(_list)

    async def update_sync(self, project_id: str):
        """Actualiza la fecha de último sync."""
        def _update():
            with db_session(self.SessionLocal) as session:
                update_field(
                    session=session,
                    model_class=Project,
                    filter_fields={'id': project_id},
                    field_name='last_sync',
                    field_value=datetime.utcnow(),
                    commit=True
                )

        return await asyncio.to_thread(_update)


