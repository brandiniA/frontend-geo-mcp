"""
Utilidades para búsqueda y filtrado en documentación de componentes.
"""

from typing import Dict, List, Tuple, Optional


def match_in_description(jsdoc: Dict, query: str) -> bool:
    """
    Comprueba si un término de búsqueda coincide en la descripción del JSDoc.
    
    Args:
        jsdoc: Diccionario JSDoc del componente
        query: Término a buscar (case-insensitive)
        
    Returns:
        True si el término se encuentra en la descripción
        
    Examples:
        >>> jsdoc = {'description': 'Button component for actions'}
        >>> match_in_description(jsdoc, 'button')
        True
    """
    description = jsdoc.get('description', '').lower()
    return query.lower() in description


def match_in_params(jsdoc: Dict, query: str) -> Optional[str]:
    """
    Busca un término en los parámetros del JSDoc.
    
    Args:
        jsdoc: Diccionario JSDoc del componente
        query: Término a buscar (case-insensitive)
        
    Returns:
        Nombre del parámetro que coincide, o None si no hay coincidencia
        
    Examples:
        >>> jsdoc = {'params': [{'name': 'onClick', 'description': 'Click handler'}]}
        >>> match_in_params(jsdoc, 'click')
        'onClick'
    """
    query_lower = query.lower()
    
    for param in jsdoc.get('params', []):
        if (query_lower in param.get('name', '').lower() or
            query_lower in param.get('description', '').lower() or
            query_lower in param.get('type', '').lower()):
            return param.get('name')
    
    return None


def match_in_returns(jsdoc: Dict, query: str) -> bool:
    """
    Comprueba si un término de búsqueda coincide en el return del JSDoc.
    
    Args:
        jsdoc: Diccionario JSDoc del componente
        query: Término a buscar (case-insensitive)
        
    Returns:
        True si el término se encuentra en description o type del return
        
    Examples:
        >>> jsdoc = {'returns': {'type': 'JSX.Element', 'description': 'Rendered button'}}
        >>> match_in_returns(jsdoc, 'jsx')
        True
    """
    returns = jsdoc.get('returns', {})
    query_lower = query.lower()
    
    return (query_lower in returns.get('description', '').lower() or
            query_lower in returns.get('type', '').lower())


def match_in_examples(jsdoc: Dict, query: str) -> bool:
    """
    Comprueba si un término de búsqueda coincide en los ejemplos del JSDoc.
    
    Args:
        jsdoc: Diccionario JSDoc del componente
        query: Término a buscar (case-insensitive)
        
    Returns:
        True si el término se encuentra en algún ejemplo
        
    Examples:
        >>> jsdoc = {'examples': ['<Button onClick={handleClick} />']}
        >>> match_in_examples(jsdoc, 'onclick')
        True
    """
    query_lower = query.lower()
    
    for example in jsdoc.get('examples', []):
        if query_lower in example.lower():
            return True
    
    return False


def search_in_jsdoc(
    components: List[Dict],
    query: str
) -> List[Tuple[Dict, str]]:
    """
    Busca un término en la documentación JSDoc de múltiples componentes.
    
    Busca en: descripción, parámetros, returns, y ejemplos.
    
    Args:
        components: Lista de componentes con JSDoc
        query: Término de búsqueda
        
    Returns:
        Lista de tuplas (componente, tipo_de_match)
        Donde tipo_de_match es uno de:
        - 'description'
        - 'param: <param_name>'
        - 'returns'
        - 'example'
        
    Examples:
        >>> components = [
        ...     {
        ...         'name': 'Button',
        ...         'jsdoc': {'description': 'A button component'}
        ...     },
        ...     {
        ...         'name': 'Link',
        ...         'jsdoc': {'description': 'A link element'}
        ...     }
        ... ]
        >>> matches = search_in_jsdoc(components, 'button')
        >>> len(matches)
        1
        >>> matches[0][1]
        'description'
    """
    matching = []
    query_lower = query.lower()
    
    for component in components:
        jsdoc = component.get('jsdoc')
        
        if not jsdoc:
            continue
        
        # Buscar en descripción
        if match_in_description(jsdoc, query):
            matching.append((component, 'description'))
            continue
        
        # Buscar en parámetros
        param_name = match_in_params(jsdoc, query)
        if param_name:
            matching.append((component, f'param: {param_name}'))
            continue
        
        # Buscar en returns
        if match_in_returns(jsdoc, query):
            matching.append((component, 'returns'))
            continue
        
        # Buscar en ejemplos
        if match_in_examples(jsdoc, query):
            matching.append((component, 'example'))
    
    return matching
