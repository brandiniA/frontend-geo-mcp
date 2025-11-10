"""
Repositorio para operaciones de FeatureFlag.
"""

import asyncio
from typing import List, Optional, Dict, Any

from src.models import FeatureFlag, ComponentFeatureFlag, Component, HookFeatureFlag, Hook
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
                
                # Obtener componentes que usan este flag con metadata
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
                
                # Crear mapeo de component_id a metadata
                metadata_map = {
                    cf.component_id: {
                        'usage_location': cf.usage_location or 'component',
                        'usage_context': cf.usage_context,
                        'container_file_path': cf.container_file_path,
                        'usage_type': cf.usage_type,
                        'combined_with': cf.combined_with or [],
                        'logic': cf.logic
                    }
                    for cf in component_flags
                }
                
                # Convertir componentes a dict y agregar metadata
                result = []
                for comp in components:
                    comp_dict = model_to_dict(comp)
                    if comp.id in metadata_map:
                        comp_dict.update(metadata_map[comp.id])
                    result.append(comp_dict)
                
                return result

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
        usage_pattern: Optional[str] = None,
        usage_location: str = 'component',
        usage_context: Optional[str] = None,
        container_file_path: Optional[str] = None,
        usage_type: Optional[str] = None,
        combined_with: Optional[List[str]] = None,
        logic: Optional[str] = None
    ) -> None:
        """
        Guarda la relación entre un componente y un feature flag.
        
        Args:
            component_id: ID del componente
            feature_flag_id: ID del feature flag
            usage_pattern: Patrón de uso detectado (opcional)
            usage_location: 'component' | 'container' - Dónde se usa el flag
            usage_context: Contexto de uso (mapStateToProps, mapDispatchToProps, etc.)
            container_file_path: Ruta del archivo container (solo si usage_location='container')
            usage_type: Tipo de uso (conditional_logic, array_construction, etc.)
            combined_with: Lista de otros flags si se combinan
            logic: 'AND' | 'OR' si se combinan flags
        """
        def _save():
            with db_session(self.SessionLocal) as session:
                try:
                    # Verificar si ya existe (considerando también usage_location para permitir duplicados)
                    existing = session.query(ComponentFeatureFlag).filter(
                        ComponentFeatureFlag.component_id == component_id,
                        ComponentFeatureFlag.feature_flag_id == feature_flag_id,
                        ComponentFeatureFlag.usage_location == usage_location
                    ).first()
                    
                    if not existing:
                        component_flag = ComponentFeatureFlag(
                            component_id=component_id,
                            feature_flag_id=feature_flag_id,
                            usage_pattern=usage_pattern,
                            usage_location=usage_location,
                            usage_context=usage_context,
                            container_file_path=container_file_path,
                            usage_type=usage_type,
                            combined_with=combined_with,
                            logic=logic
                        )
                        session.add(component_flag)
                        session.commit()
                except Exception as e:
                    session.rollback()
                    print(f"❌ Error saving component-flag usage: {e}")
                    raise

        return await asyncio.to_thread(_save)

    async def get_flags_for_component(
        self, component_id: int, project_id: str
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todos los feature flags que usa un componente específico.
        
        Args:
            component_id: ID del componente
            project_id: ID del proyecto
            
        Returns:
            Lista de feature flags usados por el componente
        """
        def _get():
            with db_session(self.SessionLocal) as session:
                # Obtener relaciones componente-flag
                component_flags = session.query(ComponentFeatureFlag).filter(
                    ComponentFeatureFlag.component_id == component_id
                ).all()
                
                if not component_flags:
                    return []
                
                # Obtener los IDs de los flags
                flag_ids = [cf.feature_flag_id for cf in component_flags]
                
                # Obtener los flags con sus detalles
                flags = session.query(FeatureFlag).filter(
                    FeatureFlag.id.in_(flag_ids),
                    FeatureFlag.project_id == project_id
                ).all()
                
                # Convertir a diccionarios y agregar el patrón de uso
                result = []
                flag_dict = {f.id: f for f in flags}
                for cf in component_flags:
                    if cf.feature_flag_id in flag_dict:
                        flag_data = model_to_dict(flag_dict[cf.feature_flag_id])
                        flag_data['usage_pattern'] = cf.usage_pattern
                        result.append(flag_data)
                
                return result

        return await asyncio.to_thread(_get)
    
    async def get_flags_for_component_by_location(
        self, component_id: int, project_id: str, usage_location: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Obtiene feature flags usados por un componente, filtrados por ubicación.
        
        Args:
            component_id: ID del componente
            project_id: ID del proyecto
            usage_location: Filtrar por ubicación ('component' | 'container' | None para todos)
            
        Returns:
            Lista de feature flags con metadata completa
        """
        def _get():
            with db_session(self.SessionLocal) as session:
                # Obtener relaciones componente-flag
                query = session.query(ComponentFeatureFlag).filter(
                    ComponentFeatureFlag.component_id == component_id
                )
                
                if usage_location:
                    # Si buscamos 'component', también incluir registros con usage_location NULL
                    # (para compatibilidad con datos antiguos)
                    if usage_location == 'component':
                        query = query.filter(
                            (ComponentFeatureFlag.usage_location == usage_location) |
                            (ComponentFeatureFlag.usage_location.is_(None))
                        )
                    else:
                        query = query.filter(ComponentFeatureFlag.usage_location == usage_location)
                
                component_flags = query.all()
                
                if not component_flags:
                    return []
                
                # Obtener los IDs de los flags
                flag_ids = [cf.feature_flag_id for cf in component_flags]
                
                # Obtener los flags con sus detalles
                flags = session.query(FeatureFlag).filter(
                    FeatureFlag.id.in_(flag_ids),
                    FeatureFlag.project_id == project_id
                ).all()
                
                # Convertir a diccionarios y agregar metadata completa
                result = []
                flag_dict = {f.id: f for f in flags}
                for cf in component_flags:
                    if cf.feature_flag_id in flag_dict:
                        flag_data = model_to_dict(flag_dict[cf.feature_flag_id])
                        flag_data['usage_pattern'] = cf.usage_pattern
                        flag_data['usage_location'] = cf.usage_location or 'component'
                        flag_data['usage_context'] = cf.usage_context
                        flag_data['container_file_path'] = cf.container_file_path
                        flag_data['usage_type'] = cf.usage_type
                        flag_data['combined_with'] = cf.combined_with or []
                        flag_data['logic'] = cf.logic
                        result.append(flag_data)
                
                return result

        return await asyncio.to_thread(_get)

    async def get_flags_for_hook(
        self, hook_id: int, project_id: str
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todos los feature flags que usa un hook específico.
        
        Args:
            hook_id: ID del hook
            project_id: ID del proyecto
            
        Returns:
            Lista de feature flags usados por el hook
        """
        def _get():
            with db_session(self.SessionLocal) as session:
                # Obtener relaciones hook-flag
                hook_flags = session.query(HookFeatureFlag).filter(
                    HookFeatureFlag.hook_id == hook_id
                ).all()
                
                if not hook_flags:
                    return []
                
                # Obtener los IDs de los flags
                flag_ids = [hf.feature_flag_id for hf in hook_flags]
                
                # Obtener los flags con sus detalles
                flags = session.query(FeatureFlag).filter(
                    FeatureFlag.id.in_(flag_ids),
                    FeatureFlag.project_id == project_id
                ).all()
                
                # Convertir a diccionarios y agregar el patrón de uso
                result = []
                flag_dict = {f.id: f for f in flags}
                for hf in hook_flags:
                    if hf.feature_flag_id in flag_dict:
                        flag_data = model_to_dict(flag_dict[hf.feature_flag_id])
                        flag_data['usage_pattern'] = hf.usage_pattern
                        result.append(flag_data)
                
                return result

        return await asyncio.to_thread(_get)

    async def save_hook_flag_usage(
        self,
        hook_id: int,
        feature_flag_id: int,
        usage_pattern: Optional[str] = None
    ) -> None:
        """
        Guarda la relación entre un hook y un feature flag.
        
        Args:
            hook_id: ID del hook
            feature_flag_id: ID del feature flag
            usage_pattern: Patrón de uso detectado (opcional)
        """
        def _save():
            with db_session(self.SessionLocal) as session:
                try:
                    # Verificar si ya existe
                    existing = session.query(HookFeatureFlag).filter(
                        HookFeatureFlag.hook_id == hook_id,
                        HookFeatureFlag.feature_flag_id == feature_flag_id
                    ).first()
                    
                    if not existing:
                        hook_flag = HookFeatureFlag(
                            hook_id=hook_id,
                            feature_flag_id=feature_flag_id,
                            usage_pattern=usage_pattern
                        )
                        session.add(hook_flag)
                        session.commit()
                except Exception as e:
                    session.rollback()
                    print(f"❌ Error saving hook-flag usage: {e}")
                    raise

        return await asyncio.to_thread(_save)

    async def get_hooks_using_flag(
        self, flag_name: str, project_id: str
    ) -> List[Dict[str, Any]]:
        """
        Obtiene todos los hooks que usan un flag específico.
        
        Args:
            flag_name: Nombre del flag
            project_id: ID del proyecto
            
        Returns:
            Lista de hooks que usan el flag
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
                
                # Obtener hooks que usan este flag
                hook_flags = session.query(HookFeatureFlag).filter(
                    HookFeatureFlag.feature_flag_id == flag.id
                ).all()
                
                # Obtener los hooks
                hook_ids = [hf.hook_id for hf in hook_flags]
                if not hook_ids:
                    return []
                
                hooks = session.query(Hook).filter(
                    Hook.id.in_(hook_ids),
                    Hook.project_id == project_id
                ).all()
                
                return to_dict_list(hooks)

        return await asyncio.to_thread(_get)

