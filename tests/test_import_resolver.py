"""
Tests para import_resolver.
"""

import pytest
from unittest.mock import Mock, MagicMock
from src.utils.import_resolver import (
    is_external_import,
    resolve_relative_path,
    normalize_path,
    resolve_imports_to_components,
)


class TestImportResolver:
    """Tests para funciones de resolución de imports."""
    
    def test_is_external_import_relative(self):
        """Test que imports relativos no son externos"""
        assert is_external_import('./components') == False
        assert is_external_import('../utils') == False
    
    def test_is_external_import_react(self):
        """Test que react es externo"""
        assert is_external_import('react') == True
        assert is_external_import('react-dom') == True
    
    def test_is_external_import_npm_packages(self):
        """Test que librerías npm comunes son externas"""
        assert is_external_import('lodash') == True
        assert is_external_import('axios') == True
        assert is_external_import('next') == True
    
    def test_is_external_import_alias(self):
        """Test que alias @ puede ser interno o externo"""
        # @types es externo
        assert is_external_import('@types/react') == True
        # @components puede ser interno (alias del proyecto)
        assert is_external_import('@components/Button') == False
    
    def test_resolve_relative_path(self):
        """Test resolución de rutas relativas"""
        current = 'src/pages/HomePage.tsx'
        
        assert resolve_relative_path('./components', current) == 'src/pages/components'
        assert resolve_relative_path('../components', current) == 'src/components'
        assert resolve_relative_path('react', current) == 'react'  # No cambia absolutos
    
    def test_normalize_path(self):
        """Test normalización de rutas"""
        assert normalize_path('src/components/Button.tsx') == 'components/Button'
        assert normalize_path('components/Button.tsx') == 'components/Button'
        assert normalize_path('Button.tsx') == 'Button'
        assert normalize_path('src/pages/Home.tsx') == 'pages/Home'
    
    def test_resolve_imports_to_components_with_mock(self):
        """Test resolución de imports a componentes con mock de sesión"""
        # Mock de componente
        mock_comp = Mock()
        mock_comp.id = 1
        mock_comp.name = 'Button'
        mock_comp.file_path = 'components/Button.tsx'
        mock_comp.to_dict = Mock(return_value={'id': 1, 'name': 'Button', 'file_path': 'components/Button.tsx'})
        
        # Mock de sesión
        mock_session = Mock()
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_comp
        mock_query.all.return_value = [mock_comp]
        
        component_imports = [
            {
                'imported_names': ['Button'],
                'from_path': './Button',
                'import_type': 'default'
            }
        ]
        
        result = resolve_imports_to_components(
            component_imports=component_imports,
            project_id='test-project',
            current_file_path='src/pages/HomePage.tsx',
            component_name='HomePage',
            db_session=mock_session
        )
        
        assert len(result) > 0
        assert result[0]['depends_on_name'] == 'Button'
        assert result[0]['is_external'] == False
    
    def test_resolve_external_imports(self):
        """Test que imports externos se marcan correctamente"""
        mock_session = Mock()
        
        component_imports = [
            {
                'imported_names': ['useState'],
                'from_path': 'react',
                'import_type': 'named'
            }
        ]
        
        result = resolve_imports_to_components(
            component_imports=component_imports,
            project_id='test-project',
            current_file_path='src/Component.tsx',
            component_name='Component',
            db_session=mock_session
        )
        
        assert len(result) > 0
        assert result[0]['is_external'] == True
        assert result[0]['depends_on_component_id'] is None

