"""
Utilidades para manipulación y análisis de componentes React.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional


def get_all_hooks(component: Dict) -> List[str]:
    """
    Extrae y combina todos los hooks de un componente.
    
    Combina native_hooks_used (ej: useState, useEffect) con
    custom_hooks_used (ej: useAuth, useLocalStorage).
    
    Args:
        component: Diccionario del componente con native_hooks_used y custom_hooks_used
        
    Returns:
        Lista combinada de todos los hooks, o lista vacía si no hay hooks
        
    Examples:
        >>> comp = {
        ...     'native_hooks_used': ['useState', 'useEffect'],
        ...     'custom_hooks_used': ['useAuth']
        ... }
        >>> get_all_hooks(comp)
        ['useState', 'useEffect', 'useAuth']
    """
    all_hooks = []
    
    if component.get('native_hooks_used'):
        all_hooks.extend(component['native_hooks_used'])
    
    if component.get('custom_hooks_used'):
        all_hooks.extend(component['custom_hooks_used'])
    
    return all_hooks


def is_new_component(component: Dict, days: int = 7) -> bool:
    """
    Determina si un componente fue creado recientemente.
    
    Un componente se considera "nuevo" si su fecha de creación
    está dentro del número de días especificado.
    
    Args:
        component: Diccionario del componente con campo 'created_at'
        days: Número de días para considerar "nuevo" (default: 7)
        
    Returns:
        True si el componente es nuevo, False si no o si no se puede determinar
        
    Examples:
        >>> comp = {
        ...     'created_at': datetime.now() - timedelta(days=2),
        ...     'name': 'Button'
        ... }
        >>> is_new_component(comp, days=7)
        True
    """
    created_at = component.get('created_at')
    
    if isinstance(created_at, str):
        try:
            created_at = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return False
    
    if not isinstance(created_at, datetime):
        return False
    
    now = datetime.now()
    threshold = now - timedelta(days=days)
    
    return created_at > threshold


def group_components_by_type(components: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Agrupa componentes por su tipo (page, component, layout, hook).
    
    Args:
        components: Lista de componentes a agrupar
        
    Returns:
        Diccionario con tipos como claves y listas de componentes como valores
        
    Examples:
        >>> components = [
        ...     {'name': 'Button', 'component_type': 'component'},
        ...     {'name': 'HomePage', 'component_type': 'page'},
        ...     {'name': 'Card', 'component_type': 'component'},
        ... ]
        >>> grouped = group_components_by_type(components)
        >>> list(grouped.keys())
        ['component', 'page']
        >>> len(grouped['component'])
        2
    """
    by_type = {}
    
    for comp in components:
        comp_type = comp.get('component_type') or 'component'
        
        if comp_type not in by_type:
            by_type[comp_type] = []
        
        by_type[comp_type].append(comp)
    
    return by_type
