"""
Utilidad para resolver rutas de import a componentes indexados en la base de datos.
"""

import os
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path


# Librerías externas comunes que deben ser filtradas
EXTERNAL_LIBRARIES = {
    'react', 'react-dom', 'react-router', 'react-router-dom',
    'prop-types', 'classnames', 'lodash', 'moment', 'date-fns',
    'axios', 'fetch', 'redux', 'react-redux', 'zustand',
    'react-query', '@tanstack/react-query', 'swr',
    'styled-components', 'emotion', '@emotion/react',
    'next', 'gatsby', 'remix', 'vite', 'webpack',
    '@testing-library', 'jest', 'vitest', 'cypress',
    'typescript', '@types/', 'tslib',
}


def is_external_import(from_path: str) -> bool:
    """
    Determina si un import es externo (librería npm) o interno del proyecto.
    
    Args:
        from_path: Ruta del import (ej: './components', 'react', '@components/Button')
    
    Returns:
        True si es librería externa, False si es interno
    """
    # Imports relativos siempre son internos
    if from_path.startswith('./') or from_path.startswith('../'):
        return False
    
    # Imports absolutos que empiezan con @ pueden ser internos o externos
    if from_path.startswith('@'):
        # Verificar si es una librería conocida
        path_lower = from_path.lower()
        for lib in EXTERNAL_LIBRARIES:
            if path_lower.startswith(lib.lower()):
                return True
        # Si no es conocido, asumir que es interno (alias del proyecto)
        return False
    
    # Verificar si es una librería conocida
    path_parts = from_path.split('/')
    first_part = path_parts[0].lower()
    
    # Si empieza con @types/ es externo
    if first_part.startswith('@types/'):
        return True
    
    # Verificar contra lista de librerías externas
    return first_part in EXTERNAL_LIBRARIES


def resolve_relative_path(from_path: str, current_file_path: str) -> str:
    """
    Resuelve una ruta relativa a una ruta absoluta basada en el archivo actual.
    También resuelve alias comunes como @/ a src/.
    
    Args:
        from_path: Ruta relativa del import (ej: './components', '../utils', '@/components/shared/page-header')
        current_file_path: Ruta del archivo actual (ej: 'src/pages/HomePage.tsx')
    
    Returns:
        Ruta absoluta resuelta (ej: 'src/components', 'src/utils', 'src/components/shared/page-header')
    """
    # Resolver alias @/ a src/ (convención común en proyectos React/Next.js)
    if from_path.startswith('@/'):
        # Reemplazar @/ con src/
        resolved = 'src/' + from_path[2:]
        resolved = resolved.replace('\\', '/')
        return resolved
    
    # Resolver alias @components/ a src/components/ (variante)
    if from_path.startswith('@components/'):
        resolved = 'src/components/' + from_path[len('@components/'):]
        resolved = resolved.replace('\\', '/')
        return resolved
    
    # Rutas relativas
    if not from_path.startswith('./') and not from_path.startswith('../'):
        return from_path
    
    # Obtener directorio del archivo actual
    current_dir = os.path.dirname(current_file_path)
    
    # Resolver ruta relativa
    resolved = os.path.normpath(os.path.join(current_dir, from_path))
    
    # Normalizar separadores
    resolved = resolved.replace('\\', '/')
    
    return resolved


def normalize_path(path: str) -> str:
    """
    Normaliza una ruta para comparación.
    
    - Remueve extensiones (.tsx, .ts, .jsx, .js)
    - Normaliza separadores
    - Remueve prefijo src/ si existe
    
    Args:
        path: Ruta a normalizar
    
    Returns:
        Ruta normalizada
    """
    # Remover extensiones
    for ext in ['.tsx', '.ts', '.jsx', '.js']:
        if path.endswith(ext):
            path = path[:-len(ext)]
            break
    
    # Normalizar separadores
    path = path.replace('\\', '/')
    
    # Remover prefijo src/ si existe
    if path.startswith('src/'):
        path = path[4:]
    
    return path


def resolve_imports_to_components(
    component_imports: List[Dict[str, Any]],
    project_id: str,
    current_file_path: str,
    component_name: str,
    db_session
) -> List[Dict[str, Any]]:
    """
    Resuelve imports estructurados a componentes indexados en la base de datos.
    
    Args:
        component_imports: Lista de imports estructurados del parser
        project_id: ID del proyecto
        current_file_path: Ruta del archivo actual
        component_name: Nombre del componente actual
        db_session: Sesión de SQLAlchemy
    
    Returns:
        Lista de dependencias resueltas:
        [
            {
                'depends_on_component_id': 123,  # None si es externo
                'depends_on_name': 'Button',
                'from_path': './components',
                'import_type': 'named',
                'is_external': False
            },
            ...
        ]
    """
    from src.models import Component
    
    dependencies = []
    
    for imp in component_imports:
        from_path = imp['from_path']
        imported_names = imp.get('imported_names', [])
        import_type = imp.get('import_type', 'named')
        
        # Determinar si es externo
        is_external = is_external_import(from_path)
        
        # Si es externo, guardar sin resolver componente
        if is_external:
            for name in imported_names:
                dependencies.append({
                    'depends_on_component_id': None,
                    'depends_on_name': name,
                    'from_path': from_path,
                    'import_type': import_type,
                    'is_external': True
                })
            continue
        
        # Resolver ruta relativa a absoluta
        resolved_path = resolve_relative_path(from_path, current_file_path)
        normalized_resolved = normalize_path(resolved_path)
        
        # ============================================
        # NUEVO: Intentar resolver via barrel export
        # ============================================
        from src.models import BarrelExport
        
        barrel = db_session.query(BarrelExport).filter(
            BarrelExport.project_id == project_id,
            BarrelExport.directory_path == normalized_resolved
        ).first()
        
        if barrel and barrel.exported_component_id:
            dependencies.append({
                'depends_on_component_id': barrel.exported_component_id,
                'depends_on_name': imported_names[0] if imported_names else barrel.exported_name,
                'from_path': from_path,
                'import_type': import_type,
                'is_external': False
            })
            continue  # Import resuelto, siguiente
        
        # Si no se resolvió via barrel export, continuar con lógica existente
        # ============================================
        
        # Buscar componentes que coincidan con la ruta
        # Intentar diferentes variaciones de la ruta
        search_paths = [
            normalized_resolved,
            resolved_path,
            from_path,
        ]
        
        # Si la ruta resuelta tiene prefijo src/, también buscar sin él
        if normalized_resolved.startswith('src/'):
            search_paths.append(normalized_resolved[4:])
        
        # Si la ruta original tenía alias @/, también buscar variaciones
        if from_path.startswith('@/'):
            # Remover @/ y buscar variaciones
            path_without_alias = from_path[2:]
            search_paths.extend([
                path_without_alias,
                normalize_path(path_without_alias),
                'src/' + path_without_alias,
                normalize_path('src/' + path_without_alias),
            ])
        
        # También buscar por nombre de archivo si es default import
        if import_type == 'default' and imported_names:
            default_name = imported_names[0]
            # Buscar componente con ese nombre en el proyecto
            component_match = db_session.query(Component).filter(
                Component.project_id == project_id,
                Component.name == default_name
            ).first()
            
            if component_match:
                normalized_file_path = normalize_path(component_match.file_path)
                # Verificar si la ruta coincide aproximadamente
                if normalized_file_path == normalized_resolved or \
                   normalized_file_path.endswith(normalized_resolved) or \
                   normalized_resolved.endswith(normalized_file_path):
                    dependencies.append({
                        'depends_on_component_id': component_match.id,
                        'depends_on_name': default_name,
                        'from_path': from_path,
                        'import_type': import_type,
                        'is_external': False
                    })
                    continue
        
        # Buscar componentes por file_path que coincida
        found_components = []
        seen_component_ids = set()  # Evitar duplicados
        
        for search_path in search_paths:
            # Buscar coincidencia exacta o parcial
            matches = db_session.query(Component).filter(
                Component.project_id == project_id
            ).all()
            
            for comp in matches:
                # Evitar duplicados
                if comp.id in seen_component_ids:
                    continue
                
                normalized_comp_path = normalize_path(comp.file_path)
                
                # Coincidencia exacta
                if normalized_comp_path == search_path:
                    found_components.append(comp)
                    seen_component_ids.add(comp.id)
                # Coincidencia parcial (el import apunta a un directorio)
                elif search_path.endswith('/') and normalized_comp_path.startswith(search_path):
                    found_components.append(comp)
                    seen_component_ids.add(comp.id)
                # Coincidencia inversa (el import es más específico)
                elif normalized_comp_path.endswith(search_path):
                    found_components.append(comp)
                    seen_component_ids.add(comp.id)
                # Coincidencia por nombre de archivo (sin extensión)
                elif not search_path.endswith('/'):
                    # Extraer nombre de archivo del search_path
                    search_filename = search_path.split('/')[-1]
                    comp_filename = normalized_comp_path.split('/')[-1]
                    if search_filename == comp_filename:
                        found_components.append(comp)
                        seen_component_ids.add(comp.id)
        
        # Para named imports, buscar componentes por nombre
        # Si no se encontró por ruta, buscar por nombre considerando la ruta del import
        if import_type in ['named', 'mixed'] and not found_components:
            for name in imported_names:
                # Buscar componente con ese nombre en el proyecto
                all_matches = db_session.query(Component).filter(
                    Component.project_id == project_id,
                    Component.name == name
                ).all()
                
                if not all_matches:
                    continue
                
                # Si hay múltiples componentes con el mismo nombre, intentar filtrar por ruta
                if len(all_matches) > 1:
                    # Intentar encontrar el que mejor coincida con la ruta del import
                    best_match = None
                    best_score = 0
                    
                    # Normalizar la ruta del import para comparación
                    import_path_normalized = normalize_path(resolved_path)
                    # Extraer partes relevantes de la ruta (ej: 'components/shared/page-header' -> 'components/shared')
                    import_path_parts = [p for p in import_path_normalized.split('/') if p]
                    
                    for comp in all_matches:
                        comp_path_normalized = normalize_path(comp.file_path)
                        comp_path_parts = [p for p in comp_path_normalized.split('/') if p]
                        
                        # Calcular score de coincidencia
                        score = 0
                        # Coincidencia exacta de ruta completa
                        if comp_path_normalized == import_path_normalized:
                            score = 100
                        # Coincidencia de partes de ruta
                        elif import_path_parts and comp_path_parts:
                            # Contar partes coincidentes desde el final
                            matching_parts = 0
                            min_len = min(len(import_path_parts), len(comp_path_parts))
                            for i in range(1, min_len + 1):
                                if import_path_parts[-i] == comp_path_parts[-i]:
                                    matching_parts += 1
                                else:
                                    break
                            score = matching_parts * 10
                        
                        if score > best_score:
                            best_score = score
                            best_match = comp
                    
                    if best_match:
                        found_components.append(best_match)
                    else:
                        # Si no hay buena coincidencia, usar el primero
                        found_components.append(all_matches[0])
                else:
                    # Solo hay un componente con ese nombre
                    found_components.append(all_matches[0])
        
        # Crear dependencias para cada componente encontrado
        if found_components:
            for comp in found_components:
                # Encontrar el nombre importado que corresponde
                matching_name = None
                for name in imported_names:
                    if comp.name == name:
                        matching_name = name
                        break
                
                if not matching_name and imported_names:
                    matching_name = imported_names[0]  # Usar el primero como fallback
                elif not matching_name:
                    matching_name = comp.name
                
                dependencies.append({
                    'depends_on_component_id': comp.id,
                    'depends_on_name': matching_name,
                    'from_path': from_path,
                    'import_type': import_type,
                    'is_external': False
                })
        else:
            # No se encontró componente, pero guardar la información del import
            for name in imported_names:
                dependencies.append({
                    'depends_on_component_id': None,
                    'depends_on_name': name,
                    'from_path': from_path,
                    'import_type': import_type,
                    'is_external': False  # Es interno pero no encontrado
                })
    
    return dependencies

