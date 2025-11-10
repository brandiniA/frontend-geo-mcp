"""
Tests unitarios para el parser de barrel exports.
"""

import pytest
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock
from src.utils.barrel_export_parser import (
    resolve_index_export,
    find_wrapped_component,
    resolve_barrel_component,
    get_directory_from_index_path,
    _is_container_name,
)


class TestResolveIndexExport:
    """Tests para la función resolve_index_export."""
    
    def test_parse_checkout_index_js(self, checkout_evidence_path):
        """Test: Parsear el index.js real de Checkout."""
        index_path = checkout_evidence_path / "index.js"
        
        result = resolve_index_export(str(index_path))
        
        assert result is not None
        assert result['exported_name'] == 'CheckoutContainer'
        assert result['source_file'] == './CheckoutContainer'
        assert result['export_type'] == 'default'
        assert result['is_container'] is True
    
    def test_parse_pattern_import_export_default(self, tmp_path):
        """Test: Patrón import X from './File'; export default X;"""
        index_file = tmp_path / "index.js"
        index_file.write_text("""
import MyComponent from './MyComponent';

export default MyComponent;
""")
        
        result = resolve_index_export(str(index_file))
        
        assert result is not None
        assert result['exported_name'] == 'MyComponent'
        assert result['source_file'] == './MyComponent'
        assert result['export_type'] == 'default'
        assert result['is_container'] is False
    
    def test_parse_pattern_export_default_from(self, tmp_path):
        """Test: Patrón export { default } from './File';"""
        index_file = tmp_path / "index.js"
        index_file.write_text("""
export { default } from './Button';
""")
        
        result = resolve_index_export(str(index_file))
        
        assert result is not None
        assert result['exported_name'] == 'Button'
        assert result['source_file'] == './Button'
        assert result['export_type'] == 'default'
    
    def test_parse_pattern_export_as_default(self, tmp_path):
        """Test: Patrón export { X as default } from './File';"""
        index_file = tmp_path / "index.js"
        index_file.write_text("""
export { ButtonContainer as default } from './ButtonContainer';
""")
        
        result = resolve_index_export(str(index_file))
        
        assert result is not None
        assert result['exported_name'] == 'ButtonContainer'
        assert result['source_file'] == './ButtonContainer'
        assert result['export_type'] == 'default'
        assert result['is_container'] is True
    
    def test_parse_pattern_export_default_as(self, tmp_path):
        """Test: Patrón export { default as X } from './File';"""
        index_file = tmp_path / "index.js"
        index_file.write_text("""
export { default as Card } from './Card';
""")
        
        result = resolve_index_export(str(index_file))
        
        assert result is not None
        assert result['exported_name'] == 'Card'
        assert result['source_file'] == './Card'
        assert result['export_type'] == 'default'
    
    def test_parse_with_comments(self, tmp_path):
        """Test: Parsear con comentarios en el código."""
        index_file = tmp_path / "index.js"
        index_file.write_text("""
// This is a barrel export for Modal
/* 
 * Multi-line comment
 * about the export
 */
import Modal from './Modal';
// Export the default
export default Modal;
""")
        
        result = resolve_index_export(str(index_file))
        
        assert result is not None
        assert result['exported_name'] == 'Modal'
        assert result['source_file'] == './Modal'
    
    def test_parse_nonexistent_file(self):
        """Test: Archivo que no existe."""
        result = resolve_index_export('/nonexistent/path/index.js')
        assert result is None
    
    def test_parse_empty_file(self, tmp_path):
        """Test: Archivo vacío."""
        index_file = tmp_path / "index.js"
        index_file.write_text("")
        
        result = resolve_index_export(str(index_file))
        assert result is None
    
    def test_parse_no_barrel_export(self, tmp_path):
        """Test: Archivo sin barrel export válido."""
        index_file = tmp_path / "index.js"
        index_file.write_text("""
const x = 5;
console.log(x);
""")
        
        result = resolve_index_export(str(index_file))
        assert result is None


class TestIsContainerName:
    """Tests para la función _is_container_name."""
    
    def test_container_suffix(self):
        """Test: Nombres con 'Container' al final."""
        assert _is_container_name('CheckoutContainer') is True
        assert _is_container_name('ButtonContainer') is True
        assert _is_container_name('MyContainer') is True
    
    def test_connected_suffix(self):
        """Test: Nombres con 'Connected'."""
        assert _is_container_name('ConnectedButton') is True
        assert _is_container_name('connected') is True
    
    def test_wrapper_suffix(self):
        """Test: Nombres con 'Wrapper'."""
        assert _is_container_name('ButtonWrapper') is True
        assert _is_container_name('Wrapper') is True
    
    def test_hoc_patterns(self):
        """Test: Patrones de HOC."""
        assert _is_container_name('withAuth') is True
        assert _is_container_name('withRouter') is True
        assert _is_container_name('EnhancedButton') is True
    
    def test_non_container_names(self):
        """Test: Nombres que no son containers."""
        assert _is_container_name('Button') is False
        assert _is_container_name('Modal') is False
        assert _is_container_name('Checkout') is False
        assert _is_container_name('MyComponent') is False
    
    def test_empty_or_none(self):
        """Test: Valores vacíos o None."""
        assert _is_container_name('') is False
        assert _is_container_name(None) is False


class TestFindWrappedComponent:
    """Tests para la función find_wrapped_component."""
    
    def test_find_wrapped_component_exists(self, mock_db_session):
        """Test: Encuentra componente envuelto."""
        # Mock component
        mock_component = Mock()
        mock_component.id = 123
        mock_component.container_file_path = 'components/Checkout/CheckoutContainer'
        
        # Mock query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_component
        mock_db_session.query.return_value = mock_query
        
        result = find_wrapped_component(
            'components/Checkout/CheckoutContainer',
            'test-project',
            mock_db_session
        )
        
        assert result == 123
    
    def test_find_wrapped_component_not_found(self, mock_db_session):
        """Test: No encuentra componente envuelto."""
        # Mock query returning None
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        result = find_wrapped_component(
            'components/NonExistent/Container',
            'test-project',
            mock_db_session
        )
        
        assert result is None


class TestResolveBarrelComponent:
    """Tests para la función resolve_barrel_component."""
    
    def test_resolve_container_component(self, mock_db_session):
        """Test: Resolver container que envuelve un componente."""
        # Mock component
        mock_component = Mock()
        mock_component.id = 456
        
        # Mock query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_component
        mock_db_session.query.return_value = mock_query
        
        result = resolve_barrel_component(
            './CheckoutContainer',
            is_container=True,
            directory_path='components/purchase/Checkout',
            project_id='test-project',
            db_session=mock_db_session
        )
        
        assert result == 456
    
    def test_resolve_direct_component(self, mock_db_session):
        """Test: Resolver componente directo (no container)."""
        # Mock component
        mock_component = Mock()
        mock_component.id = 789
        
        # Mock query
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = mock_component
        mock_db_session.query.return_value = mock_query
        
        result = resolve_barrel_component(
            './Button',
            is_container=False,
            directory_path='components/ui',
            project_id='test-project',
            db_session=mock_db_session
        )
        
        assert result == 789
    
    def test_resolve_component_not_found(self, mock_db_session):
        """Test: Componente no encontrado."""
        # Mock query returning None
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_db_session.query.return_value = mock_query
        
        result = resolve_barrel_component(
            './NonExistent',
            is_container=False,
            directory_path='components/ui',
            project_id='test-project',
            db_session=mock_db_session
        )
        
        assert result is None


class TestGetDirectoryFromIndexPath:
    """Tests para la función get_directory_from_index_path."""
    
    def test_get_directory_from_unix_path(self):
        """Test: Extraer directorio de ruta Unix."""
        index_path = '/repo/components/Checkout/index.js'
        result = get_directory_from_index_path(index_path)
        
        # El resultado depende de normalize_path
        # Debería ser algo como 'components/Checkout'
        assert 'Checkout' in result
    
    def test_get_directory_from_nested_path(self):
        """Test: Extraer directorio de ruta anidada."""
        index_path = '/repo/src/components/purchase/Checkout/index.tsx'
        result = get_directory_from_index_path(index_path)
        
        assert 'Checkout' in result

