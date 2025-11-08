"""
Repositorio para operaciones de Hook.
"""

import asyncio
from typing import List, Optional, Dict, Any

from src.models import Hook
from .base_repository import BaseRepository
from .utils import (
    db_session,
    to_dict_list,
    model_to_dict,
    safe_upsert,
)


class HookRepository(BaseRepository):
    """Repositorio para operaciones de Hook."""
    
    async def save(self, hooks: List[Dict[str, Any]], project_id: str) -> int:
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
            with db_session(self.SessionLocal) as session:
                try:
                    saved_count = 0

                    for hook_data in hooks:
                        hook_data_dict = {
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

                        # Usar safe_upsert para insertar o actualizar
                        safe_upsert(
                            session=session,
                            model_class=Hook,
                            unique_fields={
                                'name': hook_data['name'],
                                'project_id': project_id,
                                'file_path': hook_data['file_path'],
                            },
                            data=hook_data_dict,
                            update_timestamp=True
                        )

                        saved_count += 1

                    session.commit()
                    print(f"✅ Saved {saved_count} hooks to database")
                    return saved_count

                except Exception as e:
                    session.rollback()
                    print(f"❌ Error saving hooks: {e}")
                    raise

        return await asyncio.to_thread(_save)

    async def search(
        self, query: str, project_id: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca custom hooks por nombre.
        
        Args:
            query: Término de búsqueda
            project_id: Filtrar por proyecto (opcional)
            limit: Límite de resultados (opcional, sin límite por defecto)
            
        Returns:
            Lista de hooks que coinciden
        """
        def _search():
            with db_session(self.SessionLocal) as session:
                q = session.query(Hook)

                if query:
                    q = q.filter(Hook.name.ilike(f"%{query}%"))

                if project_id:
                    q = q.filter(Hook.project_id == project_id)

                if limit:
                    q = q.limit(limit)
                
                hooks = q.all()
                return to_dict_list(hooks)

        return await asyncio.to_thread(_search)

    async def get_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los custom hooks de un proyecto.
        
        Args:
            project_id: ID del proyecto
            
        Returns:
            Lista de hooks del proyecto
        """
        def _get():
            with db_session(self.SessionLocal) as session:
                hooks = session.query(Hook).filter(Hook.project_id == project_id).all()
                return to_dict_list(hooks)

        return await asyncio.to_thread(_get)

    async def get_by_name(
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
            with db_session(self.SessionLocal) as session:
                hook = session.query(Hook).filter(
                    Hook.name == hook_name,
                    Hook.project_id == project_id
                ).first()
                return model_to_dict(hook)

        return await asyncio.to_thread(_get)

