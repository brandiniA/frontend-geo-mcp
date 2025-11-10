"""
Parser de componentes React usando regex.
Extrae información de componentes sin necesidad de AST complejo.
"""

import re
import os
from typing import List, Dict, Optional, Any
from pathlib import Path

# Importar utilidades de archivos
try:
    from utils.file_utils import get_file_name_without_ext
except ImportError:
    from src.utils.file_utils import get_file_name_without_ext  # type: ignore


class ReactParser:
    """Parser para extraer información de componentes React usando regex."""
    
    # Patrones para detectar componentes
    COMPONENT_PATTERNS = [
        r'export\s+(?:default\s+)?(?:function|const|class)\s+(\w+)',
        r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>',
        r'function\s+(\w+)\s*\([^)]*\)',
        r'class\s+(\w+)\s+extends\s+(?:Component|React\.Component|PureComponent|React\.PureComponent)',
        # Clases que extienden otras clases (pueden ser componentes si tienen render o JSX)
        # Este patrón es más amplio pero se filtra después con _is_valid_component_name
        r'class\s+(\w+)\s+extends\s+\w+',
    ]
    
    # Patrones para props
    PROPS_PATTERN = r'\((?:\s*{\s*([^}]+)\s*}|([^)]+))\)'
    
    # Patrones para hooks
    HOOKS_PATTERN = r'use[A-Z]\w+'
    
    # Patrones para imports
    IMPORT_PATTERN = r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]'
    
    # Patrones para exports
    EXPORT_PATTERN = r'export\s+(?:default\s+)?(?:function|const|class)\s+(\w+)'
    
    # Hooks nativos de React
    NATIVE_HOOKS = {
        'useState', 'useEffect', 'useContext', 'useReducer', 'useCallback',
        'useMemo', 'useRef', 'useLayoutEffect', 'useDebugValue', 'useDeferredValue',
        'useTransition', 'useId', 'useSyncExternalStore', 'useInsertionEffect',
        'useImperativeHandle', 'useFormStatus', 'useFormState'
    }
    
    def extract_component_info(self, file_content: str, file_path: str) -> List[Dict]:
        """
        Extrae información de componentes de un archivo React.
        Ahora incluye documentación JSDoc completa.
        
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
                
                # Rechazar factory functions e instancias
                if self._is_factory_or_instance(file_content, component_name):
                    continue
                
                seen_components.add(component_name)
                
                # Extraer documentación JSDoc completa
                jsdoc = self._extract_jsdoc(file_content, component_name)
                
                all_hooks = self._extract_hooks(file_content)
                native_hooks, custom_hooks = self._separate_hooks(all_hooks)
                
                # Extraer imports estructurados y mantener compatibilidad
                component_imports = self._extract_component_imports(file_content)
                imports_legacy = self._extract_imports(file_content)
                
                component_info = {
                    'name': component_name,
                    'file_path': file_path,
                    'props': self._extract_props(file_content, component_name),
                    'native_hooks_used': native_hooks,
                    'custom_hooks_used': custom_hooks,
                    'imports': imports_legacy,  # Mantener formato legacy para compatibilidad
                    'component_imports': component_imports,  # Nuevo formato estructurado
                    'exports': self._extract_exports(file_content),
                    'component_type': self._determine_type(file_path),
                    'description': self._extract_description(file_content, component_name),
                    'jsdoc': jsdoc,
                }
                
                components.append(component_info)
        
        return components
    
    def _is_valid_component_name(self, name: str) -> bool:
        """
        Verifica si un nombre es válido para un componente React.
        Los componentes React DEBEN empezar con mayúscula (PascalCase).
        
        Rechaza CONSTANTES y VARIABLES comunes:
        1. SCREAMING_SNAKE_CASE: CONFIG_NAME, API_URL, DB_HOST
           - Contiene '_' Y está todo en mayúscula
        
        2. camelCase (minúscula inicial): counter, userData, myFunction
           - Empieza con minúscula → No es componente
        
        3. Constantes con prefijos comunes: 
           - REACT_APP_*, NODE_ENV, VITE_*
           - min*, max*, default* (min_width, defaultValue)
           - is*, has*, can* (isEnabled, hasAccess)
        
        4. Números al inicio: 2FActor → No es válido
        
        5. Patrones de variables de configuración:
           - *_DEFAULT, *_CONFIG, *_SETTINGS, *_OPTIONS
           - *_DARK, *_LIGHT (temas)
        
        Acepta:
        - PascalCase: Button, UserProfile, MyComponent
        - Pero NO palabras reservadas
        """
        if not name or not isinstance(name, str):
            return False
        
        # ❌ NO PUEDE EMPEZAR CON MINÚSCULA
        # Regla fundamental: componentes React = PascalCase
        if name[0].islower():
            return False
        
        # ❌ NO PUEDE EMPEZAR CON NÚMERO
        if name[0].isdigit():
            return False
        
        # ❌ NO PUEDE EMPEZAR CON GUIÓN BAJO
        # Variables privadas o protegidas: _private, __private
        if name[0] == '_':
            return False
        
        # ❌ SCREAMING_SNAKE_CASE: CONSTANT_NAME, CONFIG_API_KEY
        # Patrón: contiene '_' Y está todo en mayúsculas
        if '_' in name and name.isupper():
            return False
        
        # ❌ Constantes con prefijos típicos de env vars
        env_prefixes = {'REACT_APP_', 'VITE_', 'NODE_', 'npm_'}
        if any(name.startswith(prefix) for prefix in env_prefixes):
            return False
        
        # ❌ Patrones comunes de variables/constantes (camelCase con prefijos)
        # is*, has*, can*, should*, get*, set*, make*, create*
        prefixes_vars = [
            'is', 'has', 'can', 'should', 'get', 'set', 'make', 'create',
            'add', 'remove', 'delete', 'update', 'fetch', 'load', 'save',
            'parse', 'format', 'validate', 'check', 'compute', 'calculate'
        ]
        
        # Si empieza con uno de estos prefijos en minúscula → probable función/variable, NO componente
        name_lower = name.lower()
        for prefix in prefixes_vars:
            if name_lower.startswith(prefix) and len(name) > len(prefix):
                # isActive, hasError, canDelete → son probablemente funciones/variables
                if name[len(prefix)].isupper():
                    # Verificar que realmente sea camelCase: isProp → función
                    return False
        
        # ❌ Constantes con sufijos comunes
        suffixes_const = [
            '_DEFAULT', '_CONFIG', '_SETTINGS', '_OPTIONS',
            '_DARK', '_LIGHT', '_THEME', '_KEYS', '_TYPES',
            '_MAX', '_MIN', '_WIDTH', '_HEIGHT', '_SIZE',
            '_URL', '_API', '_HOST', '_PORT', '_TIMEOUT'
        ]
        if any(name.endswith(suffix) for suffix in suffixes_const):
            return False
        
        # ❌ Palabras reservadas y comunes que NO son componentes
        reserved = {
            'Component', 'React', 'Fragment', 'Fragment', 'StrictMode',
            'Suspense', 'Profiler', 'Help', 'Error', 'Prototype',
            'Object', 'Array', 'String', 'Number', 'Boolean', 'Symbol',
            'Function', 'Date', 'RegExp', 'Math', 'JSON', 'Promise',
            'Map', 'Set', 'WeakMap', 'WeakSet', 'Proxy', 'Reflect'
        }
        if name in reserved:
            return False
        
        # ✅ Cumple todas las reglas: es probable que sea un componente válido
        return True
    
    def _is_factory_or_instance(self, content: str, name: str) -> bool:
        """
        Detecta si un nombre es una factory function o una instancia.
        
        Ejemplos:
        - function OpenPay() { ... } → Factory (retorna objeto)
        - const openPay = OpenPay() → Instancia de factory
        - const db = DatabaseClient() → Instancia de factory
        
        Returns:
            True si parece ser factory o instancia, False si es componente
        """
        # Patrón 1: Detectar si es una factory (function que retorna objeto literal { })
        # function Name() { ... return { key: value } }
        # Debe ser más específico: buscar return seguido directamente de { con propiedades (key: value)
        # NO debe coincidir con componentes que retornan JSX (<div>)
        factory_pattern = rf'(?:function|const)\s+{name}\s*\([^)]*\)\s*\{{[^}}]*return\s+\{{[^}}]*\w+\s*:'
        if re.search(factory_pattern, content, re.DOTALL):
            # Verificar que NO es JSX (no tiene < después del return)
            # Si tiene < después del return, es un componente, no una factory
            return_jsx_check = rf'(?:function|const)\s+{name}\s*\([^)]*\)\s*\{{[^}}]*return\s*[<(]'
            if not re.search(return_jsx_check, content, re.DOTALL):
                return True
        
        # Verificación adicional: si es export default function y retorna JSX, NO es factory
        export_default_pattern = rf'export\s+default\s+function\s+{name}\s*\([^)]*\)\s*\{{'
        if re.search(export_default_pattern, content):
            # Verificar si retorna JSX
            return_jsx_check = rf'export\s+default\s+function\s+{name}\s*\([^)]*\)\s*\{{[^}}]*return\s*[<(]'
            if re.search(return_jsx_check, content, re.DOTALL):
                # Es un componente React, NO es factory
                return False
        
        # Patrón 2: Detectar si es instancia de factory
        # const instance = FactoryName()
        # const db = DatabaseClient()
        instance_pattern = rf'(?:const|let|var)\s+\w+\s*=\s*{name}\s*\('
        if re.search(instance_pattern, content):
            return True
        
        # Patrón 3: Detectar funciones normales (no componentes)
        # function utilFunction() { ... }
        # Normalmente solo tienen lógica, no retornan JSX
        # NO aplicar si es export default function (componentes React)
        plain_function_pattern = rf'function\s+{name}\s*\([^)]*\)\s*\{{'
        if re.search(plain_function_pattern, content):
            # Verificar que NO es export default (componentes React)
            export_default_check = rf'export\s+default\s+function\s+{name}\s*\([^)]*\)\s*\{{'
            if re.search(export_default_check, content):
                # Es export default, probablemente es componente, NO es factory
                return False
            
            # Verificar que no retorna JSX (no contiene <...>)
            function_body_match = re.search(rf'function\s+{name}\s*\([^)]*\)\s*\{{(.*?)(?:^export|\Z)', content, re.DOTALL | re.MULTILINE)
            if function_body_match:
                body = function_body_match.group(1)
                # Si el cuerpo no contiene JSX (<...>), es probable que NO sea componente
                # Pero si tiene 'return' seguido de '<' o '(', es componente
                if '<' not in body:
                    # Verificar si tiene return con JSX
                    return_jsx_pattern = r'return\s*[<(]'
                    if not re.search(return_jsx_pattern, body):
                        return True
        
        return False
    
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
        hooks = re.findall(self.HOOKS_PATTERN, content)
        return self._limit_and_sort(hooks, limit=15)
    
    def _separate_hooks(self, hooks: List[str]) -> tuple[List[str], List[str]]:
        """
        Separa los hooks en nativos y custom basándose en la lista de hooks nativos.
        
        Los hooks que NO están en NATIVE_HOOKS se consideran potencialmente custom.
        La validación final (si realmente existen como custom hooks indexados) 
        se hace en la BD al guardar componentes.
        
        Args:
            hooks: Lista de hooks detectados en el código
            
        Returns:
            Tupla (native_hooks, custom_hooks_names)
            - native_hooks: Hooks confirmados de React
            - custom_hooks_names: Nombres de hooks potencialmente custom
        """
        native_hooks = []
        potential_custom_hooks = []
        
        for hook in hooks:
            if hook in self.NATIVE_HOOKS:
                native_hooks.append(hook)
            else:
                # Es candidato a custom hook
                # La validación final se hace en la BD
                potential_custom_hooks.append(hook)
        
        return native_hooks, potential_custom_hooks
    
    def extract_hook_info(self, file_content: str, file_path: str) -> List[Dict]:
        """
        Extrae información de custom hooks de un archivo.
        SOLO procesa archivos que empiezan con "use" (convención de hooks).
        
        Args:
            file_content: Contenido del archivo
            file_path: Ruta del archivo (ej: hooks/useUserData.ts)
            
        Returns:
            Lista de diccionarios con información de custom hooks (vacía si no es un hook file)
        """
        # Verificar si el archivo es un custom hook
        if not self._is_hook_file(file_path):
            return []
        
        hooks = []
        seen_hooks = set()
        
        # Extraer nombres de hooks (deben empezar con 'use')
        for pattern in self.COMPONENT_PATTERNS:
            matches = re.finditer(pattern, file_content)
            for match in matches:
                hook_name = match.group(1)
                
                # ❌ RECHAZAR: Constantes (USE_CONSTANT, USE_API_URL, etc.)
                if '_' in hook_name and hook_name.isupper():
                    continue  # Es una constante, no un hook
                
                # Debe empezar con 'use' y no debe ser duplicado
                if not hook_name.startswith('use') or hook_name in seen_hooks:
                    continue
                
                seen_hooks.add(hook_name)
                
                # Extraer todos los hooks utilizados dentro
                all_hooks = self._extract_hooks(file_content)
                native_hooks, custom_hooks = self._separate_hooks(all_hooks)
                
                # Extraer parámetros del JSDoc
                jsdoc = self._extract_jsdoc(file_content, hook_name)
                parameters = jsdoc.get('params', []) if jsdoc else []
                return_type = jsdoc.get('returns', {}).get('type', 'unknown') if jsdoc else 'unknown'
                
                # Extraer imports estructurados y mantener compatibilidad
                component_imports = self._extract_component_imports(file_content)
                imports_legacy = self._extract_imports(file_content)
                
                hook_info = {
                    'name': hook_name,
                    'file_path': file_path,
                    'hook_type': 'custom',
                    'description': self._extract_description(file_content, hook_name),
                    'return_type': return_type,
                    'parameters': parameters,
                    'imports': imports_legacy,  # Mantener formato legacy para compatibilidad
                    'component_imports': component_imports,  # Nuevo formato estructurado
                    'exports': self._extract_exports(file_content),
                    'native_hooks_used': native_hooks,
                    'custom_hooks_used': custom_hooks,
                    'jsdoc': jsdoc,
                }
                
                hooks.append(hook_info)
        
        return hooks
    
    def _is_hook_file(self, file_path: str) -> bool:
        """
        Verifica si un archivo es un custom hook basado en su nombre.
        Convención: el nombre de archivo debe empezar con 'use' seguido de mayúscula (ej: useUserData.ts)
        
        Args:
            file_path: Ruta del archivo (ej: hooks/useUserData.ts)
            
        Returns:
            True si el archivo probablemente contiene un custom hook
        """
        # Obtener el nombre del archivo sin extensión usando utilidad
        name_without_ext = get_file_name_without_ext(file_path)
        
        # Debe empezar con 'use' seguido de mayúscula
        return bool(re.match(r'^use[A-Z]', name_without_ext))
    
    def _extract_imports(self, content: str) -> List[str]:
        """
        Extrae rutas de imports (método legacy para compatibilidad).
        
        Retorna solo las rutas de los módulos importados.
        Para información completa de imports, usar _extract_component_imports().
        """
        imports = re.findall(self.IMPORT_PATTERN, content)
        # Filtrar imports relativos muy largos
        imports = [imp for imp in imports if len(imp) < 100]
        return self._limit_and_sort(imports, limit=10)
    
    def _extract_component_imports(self, content: str) -> List[Dict[str, Any]]:
        """
        Extrae imports con nombres de componentes importados.
        
        Soporta múltiples patrones de import:
        - Named imports: import { Button, Card } from './components'
        - Default import: import Button from './Button'
        - Mixed: import Button, { Card } from './components'
        - Namespace: import * as Components from './components'
        
        Args:
            content: Contenido del archivo
            
        Returns:
            Lista de diccionarios con estructura:
            [
                {
                    'imported_names': ['Button', 'Card'],
                    'from_path': './components',
                    'import_type': 'named'
                },
                {
                    'imported_names': ['Button'],
                    'from_path': './Button',
                    'import_type': 'default'
                }
            ]
        """
        imports = []
        
        # Patrón 1: Named imports - import { Button, Card } from './components'
        named_pattern = r'import\s+\{([^}]+)\}\s+from\s+[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(named_pattern, content):
            names_str = match.group(1)
            from_path = match.group(2)
            
            # Extraer nombres individuales (manejar alias: Button as Btn)
            names = []
            for name_part in names_str.split(','):
                name_part = name_part.strip()
                # Manejar alias: "Button as Btn" -> usar "Button"
                if ' as ' in name_part:
                    name_part = name_part.split(' as ')[0].strip()
                if name_part:
                    names.append(name_part)
            
            if names and len(from_path) < 100:
                imports.append({
                    'imported_names': names,
                    'from_path': from_path,
                    'import_type': 'named'
                })
        
        # Patrón 2: Default import - import Button from './Button'
        default_pattern = r'import\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(default_pattern, content):
            name = match.group(1)
            from_path = match.group(2)
            
            # Evitar duplicados con named imports
            if not any(imp['from_path'] == from_path and imp['import_type'] == 'default' 
                      for imp in imports):
                if len(from_path) < 100:
                    imports.append({
                        'imported_names': [name],
                        'from_path': from_path,
                        'import_type': 'default'
                    })
        
        # Patrón 3: Mixed - import Button, { Card } from './components'
        mixed_pattern = r'import\s+(\w+)\s*,\s*\{([^}]+)\}\s+from\s+[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(mixed_pattern, content):
            default_name = match.group(1)
            names_str = match.group(2)
            from_path = match.group(3)
            
            # Extraer nombres named
            names = [default_name]
            for name_part in names_str.split(','):
                name_part = name_part.strip()
                if ' as ' in name_part:
                    name_part = name_part.split(' as ')[0].strip()
                if name_part:
                    names.append(name_part)
            
            if names and len(from_path) < 100:
                # Remover si ya existe un import de esta ruta
                imports = [imp for imp in imports if not (
                    imp['from_path'] == from_path and 
                    imp['import_type'] in ['default', 'named']
                )]
                imports.append({
                    'imported_names': names,
                    'from_path': from_path,
                    'import_type': 'mixed'
                })
        
        # Patrón 4: Namespace - import * as Components from './components'
        namespace_pattern = r'import\s+\*\s+as\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(namespace_pattern, content):
            namespace_name = match.group(1)
            from_path = match.group(2)
            
            if len(from_path) < 100:
                imports.append({
                    'imported_names': [namespace_name],
                    'from_path': from_path,
                    'import_type': 'namespace'
                })
        
        # Limitar número de imports
        return imports[:20]
    
    def _extract_exports(self, content: str) -> List[str]:
        """Extrae exports."""
        exports = re.findall(self.EXPORT_PATTERN, content)
        return self._limit_and_sort(exports, limit=10)
    
    def _limit_and_sort(self, items: List[str], limit: int = 10) -> List[str]:
        """
        Limita y ordena una lista de items.
        
        Utilidad común para imports, exports, hooks, etc.
        
        Args:
            items: Lista de items
            limit: Límite máximo de items a retornar
        
        Returns:
            Lista limitada y ordenada
        """
        return sorted(list(set(items)))[:limit]
    
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
    
    def _extract_jsdoc(self, content: str, component_name: str) -> Optional[Dict]:
        """
        Extrae documentación JSDoc completa incluyendo @param, @returns, @example, etc.
        
        Returns:
            Dict con estructura:
            {
                "description": "...",
                "params": [{"name": "...", "type": "...", "description": "..."}],
                "returns": {"type": "...", "description": "..."},
                "examples": ["...", "..."],
                "deprecated": boolean,
                "tags": {...}
            }
        """
        # Patrón para JSDoc completo
        jsdoc_pattern = r'/\*\*\s*([\s\S]*?)\*/'
        match = re.search(jsdoc_pattern, content)
        
        if not match:
            return None
        
        jsdoc_text = match.group(1)
        
        # Validar que pertenece al componente (debe estar cerca)
        component_check = rf'/\*\*.*?(?:export\s+)?(?:default\s+)?(?:function|const)\s+{component_name}'
        if not re.search(component_check, content, re.DOTALL):
            return None
        
        result = {}
        
        # Extraer descripción principal
        desc_lines = []
        for line in jsdoc_text.split('\n'):
            line = line.strip().lstrip('*').strip()
            if line and not line.startswith('@'):
                desc_lines.append(line)
            elif line.startswith('@'):
                break
        
        if desc_lines:
            result['description'] = ' '.join(desc_lines)
        
        # Extraer @param tags
        params = []
        param_pattern = r'@param\s+(?:\{([^}]+)\})?\s+(\w+)\s*-?\s*([^\n]*)'
        for param_match in re.finditer(param_pattern, jsdoc_text):
            params.append({
                'type': param_match.group(1) or 'unknown',
                'name': param_match.group(2),
                'description': param_match.group(3).strip()
            })
        if params:
            result['params'] = params
        
        # Extraer @returns
        returns_pattern = r'@returns?\s+(?:\{([^}]+)\})?\s*-?\s*([^\n]*)'
        returns_match = re.search(returns_pattern, jsdoc_text)
        if returns_match:
            result['returns'] = {
                'type': returns_match.group(1) or 'JSX.Element',
                'description': returns_match.group(2).strip()
            }
        
        # Extraer @example
        examples = []
        example_pattern = r'@example\s+([\s\S]*?)(?=@\w+|$)'
        for example_match in re.finditer(example_pattern, jsdoc_text):
            example_code = example_match.group(1).strip()
            # Limpiar asteriscos y espacios
            example_code = '\n'.join(
                line.lstrip('*').strip() for line in example_code.split('\n')
                if line.strip() and not line.strip().startswith('@')
            )
            if example_code:
                examples.append(example_code)
        if examples:
            result['examples'] = examples
        
        # Extraer otros tags útiles
        result['deprecated'] = bool(re.search(r'@deprecated', jsdoc_text))
        result['author'] = None
        result['version'] = None
        
        author_match = re.search(r'@author\s+([^\n]+)', jsdoc_text)
        if author_match:
            result['author'] = author_match.group(1).strip()
        
        version_match = re.search(r'@version\s+([^\n]+)', jsdoc_text)
        if version_match:
            result['version'] = version_match.group(1).strip()
        
        return result if result else None
    
    def _detect_redox_container(self, content: str, file_path: str) -> Optional[Dict]:
        """
        Detecta si un archivo es un container de Redux.
        
        Args:
            content: Contenido del archivo
            file_path: Ruta del archivo
            
        Returns:
            Dict con información del container o None si no es container
        """
        # Patrón para detectar: export default connect(...)(ComponentName)
        # Usar re.DOTALL para que . coincida con saltos de línea
        connect_pattern = r'export\s+default\s+connect\s*\([^)]+\)\s*\((\w+)\)'
        # Patrón para detectar: export default compose(...)(ComponentName)
        # Usar re.DOTALL para manejar múltiples líneas dentro de compose
        compose_pattern = r'export\s+default\s+compose\s*\([\s\S]*?\)\s*\((\w+)\)'
        
        # Patrón para detectar: const ContainerName = connect(...)(ComponentName)
        # Para casos donde el connect no está directamente en el export default
        connect_var_pattern = r'const\s+\w+Container\w*\s*=\s*connect\s*\([^)]+\)\s*\((\w+)\)'
        # Patrón para detectar: const ContainerName = compose(...)(ComponentName)
        compose_var_pattern = r'const\s+\w+Container\w*\s*=\s*compose\s*\([\s\S]*?\)\s*\((\w+)\)'
        
        wrapped_component = None
        hocs_used = []
        has_merge_props = False
        compose_match = None  # Inicializar para evitar UnboundLocalError
        
        # Buscar patrón connect en export default
        connect_match = re.search(connect_pattern, content)
        if connect_match:
            wrapped_component = connect_match.group(1)
            hocs_used.append('connect')
        
        # Buscar patrón compose en export default (con soporte para múltiples líneas)
        if not wrapped_component:
            compose_match = re.search(compose_pattern, content, re.DOTALL)
            if compose_match:
                wrapped_component = compose_match.group(1)
                hocs_used.append('compose')
        
        # Si no encontramos en export default, buscar en variables (casos como CheckoutContainer)
        if not wrapped_component:
            connect_var_match = re.search(connect_var_pattern, content)
            if connect_var_match:
                wrapped_component = connect_var_match.group(1)
                hocs_used.append('connect')
        
        if not wrapped_component:
            compose_var_match = re.search(compose_var_pattern, content, re.DOTALL)
            if compose_var_match:
                wrapped_component = compose_var_match.group(1)
                hocs_used.append('compose')
                compose_match = compose_var_match  # Guardar para uso posterior
        
        # Si no encontramos ningún patrón, no es container
        if not wrapped_component:
            return None
        
        # Detectar otros HOCs comunes (buscar también dentro de compose)
        if 'reduxForm(' in content:
            hocs_used.append('reduxForm')
        if 'withTranslation(' in content:
            hocs_used.append('withTranslation')
        if 'withRouter(' in content:
            hocs_used.append('withRouter')
        # Si hay compose, también buscar connect dentro de él
        if compose_match and 'connect(' in content:
            hocs_used.append('connect')
        
        # Detectar mergeProps
        if 'mergeProps' in content or 'const mergeProps' in content:
            has_merge_props = True
        
        return {
            'is_container': True,
            'wrapped_component': wrapped_component,
            'hocs_used': list(set(hocs_used)),  # Eliminar duplicados
            'has_merge_props': has_merge_props,
            'file_path': file_path
        }
    
    def _extract_usage_context(self, content: str, flag_name: str) -> Dict:
        """
        Extrae metadata del contexto de uso de un feature flag.
        
        Args:
            content: Contenido del archivo
            flag_name: Nombre del feature flag
            
        Returns:
            Dict con metadata del contexto
        """
        usage_context = None
        usage_type = None
        combined_with = []
        logic = None
        
        # Detectar contexto: mapStateToProps, mapDispatchToProps, mergeProps
        map_state_match = re.search(r'const\s+mapStateToProps\s*=\s*\([^)]*\)\s*=>\s*\{', content)
        map_dispatch_match = re.search(r'const\s+mapDispatchToProps\s*=\s*\([^)]*\)\s*=>\s*\{', content)
        merge_props_match = re.search(r'const\s+mergeProps\s*=\s*\([^)]*\)\s*=>\s*\{', content)
        
        # Buscar el flag en el contenido
        flag_pattern = rf'\b{re.escape(flag_name)}\b'
        flag_matches = list(re.finditer(flag_pattern, content))
        
        if not flag_matches:
            return {
                'usage_context': None,
                'usage_type': None,
                'combined_with': [],
                'logic': None
            }
        
        # Determinar contexto basado en dónde aparece el flag
        for match in flag_matches:
            match_pos = match.start()
            
            # Buscar en qué función está
            if map_state_match and map_dispatch_match:
                if map_state_match.start() < match_pos < map_dispatch_match.start():
                    usage_context = 'mapStateToProps'
                    break
                elif map_dispatch_match.start() < match_pos:
                    if merge_props_match and match_pos < merge_props_match.start():
                        usage_context = 'mapDispatchToProps'
                    elif merge_props_match and match_pos > merge_props_match.start():
                        usage_context = 'mergeProps'
                    else:
                        usage_context = 'mapDispatchToProps'
                    break
            elif map_state_match:
                if map_state_match.start() < match_pos:
                    usage_context = 'mapStateToProps'
                    break
            elif map_dispatch_match:
                if map_dispatch_match.start() < match_pos:
                    usage_context = 'mapDispatchToProps'
                    break
        
        # Detectar tipo de uso (en orden de especificidad, más específico primero)
        # 1. Construcción de array: features.FLAG && 'value' (más específico)
        array_pattern = rf'{re.escape(flag_name)}\s*&&\s*[\'"][^\'"]+[\'"]'
        if re.search(array_pattern, content):
            usage_type = 'array_construction'
        
        # 2. Validación condicional: if (key === 'field' && !features.FLAG)
        elif re.search(rf'if\s*\([^)]*{re.escape(flag_name)}', content):
            usage_type = 'conditional_validation'
        
        # 3. Lógica condicional: features.FLAG === 'value' o const x = features.FLAG
        elif re.search(rf'{re.escape(flag_name)}\s*[=!]+\s*[\'"]', content) or re.search(rf'const\s+\w+\s*=\s*.*{re.escape(flag_name)}', content):
            usage_type = 'conditional_logic'
        
        # 4. Prop passing: features, o features.FLAG en return (menos específico, último)
        # Solo si no se detectó otro tipo más específico
        elif re.search(rf'features\s*[,}}]', content) and not usage_type:
            usage_type = 'prop_passing'
        
        # Detectar flags combinados (AND/OR)
        # Buscar patrones como: features.FLAG1 === 'value' && features.FLAG2
        combined_and_pattern = rf'{re.escape(flag_name)}\s*[=!]+\s*[^\s&|]+\s*&&\s*features\.(\w+)'
        combined_and_match = re.search(combined_and_pattern, content)
        if combined_and_match:
            combined_with.append(combined_and_match.group(1))
            logic = 'AND'
        
        # Buscar: features.FLAG1 && features.FLAG2
        simple_and_pattern = rf'{re.escape(flag_name)}\s*&&\s*features\.(\w+)'
        simple_and_match = re.search(simple_and_pattern, content)
        if simple_and_match and simple_and_match.group(1) not in combined_with:
            combined_with.append(simple_and_match.group(1))
            if not logic:
                logic = 'AND'
        
        # Buscar OR
        combined_or_pattern = rf'{re.escape(flag_name)}\s*\|\|\s*features\.(\w+)'
        combined_or_match = re.search(combined_or_pattern, content)
        if combined_or_match:
            combined_with.append(combined_or_match.group(1))
            logic = 'OR'
        
        return {
            'usage_context': usage_context,
            'usage_type': usage_type,
            'combined_with': combined_with if combined_with else None,
            'logic': logic
        }


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

