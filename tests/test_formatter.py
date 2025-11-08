"""
Tests para utilidades de formateo (formatter).
"""

import pytest
from datetime import datetime, timedelta
from src.tools.utils.formatter import (
    generate_import_path,
    format_component_entry,
    format_component_with_details,
)


class TestGenerateImportPath:
    """Tests para generate_import_path."""
    
    def test_with_src_prefix_and_tsx(self):
        """Test con prefijo src/ y extensión .tsx."""
        result = generate_import_path('src/components/Button.tsx')
        
        assert result == './components/Button'
    
    def test_with_src_prefix_and_jsx(self):
        """Test con prefijo src/ y extensión .jsx."""
        result = generate_import_path('src/components/Card.jsx')
        
        assert result == './components/Card'
    
    def test_with_module_prefix(self):
        """Test con prefijo de módulo (@)."""
        result = generate_import_path('@ui/components/Card.jsx')
        
        assert result == '@ui/components/Card'
    
    def test_without_src_prefix(self):
        """Test sin prefijo src/."""
        # Nota: generate_import_path solo remueve .tsx y .jsx, no .ts o .js
        result = generate_import_path('hooks/useAuth.ts')
        
        assert result == './hooks/useAuth.ts'
    
    def test_already_has_dot_slash(self):
        """Test que ya tiene ./."""
        result = generate_import_path('./components/Button.tsx')
        
        assert result == './components/Button'
    
    def test_with_js_extension(self):
        """Test con extensión .js (no se remueve)."""
        result = generate_import_path('src/components/Button.js')
        
        assert result == './components/Button.js'
    
    def test_with_ts_extension(self):
        """Test con extensión .ts (no se remueve)."""
        result = generate_import_path('src/components/Button.ts')
        
        assert result == './components/Button.ts'
    
    def test_root_level_file(self):
        """Test con archivo en raíz."""
        result = generate_import_path('src/index.tsx')
        
        assert result == './index'


class TestFormatComponentEntry:
    """Tests para format_component_entry."""
    
    def test_basic_entry(self):
        """Test entrada básica."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx'
        }
        
        result = format_component_entry(component)
        
        assert '**Button**' in result
        assert 'src/components/Button.tsx' in result
    
    def test_with_new_badge(self):
        """Test con badge de nuevo."""
        component = {
            'name': 'NewButton',
            'file_path': 'src/components/NewButton.tsx',
            'created_at': datetime.now() - timedelta(days=2)
        }
        
        result = format_component_entry(component, show_new_badge=True)
        
        assert '🆕' in result
    
    def test_without_new_badge(self):
        """Test sin badge de nuevo."""
        component = {
            'name': 'OldButton',
            'file_path': 'src/components/OldButton.tsx',
            'created_at': datetime.now() - timedelta(days=10)
        }
        
        result = format_component_entry(component, show_new_badge=True)
        
        assert '🆕' not in result
    
    def test_with_description(self):
        """Test con descripción."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx',
            'description': 'A reusable button component'
        }
        
        result = format_component_entry(component, show_description=True)
        
        assert 'A reusable button component' in result
    
    def test_without_description(self):
        """Test sin descripción cuando show_description=True."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx'
        }
        
        result = format_component_entry(component, show_description=True)
        
        assert 'description' not in result.lower()
    
    def test_with_missing_name(self):
        """Test con nombre faltante."""
        component = {
            'file_path': 'src/components/Button.tsx'
        }
        
        result = format_component_entry(component)
        
        assert 'Unknown' in result
    
    def test_with_missing_file_path(self):
        """Test con file_path faltante."""
        component = {
            'name': 'Button'
        }
        
        result = format_component_entry(component)
        
        assert 'unknown' in result


class TestFormatComponentWithDetails:
    """Tests para format_component_with_details."""
    
    def test_basic_formatting(self):
        """Test formateo básico."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx',
            'component_type': 'component'
        }
        
        result = format_component_with_details(component)
        
        assert '**Button**' in result
        assert 'src/components/Button.tsx' in result
        assert 'component' in result
    
    def test_with_props(self):
        """Test con props."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx',
            'props': ['onClick', 'text', 'variant']
        }
        
        result = format_component_with_details(component, include_props=True)
        
        assert 'Props' in result
        assert 'onClick' in result
        assert 'text' in result
        assert 'variant' in result
    
    def test_without_props(self):
        """Test sin incluir props."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx',
            'props': ['onClick', 'text']
        }
        
        result = format_component_with_details(component, include_props=False)
        
        assert 'Props' not in result
    
    def test_with_hooks(self):
        """Test con hooks."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx',
            'native_hooks_used': ['useState', 'useEffect']
        }
        
        result = format_component_with_details(component, include_hooks=True)
        
        assert 'Hooks' in result
        assert 'useState' in result
        assert 'useEffect' in result
    
    def test_without_hooks(self):
        """Test sin incluir hooks."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx',
            'native_hooks_used': ['useState']
        }
        
        result = format_component_with_details(component, include_hooks=False)
        
        assert 'Hooks' not in result
    
    def test_without_type(self):
        """Test sin incluir tipo."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx',
            'component_type': 'component'
        }
        
        result = format_component_with_details(component, include_type=False)
        
        assert 'Type' not in result
    
    def test_with_description(self):
        """Test con descripción."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx',
            'description': 'A reusable button'
        }
        
        result = format_component_with_details(component)
        
        assert 'Description' in result
        assert 'A reusable button' in result
    
    def test_with_max_items(self):
        """Test con max_items limitando la salida."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx',
            'props': ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        }
        
        result = format_component_with_details(component, max_items=3)
        
        assert 'a' in result
        assert 'b' in result
        assert 'c' in result
        assert '(+4 more)' in result
    
    def test_with_custom_hooks(self):
        """Test con custom hooks."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx',
            'custom_hooks_used': ['useAuth', 'useTheme']
        }
        
        result = format_component_with_details(component, include_hooks=True)
        
        assert 'useAuth' in result
        assert 'useTheme' in result
    
    def test_with_both_hook_types(self):
        """Test con hooks nativos y custom."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx',
            'native_hooks_used': ['useState'],
            'custom_hooks_used': ['useAuth']
        }
        
        result = format_component_with_details(component, include_hooks=True)
        
        assert 'useState' in result
        assert 'useAuth' in result
    
    def test_with_missing_fields(self):
        """Test con campos faltantes."""
        component = {
            'name': 'Button'
        }
        
        result = format_component_with_details(component)
        
        assert '**Button**' in result
        assert 'unknown' in result

