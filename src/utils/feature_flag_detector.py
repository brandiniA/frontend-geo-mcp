"""
Detector de uso de feature flags en componentes React.
"""

import re
from typing import List, Dict, Set


class FeatureFlagUsageDetector:
    """Detector para encontrar uso de feature flags en código de componentes."""
    
    def detect_flag_usage(self, content: str, flag_names: List[str]) -> List[Dict[str, str]]:
        """
        Detecta uso de feature flags específicos en el contenido del componente.
        
        Args:
            content: Contenido del archivo del componente
            flag_names: Lista de nombres de flags a buscar
            
        Returns:
            Lista de diccionarios con formato: {'flag_name': 'FLAG_NAME', 'pattern': 'features.FLAG_NAME'}
        """
        detected_flags = []
        flag_names_set = set(flag_names)
        
        for flag_name in flag_names:
            patterns_found = self._find_flag_patterns(content, flag_name)
            if patterns_found:
                detected_flags.extend(patterns_found)
        
        return detected_flags
    
    def _find_flag_patterns(self, content: str, flag_name: str) -> List[Dict[str, str]]:
        """
        Busca todos los patrones de uso de un flag específico.
        
        Args:
            content: Contenido del archivo
            flag_name: Nombre del flag a buscar
            
        Returns:
            Lista de diccionarios con flag_name y pattern detectado
        """
        patterns_found = []
        
        # Patrón 1: features.FLAG_NAME
        pattern1 = rf'features\.{re.escape(flag_name)}\b'
        if re.search(pattern1, content):
            patterns_found.append({
                'flag_name': flag_name,
                'pattern': f'features.{flag_name}'
            })
        
        # Patrón 1b: features?.FLAG_NAME (con optional chaining)
        pattern1b = rf'features\s*\?\.\s*{re.escape(flag_name)}\b'
        if re.search(pattern1b, content):
            patterns_found.append({
                'flag_name': flag_name,
                'pattern': f'features?.{flag_name}'
            })
        
        # Patrón 2: features['FLAG_NAME'] o features["FLAG_NAME"]
        pattern2 = rf"features\s*\[\s*['\"]{re.escape(flag_name)}['\"]\s*\]"
        if re.search(pattern2, content):
            patterns_found.append({
                'flag_name': flag_name,
                'pattern': f"features['{flag_name}']"
            })
        
        # Patrón 3: const { FLAG_NAME } = useWhitelabelFeatures() o const { FLAG1, FLAG2 } = useWhitelabelFeatures()
        # Buscar si el flag está en el destructuring (puede estar con otros flags)
        # El patrón busca: const { ... FLAG_NAME ... } = useWhitelabelFeatures()
        pattern3 = rf'const\s+\{{[^}}]*\b{re.escape(flag_name)}\b[^}}]*}}\s*=\s*useWhitelabelFeatures\s*\('
        if re.search(pattern3, content):
            patterns_found.append({
                'flag_name': flag_name,
                'pattern': f'const {{ {flag_name} }} = useWhitelabelFeatures()'
            })
        
        # Patrón 3b: Uso directo de variable después de destructuring
        # Buscar uso directo: {FLAG_NAME} o FLAG_NAME && o if (FLAG_NAME)
        # Solo si hay un destructuring de useWhitelabelFeatures en el archivo
        if re.search(r'useWhitelabelFeatures\s*\(', content):
            pattern3b = rf'(?:{{\s*{re.escape(flag_name)}\s*}}|{re.escape(flag_name)}\s*(?:&&|\|\||\?|===|!==))'
            if re.search(pattern3b, content):
                patterns_found.append({
                    'flag_name': flag_name,
                    'pattern': f'const {{ {flag_name} }} = useWhitelabelFeatures() -> direct usage'
                })
        
        # Patrón 4: const { features } = useSelector(...) y luego features.FLAG_NAME
        # Primero verificar si hay useSelector con features
        useSelector_pattern = r'const\s+\{\s*features\s*}\s*=\s*useSelector\s*\('
        if re.search(useSelector_pattern, content):
            # Luego buscar uso de features.FLAG_NAME después del useSelector
            pattern4 = rf'features\.{re.escape(flag_name)}\b'
            if re.search(pattern4, content):
                patterns_found.append({
                    'flag_name': flag_name,
                    'pattern': f'const {{ features }} = useSelector(...) -> features.{flag_name}'
                })
        
        # Patrón 5: whitelabelConfig.features.FLAG_NAME (en mapStateToProps)
        pattern5 = rf'whitelabelConfig\s*\.\s*features\s*\.\s*{re.escape(flag_name)}\b'
        if re.search(pattern5, content):
            patterns_found.append({
                'flag_name': flag_name,
                'pattern': f'whitelabelConfig.features.{flag_name}'
            })
        
        # Patrón 5b: whitelabelConfig?.features?.FLAG_NAME (con optional chaining)
        pattern5b = rf'whitelabelConfig\s*\?\.\s*features\s*\?\.\s*{re.escape(flag_name)}\b'
        if re.search(pattern5b, content):
            patterns_found.append({
                'flag_name': flag_name,
                'pattern': f'whitelabelConfig?.features?.{flag_name}'
            })
        
        # Patrón 5c: state.whitelabelConfig?.features?.FLAG_NAME (en mapStateToProps con optional chaining)
        pattern5c = rf'state\s*\.\s*whitelabelConfig\s*\?\.\s*features\s*\?\.\s*{re.escape(flag_name)}\b'
        if re.search(pattern5c, content):
            patterns_found.append({
                'flag_name': flag_name,
                'pattern': f'state.whitelabelConfig?.features?.{flag_name}'
            })
        
        # Patrón 6: Destructuring en mapStateToProps: whitelabelConfig: { features, env }
        # y luego uso de features.FLAG_NAME
        mapStateToProps_pattern = r'whitelabelConfig\s*:\s*\{\s*features'
        if re.search(mapStateToProps_pattern, content):
            pattern6 = rf'features\.{re.escape(flag_name)}\b'
            if re.search(pattern6, content):
                patterns_found.append({
                    'flag_name': flag_name,
                    'pattern': f'mapStateToProps -> features.{flag_name}'
                })
        
        # Patrón 7: Destructuring directo de features: const { FLAG_NAME } = features;
        # Este patrón detecta cuando se hace destructuring directo de features (desde props, useSelector, etc.)
        # Maneja casos de múltiples líneas: const { FLAG1, FLAG2 } = features;
        pattern7_destructure = rf'const\s+\{{[^}}]*\b{re.escape(flag_name)}\b[^}}]*}}\s*=\s*features'
        # También buscar en múltiples líneas
        pattern7_multiline = rf'const\s+\{{[^}}]*\b{re.escape(flag_name)}\b[^}}]*}}\s*=\s*\n\s*features'
        if re.search(pattern7_destructure, content) or re.search(pattern7_multiline, content, re.MULTILINE):
            patterns_found.append({
                'flag_name': flag_name,
                'pattern': f'const {{ {flag_name} }} = features'
            })
        
        # Patrón 8: Uso directo de variable después de destructuring de features
        # Si hay destructuring de features en el archivo, buscar uso directo de la variable
        # Buscar: const { ... } = features o const { features } = useSelector o features viene de props
        has_features_destructure = (
            re.search(r'const\s+\{[^}]*features[^}]*\}\s*=', content) or
            re.search(r'const\s+\{\s*features\s*}\s*=\s*useSelector', content) or
            re.search(r'whitelabelConfig\s*:\s*\{\s*features', content) or
            re.search(r'features\s*:\s*PropTypes', content) or
            re.search(r'const\s+\{\s*features\s*}\s*=\s*this\.props', content) or
            re.search(r'const\s+\{\s*features\s*}\s*=\s*props', content) or
            re.search(r'const\s+\{\s*features\s*}\s*=\s*useSelector', content)
        )
        
        if has_features_destructure:
            # Buscar uso directo de la variable (no features.FLAG_NAME sino solo FLAG_NAME)
            # En contextos específicos: if (FLAG_NAME && ...), FLAG_NAME ? ... : ..., FLAG_NAME &&, etc.
            # Evitar falsos positivos buscando en contextos válidos de uso
            pattern8_contexts = [
                rf'\b{re.escape(flag_name)}\s*(?:&&|\|\||\?|===|!==|\)|,|;|\s*&&|\s*\|\|)',  # if (FLAG && ...), FLAG &&
                rf'\({re.escape(flag_name)}\s*[&|?=!]',  # (FLAG && ...), (FLAG ? ...)
                rf'=\s*{re.escape(flag_name)}\s*[&|?]',  # const x = FLAG && ...
                rf'{re.escape(flag_name)}\s*\?',  # FLAG ? ... : ...
                rf'!\s*{re.escape(flag_name)}\b',  # !FLAG
                rf'\?\s*\.\s*{re.escape(flag_name)}\b',  # features?.FLAG_NAME (aunque esto ya está cubierto)
            ]
            
            for pattern8_usage in pattern8_contexts:
                if re.search(pattern8_usage, content):
                    patterns_found.append({
                        'flag_name': flag_name,
                        'pattern': f'const {{ ... }} = features -> direct usage: {flag_name}'
                    })
                    break  # Solo agregar una vez
        
        # Eliminar duplicados manteniendo el primer patrón encontrado
        seen = set()
        unique_patterns = []
        for item in patterns_found:
            key = (item['flag_name'], item['pattern'])
            if key not in seen:
                seen.add(key)
                unique_patterns.append(item)
        
        return unique_patterns
    
    def detect_orphaned_flags(self, content: str, defined_flags: Set[str]) -> List[str]:
        """
        Detecta flags usados en el código que NO están en la lista de flags definidos.
        
        Busca patrones genéricos de uso de flags y compara con la lista de definidos.
        
        Args:
            content: Contenido del archivo
            defined_flags: Set de nombres de flags definidos
            
        Returns:
            Lista de nombres de flags huérfanos (usados pero no definidos)
        """
        orphaned_flags = []
        
        # Buscar todos los patrones de flags en SCREAMING_SNAKE_CASE
        # Patrón: features.FLAG_NAME o features['FLAG_NAME']
        patterns = [
            r'features\.([A-Z][A-Z0-9_]+)\b',
            r"features\s*\[\s*['\"]([A-Z][A-Z0-9_]+)['\"]\s*\]",
            r'const\s+\{\s*([A-Z][A-Z0-9_]+)\s*}\s*=\s*useWhitelabelFeatures\s*\(',
            r'whitelabelConfig\s*\.\s*features\s*\.\s*([A-Z][A-Z0-9_]+)\b',
        ]
        
        found_flags = set()
        for pattern in patterns:
            matches = re.findall(pattern, content)
            found_flags.update(matches)
        
        # Filtrar flags que no están definidos
        for flag in found_flags:
            if flag not in defined_flags:
                orphaned_flags.append(flag)
        
        return list(set(orphaned_flags))  # Eliminar duplicados

