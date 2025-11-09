"""
Repositorio para operaciones de ComponentDependency.
"""

import asyncio
from typing import List, Optional, Dict, Any

from src.models import ComponentDependency, Component
from .base_repository import BaseRepository
from .utils import (
    db_session,
    to_dict_list,
    model_to_dict,
)


class DependencyRepository(BaseRepository):
    """Repositorio para operaciones de ComponentDependency."""
    
    async def save_dependencies(
        self,
        component_id: int,
        project_id: str,
        dependencies: List[Dict[str, Any]]
    ) -> int:
        """
        Guarda las dependencias de un componente.
        
        Args:
            component_id: ID del componente
            project_id: ID del proyecto
            dependencies: Lista de dependencias resueltas desde import_resolver
        
        Returns:
            Número de dependencias guardadas
        """
        if not dependencies:
            return 0
        
        def _save():
            with db_session(self.SessionLocal) as session:
                try:
                    saved_count = 0
                    
                    for dep in dependencies:
                        # Verificar si ya existe
                        existing = session.query(ComponentDependency).filter(
                            ComponentDependency.component_id == component_id,
                            ComponentDependency.depends_on_component_id == dep.get('depends_on_component_id'),
                            ComponentDependency.depends_on_name == dep['depends_on_name']
                        ).first()
                        
                        if existing:
                            # Actualizar existente
                            existing.from_path = dep['from_path']
                            existing.import_type = dep['import_type']
                            existing.is_external = dep.get('is_external', False)
                        else:
                            # Crear nuevo
                            new_dep = ComponentDependency(
                                component_id=component_id,
                                depends_on_component_id=dep.get('depends_on_component_id'),
                                depends_on_name=dep['depends_on_name'],
                                from_path=dep['from_path'],
                                import_type=dep['import_type'],
                                is_external=dep.get('is_external', False),
                                project_id=project_id
                            )
                            session.add(new_dep)
                        
                        saved_count += 1
                    
                    session.commit()
                    return saved_count
                    
                except Exception as e:
                    session.rollback()
                    print(f"❌ Error saving dependencies: {e}")
                    raise
        
        return await asyncio.to_thread(_save)
    
    async def get_dependencies(self, component_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene los componentes que usa este componente (dependencias descendentes).
        
        Args:
            component_id: ID del componente
        
        Returns:
            Lista de componentes de los que depende
        """
        def _get():
            with db_session(self.SessionLocal) as session:
                deps = session.query(ComponentDependency).filter(
                    ComponentDependency.component_id == component_id,
                    ComponentDependency.is_external == False,
                    ComponentDependency.depends_on_component_id.isnot(None)
                ).all()
                
                # Obtener información de los componentes dependientes
                result = []
                for dep in deps:
                    comp = dep.depends_on_component
                    if comp:
                        comp_dict = comp.to_dict()
                        comp_dict['import_type'] = dep.import_type
                        comp_dict['from_path'] = dep.from_path
                        result.append(comp_dict)
                
                return result
        
        return await asyncio.to_thread(_get)
    
    async def get_dependents(self, component_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene los componentes que usan este componente (dependientes ascendentes).
        
        Args:
            component_id: ID del componente
        
        Returns:
            Lista de componentes que dependen de este
        """
        def _get():
            with db_session(self.SessionLocal) as session:
                deps = session.query(ComponentDependency).filter(
                    ComponentDependency.depends_on_component_id == component_id,
                    ComponentDependency.is_external == False
                ).all()
                
                # Obtener información de los componentes que dependen
                result = []
                for dep in deps:
                    comp = dep.component
                    if comp:
                        comp_dict = comp.to_dict()
                        comp_dict['import_type'] = dep.import_type
                        comp_dict['from_path'] = dep.from_path
                        result.append(comp_dict)
                
                return result
        
        return await asyncio.to_thread(_get)
    
    async def get_dependency_tree(
        self,
        component_id: int,
        direction: str = 'down',
        max_depth: int = 5,
        visited: Optional[set] = None
    ) -> Dict[str, Any]:
        """
        Construye un árbol de dependencias recursivo.
        
        Args:
            component_id: ID del componente raíz
            direction: 'down' (dependencias), 'up' (dependientes), 'both'
            max_depth: Profundidad máxima del árbol
            visited: Set de IDs visitados (para evitar loops)
        
        Returns:
            Diccionario con estructura de árbol:
            {
                'component': {...},
                'children': [...],
                'depth': 0,
                'circular': False
            }
        """
        if visited is None:
            visited = set()
        
        if max_depth <= 0:
            return {
                'component_id': component_id,
                'max_depth_reached': True,
                'children': []
            }
        
        def _build_tree():
            with db_session(self.SessionLocal) as session:
                return self._build_tree_recursive(
                    component_id, direction, max_depth, visited.copy(), session
                )
        
        # Nota: Esta función necesita ser async pero usa db_session sincrónico
        # Necesitamos refactorizar para usar async_db_operation
        result = await asyncio.to_thread(_build_tree)
        
        return result or {
            'component_id': component_id,
            'children': [],
            'depth': 5 - max_depth
        }
    
    def _build_tree_recursive(
        self,
        component_id: int,
        direction: str,
        max_depth: int,
        visited: set,
        session
    ) -> Optional[Dict[str, Any]]:
        """
        Método auxiliar recursivo para construir árbol (debe ejecutarse dentro de una sesión).
        """
        if component_id in visited:
            return {
                'component_id': component_id,
                'circular': True,
                'children': []
            }
        
        if max_depth <= 0:
            return {
                'component_id': component_id,
                'max_depth_reached': True,
                'children': []
            }
        
        visited.add(component_id)
        
        comp = session.query(Component).filter(Component.id == component_id).first()
        if not comp:
            visited.discard(component_id)
            return None
        
        comp_dict = comp.to_dict()
        children = []
        
        if direction in ['down', 'both']:
            deps = session.query(ComponentDependency).filter(
                ComponentDependency.component_id == component_id,
                ComponentDependency.is_external == False,
                ComponentDependency.depends_on_component_id.isnot(None)
            ).all()
            
            for dep in deps:
                if dep.depends_on_component_id:
                    child_tree = self._build_tree_recursive(
                        dep.depends_on_component_id,
                        'down',
                        max_depth - 1,
                        visited.copy(),
                        session
                    )
                    if child_tree:
                        child_tree['import_type'] = dep.import_type
                        child_tree['from_path'] = dep.from_path
                        children.append(child_tree)
        
        if direction in ['up', 'both']:
            dependents = session.query(ComponentDependency).filter(
                ComponentDependency.depends_on_component_id == component_id,
                ComponentDependency.is_external == False
            ).all()
            
            for dep in dependents:
                child_tree = self._build_tree_recursive(
                    dep.component_id,
                    'up',
                    max_depth - 1,
                    visited.copy(),
                    session
                )
                if child_tree:
                    child_tree['import_type'] = dep.import_type
                    child_tree['from_path'] = dep.from_path
                    children.append(child_tree)
        
        visited.discard(component_id)
        
        return {
            'component': comp_dict,
            'children': children,
            'depth': 5 - max_depth,
            'circular': False
        }

