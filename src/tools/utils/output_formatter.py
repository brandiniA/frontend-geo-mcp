"""
Utilidades para formateo de output y agrupación de resultados.
"""

from typing import Dict, List, Any


def group_by_project(items: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Agrupa items por su project_id.
    
    Útil para agrupar resultados de búsqueda de componentes,
    hooks o resultados de queries que incluyen múltiples proyectos.
    
    Args:
        items: Lista de items (componentes, hooks, etc) con 'project_id'
        
    Returns:
        Diccionario agrupado por project_id
        
    Examples:
        >>> items = [
        ...     {'name': 'Button', 'project_id': 'ui-library'},
        ...     {'name': 'Card', 'project_id': 'ui-library'},
        ...     {'name': 'HomePage', 'project_id': 'main-app'},
        ... ]
        >>> grouped = group_by_project(items)
        >>> list(grouped.keys())
        ['ui-library', 'main-app']
        >>> len(grouped['ui-library'])
        2
    """
    by_project = {}
    
    for item in items:
        project_id = item.get('project_id')
        
        if project_id not in by_project:
            by_project[project_id] = []
        
        by_project[project_id].append(item)
    
    return by_project


def format_list_with_more(
    items: List[str],
    max_items: int = 5,
    separator: str = ', '
) -> str:
    """
    Formatea una lista de strings con "... X more" si excede el máximo.
    
    Usado para mostrar listas de props, hooks, imports, etc
    sin abrumar al usuario con información.
    
    Args:
        items: Lista de items a formatear
        max_items: Máximo número de items a mostrar (default: 5)
        separator: Separador entre items (default: ', ')
        
    Returns:
        String formateado, ej: "useState, useEffect, useContext (+2 more)"
        
    Examples:
        >>> props = ['label', 'onClick', 'disabled', 'variant', 'size', 'loading']
        >>> format_list_with_more(props, max_items=3)
        'label, onClick, disabled (+3 more)'
    """
    if not items:
        return ""
    
    if len(items) <= max_items:
        return separator.join(items)
    
    shown = items[:max_items]
    remaining = len(items) - max_items
    
    return f"{separator.join(shown)} (+{remaining} more)"
