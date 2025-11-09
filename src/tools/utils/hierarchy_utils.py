"""
Utilidades para construir y formatear árboles de jerarquía de componentes.
"""

from typing import Dict, List, Any, Optional, Set


def build_dependency_tree(
    tree_data: Dict[str, Any],
    direction: str = 'down'
) -> Dict[str, Any]:
    """
    Construye un árbol de dependencias desde datos del repositorio.
    
    Args:
        tree_data: Datos del árbol desde DependencyRepository.get_dependency_tree()
        direction: 'down' (dependencias), 'up' (dependientes), 'both'
    
    Returns:
        Árbol estructurado con información adicional
    """
    if not tree_data:
        return {}
    
    # Agregar estadísticas al árbol
    stats = _calculate_tree_stats(tree_data)
    
    return {
        **tree_data,
        'stats': stats,
        'direction': direction
    }


def format_tree(
    tree: Dict[str, Any],
    max_depth: Optional[int] = None,
    show_external: bool = False
) -> str:
    """
    Formatea un árbol de dependencias en markdown ASCII.
    
    Args:
        tree: Árbol de dependencias
        max_depth: Profundidad máxima a mostrar (None = todo)
        show_external: Si mostrar dependencias externas
    
    Returns:
        String formateado en markdown
    """
    if not tree or 'component' not in tree:
        return "🌳 No hierarchy data available"
    
    component = tree.get('component', {})
    children = tree.get('children', [])
    direction = tree.get('direction', 'down')
    stats = tree.get('stats', {})
    
    # Header
    comp_name = component.get('name', 'Unknown')
    comp_type = component.get('component_type', 'component')
    comp_path = component.get('file_path', 'unknown')
    
    result = f"## 🌳 Component Hierarchy: {comp_name}\n\n"
    result += f"**Type:** {comp_type}  \n"
    result += f"**Path:** `{comp_path}`  \n"
    
    # Estadísticas
    if stats:
        total_deps = stats.get('total_dependencies', 0)
        total_dependents = stats.get('total_dependents', 0)
        max_tree_depth = stats.get('max_depth', 0)
        has_circular = stats.get('has_circular', False)
        
        result += f"\n**Statistics:**\n"
        result += f"- Total dependencies: {total_deps}\n"
        result += f"- Total dependents: {total_dependents}\n"
        result += f"- Max depth: {max_tree_depth}\n"
        if has_circular:
            result += f"- ⚠️ Circular dependencies detected\n"
    
    result += "\n"
    
    # Dirección
    if direction == 'down':
        result += "### 📥 Dependencies (Components this uses)\n\n"
    elif direction == 'up':
        result += "### 📤 Dependents (Components that use this)\n\n"
    else:
        result += "### 🔄 Full Hierarchy (Dependencies & Dependents)\n\n"
    
    # Construir árbol visual
    if children:
        tree_lines = _build_tree_lines(children, prefix="", is_last=True, depth=0, max_depth=max_depth, show_external=show_external)
        result += "```\n"
        result += tree_lines
        result += "```\n"
    else:
        result += "*No dependencies found*\n"
    
    return result


def _build_tree_lines(
    children: List[Dict[str, Any]],
    prefix: str = "",
    is_last: bool = True,
    depth: int = 0,
    max_depth: Optional[int] = None,
    show_external: bool = False
) -> str:
    """
    Construye las líneas del árbol recursivamente.
    """
    if max_depth is not None and depth >= max_depth:
        return ""
    
    result = ""
    
    for i, child in enumerate(children):
        is_last_child = i == len(children) - 1
        child_component = child.get('component', {})
        child_name = child_component.get('name', 'Unknown')
        child_type = child_component.get('component_type', 'component')
        import_type = child.get('import_type', 'unknown')
        from_path = child.get('from_path', '')
        is_circular = child.get('circular', False)
        max_depth_reached = child.get('max_depth_reached', False)
        
        # Icono según tipo
        icons = {
            'page': '📄',
            'component': '🧩',
            'layout': '📐',
            'hook': '🪝',
        }
        icon = icons.get(child_type, '📦')
        
        # Prefijo para esta línea
        connector = "└── " if is_last_child else "├── "
        current_prefix = prefix + connector
        
        # Información adicional
        info_parts = []
        if import_type != 'unknown':
            info_parts.append(f"({import_type})")
        if from_path:
            info_parts.append(f"from {from_path}")
        info_str = " ".join(info_parts)
        
        # Marcar circular o max depth
        if is_circular:
            child_name += " ⚠️ [CIRCULAR]"
        elif max_depth_reached:
            child_name += " ..."
        
        result += f"{current_prefix}{icon} {child_name}"
        if info_str:
            result += f" {info_str}"
        result += "\n"
        
        # Recursión para hijos
        child_children = child.get('children', [])
        if child_children:
            next_prefix = prefix + ("    " if is_last_child else "│   ")
            result += _build_tree_lines(
                child_children,
                prefix=next_prefix,
                is_last=is_last_child,
                depth=depth + 1,
                max_depth=max_depth,
                show_external=show_external
            )
    
    return result


def detect_circular_dependencies(tree: Dict[str, Any]) -> List[List[str]]:
    """
    Detecta dependencias circulares en el árbol.
    
    Args:
        tree: Árbol de dependencias
    
    Returns:
        Lista de ciclos detectados (cada ciclo es una lista de nombres de componentes)
    """
    cycles = []
    visited = set()
    path = []
    
    def _detect(node: Dict[str, Any], path_set: Set[str]):
        component = node.get('component', {})
        comp_name = component.get('name', '')
        
        if comp_name in path_set:
            # Ciclo detectado
            cycle_start = path.index(comp_name)
            cycle = path[cycle_start:] + [comp_name]
            cycles.append(cycle)
            return
        
        if comp_name in visited:
            return
        
        visited.add(comp_name)
        path.append(comp_name)
        path_set.add(comp_name)
        
        for child in node.get('children', []):
            _detect(child, path_set.copy())
        
        path.pop()
        path_set.discard(comp_name)
    
    if tree:
        _detect(tree, set())
    
    return cycles


def _calculate_tree_stats(tree: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula estadísticas del árbol.
    """
    def _count_nodes(node: Dict[str, Any], direction: str) -> tuple[int, int, bool]:
        """
        Cuenta nodos y detecta circularidad.
        Retorna: (count, max_depth, has_circular)
        """
        if node.get('circular', False):
            return (0, 0, True)
        
        count = 1
        max_depth = 0
        has_circular = False
        
        for child in node.get('children', []):
            child_count, child_depth, child_circular = _count_nodes(child, direction)
            count += child_count
            max_depth = max(max_depth, child_depth + 1)
            has_circular = has_circular or child_circular
        
        return (count, max_depth, has_circular)
    
    total_deps = 0
    total_dependents = 0
    max_depth = 0
    has_circular = False
    
    # Contar según dirección
    direction = tree.get('direction', 'down')
    
    if direction in ['down', 'both']:
        count, depth, circular = _count_nodes(tree, 'down')
        total_deps = count - 1  # Excluir el nodo raíz
        max_depth = max(max_depth, depth)
        has_circular = has_circular or circular
    
    if direction in ['up', 'both']:
        count, depth, circular = _count_nodes(tree, 'up')
        total_dependents = count - 1  # Excluir el nodo raíz
        max_depth = max(max_depth, depth)
        has_circular = has_circular or circular
    
    return {
        'total_dependencies': total_deps,
        'total_dependents': total_dependents,
        'max_depth': max_depth,
        'has_circular': has_circular
    }

