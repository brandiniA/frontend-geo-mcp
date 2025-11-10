"""
Repositorio para operaciones de Component.
"""

import asyncio
from typing import List, Optional, Dict, Any

from src.models import Component, Hook
from .base_repository import BaseRepository
from .utils import (
    db_session,
    to_dict_list,
    model_to_dict,
    make_serializable,
    safe_upsert,
)
from src.utils.import_resolver import resolve_imports_to_components


class ComponentRepository(BaseRepository):
    """Repositorio para operaciones de Component."""
    
    def _component_to_dict(self, c):
        """Convierte un componente a diccionario, manejando diferentes tipos."""
        if isinstance(c, dict):
            return c
        result = model_to_dict(c)
        if result:
            return result
        # Fallback: crear diccionario manualmente si model_to_dict falla
        return {
            'id': getattr(c, 'id', None),
            'name': getattr(c, 'name', ''),
            'project_id': getattr(c, 'project_id', ''),
            'file_path': getattr(c, 'file_path', ''),
            'props': getattr(c, 'props', []),
            'native_hooks_used': getattr(c, 'native_hooks_used', []),
            'custom_hooks_used': getattr(c, 'custom_hooks_used', []),
            'imports': getattr(c, 'imports', []),
            'exports': getattr(c, 'exports', []),
            'component_type': getattr(c, 'component_type', None),
            'description': getattr(c, 'description', None),
            'jsdoc': getattr(c, 'jsdoc', None),
            'created_at': getattr(c, 'created_at', None),
            'updated_at': getattr(c, 'updated_at', None),
        }
    
    def _rank_component(self, comp_dict: Dict[str, Any], query: str) -> int:
        """Calcula el score de relevancia de un componente."""
        score = 0
        query_lower = query.lower()
        
        # Name match es más importante
        if query_lower in comp_dict.get('name', '').lower():
            score += 10
            if comp_dict.get('name', '').lower() == query_lower:
                score += 5
        
        # Description match
        if comp_dict.get('description') and query_lower in comp_dict['description'].lower():
            score += 5
        
        # File path match
        if query_lower in comp_dict.get('file_path', '').lower():
            score += 2
        
        return score
    
    
    async def save(self, components: List[Dict[str, Any]], project_id: str, resolve_dependencies: bool = True) -> int:
        """
        Guarda componentes en la base de datos.
        Separa y valida hooks:
        - native_hooks_used: Se guarda tal cual (ej: ["useState", "useEffect"])
        - custom_hooks_used: Se valida contra tabla de hooks y se guardan solo nombres existentes
        
        Args:
            components: Lista de componentes a guardar
            project_id: ID del proyecto
            resolve_dependencies: Si True, resuelve dependencias al guardar. Si False, solo guarda el componente.
            
        Returns:
            Número de componentes guardados
        """
        if not components:
            return 0

        def _save():
            with db_session(self.SessionLocal) as session:
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
                        
                        component_data = {
                            'props': comp_data.get('props', []),
                            'native_hooks_used': native_hooks,
                            'custom_hooks_used': valid_custom_hooks,
                            'imports': comp_data.get('imports', []),
                            'component_imports': comp_data.get('component_imports', []),  # Nuevo formato estructurado
                            'exports': comp_data.get('exports', []),
                            'component_type': comp_data.get('component_type', 'component'),
                            'description': comp_data.get('description'),
                            'jsdoc': comp_data.get('jsdoc'),
                        }

                        # Usar safe_upsert para insertar o actualizar
                        component = safe_upsert(
                            session=session,
                            model_class=Component,
                            unique_fields={
                                'name': comp_data['name'],
                                'project_id': project_id,
                                'file_path': comp_data['file_path'],
                            },
                            data=component_data,
                            update_timestamp=True
                        )
                        
                        # Resolver y guardar dependencias si hay component_imports
                        # ⭐ NUEVO: Solo si resolve_dependencies=True
                        component_imports = comp_data.get('component_imports', [])
                        if component_imports and resolve_dependencies:
                            try:
                                # Eliminar dependencias antiguas antes de recalcular
                                # Esto asegura que siempre usamos la lógica más reciente de resolución
                                from src.models import ComponentDependency
                                session.query(ComponentDependency).filter(
                                    ComponentDependency.component_id == component.id
                                ).delete()
                                
                                dependencies = resolve_imports_to_components(
                                    component_imports=component_imports,
                                    project_id=project_id,
                                    current_file_path=comp_data['file_path'],
                                    component_name=comp_data['name'],
                                    db_session=session
                                )
                                
                                # Guardar nuevas dependencias
                                for dep in dependencies:
                                    new_dep = ComponentDependency(
                                        component_id=component.id,
                                        depends_on_component_id=dep.get('depends_on_component_id'),
                                        depends_on_name=dep['depends_on_name'],
                                        from_path=dep['from_path'],
                                        import_type=dep['import_type'],
                                        is_external=dep.get('is_external', False),
                                        project_id=project_id
                                    )
                                    session.add(new_dep)
                            except Exception as dep_error:
                                # No fallar si hay error resolviendo dependencias
                                print(f"⚠️  Warning: Could not resolve dependencies for {comp_data['name']}: {dep_error}")

                        saved_count += 1

                    session.commit()
                    print(f"✅ Saved {saved_count} components to database")
                    return saved_count
                except Exception as e:
                    session.rollback()
                    print(f"❌ Error saving components: {e}")
                    raise

        return await asyncio.to_thread(_save)
    
    async def resolve_all_dependencies(self, project_id: str) -> int:
        """
        Resuelve dependencias para TODOS los componentes de un proyecto.
        Útil para ejecutar DESPUÉS de indexar barrel exports.
        
        Args:
            project_id: ID del proyecto
            
        Returns:
            Número de componentes procesados
        """
        def _resolve():
            with db_session(self.SessionLocal) as session:
                try:
                    from src.models import ComponentDependency
                    from src.utils.import_resolver import resolve_imports_to_components
                    
                    # Obtener todos los componentes del proyecto
                    components = session.query(Component).filter(
                        Component.project_id == project_id
                    ).all()
                    
                    processed = 0
                    
                    for component in components:
                        # Obtener component_imports del JSON
                        component_imports = component.component_imports if hasattr(component, 'component_imports') else []
                        
                        if not component_imports:
                            continue
                        
                        # Eliminar dependencias antiguas
                        session.query(ComponentDependency).filter(
                            ComponentDependency.component_id == component.id
                        ).delete()
                        
                        # Resolver nuevamente con barrel exports disponibles
                        try:
                            dependencies = resolve_imports_to_components(
                                component_imports=component_imports,
                                project_id=project_id,
                                current_file_path=component.file_path,
                                component_name=component.name,
                                db_session=session
                            )
                            
                            # Guardar nuevas dependencias
                            for dep in dependencies:
                                dependency = ComponentDependency(
                                    component_id=component.id,
                                    project_id=project_id,
                                    **dep
                                )
                                session.add(dependency)
                        except Exception as dep_error:
                            # No fallar por un componente
                            print(f"⚠️  Warning: Could not resolve dependencies for {component.name}: {dep_error}")
                        
                        processed += 1
                    
                    session.commit()
                    return processed
                    
                except Exception as e:
                    print(f"❌ Error resolviendo dependencias: {str(e)}")
                    session.rollback()
                    raise

        return await asyncio.to_thread(_resolve)

    async def search(
        self, query: str, project_id: Optional[str] = None, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Busca componentes por nombre, descripción y ruta.
        
        Args:
            query: Término de búsqueda
            project_id: Filtrar por proyecto (opcional)
            limit: Límite de resultados (opcional, sin límite por defecto)
        """
        def _search():
            with db_session(self.SessionLocal) as session:
                from sqlalchemy import or_
                
                q = session.query(Component)

                if query:
                    # Buscar en múltiples campos: name, description, file_path
                    search_conditions = [
                        Component.name.ilike(f"%{query}%"),
                        Component.description.ilike(f"%{query}%"),
                        Component.file_path.ilike(f"%{query}%"),
                    ]
                    q = q.filter(or_(*search_conditions))

                if project_id:
                    q = q.filter(Component.project_id == project_id)

                if limit:
                    q = q.limit(limit)
                
                components = q.all()
                
                # Convertir a diccionarios usando utilidad
                components_dict = [self._component_to_dict(c) for c in components]
                
                # Ranking básico por relevancia si hay query
                if query:
                    components_dict.sort(
                        key=lambda c: self._rank_component(c, query), 
                        reverse=True
                    )
                
                return components_dict

        return await asyncio.to_thread(_search)

    async def get_all(self) -> List[Dict[str, Any]]:
        """Obtiene todos los componentes indexados."""
        def _get_all():
            with db_session(self.SessionLocal) as session:
                components = session.query(Component).all()
                return to_dict_list(components)

        return await asyncio.to_thread(_get_all)

    async def get_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """Obtiene todos los componentes de un proyecto."""
        def _get():
            with db_session(self.SessionLocal) as session:
                components = session.query(Component).filter(Component.project_id == project_id).all()
                return to_dict_list(components)

        return await asyncio.to_thread(_get)

    async def list_in_path(
        self, path: str, project_id: str
    ) -> List[Dict[str, Any]]:
        """
        Lista todos los componentes en una ruta específica.
        
        Args:
            path: Ruta del directorio (ej: "src/components/purchase")
            project_id: ID del proyecto
            
        Returns:
            Lista de componentes en esa ruta (sin límite)
        """
        def _list():
            with db_session(self.SessionLocal) as session:
                q = session.query(Component).filter(
                    Component.project_id == project_id,
                    Component.file_path.like(f"{path}%")
                )
                components = q.all()
                return to_dict_list(components)
        
        return await asyncio.to_thread(_list)

    async def search_semantic(
        self,
        query: Optional[str] = None,
        project_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Búsqueda semántica en múltiples campos con filtros avanzados.
        
        Args:
            query: Término de búsqueda (opcional)
            project_id: Filtrar por proyecto (opcional)
            filters: Filtros adicionales {
                'type': 'atom' | 'molecule' | 'page' | 'hook' | 'container',
                'path': 'src/components/purchase',
                'contains_hook': 'useState',
                'contains_dependency': 'react-router'
            }
            
        Returns:
            Lista de componentes ordenados por relevancia
        """
        def _search():
            with db_session(self.SessionLocal) as session:
                from sqlalchemy import or_, cast, String
                
                q = session.query(Component)
                
                # Buscar en múltiples campos
                if query and isinstance(query, str) and query.strip():
                    search_conditions = [
                        Component.name.ilike(f"%{query}%"),
                        Component.description.ilike(f"%{query}%"),
                        cast(Component.jsdoc, String).ilike(f"%{query}%"),
                        Component.file_path.ilike(f"%{query}%"),
                    ]
                    q = q.filter(or_(*search_conditions))
                
                # Filtros base
                if project_id:
                    q = q.filter(Component.project_id == project_id)
                
                # Filtros avanzados
                if filters:
                    if filters.get('type'):
                        q = q.filter(Component.component_type == filters['type'])
                    
                    if filters.get('path'):
                        q = q.filter(Component.file_path.like(f"{filters['path']}%"))
                    
                    if filters.get('contains_hook'):
                        hook_name = filters['contains_hook']
                        native_search = cast(Component.native_hooks_used, String).contains(f'"{hook_name}"')
                        custom_search = cast(Component.custom_hooks_used, String).contains(f'"{hook_name}"')
                        q = q.filter(or_(native_search, custom_search))
                    
                    if filters.get('contains_dependency'):
                        dep_name = filters['contains_dependency']
                        q = q.filter(cast(Component.imports, String).contains(f'"{dep_name}"'))
                
                components = q.all()
                
                # Convertir a diccionarios
                components_dict = []
                for c in components:
                    try:
                        components_dict.append(self._component_to_dict(c))
                    except Exception as e:
                        import traceback
                        print(f"Error converting component to dict: {e}")
                        print(traceback.format_exc())
                        continue
                
                # Ranking por relevancia (solo si hay query)
                if query and isinstance(query, str) and query.strip():
                    components_dict.sort(
                        key=lambda c: self._rank_component(c, query), 
                        reverse=True
                    )
                
                # Asegurar que todos los valores son serializables usando utilidad
                return [make_serializable(c) for c in components_dict]
        return await asyncio.to_thread(_search)

    async def count(self, project_id: Optional[str] = None) -> int:
        """Obtiene el conteo de componentes."""
        def _count():
            with db_session(self.SessionLocal) as session:
                q = session.query(Component)
                if project_id:
                    q = q.filter(Component.project_id == project_id)
                return q.count()

        return await asyncio.to_thread(_count)

    async def get_index_stats(
        self, 
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas detalladas del índice de componentes.
        
        Args:
            project_id: Filtrar por proyecto (opcional)
            
        Returns:
            Dict con estadísticas completas: total, byType, byPath, lastUpdated, indexCoverage
        """
        def _stats():
            with db_session(self.SessionLocal) as session:
                q = session.query(Component)
                if project_id:
                    q = q.filter(Component.project_id == project_id)
                
                all_components = q.all()
                total = len(all_components)
                
                # Por tipo
                by_type = {}
                for comp in all_components:
                    comp_type = comp.component_type or 'unknown'
                    by_type[comp_type] = by_type.get(comp_type, 0) + 1
                
                # Por ruta (agrupar por directorio padre)
                by_path = {}
                for comp in all_components:
                    path_parts = comp.file_path.split('/')
                    if len(path_parts) > 1:
                        # Tomar directorio padre
                        parent_path = '/'.join(path_parts[:-1])
                        by_path[parent_path] = by_path.get(parent_path, 0) + 1
                    else:
                        by_path['root'] = by_path.get('root', 0) + 1
                
                # Última actualización
                last_updated = None
                if all_components:
                    updated_dates = [c.updated_at for c in all_components if c.updated_at]
                    if updated_dates:
                        last_updated = max(updated_dates)
                
                result = {
                    'total': total,
                    'byType': by_type,
                    'byPath': dict(sorted(by_path.items(), key=lambda x: x[1], reverse=True)[:20]),  # Top 20
                    'lastUpdated': last_updated.isoformat() if last_updated else None,
                    'indexCoverage': 100.0  # Asumimos 100% si están indexados
                }
                # Serializar para asegurar que lastUpdated es string
                return make_serializable(result)
        return await asyncio.to_thread(_stats)

    async def search_by_hook(
        self, hook_name: str, project_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Busca componentes que usan un hook específico (búsqueda en la BD).
        Busca tanto en hooks nativos (React) como en custom hooks.
        Más eficiente que traer todos los componentes y filtrar en memoria.
        
        Args:
            hook_name: Nombre del hook (ej: useState, useEffect, useAuth)
            project_id: Filtrar por proyecto (opcional)
            
        Returns:
            Lista de componentes que usan el hook (nativo o custom)
        """
        def _search():
            with db_session(self.SessionLocal) as session:
                from sqlalchemy import cast, String, or_
                
                q = session.query(Component)
                
                # Buscar el hook en native_hooks_used O custom_hooks_used
                # Convierte JSON a texto y busca el nombre entre comillas (ej: "useState")
                native_search = cast(Component.native_hooks_used, String).contains(f'"{hook_name}"')
                custom_search = cast(Component.custom_hooks_used, String).contains(f'"{hook_name}"')
                
                q = q.filter(or_(native_search, custom_search))
                
                if project_id:
                    q = q.filter(Component.project_id == project_id)
                
                components = q.all()
                return to_dict_list(components)

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
            with db_session(self.SessionLocal) as session:
                from sqlalchemy import cast, String
                
                q = session.query(Component)
                
                # Convertir JSON a texto y buscar la prop
                q = q.filter(cast(Component.props, String).contains(f'"{prop_name}"'))
                
                if project_id:
                    q = q.filter(Component.project_id == project_id)
                
                components = q.all()
                return to_dict_list(components)

        return await asyncio.to_thread(_search)
    
    async def update_container_file_path(
        self, component_name: str, project_id: str, container_file_path: str
    ) -> bool:
        """
        Actualiza el container_file_path de un componente.
        
        Args:
            component_name: Nombre del componente
            project_id: ID del proyecto
            container_file_path: Ruta del archivo container
            
        Returns:
            True si se actualizó, False si no se encontró el componente
        """
        def _update():
            with db_session(self.SessionLocal) as session:
                component = session.query(Component).filter(
                    Component.name == component_name,
                    Component.project_id == project_id
                ).first()
                
                if component:
                    component.container_file_path = container_file_path
                    session.commit()
                    return True
                return False
        
        return await asyncio.to_thread(_update)


