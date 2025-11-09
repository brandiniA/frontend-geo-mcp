"""
Parser para extraer feature flags del archivo defaultFeatures.js.
"""

import re
import os
import json
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

# Importar utilidades de archivos
try:
    from utils.file_utils import read_file_safe, get_relative_path
except ImportError:
    from src.utils.file_utils import read_file_safe, get_relative_path  # type: ignore


class FeatureFlagParser:
    """Parser para extraer información de feature flags desde archivo defaultFeatures.js."""
    
    def find_feature_flags_file(self, repo_path: str) -> Optional[str]:
        """
        Busca el archivo de feature flags usando estrategia híbrida.
        
        Estrategia:
        1. Buscar archivo con nombre exacto: defaultFeatures.js en config/
        2. Fallback: Buscar archivos *feature*.js o *default*.js en config/
        3. Último recurso: Buscar cualquier archivo en config/ que exporte objeto con SCREAMING_SNAKE_CASE
        
        Args:
            repo_path: Ruta base del repositorio
            
        Returns:
            Ruta absoluta del archivo encontrado o None
        """
        config_dir = os.path.join(repo_path, 'config')
        
        # Estrategia 1: Nombre exacto
        exact_path = os.path.join(config_dir, 'defaultFeatures.js')
        if os.path.exists(exact_path):
            return exact_path
        
        # Estrategia 2: Patrones
        if os.path.exists(config_dir):
            for file in os.listdir(config_dir):
                if file.endswith('.js') or file.endswith('.ts'):
                    if 'feature' in file.lower() or 'default' in file.lower():
                        file_path = os.path.join(config_dir, file)
                        # Verificar que exporta un objeto con propiedades SCREAMING_SNAKE_CASE
                        content = read_file_safe(file_path)
                        if content and self._is_feature_flags_file(content):
                            return file_path
        
        # Estrategia 3: Buscar cualquier archivo en config/ que tenga estructura de feature flags
        if os.path.exists(config_dir):
            for root, dirs, files in os.walk(config_dir):
                for file in files:
                    if file.endswith(('.js', '.ts')):
                        file_path = os.path.join(root, file)
                        content = read_file_safe(file_path)
                        if content and self._is_feature_flags_file(content):
                            return file_path
        
        return None
    
    def _is_feature_flags_file(self, content: str) -> bool:
        """
        Verifica si un archivo parece ser un archivo de feature flags.
        
        Busca patrones como:
        - Objeto con propiedades en SCREAMING_SNAKE_CASE
        - Export default de un objeto
        """
        # Buscar patrón de objeto con propiedades SCREAMING_SNAKE_CASE
        # Ejemplo: FLAG_NAME: true,
        flag_pattern = r'[A-Z][A-Z0-9_]+:\s*[^,}]+[,}]'
        matches = re.findall(flag_pattern, content)
        
        # Si tiene al menos 3 propiedades en SCREAMING_SNAKE_CASE, probablemente es un archivo de flags
        if len(matches) >= 3:
            # Verificar que tiene export default
            if re.search(r'export\s+default', content):
                return True
        
        return False
    
    def extract_feature_flags(self, file_content: str, file_path: str) -> List[Dict[str, Any]]:
        """
        Extrae feature flags del contenido del archivo.
        
        Args:
            file_content: Contenido del archivo
            file_path: Ruta del archivo
            
        Returns:
            Lista de diccionarios con información de feature flags
        """
        flags = []
        
        # Buscar el inicio del objeto de features
        # Patrón para encontrar el inicio: const defaultFeatures = { o export default {
        start_pattern = r'(?:const\s+\w+\s*=\s*|export\s+default\s+)\{'
        start_match = re.search(start_pattern, file_content)
        
        if not start_match:
            return flags
        
        # Encontrar el cierre correcto del objeto contando llaves
        # Necesitamos ignorar llaves dentro de strings y comentarios
        start_pos = start_match.end() - 1  # Posición de la llave de apertura {
        brace_count = 0
        in_string = False
        string_char = None
        in_single_line_comment = False
        in_multi_line_comment = False
        i = start_pos
        
        while i < len(file_content):
            char = file_content[i]
            prev_char = file_content[i-1] if i > 0 else ''
            next_char = file_content[i+1] if i < len(file_content) - 1 else ''
            
            # Manejar comentarios de una línea
            if not in_string and not in_multi_line_comment and char == '/' and next_char == '/':
                in_single_line_comment = True
            elif in_single_line_comment and char == '\n':
                in_single_line_comment = False
            
            # Manejar comentarios de múltiples líneas
            if not in_string and not in_single_line_comment and char == '/' and next_char == '*':
                in_multi_line_comment = True
                i += 1  # Saltar el siguiente carácter
            elif in_multi_line_comment and char == '*' and next_char == '/':
                in_multi_line_comment = False
                i += 1  # Saltar el siguiente carácter
            
            # Manejar strings para ignorar llaves dentro de strings
            if not in_string and not in_single_line_comment and not in_multi_line_comment:
                if char == '"' or char == "'" or char == '`':
                    in_string = True
                    string_char = char
            elif in_string and char == string_char and prev_char != '\\':
                in_string = False
                string_char = None
            
            # Contar llaves solo si no estamos dentro de un string o comentario
            if not in_string and not in_single_line_comment and not in_multi_line_comment:
                if char == '{':
                    brace_count += 1
                elif char == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        # Encontramos el cierre correcto
                        object_content = file_content[start_pos + 1:i]
                        break
            i += 1
        else:
            # No se encontró el cierre, usar el patrón anterior como fallback
            object_pattern = r'(?:const\s+\w+\s*=\s*|export\s+default\s+)\{([\s\S]*)\}'
            match = re.search(object_pattern, file_content, re.DOTALL)
            if not match:
                return flags
            object_content = match.group(1)
        
        # Dividir por líneas pero mantener contexto de comentarios
        lines = object_content.split('\n')
        current_flag = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Saltar líneas vacías y comentarios de bloque completos
            if not line or line.startswith('//') or line.startswith('*'):
                continue
            
            # Buscar definición de flag: FLAG_NAME: value,
            flag_match = re.match(r'([A-Z][A-Z0-9_]+)\s*:\s*(.+?)(?:,\s*)?$', line)
            
            if flag_match:
                flag_name = flag_match.group(1)
                value_str = flag_match.group(2).strip()
                
                # Extraer comentario inline si existe (antes de procesar el valor)
                comment_match = re.search(r'//\s*(.+)$', value_str)
                description = None
                possible_values = []
                
                if comment_match:
                    comment = comment_match.group(1).strip()
                    description = comment
                    # Extraer el valor sin el comentario
                    value_str = value_str[:comment_match.start()].strip()
                    # Extraer valores posibles de enums (ej: // CLASSIC | FLAT)
                    possible_values = self._extract_possible_values(comment)
                
                # Remover coma final si existe (después de quitar comentario)
                value_str = value_str.rstrip(',').strip()
                
                # Parsear valor y tipo
                default_value, value_type = self._parse_flag_value(value_str)
                
                # Si no hay descripción, buscar en línea anterior
                if not description:
                    if i > 0:
                        prev_line = lines[i - 1].strip()
                        if prev_line.startswith('//'):
                            description = prev_line.lstrip('//').strip()
                
                flag_info = {
                    'name': flag_name,
                    'default_value': default_value,
                    'value_type': value_type,
                    'description': description,
                    'possible_values': possible_values,
                }
                
                flags.append(flag_info)
        
        return flags
    
    def _parse_flag_value(self, value_str: str) -> Tuple[Any, str]:
        """
        Parsea el valor de un flag y determina su tipo.
        
        Args:
            value_str: String con el valor del flag
            
        Returns:
            Tupla (valor_parseado, tipo)
        """
        value_str = value_str.strip()
        
        # Boolean
        if value_str.lower() in ('true', 'false'):
            return value_str.lower() == 'true', 'boolean'
        
        # Number
        if value_str.isdigit() or (value_str.startswith('-') and value_str[1:].isdigit()):
            return int(value_str), 'number'
        
        # Float
        try:
            float_val = float(value_str)
            return float_val, 'number'
        except ValueError:
            pass
        
        # String (entre comillas)
        if (value_str.startswith("'") and value_str.endswith("'")) or \
           (value_str.startswith('"') and value_str.endswith('"')):
            return value_str[1:-1], 'string'
        
        # Array
        if value_str.startswith('[') and value_str.endswith(']'):
            # Array vacío
            if value_str.strip() == '[]':
                return [], 'array'
            # Array con valores - intentar parsear valores básicos
            try:
                # Remover corchetes y dividir por comas
                inner = value_str[1:-1].strip()
                if not inner:
                    return [], 'array'
                # Intentar parsear como JSON para arrays simples
                parsed = json.loads(value_str)
                return parsed, 'array'
            except:
                # Si falla, retornar array vacío pero marcar como array
                return [], 'array'
        
        # Object
        if value_str.startswith('{') and value_str.endswith('}'):
            # Objeto vacío
            if value_str.strip() == '{}':
                return {}, 'object'
            # Intentar parsear como JSON para objetos simples
            try:
                parsed = json.loads(value_str)
                return parsed, 'object'
            except:
                # Si falla, retornar objeto vacío pero marcar como object
                return {}, 'object'
        
        # String sin comillas (fallback)
        return value_str, 'string'
    
    def _extract_possible_values(self, comment: str) -> List[str]:
        """
        Extrae valores posibles de un comentario de enum.
        
        Ejemplos:
        - "CLASSIC | FLAT" -> ['CLASSIC', 'FLAT']
        - "12 | 24" -> ['12', '24']
        - "transporter-key | purchase-token" -> ['transporter-key', 'purchase-token']
        
        Args:
            comment: Comentario inline
            
        Returns:
            Lista de valores posibles
        """
        # Buscar patrón: valor1 | valor2 | valor3
        if '|' in comment:
            values = [v.strip() for v in comment.split('|')]
            # Limitar a valores que parecen válidos (no muy largos)
            return [v for v in values if len(v) < 50]
        
        return []

