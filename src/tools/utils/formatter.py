"""
Utilidades para formateo de componentes y generación de rutas de importación.
"""

from typing import Dict, Optional


def generate_import_path(file_path: str) -> str:
    """
    Genera la ruta de import correcta para un componente desde su file_path.
    
    Realiza las siguientes transformaciones:
    1. Remueve extensiones (.tsx, .jsx)
    2. Remueve prefijo 'src/' si existe
    3. Agrega './' al inicio si no tiene prefix de módulo
    
    Args:
        file_path: Ruta del archivo (ej: 'src/components/Button.tsx')
        
    Returns:
        Ruta de import válida (ej: './components/Button')
        
    Examples:
        >>> generate_import_path('src/components/Button.tsx')
        './components/Button'
        
        >>> generate_import_path('@ui/components/Card.jsx')
        '@ui/components/Card'
        
        >>> generate_import_path('hooks/useAuth.ts')
        './hooks/useAuth'
    """
    # Remover extensión
    import_path = file_path.replace('.tsx', '').replace('.jsx', '')
    
    # Si empieza con src/, removerlo
    if import_path.startswith('src/'):
        import_path = import_path[4:]
    
    # Agregar ./ al inicio si no tiene prefix de módulo
    if not import_path.startswith('./') and not import_path.startswith('@'):
        import_path = './' + import_path
    
    return import_path


def format_component_entry(
    component: Dict,
    show_new_badge: bool = False,
    show_description: bool = False
) -> str:
    """
    Formatea una entrada de componente para output legible.
    
    Genera una línea formateada con información del componente,
    útil para listas y catálogos.
    
    Args:
        component: Diccionario del componente
        show_new_badge: Si mostrar badge 🆕 para componentes nuevos
        show_description: Si incluir descripción del componente
        
    Returns:
        String formateado para mostrar, ej: "- **Button** - `src/components/Button.tsx` 🆕"
        
    Examples:
        >>> comp = {
        ...     'name': 'Button',
        ...     'file_path': 'src/components/Button.tsx',
        ...     'description': 'Reusable button',
        ...     'created_at': '2024-10-28T10:30:00Z'
        ... }
        >>> format_component_entry(comp, show_new_badge=True)
        '- **Button** - `src/components/Button.tsx` 🆕'
    """
    from .component_utils import is_new_component
    
    name = component.get('name', 'Unknown')
    file_path = component.get('file_path', 'unknown')
    
    entry = f"- **{name}** - `{file_path}`"
    
    if show_new_badge and is_new_component(component):
        entry += " 🆕"
    
    if show_description and component.get('description'):
        entry += f"\n  {component['description']}"
    
    return entry


def format_component_with_details(
    component: Dict,
    include_props: bool = True,
    include_hooks: bool = True,
    include_type: bool = True,
    max_items: int = 5
) -> str:
    """
    Formatea un componente con detalles adicionales en líneas múltiples.
    
    Genera un formato más elaborado incluyendo props, hooks, y tipo,
    útil para resultados de búsqueda detallados.
    
    Args:
        component: Diccionario del componente
        include_props: Si incluir props en la salida
        include_hooks: Si incluir hooks en la salida
        include_type: Si incluir tipo de componente
        max_items: Máximo número de items a mostrar por categoría
        
    Returns:
        String multilínea formateado
        
    Examples:
        >>> comp = {
        ...     'name': 'Button',
        ...     'file_path': 'src/components/Button.tsx',
        ...     'component_type': 'component',
        ...     'props': ['label', 'onClick', 'disabled'],
        ...     'native_hooks_used': ['useState']
        ... }
        >>> print(format_component_with_details(comp))
        **Button**
        - 📂 Path: `src/components/Button.tsx`
        - 🏷️  Type: component
        - 📦 Props: label, onClick, disabled
        - 🪝 Hooks: useState
    """
    from .output_formatter import format_list_with_more
    from .component_utils import get_all_hooks
    
    lines = []
    
    # Nombre
    lines.append(f"**{component.get('name', 'Unknown')}**")
    
    # Path
    lines.append(f"- 📂 Path: `{component.get('file_path', 'unknown')}`")
    
    # Type
    if include_type:
        comp_type = component.get('component_type', 'component')
        lines.append(f"- 🏷️  Type: {comp_type}")
    
    # Props
    if include_props and component.get('props'):
        props_str = format_list_with_more(component['props'], max_items)
        lines.append(f"- 📦 Props: {props_str}")
    
    # Hooks
    if include_hooks:
        all_hooks = get_all_hooks(component)
        if all_hooks:
            hooks_str = format_list_with_more(all_hooks, max_items)
            lines.append(f"- 🪝 Hooks: {hooks_str}")
    
    # Description
    if component.get('description'):
        lines.append(f"- 📝 Description: {component['description']}")
    
    return '\n'.join(lines)
