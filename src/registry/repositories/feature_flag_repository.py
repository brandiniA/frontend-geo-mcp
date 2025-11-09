"""
Repositorio para operaciones de FeatureFlag.
"""

import asyncio
from typing import List, Optional, Dict, Any

from src.models import FeatureFlag, ComponentFeatureFlag, Component
from .base_repository import BaseRepository
from .utils import (
    db_session,
    to_dict_list,
    model_to_dict,
    safe_upsert,
)


class FeatureFlagRepository(BaseRepository):
    """Repositorio para operaciones de FeatureFlag."""
    
    async def save(self, flags: List[Dict[str, Any]], project_id: str) -> int:
        """
        Guarda feature flags en la base de datos.
        
        Args:
            flags: Lista de feature flags a guardar
            project_id: ID del proyecto
            
        Returns:
            Número de flags guardados
        """
        if not flags:
            return 0

        def _save():
            with db_session(self.SessionLocal) as session:
                try:
                    saved_count = 0

                    for flag_data in flags:
                        flag_data_dict = {
                            'file_path': flag_data.get('file_path'),
                            'default_value': flag_data.get('default_value'),
                            'value_type': flag_data.get('value_type'),
                            'description': flag_data.get('description'),
                            'possible_values': flag_data.get('possible_values', []),
                        }

                        # Usar safe_upsert para insertar o actualizar
                        safe_upsert(
                            session=session,
                            model_class=FeatureFlag,
                            unique_fields={
                                'name': flag_data['name'],
                                'project_id': project_id,
                            },
                            data=flag_data_dict,
                            update_timestamp=True
                        )

                        saved_count += 1

                    session.commit()
                    print(f"✅ Saved {saved_count} feature flags to database")
                    return saved_count

                except Exception as e:
                    session.rollback()
                    print(f"❌ Error saving feature flags: {e}")
                    raise

        return await asyncio.to_thread(_save)

    async def search(
        self, query: str, project_id: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca feature flags por nombre.
        
        Args:
            query: Término de búsqueda
            project_id: Filtrar por proyecto (opcional)
            limit: Límite de resultados (opcional)
            
        Returns:
            Lista de flags que coinciden
        """
        def _search():
            with db_session(self.SessionLocal) as session:
                q = session.query(FeatureFlag)

                if query:
                    q = q.filter(FeatureFlag.name.ilike(f"%{query}%"))

                if project_id:
                    q = q.filter(FeatureFlag.project_id == project_id)

                if limit:
                    q = q.limit(limit)
                
                flags = q.all()
                return to_dict_list(flags)

        return await asyncio.to_thread(_search)

    async def get_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los feature flags de un proyecto.
        
        Args:
            project_id: ID del proyecto
            
        Returns:
            Lista de flags del proyecto
        """
        def _get():
            with db_session(self.SessionLocal) as session:
                flags = session.query(FeatureFlag).filter(
                    FeatureFlag.project_id == project_id
                ).all()
                return to_dict_list(flags)

        return await asyncio.to_thread(_get)

    async def get_by_name(
        self, flag_name: str, project_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene un feature flag por nombre y proyecto.
        
        Args:
            flag_name: Nombre del flag
            project_id: ID del proyecto
            
        Returns:
            Diccionario con información del flag o None
        """
        def _get():
            with db_session(self.SessionLocal) as session:
                flag = session.query(FeatureFlag).filter(
                    FeatureFlag.name == flag_name,
                    FeatureFlag.project_id == project_id
                ).first()
                return model_to_dict(flag)

        return await asyncio.to_thread(_get)

    async def get_components_using_flag(
        self, flag_name: str, project_id: str
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todos los componentes que usan un flag específico.
        
        Args:
            flag_name: Nombre del flag
            project_id: ID del proyecto
            
        Returns:
            Lista de componentes que usan el flag
        """
        def _get():
            with db_session(self.SessionLocal) as session:
                # Buscar el flag primero
                flag = session.query(FeatureFlag).filter(
                    FeatureFlag.name == flag_name,
                    FeatureFlag.project_id == project_id
                ).first()
                
                if not flag:
                    return []
                
                # Obtener componentes que usan este flag
                component_flags = session.query(ComponentFeatureFlag).filter(
                    ComponentFeatureFlag.feature_flag_id == flag.id
                ).all()
                
                # Obtener los componentes
                component_ids = [cf.component_id for cf in component_flags]
                if not component_ids:
                    return []
                
                components = session.query(Component).filter(
                    Component.id.in_(component_ids),
                    Component.project_id == project_id
                ).all()
                
                return to_dict_list(components)

        return await asyncio.to_thread(_get)

    async def get_unused_flags(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene flags definidos que NO se usan en ningún componente.
        
        Args:
            project_id: ID del proyecto
            
        Returns:
            Lista de flags no usados
        """
        def _get():
            with db_session(self.SessionLocal) as session:
                # Obtener todos los flags del proyecto
                all_flags = session.query(FeatureFlag).filter(
                    FeatureFlag.project_id == project_id
                ).all()
                
                # Obtener IDs de flags que SÍ se usan
                used_flag_ids = session.query(
                    ComponentFeatureFlag.feature_flag_id
                ).join(
                    FeatureFlag, ComponentFeatureFlag.feature_flag_id == FeatureFlag.id
                ).filter(
                    FeatureFlag.project_id == project_id
                ).distinct().all()
                
                used_flag_ids_set = {fid[0] for fid in used_flag_ids}
                
                # Filtrar flags no usados
                unused_flags = [
                    flag for flag in all_flags if flag.id not in used_flag_ids_set
                ]
                
                return to_dict_list(unused_flags)

        return await asyncio.to_thread(_get)

    async def save_component_flag_usage(
        self,
        component_id: int,
        feature_flag_id: int,
        usage_pattern: Optional[str] = None
    ) -> None:
        """
        Guarda la relación entre un componente y un feature flag.
        
        Args:
            component_id: ID del componente
            feature_flag_id: ID del feature flag
            usage_pattern: Patrón de uso detectado (opcional)
        """
        def _save():
            with db_session(self.SessionLocal) as session:
                try:
                    # Verificar si ya existe
                    existing = session.query(ComponentFeatureFlag).filter(
                        ComponentFeatureFlag.component_id == component_id,
                        ComponentFeatureFlag.feature_flag_id == feature_flag_id
                    ).first()
                    
                    if not existing:
                        component_flag = ComponentFeatureFlag(
                            component_id=component_id,
                            feature_flag_id=feature_flag_id,
                            usage_pattern=usage_pattern
                        )
                        session.add(component_flag)
                        session.commit()
                except Exception as e:
                    session.rollback()
                    print(f"❌ Error saving component-flag usage: {e}")
                    raise

        return await asyncio.to_thread(_save)

