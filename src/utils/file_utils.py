"""
Utilidades para operaciones de archivos y directorios.
"""

import os
from typing import List, Callable, Set, Tuple, Optional, Any
from pathlib import Path


# Extensiones de archivos React comunes
REACT_EXTENSIONS = ('.tsx', '.ts', '.jsx', '.js')

# Directorios base a ignorar (comunes para hooks y componentes)
BASE_IGNORE_DIRS = {'node_modules', '.git', '.next', 'dist', 'build', '.venv', 'venv'}

# Directorios adicionales a ignorar para componentes (no hooks)
COMPONENT_IGNORE_DIRS = {
    'constants', 'consts', 'const',
    'config', 'configs', 'configuration',
    'types', 'interfaces',
    'enums',
    '__tests__', 'tests', 'test',
    '.storybook',
    'vendor',
    'public',
    'static',
    'assets',
    'images',
    'icons',
    'logos',
    'fonts',
    'videos',
}


def filter_ignore_dirs(dirs: List[str], ignore_dirs: Set[str]) -> None:
    """
    Filtra directorios ignorados in-place.
    
    Modifica la lista `dirs` para excluir directorios que deben ser ignorados.
    Esto optimiza `os.walk()` para que no entre en esos directorios.
    
    Args:
        dirs: Lista de directorios (modificada in-place)
        ignore_dirs: Set de nombres de directorios a ignorar
    
    Example:
        for root, dirs, files in os.walk(repo_path):
            filter_ignore_dirs(dirs, BASE_IGNORE_DIRS)
            # Ahora os.walk no entrará en node_modules, .git, etc.
    """
    dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]


def read_file_safe(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    Lee un archivo de forma segura con manejo de errores.
    
    Args:
        file_path: Ruta al archivo
        encoding: Codificación del archivo (default: utf-8)
    
    Returns:
        Contenido del archivo o None si hay error
    
    Example:
        content = read_file_safe('src/components/Button.jsx')
        if content:
            # procesar contenido
    """
    try:
        with open(file_path, 'r', encoding=encoding, errors='ignore') as f:
            return f.read()
    except Exception:
        return None


def get_relative_path(file_path: str, base_path: str) -> str:
    """
    Obtiene la ruta relativa de un archivo respecto a una base.
    
    Args:
        file_path: Ruta absoluta del archivo
        base_path: Ruta base para calcular la relativa
    
    Returns:
        Ruta relativa del archivo
    
    Example:
        rel_path = get_relative_path('/tmp/repo/src/Button.jsx', '/tmp/repo')
        # 'src/Button.jsx'
    """
    return os.path.relpath(file_path, base_path)


def get_file_name_without_ext(file_path: str) -> str:
    """
    Obtiene el nombre del archivo sin extensión.
    
    Args:
        file_path: Ruta del archivo
    
    Returns:
        Nombre del archivo sin extensión
    
    Example:
        name = get_file_name_without_ext('hooks/useAuth.ts')
        # 'useAuth'
    """
    return os.path.splitext(os.path.basename(file_path))[0]


def scan_files(
    repo_path: str,
    file_filter: Callable[[str], bool],
    ignore_dirs: Optional[Set[str]] = None,
    process_file: Optional[Callable[[str, str], List]] = None,
    progress_callback: Optional[Callable[[int, str], None]] = None
) -> List:
    """
    Escanea archivos en un directorio recursivamente con filtros.
    
    Función genérica para escanear archivos que puede ser reutilizada
    tanto para hooks como para componentes.
    
    Args:
        repo_path: Ruta base del repositorio
        file_filter: Función que retorna True si el archivo debe procesarse
                    Recibe el nombre del archivo
        ignore_dirs: Set de directorios a ignorar (default: BASE_IGNORE_DIRS)
        process_file: Función opcional para procesar cada archivo
                    Recibe (file_path, relative_path) y retorna lista de resultados
                    Si no se proporciona, solo retorna las rutas relativas
    
    Returns:
        Lista de resultados (componentes, hooks, etc.)
    
    Example:
        def is_hook_file(filename):
            return filename.startswith('use') and filename.endswith(REACT_EXTENSIONS)
        
        def process_hook(content, relative_path):
            return parser.extract_hook_info(content, relative_path)
        
        hooks = scan_files(
            repo_path,
            file_filter=is_hook_file,
            process_file=process_hook
        )
    """
    if ignore_dirs is None:
        ignore_dirs = BASE_IGNORE_DIRS
    
    results = []
    files_processed = 0
    
    for root, dirs, files in os.walk(repo_path):
        # Filtrar directorios ignorados
        filter_ignore_dirs(dirs, ignore_dirs)
        
        for file in files:
            # Aplicar filtro de archivo
            if not file_filter(file):
                continue
            
            file_path = os.path.join(root, file)
            relative_path = get_relative_path(file_path, repo_path)
            
            # Si hay función de procesamiento, leer archivo y procesarlo
            if process_file:
                try:
                    content = read_file_safe(file_path)
                    if content:
                        parsed = process_file(content, relative_path)
                        results.extend(parsed)
                        files_processed += 1
                        
                        # Llamar callback de progreso cada 50 archivos o al final
                        if progress_callback and (files_processed % 50 == 0 or files_processed == 1):
                            progress_callback(files_processed, relative_path)
                except Exception as e:
                    print(f"⚠️  Error procesando {relative_path}: {str(e)}")
                    continue
            else:
                # Solo agregar la ruta si no hay procesamiento
                results.append(relative_path)
                files_processed += 1
                if progress_callback and files_processed % 50 == 0:
                    progress_callback(files_processed, relative_path)
    
    return results

