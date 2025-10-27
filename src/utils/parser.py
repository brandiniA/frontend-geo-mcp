"""
Parser de componentes React usando regex.
Extrae información de componentes sin necesidad de AST complejo.
"""

import re
from typing import List, Dict, Optional
from pathlib import Path


class ReactParser:
    """Parser para extraer información de componentes React usando regex."""
    
    # Patrones para detectar componentes
    COMPONENT_PATTERNS = [
        r'export\s+(?:default\s+)?(?:function|const)\s+(\w+)',
        r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>',
        r'function\s+(\w+)\s*\([^)]*\)',
    ]
    
    # Patrones para props
    PROPS_PATTERN = r'\((?:\s*{\s*([^}]+)\s*}|([^)]+))\)'
    
    # Patrones para hooks
    HOOKS_PATTERN = r'use[A-Z]\w+'
    
    # Patrones para imports
    IMPORT_PATTERN = r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]'
    
    # Patrones para exports
    EXPORT_PATTERN = r'export\s+(?:default\s+)?(?:function|const|class)\s+(\w+)'
    
    def extract_component_info(self, file_content: str, file_path: str) -> List[Dict]:
        """
        Extrae información de componentes de un archivo React.
        
        Args:
            file_content: Contenido del archivo
            file_path: Ruta del archivo
            
        Returns:
            Lista de diccionarios con información de componentes
        """
        components = []
        seen_components = set()
        
        # Extraer nombres de componentes
        for pattern in self.COMPONENT_PATTERNS:
            matches = re.finditer(pattern, file_content)
            for match in matches:
                component_name = match.group(1)
                
                # Evitar duplicados
                if component_name in seen_components:
                    continue
                
                # Filtrar nombres que no parecen componentes
                if not self._is_valid_component_name(component_name):
                    continue
                
                seen_components.add(component_name)
                
                component_info = {
                    'name': component_name,
                    'file_path': file_path,
                    'props': self._extract_props(file_content, component_name),
                    'hooks': self._extract_hooks(file_content),
                    'imports': self._extract_imports(file_content),
                    'exports': self._extract_exports(file_content),
                    'component_type': self._determine_type(file_path),
                    'description': self._extract_description(file_content, component_name),
                }
                
                components.append(component_info)
        
        return components
    
    def _is_valid_component_name(self, name: str) -> bool:
        """
        Verifica si un nombre es válido para un componente React.
        Los componentes React deben empezar con mayúscula.
        """
        if not name:
            return False
        
        # Debe empezar con mayúscula
        if not name[0].isupper():
            return False
        
        # No debe ser una palabra reservada común
        reserved = {'Component', 'React', 'Fragment', 'StrictMode'}
        if name in reserved:
            return False
        
        return True
    
    def _extract_props(self, content: str, component_name: str) -> List[str]:
        """Extrae props del componente."""
        props = []
        
        # Buscar patrón de props destructurados
        patterns = [
            rf'{component_name}\s*[=:]\s*\(?\s*{{\s*([^}}]+)\s*}}',
            rf'{component_name}\s*=\s*\([^)]*{{\s*([^}}]+)\s*}}',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                props_str = match.group(1)
                # Limpiar y separar props
                prop_items = [p.strip().split(':')[0].strip() for p in props_str.split(',')]
                props = [p for p in prop_items if p and not p.startswith('...')]
                break
        
        return props[:20]  # Limitar a 20 props
    
    def _extract_hooks(self, content: str) -> List[str]:
        """Extrae hooks utilizados."""
        hooks = list(set(re.findall(self.HOOKS_PATTERN, content)))
        return sorted(hooks)[:15]  # Limitar a 15 hooks
    
    def _extract_imports(self, content: str) -> List[str]:
        """Extrae imports."""
        imports = re.findall(self.IMPORT_PATTERN, content)
        # Filtrar imports relativos muy largos
        imports = [imp for imp in imports if len(imp) < 100]
        return imports[:10]  # Limitar a 10 para no saturar
    
    def _extract_exports(self, content: str) -> List[str]:
        """Extrae exports."""
        exports = list(set(re.findall(self.EXPORT_PATTERN, content)))
        return sorted(exports)[:10]
    
    def _determine_type(self, file_path: str) -> str:
        """Determina el tipo de componente basado en la ruta."""
        path_lower = file_path.lower()
        
        if 'pages' in path_lower or 'app' in path_lower:
            return 'page'
        elif 'layout' in path_lower:
            return 'layout'
        elif 'hook' in path_lower or path_lower.startswith('use'):
            return 'hook'
        elif 'component' in path_lower:
            return 'component'
        else:
            return 'component'
    
    def _extract_description(self, content: str, component_name: str) -> Optional[str]:
        """
        Intenta extraer una descripción del componente desde comentarios.
        """
        # Buscar comentarios JSDoc antes del componente
        jsdoc_pattern = rf'/\*\*\s*\n\s*\*\s*([^\n]+)\s*\n[^*]*\*/\s*(?:export\s+)?(?:default\s+)?(?:function|const)\s+{component_name}'
        match = re.search(jsdoc_pattern, content)
        
        if match:
            description = match.group(1).strip()
            return description[:200]  # Limitar longitud
        
        # Buscar comentario de línea simple
        line_comment_pattern = rf'//\s*([^\n]+)\s*\n\s*(?:export\s+)?(?:default\s+)?(?:function|const)\s+{component_name}'
        match = re.search(line_comment_pattern, content)
        
        if match:
            description = match.group(1).strip()
            return description[:200]
        
        return None


# Función de utilidad para testing
def parse_file(file_path: str) -> List[Dict]:
    """
    Parsea un archivo React y retorna los componentes encontrados.
    
    Args:
        file_path: Ruta al archivo
        
    Returns:
        Lista de componentes
    """
    parser = ReactParser()
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return parser.extract_component_info(content, file_path)
    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return []

