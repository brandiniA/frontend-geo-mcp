"""
Utilidades para formateo de componentes en markdown y navegación.
"""

from typing import Dict, List, Optional


# Iconos para tipos de componentes
COMPONENT_TYPE_ICONS = {
    'page': '📄',
    'component': '🧩',
    'layout': '📐',
    'hook': '🪝',
}


def get_component_type_icon(component_type: str) -> str:
    """
    Obtiene el icono para un tipo de componente.
    
    Args:
        component_type: Tipo de componente (page, component, layout, hook)
    
    Returns:
        Emoji icono para el tipo
    """
    return COMPONENT_TYPE_ICONS.get(component_type, '📦')


def format_jsdoc_section(jsdoc: Dict) -> str:
    """
    Formatea una sección completa de JSDoc en markdown.
    
    Incluye descripción, parámetros, returns, ejemplos, y metadata.
    
    Args:
        jsdoc: Diccionario con información JSDoc
    
    Returns:
        String formateado en markdown
    """
    response = ""
    
    # Descripción principal
    if jsdoc.get('description'):
        response += f"### 📝 Overview\n{jsdoc['description']}\n\n"
    
    # Parámetros
    if jsdoc.get('params'):
        response += "### 📥 Parameters\n"
        for param in jsdoc['params']:
            param_type = param.get('type', 'unknown')
            param_name = param.get('name', 'unknown')
            param_desc = param.get('description', '')
            
            if param_desc:
                response += f"- **`{param_name}`** (`{param_type}`): {param_desc}\n"
            else:
                response += f"- **`{param_name}`** (`{param_type}`)\n"
        response += "\n"
    
    # Returns
    if jsdoc.get('returns'):
        returns = jsdoc['returns']
        response += "### 📤 Returns\n"
        response += f"**Type:** `{returns.get('type', 'unknown')}`\n"
        if returns.get('description'):
            response += f"**Description:** {returns['description']}\n"
        response += "\n"
    
    # Ejemplos
    if jsdoc.get('examples'):
        response += "### 💡 Examples\n"
        for i, example in enumerate(jsdoc['examples'], 1):
            response += f"**Example {i}:**\n```tsx\n{example}\n```\n"
        response += "\n"
    
    # Información adicional
    if jsdoc.get('deprecated'):
        response += "⚠️ **DEPRECATED** - This component is deprecated\n\n"
    
    if jsdoc.get('author'):
        response += f"👤 **Author:** {jsdoc['author']}\n"
    
    if jsdoc.get('version'):
        response += f"📌 **Version:** {jsdoc['version']}\n"
    
    return response


def format_hooks_section(
    component: Dict,
    max_hooks: int = 10,
    show_native: bool = True,
    show_custom: bool = True
) -> str:
    """
    Formatea la sección de hooks de un componente.
    
    Muestra hooks nativos y custom separados con límites.
    
    Args:
        component: Diccionario del componente
        max_hooks: Máximo número de hooks a mostrar por tipo
        show_native: Si mostrar hooks nativos
        show_custom: Si mostrar hooks custom
    
    Returns:
        String formateado en markdown o string vacío si no hay hooks
    """
    native_hooks = component.get('native_hooks_used', [])
    custom_hooks = component.get('custom_hooks_used', [])
    
    if not (native_hooks or custom_hooks):
        return ""
    
    response = "### 🪝 Hooks Used\n"
    
    if show_native and native_hooks:
        response += "**Native Hooks:**\n"
        for hook in native_hooks[:max_hooks]:
            response += f"- `{hook}`\n"
        if len(native_hooks) > max_hooks:
            response += f"- ... and {len(native_hooks) - max_hooks} more\n"
        response += "\n"
    
    if show_custom and custom_hooks:
        response += "**Custom Hooks:**\n"
        for hook in custom_hooks[:max_hooks]:
            response += f"- `{hook}`\n"
        if len(custom_hooks) > max_hooks:
            response += f"- ... and {len(custom_hooks) - max_hooks} more\n"
        response += "\n"
    
    return response


def format_hooks_inline(
    component: Dict,
    max_items: int = 5
) -> tuple[str, str]:
    """
    Formatea hooks para mostrar inline (en una línea).
    
    Retorna dos strings separados: uno para hooks nativos y otro para custom.
    
    Args:
        component: Diccionario del componente
        max_items: Máximo número de hooks a mostrar
    
    Returns:
        Tupla (native_hooks_str, custom_hooks_str)
    """
    from .output_formatter import format_list_with_more
    
    native_hooks = component.get('native_hooks_used', [])
    custom_hooks = component.get('custom_hooks_used', [])
    
    native_str = format_list_with_more(native_hooks, max_items) if native_hooks else ""
    custom_str = format_list_with_more(custom_hooks, max_items) if custom_hooks else ""
    
    return native_str, custom_str


def format_components_by_type(
    components: List[Dict],
    show_new_badge: bool = True,
    max_per_type: Optional[int] = None
) -> str:
    """
    Formatea componentes agrupados por tipo.
    
    Args:
        components: Lista de componentes
        show_new_badge: Si mostrar badge 🆕 para componentes nuevos
        max_per_type: Máximo número de componentes a mostrar por tipo (None = todos)
    
    Returns:
        String formateado en markdown
    """
    from .component_utils import group_components_by_type, is_new_component
    
    if not components:
        return "📂 No components found"
    
    by_type = group_components_by_type(components)
    response = ""
    
    for comp_type, comps in sorted(by_type.items()):
        icon = get_component_type_icon(comp_type)
        response += f"### {icon} {comp_type.title()}s ({len(comps)})\n\n"
        
        # Limitar si se especifica
        comps_to_show = comps[:max_per_type] if max_per_type else comps
        remaining = len(comps) - len(comps_to_show) if max_per_type and len(comps) > max_per_type else 0
        
        for comp in sorted(comps_to_show, key=lambda x: x['name']):
            new_badge = " 🆕" if show_new_badge and is_new_component(comp) else ""
            response += f"- **{comp['name']}** - `{comp['file_path']}`{new_badge}\n"
        
        if remaining > 0:
            response += f"- ... and {remaining} more\n"
        
        response += "\n"
    
    return response


def format_component_summary(
    component: Dict,
    include_props: bool = True,
    include_hooks: bool = True,
    include_description: bool = True,
    include_import: bool = False,
    max_items: int = 5
) -> str:
    """
    Formatea un resumen de componente para resultados de búsqueda.
    
    Args:
        component: Diccionario del componente
        include_props: Si incluir props
        include_hooks: Si incluir hooks (inline)
        include_description: Si incluir descripción
        include_import: Si incluir statement de import
        max_items: Máximo número de items por categoría
    
    Returns:
        String formateado en markdown
    """
    from .output_formatter import format_list_with_more
    from .formatter import generate_import_path
    
    lines = []
    
    # Nombre
    lines.append(f"**{component.get('name', 'Unknown')}**")
    
    # Path y tipo
    lines.append(f"- 📂 Path: `{component.get('file_path', 'unknown')}`")
    lines.append(f"- 🏷️  Type: {component.get('component_type', 'unknown')}")
    
    # Props
    if include_props and component.get('props'):
        props_str = format_list_with_more(component['props'], max_items)
        lines.append(f"- 📦 Props: {props_str}")
    
    # Hooks (inline)
    if include_hooks:
        native_str, custom_str = format_hooks_inline(component, max_items)
        if native_str:
            lines.append(f"- 🪝 Native Hooks: {native_str}")
        if custom_str:
            lines.append(f"- 🎣 Custom Hooks: {custom_str}")
    
    # Descripción
    if include_description and component.get('description'):
        lines.append(f"- 📝 Description: {component['description']}")
    
    # Import
    if include_import:
        import_path = generate_import_path(component['file_path'])
        comp_name = component.get('name', 'Unknown')
        lines.append(f"- 🔗 Import: `import {{ {comp_name} }} from '{import_path}'`")
    
    return '\n'.join(lines)


def format_project_header(project: Optional[Dict], project_id: str) -> str:
    """
    Formatea el header de un proyecto para agrupación.
    
    Args:
        project: Diccionario del proyecto (opcional)
        project_id: ID del proyecto
    
    Returns:
        String formateado en markdown (ej: "### 🏢 PROJECT_NAME (type)")
    """
    if project:
        project_name = project.get('name', project_id)
        project_type = project.get('type', 'unknown')
        return f"### 🏢 {project_name.upper()} ({project_type})"
    else:
        return f"### 🏢 {project_id.upper()}"


def truncate_description(description: str, max_length: int = 100) -> str:
    """
    Trunca una descripción a un máximo de caracteres.
    
    Args:
        description: Descripción a truncar
        max_length: Longitud máxima
    
    Returns:
        Descripción truncada con "..." si es necesario
    """
    if not description:
        return ""
    
    if len(description) <= max_length:
        return description
    
    return description[:max_length] + "..."


def format_usage_example(
    component: Dict,
    include_props: bool = True,
    max_props: int = 3
) -> str:
    """
    Genera un ejemplo de uso básico para un componente.
    
    Args:
        component: Diccionario del componente
        include_props: Si incluir props en el ejemplo
        max_props: Máximo número de props a mostrar
    
    Returns:
        String formateado en markdown con código TSX
    """
    from .formatter import generate_import_path
    
    comp_name = component.get('name', 'Unknown')
    import_path = generate_import_path(component['file_path'])
    
    response = "### 💡 Basic Usage\n"
    response += "```tsx\n"
    response += f"import {{ {comp_name} }} from '{import_path}';\n\n"
    
    if include_props and component.get('props'):
        props = component['props'][:max_props]
        remaining = len(component['props']) - len(props)
        
        response += f"<{comp_name}\n"
        for prop in props:
            response += f"  {prop}={{/* value */}}\n"
        if remaining > 0:
            response += f"  // ... and {remaining} more props\n"
        response += "/>\n"
    else:
        response += f"<{comp_name} />\n"
    
    response += "```\n"
    
    return response

