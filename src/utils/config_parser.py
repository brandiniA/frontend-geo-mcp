"""
Parser de archivos de configuración para detectar aliases de imports.
Soporta webpack.config.js, babel.config.js, tsconfig.json, jsconfig.json
"""

import os
import re
import json
from typing import Dict, Optional, List
from pathlib import Path


class AliasConfigParser:
    """Parser para detectar aliases en archivos de configuración."""
    
    # Archivos de configuración a buscar (en orden de prioridad)
    CONFIG_FILES = [
        'webpack.config.js',
        'webpack.config.ts',
        'webpack.base.config.js',
        'webpack.common.js',
        'babel.config.js',
        'babel.config.json',
        '.babelrc',
        '.babelrc.js',
        'tsconfig.json',
        'jsconfig.json',
    ]
    
    def __init__(self):
        self.aliases: Dict[str, str] = {}
    
    def find_config_files(self, repo_path: str) -> List[str]:
        """
        Busca archivos de configuración en el repositorio.
        
        Args:
            repo_path: Ruta del repositorio
            
        Returns:
            Lista de rutas a archivos de configuración encontrados
        """
        found_configs = []
        
        # Buscar en raíz del proyecto
        for config_file in self.CONFIG_FILES:
            config_path = os.path.join(repo_path, config_file)
            if os.path.exists(config_path):
                found_configs.append(config_path)
        
        # También buscar en subdirectorios comunes (config/, etc)
        common_dirs = ['config', 'configs', '.config']
        for dirname in common_dirs:
            dir_path = os.path.join(repo_path, dirname)
            if os.path.exists(dir_path):
                for config_file in self.CONFIG_FILES:
                    config_path = os.path.join(dir_path, config_file)
                    if os.path.exists(config_path):
                        found_configs.append(config_path)
        
        return found_configs
    
    def parse_all_configs(self, repo_path: str) -> Dict[str, str]:
        """
        Parsea todos los archivos de configuración encontrados.
        
        Args:
            repo_path: Ruta del repositorio
            
        Returns:
            Diccionario con aliases detectados {alias: ruta_real}
        """
        config_files = self.find_config_files(repo_path)
        
        if not config_files:
            return {}
        
        print(f"   📄 Archivos de configuración encontrados: {len(config_files)}")
        
        all_aliases = {}
        
        for config_path in config_files:
            filename = os.path.basename(config_path)
            print(f"   🔍 Parseando: {filename}")
            
            if 'webpack' in filename:
                aliases = self._parse_webpack_config(config_path)
            elif 'babel' in filename or '.babelrc' in filename:
                aliases = self._parse_babel_config(config_path)
            elif 'tsconfig' in filename or 'jsconfig' in filename:
                aliases = self._parse_tsconfig(config_path)
            else:
                continue
            
            if aliases:
                print(f"      ✅ Encontrados {len(aliases)} aliases en {filename}")
                # Merge aliases (últimos archivos tienen prioridad)
                all_aliases.update(aliases)
        
        if all_aliases:
            print(f"   ✅ Total de aliases únicos detectados: {len(all_aliases)}")
            print(f"   📋 Aliases: {list(all_aliases.keys())}")
        else:
            print(f"   ℹ️  No se detectaron aliases en archivos de configuración")
        
        return all_aliases
    
    def _parse_webpack_config(self, config_path: str) -> Dict[str, str]:
        """
        Parsea webpack.config.js para extraer aliases.
        
        Busca patrones como:
        resolve: {
            alias: {
                '@': path.resolve(__dirname, 'src'),
                'components': path.resolve(__dirname, 'src/components'),
            }
        }
        """
        aliases = {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"      ⚠️  Error leyendo {config_path}: {e}")
            return aliases
        
        # Patrón para capturar el bloque alias
        # Buscar: alias: { ... }
        alias_block_pattern = r"alias\s*:\s*\{([^}]+)\}"
        alias_blocks = re.findall(alias_block_pattern, content, re.DOTALL)
        
        for block in alias_blocks:
            # Extraer cada entrada de alias
            # Patrones comunes:
            # '@': path.resolve(__dirname, 'src')
            # 'components': path.resolve(__dirname, 'src/components')
            # '@/': path.resolve('src/')
            
            # Patrón 1: 'alias': path.resolve(__dirname, 'src') o path.resolve('src')
            # Captura el último argumento de path.resolve que es la ruta
            # Busca el último string entre comillas dentro de path.resolve
            pattern1 = r"['\"]([^'\"]+)['\"]\s*:\s*path\.resolve\([^)]*,\s*['\"]([^'\"]+)['\"]\)|['\"]([^'\"]+)['\"]\s*:\s*path\.resolve\(['\"]([^'\"]+)['\"]\)"
            matches = re.findall(pattern1, block)
            
            # Reorganizar matches: pattern1 puede tener grupos opcionales
            processed_matches = []
            for match in matches:
                if match[0] and match[1]:  # path.resolve(__dirname, 'src')
                    processed_matches.append((match[0], match[1]))
                elif match[2] and match[3]:  # path.resolve('src')
                    processed_matches.append((match[2], match[3]))
            matches = processed_matches
            
            for alias_key, alias_path in matches:
                # Normalizar la ruta (quitar __dirname, ./, etc)
                normalized_path = alias_path.strip('./')
                
                # Asegurar que termina con / si el alias termina con /
                if alias_key.endswith('/') and not normalized_path.endswith('/'):
                    normalized_path += '/'
                
                aliases[alias_key] = normalized_path
            
            # Patrón 2: 'alias': 'path/to/dir' (sin path.resolve)
            pattern2 = r"['\"]([^'\"]+)['\"]\s*:\s*['\"]([^'\"]+)['\"]"
            matches2 = re.findall(pattern2, block)
            
            for alias_key, alias_path in matches2:
                # Solo agregar si no es parte de un path.resolve (ya procesado)
                if alias_key not in aliases and 'path.resolve' not in block[:block.find(f"'{alias_key}'")]:
                    normalized_path = alias_path.strip('./')
                    if alias_key.endswith('/') and not normalized_path.endswith('/'):
                        normalized_path += '/'
                    aliases[alias_key] = normalized_path
        
        return aliases
    
    def _parse_babel_config(self, config_path: str) -> Dict[str, str]:
        """
        Parsea babel.config.js o .babelrc para extraer aliases.
        
        Busca el plugin module-resolver:
        plugins: [
            ['module-resolver', {
                alias: {
                    '@': './src',
                    'components': './src/components'
                }
            }]
        ]
        """
        aliases = {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"      ⚠️  Error leyendo {config_path}: {e}")
            return aliases
        
        # Si es JSON, intentar parsearlo
        if config_path.endswith('.json') or config_path.endswith('.babelrc'):
            try:
                config_data = json.loads(content)
                plugins = config_data.get('plugins', [])
                
                for plugin in plugins:
                    if isinstance(plugin, list) and len(plugin) > 1:
                        plugin_name = plugin[0]
                        if 'module-resolver' in plugin_name:
                            plugin_config = plugin[1]
                            alias_config = plugin_config.get('alias', {})
                            
                            for alias_key, alias_path in alias_config.items():
                                normalized_path = alias_path.strip('./')
                                if alias_key.endswith('/') and not normalized_path.endswith('/'):
                                    normalized_path += '/'
                                aliases[alias_key] = normalized_path
                
                return aliases
            except json.JSONDecodeError:
                # Si no es JSON válido, continuar con parsing de texto
                pass
        
        # Parsing de texto para archivos .js
        # Buscar module-resolver alias
        resolver_pattern = r"module-resolver['\"],\s*\{[^}]*alias\s*:\s*\{([^}]+)\}"
        matches = re.findall(resolver_pattern, content, re.DOTALL)
        
        for block in matches:
            # Extraer cada entrada de alias
            alias_pattern = r"['\"]([^'\"]+)['\"]\s*:\s*['\"]([^'\"]+)['\"]"
            alias_matches = re.findall(alias_pattern, block)
            
            for alias_key, alias_path in alias_matches:
                normalized_path = alias_path.strip('./')
                if alias_key.endswith('/') and not normalized_path.endswith('/'):
                    normalized_path += '/'
                aliases[alias_key] = normalized_path
        
        return aliases
    
    def _parse_tsconfig(self, config_path: str) -> Dict[str, str]:
        """
        Parsea tsconfig.json o jsconfig.json para extraer aliases.
        
        Busca paths en compilerOptions:
        {
            "compilerOptions": {
                "baseUrl": ".",
                "paths": {
                    "@/*": ["src/*"],
                    "components/*": ["src/components/*"]
                }
            }
        }
        """
        aliases = {}
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Eliminar comentarios JSON (// y /* */)
            content = re.sub(r'//.*', '', content)
            content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
            
            config_data = json.loads(content)
        except Exception as e:
            print(f"      ⚠️  Error parseando {config_path}: {e}")
            return aliases
        
        compiler_options = config_data.get('compilerOptions', {})
        base_url = compiler_options.get('baseUrl', '.')
        paths = compiler_options.get('paths', {})
        
        for alias_key, alias_paths in paths.items():
            if not alias_paths or not isinstance(alias_paths, list):
                continue
            
            # Tomar el primer path (usualmente hay uno solo)
            alias_path = alias_paths[0]
            
            # Remover wildcards y normalizar
            alias_key_clean = alias_key.rstrip('/*')
            alias_path_clean = alias_path.rstrip('/*')
            
            # Combinar con baseUrl si existe
            if base_url and base_url != '.':
                full_path = os.path.join(base_url, alias_path_clean)
            else:
                full_path = alias_path_clean
            
            # Normalizar la ruta
            normalized_path = full_path.strip('./')
            
            # Preservar el trailing slash si el alias original lo tenía
            if alias_key.endswith('/') and not normalized_path.endswith('/'):
                normalized_path += '/'
            
            aliases[alias_key_clean] = normalized_path
        
        return aliases
    
    def resolve_alias(self, import_path: str, aliases: Dict[str, str]) -> Optional[str]:
        """
        Resuelve un import path usando los aliases detectados.
        
        Args:
            import_path: 'utils/helper' o '@/components/Button'
            aliases: Dict de aliases detectados
            
        Returns:
            'src/utils/helper' o 'src/components/Button', None si no se resolvió
        """
        if not aliases:
            return None
        
        # Intentar match exacto primero
        if import_path in aliases:
            return aliases[import_path]
        
        # Intentar match con prefijo (para aliases con /)
        for alias_key, alias_path in aliases.items():
            if import_path.startswith(alias_key):
                # Reemplazar el alias con la ruta real
                resolved = import_path.replace(alias_key, alias_path, 1)
                return resolved
        
        return None


def detect_project_aliases(repo_path: str) -> Dict[str, str]:
    """
    Función helper para detectar todos los aliases de un proyecto.
    
    Args:
        repo_path: Ruta del repositorio
        
    Returns:
        Diccionario con aliases {alias: ruta_real}
    """
    parser = AliasConfigParser()
    return parser.parse_all_configs(repo_path)

