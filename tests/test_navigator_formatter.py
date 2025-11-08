"""
Tests para utilidades de formateo de navegador (navigator_formatter).
"""

import pytest
from src.tools.utils.navigator_formatter import (
    COMPONENT_TYPE_ICONS,
    get_component_type_icon,
    format_jsdoc_section,
    format_hooks_section,
    format_hooks_inline,
    format_components_by_type,
    format_component_summary,
    format_project_header,
    truncate_description,
    format_usage_example,
)


class TestComponentTypeIcons:
    """Tests para iconos de tipos de componentes."""
    
    def test_component_type_icons_contains_all_types(self):
        """Test que COMPONENT_TYPE_ICONS contiene todos los tipos esperados."""
        assert 'page' in COMPONENT_TYPE_ICONS
        assert 'component' in COMPONENT_TYPE_ICONS
        assert 'layout' in COMPONENT_TYPE_ICONS
        assert 'hook' in COMPONENT_TYPE_ICONS
    
    def test_get_component_type_icon_valid_types(self):
        """Test obtener iconos para tipos válidos."""
        assert get_component_type_icon('page') == '📄'
        assert get_component_type_icon('component') == '🧩'
        assert get_component_type_icon('layout') == '📐'
        assert get_component_type_icon('hook') == '🪝'
    
    def test_get_component_type_icon_invalid_type(self):
        """Test obtener icono para tipo inválido retorna default."""
        assert get_component_type_icon('unknown') == '📦'
        assert get_component_type_icon('invalid') == '📦'


class TestFormatJSDocSection:
    """Tests para formateo de secciones JSDoc."""
    
    def test_format_jsdoc_with_description(self):
        """Test formateo con descripción."""
        jsdoc = {'description': 'A test component'}
        result = format_jsdoc_section(jsdoc)
        assert '### 📝 Overview' in result
        assert 'A test component' in result
    
    def test_format_jsdoc_params_without_description(self):
        """Test formateo de parámetros sin descripción."""
        jsdoc = {
            'params': [
                {'name': 'label', 'type': 'string'}  # Sin description
            ]
        }
        result = format_jsdoc_section(jsdoc)
        assert '### 📥 Parameters' in result
        assert '`label`' in result
        assert '`string`' in result
        # Debe funcionar sin description
    
    def test_format_jsdoc_with_returns(self):
        """Test formateo con returns."""
        jsdoc = {
            'returns': {
                'type': 'JSX.Element',
                'description': 'Rendered button component'
            }
        }
        result = format_jsdoc_section(jsdoc)
        assert '### 📤 Returns' in result
        assert '`JSX.Element`' in result
        assert 'Rendered button component' in result
    
    def test_format_jsdoc_with_examples(self):
        """Test formateo con ejemplos."""
        jsdoc = {
            'examples': [
                '<Button label="Click me" />',
                '<Button label="Submit" onClick={handleClick} />'
            ]
        }
        result = format_jsdoc_section(jsdoc)
        assert '### 💡 Examples' in result
        assert '**Example 1:**' in result
        assert '**Example 2:**' in result
        assert '```tsx' in result
    
    def test_format_jsdoc_with_metadata(self):
        """Test formateo con metadata (deprecated, author, version)."""
        jsdoc = {
            'deprecated': True,
            'author': 'John Doe',
            'version': '1.0.0'
        }
        result = format_jsdoc_section(jsdoc)
        assert 'DEPRECATED' in result
        assert 'John Doe' in result
        assert '1.0.0' in result
    
    def test_format_jsdoc_empty(self):
        """Test formateo con JSDoc vacío."""
        jsdoc = {}
        result = format_jsdoc_section(jsdoc)
        assert result == ""


class TestFormatHooksSection:
    """Tests para formateo de secciones de hooks."""
    
    def test_format_hooks_section_native_only(self):
        """Test formateo solo con hooks nativos."""
        component = {'native_hooks_used': ['useState', 'useEffect']}
        result = format_hooks_section(component)
        assert '### 🪝 Hooks Used' in result
        assert '**Native Hooks:**' in result
        assert '`useState`' in result
        assert '`useEffect`' in result
    
    def test_format_hooks_section_custom_only(self):
        """Test formateo solo con hooks custom."""
        component = {'custom_hooks_used': ['useAuth', 'useTheme']}
        result = format_hooks_section(component)
        assert '**Custom Hooks:**' in result
        assert '`useAuth`' in result
        assert '`useTheme`' in result
    
    def test_format_hooks_section_both(self):
        """Test formateo con ambos tipos de hooks."""
        component = {
            'native_hooks_used': ['useState'],
            'custom_hooks_used': ['useAuth']
        }
        result = format_hooks_section(component)
        assert '**Native Hooks:**' in result
        assert '**Custom Hooks:**' in result
    
    def test_format_hooks_section_with_limit(self):
        """Test formateo con límite de hooks."""
        component = {'native_hooks_used': ['useState', 'useEffect', 'useContext', 'useReducer', 'useCallback', 'useMemo']}
        result = format_hooks_section(component, max_hooks=3)
        assert '`useState`' in result
        assert '`useEffect`' in result
        assert '`useContext`' in result
        assert '... and 3 more' in result
    
    def test_format_hooks_section_show_native_false(self):
        """Test formateo con show_native=False."""
        component = {
            'native_hooks_used': ['useState'],
            'custom_hooks_used': ['useAuth']
        }
        result = format_hooks_section(component, show_native=False)
        assert '**Native Hooks:**' not in result
        assert '**Custom Hooks:**' in result
    
    def test_format_hooks_section_show_custom_false(self):
        """Test formateo con show_custom=False."""
        component = {
            'native_hooks_used': ['useState'],
            'custom_hooks_used': ['useAuth']
        }
        result = format_hooks_section(component, show_custom=False)
        assert '**Native Hooks:**' in result
        assert '**Custom Hooks:**' not in result


class TestFormatHooksInline:
    """Tests para formateo inline de hooks."""
    
    def test_format_hooks_inline_native(self):
        """Test formateo inline de hooks nativos."""
        component = {'native_hooks_used': ['useState', 'useEffect']}
        native_str, custom_str = format_hooks_inline(component, max_items=5)
        assert native_str == 'useState, useEffect'
        assert custom_str == ""
    
    def test_format_hooks_inline_custom(self):
        """Test formateo inline de hooks custom."""
        component = {'custom_hooks_used': ['useAuth', 'useTheme']}
        native_str, custom_str = format_hooks_inline(component, max_items=5)
        assert native_str == ""
        assert custom_str == 'useAuth, useTheme'
    
    def test_format_hooks_inline_with_limit(self):
        """Test formateo inline con límite."""
        component = {'native_hooks_used': ['useState', 'useEffect', 'useContext', 'useReducer', 'useCallback', 'useMemo']}
        native_str, custom_str = format_hooks_inline(component, max_items=3)
        assert 'useState, useEffect, useContext' in native_str
        assert '(+3 more)' in native_str


class TestFormatComponentsByType:
    """Tests para formateo de componentes agrupados por tipo."""
    
    def test_format_components_by_type_basic(self):
        """Test formateo básico agrupado por tipo."""
        components = [
            {'name': 'Button', 'file_path': 'src/Button.tsx', 'component_type': 'component'},
            {'name': 'HomePage', 'file_path': 'src/HomePage.tsx', 'component_type': 'page'},
        ]
        result = format_components_by_type(components)
        assert '### 🧩 Components (1)' in result
        assert '### 📄 Pages (1)' in result
        assert '**Button**' in result
        assert '**HomePage**' in result
    
    def test_format_components_by_type_with_new_badge(self):
        """Test formateo con badge de nuevo."""
        from datetime import datetime, timedelta
        recent_date = (datetime.now() - timedelta(days=3)).isoformat()
        old_date = (datetime.now() - timedelta(days=10)).isoformat()
        
        components = [
            {'name': 'NewButton', 'file_path': 'src/NewButton.tsx', 'component_type': 'component', 'created_at': recent_date},
            {'name': 'OldButton', 'file_path': 'src/OldButton.tsx', 'component_type': 'component', 'created_at': old_date},
        ]
        result = format_components_by_type(components, show_new_badge=True)
        assert '🆕' in result
        assert result.count('🆕') == 1  # Solo uno es nuevo
    
    def test_format_components_by_type_with_limit(self):
        """Test formateo con límite por tipo."""
        components = [
            {'name': f'Button{i}', 'file_path': f'src/Button{i}.tsx', 'component_type': 'component'}
            for i in range(25)
        ]
        result = format_components_by_type(components, max_per_type=20)
        assert '... and 5 more' in result
    
    def test_format_components_by_type_empty(self):
        """Test formateo con lista vacía."""
        result = format_components_by_type([])
        assert result == "📂 No components found"


class TestFormatComponentSummary:
    """Tests para formateo de resumen de componente."""
    
    def test_format_component_summary_basic(self):
        """Test formateo básico de resumen."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx',
            'component_type': 'component'
        }
        result = format_component_summary(component)
        assert '**Button**' in result
        assert '📂 Path:' in result
        assert '🏷️  Type:' in result
    
    def test_format_component_summary_with_props(self):
        """Test formateo con props."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx',
            'component_type': 'component',
            'props': ['label', 'onClick', 'disabled']
        }
        result = format_component_summary(component, include_props=True)
        assert '📦 Props:' in result
        assert 'label' in result
    
    def test_format_component_summary_with_hooks(self):
        """Test formateo con hooks."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx',
            'component_type': 'component',
            'native_hooks_used': ['useState'],
            'custom_hooks_used': ['useAuth']
        }
        result = format_component_summary(component, include_hooks=True)
        assert '🪝 Native Hooks:' in result
        assert '🎣 Custom Hooks:' in result
    
    def test_format_component_summary_with_import(self):
        """Test formateo con import statement."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx',
            'component_type': 'component'
        }
        result = format_component_summary(component, include_import=True)
        assert '🔗 Import:' in result
        assert 'import' in result
        assert 'Button' in result
    
    def test_format_component_summary_with_description(self):
        """Test formateo con descripción."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx',
            'component_type': 'component',
            'description': 'A reusable button component'
        }
        result = format_component_summary(component, include_description=True)
        assert '📝 Description:' in result
        assert 'A reusable button component' in result


class TestFormatProjectHeader:
    """Tests para formateo de header de proyecto."""
    
    def test_format_project_header_with_project(self):
        """Test formateo con información de proyecto."""
        project = {'name': 'My Project', 'type': 'web'}
        result = format_project_header(project, 'project-id')
        assert '### 🏢 MY PROJECT (web)' in result
    
    def test_format_project_header_without_project(self):
        """Test formateo sin información de proyecto."""
        result = format_project_header(None, 'project-id')
        assert '### 🏢 PROJECT-ID' in result
    
    def test_format_project_header_missing_fields(self):
        """Test formateo con proyecto parcial."""
        project = {'name': 'My Project'}  # Sin type
        result = format_project_header(project, 'project-id')
        assert 'MY PROJECT' in result
        assert 'unknown' in result


class TestTruncateDescription:
    """Tests para truncado de descripciones."""
    
    def test_truncate_description_short(self):
        """Test truncado de descripción corta."""
        desc = "Short description"
        result = truncate_description(desc, max_length=100)
        assert result == "Short description"
    
    def test_truncate_description_long(self):
        """Test truncado de descripción larga."""
        desc = "A" * 150
        result = truncate_description(desc, max_length=100)
        assert len(result) == 103  # 100 + "..."
        assert result.endswith("...")
    
    def test_truncate_description_empty(self):
        """Test truncado de descripción vacía."""
        result = truncate_description("", max_length=100)
        assert result == ""
    
    def test_truncate_description_none(self):
        """Test truncado de descripción None."""
        result = truncate_description(None, max_length=100)
        assert result == ""


class TestFormatUsageExample:
    """Tests para formateo de ejemplos de uso."""
    
    def test_format_usage_example_basic(self):
        """Test formateo básico de ejemplo."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx'
        }
        result = format_usage_example(component)
        assert '### 💡 Basic Usage' in result
        assert '```tsx' in result
        assert 'import' in result
        assert 'Button' in result
        assert '<Button />' in result
    
    def test_format_usage_example_with_props(self):
        """Test formateo con props."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx',
            'props': ['label', 'onClick', 'disabled']
        }
        result = format_usage_example(component, include_props=True)
        assert 'label' in result
        assert 'onClick' in result
        assert 'disabled' in result
    
    def test_format_usage_example_with_many_props(self):
        """Test formateo con muchas props (debe truncar)."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx',
            'props': ['label', 'onClick', 'disabled', 'variant', 'size', 'loading']
        }
        result = format_usage_example(component, include_props=True, max_props=3)
        assert 'label' in result
        assert 'onClick' in result
        assert 'disabled' in result
        assert '... and 3 more props' in result
    
    def test_format_usage_example_without_props(self):
        """Test formateo sin props."""
        component = {
            'name': 'Button',
            'file_path': 'src/components/Button.tsx',
            'props': []
        }
        result = format_usage_example(component, include_props=True)
        assert '<Button />' in result
        assert 'label' not in result

