"""
Utilidades para búsqueda y selección de componentes.
"""

from typing import List, Dict, Any, Optional


def find_exact_or_first_component(
    components: List[Dict],
    component_name: str
) -> Optional[Dict]:
    """
    Busca un componente por nombre exacto, o retorna el primero si no hay match exacto.
    
    Útil cuando se busca un componente específico pero se quiere un fallback
    si no hay coincidencia exacta (por ejemplo, búsquedas parciales).
    
    Args:
        components: Lista de componentes a buscar
        component_name: Nombre exacto del componente a buscar
        
    Returns:
        Componente encontrado o None si la lista está vacía
        
    Examples:
        >>> components = [
        ...     {'name': 'Button', 'file_path': 'Button.tsx'},
        ...     {'name': 'ButtonGroup', 'file_path': 'ButtonGroup.tsx'},
        ... ]
        >>> find_exact_or_first_component(components, 'Button')
        {'name': 'Button', 'file_path': 'Button.tsx'}
        >>> find_exact_or_first_component(components, 'Card')
        {'name': 'Button', 'file_path': 'Button.tsx'}  # Retorna el primero
    """
    if not components:
        return None
    
    # Buscar match exacto primero
    for comp in components:
        if comp.get('name') == component_name:
            return comp
    
    # Si no hay match exacto, retornar el primero
    return components[0]


def normalize_components_to_dicts(components: List[Any]) -> List[Dict]:
    """
    Normaliza una lista de componentes a diccionarios.
    
    Maneja diferentes tipos de objetos:
    - Diccionarios: se mantienen tal cual
    - Objetos con método to_dict(): se convierte usando el método
    - Otros objetos: se extraen atributos comunes manualmente
    
    Args:
        components: Lista de componentes (pueden ser dicts u objetos)
        
    Returns:
        Lista de componentes normalizados como diccionarios
        
    Examples:
        >>> class Component:
        ...     def __init__(self):
        ...         self.name = 'Button'
        ...         self.project_id = 'ui'
        >>> comps = [{'name': 'Card'}, Component()]
        >>> normalized = normalize_components_to_dicts(comps)
        >>> len(normalized)
        2
        >>> normalized[0]['name']
        'Card'
    """
    normalized = []
    
    for comp in components:
        if isinstance(comp, dict):
            normalized.append(comp)
        elif hasattr(comp, 'to_dict'):
            normalized.append(comp.to_dict())
        else:
            # Fallback: crear diccionario manualmente
            normalized.append({
                'id': getattr(comp, 'id', None),
                'name': getattr(comp, 'name', ''),
                'project_id': getattr(comp, 'project_id', ''),
                'file_path': getattr(comp, 'file_path', ''),
                'props': getattr(comp, 'props', []),
                'component_type': getattr(comp, 'component_type', None),
                'description': getattr(comp, 'description', None),
                'jsdoc': getattr(comp, 'jsdoc', None),
                'hooks': getattr(comp, 'hooks', []),
                'imports': getattr(comp, 'imports', []),
            })
    
    return normalized

