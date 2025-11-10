"""
Parser para barrel exports (index.js/index.ts).
Analiza archivos index que re-exportan componentes de otros archivos en el mismo directorio.
"""

import os
import re
from typing import Optional, Dict, Any, List
from pathlib import Path

# Directorios a excluir del indexado de barrel exports (no son componentes)
EXCLUDE_BARREL_PATHS = [
    'payments/core/methods',
    'payments/core/factories',
    'payments/core/engines',
    'utils/engines',
    'core/factories',
]


def resolve_index_export(index_file_path: str) -> Optional[Dict[str, Any]]:
    """
    Parsea un archivo index.js/index.ts y retorna información del export.
    
    Patrones soportados:
    1. import X from './File'; export default X;
    2. export { default } from './File';
    3. export { default as X } from './File';
    4. export { X as default } from './File';
    5. export default from './File';  (no estándar pero usado)
    
    Args:
        index_file_path: Ruta completa al archivo index.js/ts
        
    Returns:
        Dict con:
        - exported_name: Nombre del componente exportado
        - source_file: Ruta relativa al archivo fuente (ej: './CheckoutContainer')
        - export_type: Tipo de export ('default', 'named')
        - is_container: Si el nombre sugiere que es un container
        
        None si no se puede parsear o no es un barrel export válido
    """
    if not os.path.exists(index_file_path):
        return None
        
    try:
        with open(index_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {index_file_path}: {e}")
        return None
    
    # Normalizar el contenido (remover comentarios de línea)
    content = re.sub(r'//.*$', '', content, flags=re.MULTILINE)
    # Remover comentarios de bloque
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    
    # Patrón 1: import X from './File'; ... export default X;
    # Captura: import CheckoutContainer from './CheckoutContainer';
    #          export default CheckoutContainer;
    pattern1 = r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"];?\s*.*?export\s+default\s+\1"
    match1 = re.search(pattern1, content, re.DOTALL)
    if match1:
        exported_name = match1.group(1)
        source_file = match1.group(2)
        return {
            'exported_name': exported_name,
            'source_file': source_file,
            'export_type': 'default',
            'is_container': _is_container_name(exported_name),
        }
    
    # Patrón 2: export { default } from './File';
    pattern2 = r"export\s+{\s*default\s*}\s+from\s+['\"]([^'\"]+)['\"]"
    match2 = re.search(pattern2, content)
    if match2:
        source_file = match2.group(1)
        # Inferir el nombre del archivo
        file_name = Path(source_file).stem
        return {
            'exported_name': file_name,
            'source_file': source_file,
            'export_type': 'default',
            'is_container': _is_container_name(file_name),
        }
    
    # Patrón 3: export { X as default } from './File';
    pattern3 = r"export\s+{\s*(\w+)\s+as\s+default\s*}\s+from\s+['\"]([^'\"]+)['\"]"
    match3 = re.search(pattern3, content)
    if match3:
        exported_name = match3.group(1)
        source_file = match3.group(2)
        return {
            'exported_name': exported_name,
            'source_file': source_file,
            'export_type': 'default',
            'is_container': _is_container_name(exported_name),
        }
    
    # Patrón 4: export { default as X } from './File';
    pattern4 = r"export\s+{\s*default\s+as\s+(\w+)\s*}\s+from\s+['\"]([^'\"]+)['\"]"
    match4 = re.search(pattern4, content)
    if match4:
        exported_name = match4.group(1)
        source_file = match4.group(2)
        return {
            'exported_name': exported_name,
            'source_file': source_file,
            'export_type': 'default',
            'is_container': _is_container_name(exported_name),
        }
    
    # Patrón 5: export default from './File'; (sintaxis no estándar pero puede aparecer)
    # O simplemente: export default X; donde X fue importado antes
    pattern5 = r"export\s+default\s+from\s+['\"]([^'\"]+)['\"]"
    match5 = re.search(pattern5, content)
    if match5:
        source_file = match5.group(1)
        file_name = Path(source_file).stem
        return {
            'exported_name': file_name,
            'source_file': source_file,
            'export_type': 'default',
            'is_container': _is_container_name(file_name),
        }
    
    # Si no se encontró ningún patrón válido
    return None


def _is_container_name(name: str) -> bool:
    """
    Determina si un nombre sugiere que es un container/HOC.
    
    Args:
        name: Nombre del componente/archivo
        
    Returns:
        True si parece ser un container
    """
    if not name:
        return False
    
    name_lower = name.lower()
    container_patterns = [
        'container',
        'connected',
        'wrapper',
        'hoc',
        'enhanced',
        'with',  # HOCs suelen empezar con 'with'
    ]
    
    return any(pattern in name_lower for pattern in container_patterns)


def parse_component_imports(file_path: str) -> List[Dict[str, str]]:
    """
    Parsea un archivo JS/TS y extrae imports de componentes (no de librerías).
    
    Args:
        file_path: Ruta al archivo a parsear
    
    Returns:
        Lista de dicts con 'name' y 'path' de cada import
    """
    imports = []
    
    if not os.path.exists(file_path):
        return imports
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception:
        return imports
    
    # Patrones de import
    patterns = [
        # import Component from 'path'
        r"import\s+(\w+)\s+from\s+['\"]([^'\"]+)['\"]",
        # import { Component } from 'path'  (tomamos el primer named import)
        r"import\s+\{\s*(\w+)(?:\s+as\s+\w+)?\s*(?:,|}).*from\s+['\"]([^'\"]+)['\"]",
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, content, re.MULTILINE)
        for match in matches:
            if len(match) == 2:
                name, path = match
                imports.append({'name': name, 'path': path})
    
    return imports


def filter_component_imports(imports: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """
    Filtra imports para quedarse solo con posibles componentes.
    
    Excluye librerías, utilities, actions, constants, hooks.
    """
    LIBRARY_PREFIXES = [
        'react', 'redux', 'prop-types', '@', 'lodash', 'axios', 'moment',
        'react-router', 'react-dom', 'styled-components', '@reservamos'
    ]
    
    NON_COMPONENT_PATTERNS = [
        'actions', 'utils', 'constants', 'helpers', 'services',
        'api', 'config', 'metrics', 'payments/core', 'hooks/use'
    ]
    
    filtered = []
    
    for imp in imports:
        path = imp['path']
        name = imp['name']
        
        # Excluir librerías
        if any(path.startswith(lib) for lib in LIBRARY_PREFIXES):
            continue
        
        # Excluir utilities
        if any(pattern in path.lower() for pattern in NON_COMPONENT_PATTERNS):
            continue
        
        # Excluir hooks (pero NO HOCs como withRouter)
        if name.startswith('use') and len(name) > 3 and name[3].isupper():
            continue
        
        # El resto son posibles componentes
        filtered.append(imp)
    
    return filtered


def resolve_relative_import_path(
    import_path: str,
    from_file: str,
    project_root: str
) -> str:
    """
    Resuelve una ruta de import relativa a ruta relativa del proyecto.
    
    Args:
        import_path: '../../../ui/atoms/Component'
        from_file: '/full/path/src/components/search/Container.js'
        project_root: '/full/path'
    
    Returns:
        'src/ui/atoms/Component'
    """
    # Directorio del archivo que hace el import
    from_dir = os.path.dirname(from_file)
    
    # Resolver la ruta relativa
    absolute_path = os.path.normpath(os.path.join(from_dir, import_path))
    
    # Convertir a relativa del proyecto
    try:
        relative_path = os.path.relpath(absolute_path, project_root)
    except ValueError:
        # En Windows, si están en diferentes drives
        relative_path = absolute_path
    
    return relative_path


def resolve_alias_import_path(
    import_path: str,
    project_aliases: Dict[str, str],
    src_dir: str = 'src'
) -> Optional[str]:
    """
    Resuelve imports con alias usando aliases detectados.
    
    Args:
        import_path: 'utils/helper' o '@/components/Button'
        project_aliases: Dict de aliases detectados del proyecto
        src_dir: 'src' (directorio donde están los archivos fuente)
    
    Returns:
        'src/utils/helper' o 'src/components/Button', None si no se resolvió
    """
    # Si hay aliases configurados, intentar resolver con ellos primero
    if project_aliases:
        # Intentar match exacto primero
        if import_path in project_aliases:
            return project_aliases[import_path]
        
        # Intentar match con prefijo (para aliases con /)
        for alias_key, alias_path in project_aliases.items():
            if import_path.startswith(alias_key):
                # Reemplazar el alias con la ruta real
                resolved = import_path.replace(alias_key, alias_path, 1)
                return resolved
    
    # Fallback: Si no tiene ./ al inicio y no es una librería, asumir src/
    if not import_path.startswith('.') and not import_path.startswith('@'):
        # Verificar que no sea una librería conocida
        KNOWN_LIBRARIES = ['react', 'redux', 'lodash', 'axios', 'moment', 'react-dom', 'react-router']
        if not any(import_path.startswith(lib) for lib in KNOWN_LIBRARIES):
            return f'{src_dir}/{import_path}'
    
    return None


def find_component_by_import_path(
    import_path: str,
    db_session,
    project_id: str
) -> Optional[int]:
    """
    Busca un componente en la BD por su ruta de archivo.
    Intenta con diferentes extensiones (.js, .jsx, .ts, .tsx).
    
    Args:
        import_path: 'src/ui/atoms/Component' (sin extensión)
        db_session: Sesión de SQLAlchemy
        project_id: ID del proyecto
    
    Returns:
        component.id si se encuentra, None si no
    """
    from src.models import Component
    
    extensions = ['.js', '.jsx', '.ts', '.tsx', '/index.js', '/index.jsx', '/index.ts', '/index.tsx']
    
    for ext in extensions:
        full_path = import_path + ext
        
        component = db_session.query(Component).filter(
            Component.project_id == project_id,
            Component.file_path == full_path
        ).first()
        
        if component:
            return component.id
    
    return None


def find_wrapped_component(
    container_file_path: str, 
    project_id: str, 
    db_session
) -> Optional[int]:
    """
    Busca el componente envuelto por un container.
    Usa Component.container_file_path para encontrar el componente original.
    
    Args:
        container_file_path: Ruta normalizada del archivo container
        project_id: ID del proyecto
        db_session: Sesión de base de datos
        
    Returns:
        ID del componente envuelto, o None si no se encuentra
    """
    from src.models import Component
    
    # Buscar componente que tiene este container
    component = db_session.query(Component).filter(
        Component.project_id == project_id,
        Component.container_file_path == container_file_path
    ).first()
    
    if component:
        return component.id
    
    return None


def resolve_barrel_component(
    source_file_path: str,
    is_container: bool,
    directory_path: str,
    project_id: str,
    db_session,
    repo_path: str = None,
    project_aliases: Dict[str, str] = None
) -> Optional[int]:
    """
    Resuelve qué componente ID corresponde al barrel export.
    
    Nueva lógica mejorada:
    1. Si is_container=True:
       a. Parsear imports del container
       b. Filtrar imports para quedarse con componentes
       c. Resolver rutas (relativos + aliases)
       d. Buscar componente en BD
       e. Si no se encuentra, buscar "self-component"
    2. Si no, buscar componente directamente en source_file_path
    
    Args:
        source_file_path: Ruta relativa del archivo fuente (ej: './CheckoutContainer')
        is_container: Si el archivo es un container
        directory_path: Directorio del barrel export (para resolver rutas relativas)
        project_id: ID del proyecto
        db_session: Sesión de base de datos
        repo_path: Ruta del repositorio clonado (para resolver imports)
        project_aliases: Dict de aliases detectados del proyecto
        
    Returns:
        ID del componente, o None si no se encuentra
    """
    from src.models import Component
    
    # Remover './' del inicio si existe
    clean_source = source_file_path.lstrip('./')
    
    if is_container and repo_path:
        # === NUEVA LÓGICA: Parser de imports ===
        # Construir ruta completa al container
        for ext in ['.js', '.jsx', '.ts', '.tsx']:
            container_full_path = os.path.join(repo_path, directory_path, clean_source + ext)
            
            if not os.path.exists(container_full_path):
                continue
            
            # Parsear imports del container
            imports = parse_component_imports(container_full_path)
            filtered_imports = filter_component_imports(imports)
            
            # Intentar resolver cada import
            for imp in filtered_imports:
                import_path = imp['path']
                
                resolved_path = None
                
                # Fase 1: Imports relativos
                if import_path.startswith('.'):
                    resolved_path = resolve_relative_import_path(
                        import_path,
                        container_full_path,
                        repo_path
                    )
                
                # Fase 2: Imports con alias
                elif project_aliases:
                    resolved_path = resolve_alias_import_path(
                        import_path,
                        project_aliases
                    )
                
                # Si se resolvió el path, buscar en BD
                if resolved_path:
                    component_id = find_component_by_import_path(
                        resolved_path,
                        db_session,
                        project_id
                    )
                    
                    if component_id:
                        return component_id
            
            # Si no se encontró ningún componente en los imports,
            # intentar buscar "self-component" (el container ES el componente)
            
            # Buscar componente con la misma ruta que el container
            full_path = os.path.join(directory_path, clean_source + ext)
            component = db_session.query(Component).filter(
                Component.project_id == project_id,
                Component.file_path == full_path
            ).first()
            
            if component:
                return component.id
            
            # También buscar por container_file_path
            component = db_session.query(Component).filter(
                Component.project_id == project_id,
                Component.container_file_path == full_path
            ).first()
            
            if component:
                return component.id
    
    # === LÓGICA ORIGINAL (fallback) ===
    # Si no es container o no se proporcionó repo_path
    full_path_base = f"{directory_path}/{clean_source}"
    possible_extensions = ['.js', '.jsx', '.ts', '.tsx']
    
    for ext in possible_extensions:
        full_path = full_path_base + ext
        
        if is_container:
            # Buscar componente que tiene este container
            component = db_session.query(Component).filter(
                Component.project_id == project_id,
                Component.container_file_path == full_path
            ).first()
            
            if component:
                return component.id
        else:
            # Buscar componente directamente
            component = db_session.query(Component).filter(
                Component.project_id == project_id,
                Component.file_path == full_path
            ).first()
            
            if component:
                return component.id
    
    return None


def get_directory_from_index_path(index_file_path: str) -> str:
    """
    Obtiene el directorio normalizado de un archivo index.
    
    Args:
        index_file_path: Ruta completa al archivo index (ej: /repo/components/Checkout/index.js)
        
    Returns:
        Directorio normalizado (ej: components/Checkout)
    """
    from src.utils.import_resolver import normalize_path
    
    # Obtener el directorio padre del index.js
    directory = os.path.dirname(index_file_path)
    
    # Normalizar (remover prefijos de repo, etc.)
    return normalize_path(directory)

