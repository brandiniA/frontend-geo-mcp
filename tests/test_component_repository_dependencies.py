"""
Tests adicionales para ComponentRepository con dependencias.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from src.registry.repositories.component_repository import ComponentRepository
from src.models import Component, Hook


class TestComponentRepositoryDependencies:
    """Tests para ComponentRepository con resolución de dependencias."""
    
    @pytest.fixture
    def mock_session_factory(self):
        """Fixture para mock de session factory"""
        return Mock()
    
    @pytest.fixture
    def component_repo(self, mock_session_factory):
        """Fixture para ComponentRepository"""
        repo = ComponentRepository(mock_session_factory)
        repo.SessionLocal = mock_session_factory
        return repo
    
    @pytest.mark.asyncio
    @patch('src.registry.repositories.component_repository.resolve_imports_to_components')
    @patch('src.registry.repositories.component_repository.db_session')
    async def test_save_with_component_imports(self, mock_db_session, mock_resolve, component_repo):
        """Test que save resuelve y guarda dependencias cuando hay component_imports"""
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session
        mock_db_session.return_value.__exit__.return_value = None
        
        # Mock de hooks - session.query(Hook.name) retorna un query que luego se filtra
        mock_hook_name_query = Mock()
        mock_hook_name_query.filter.return_value = mock_hook_name_query
        mock_hook_name_query.all.return_value = []  # Lista vacía de tuplas
        
        # Mock de query para ComponentDependency
        mock_dep_query = Mock()
        mock_dep_query.filter.return_value = mock_dep_query
        mock_dep_query.first.return_value = None  # No existe
        
        # Configurar query para retornar diferentes cosas según el argumento
        def mock_query(arg):
            # Si es Hook.name (un InstrumentedAttribute), verificar por el atributo 'key'
            if hasattr(arg, 'key') and arg.key == 'name':
                return mock_hook_name_query
            # Si es ComponentDependency (clase)
            elif hasattr(arg, '__name__') and arg.__name__ == 'ComponentDependency':
                return mock_dep_query
            else:
                return Mock()
        
        mock_session.query = Mock(side_effect=mock_query)
        
        # Mock de componente guardado
        mock_comp = Mock()
        mock_comp.id = 1
        mock_comp.name = 'TestComponent'
        mock_comp.file_path = 'components/TestComponent.tsx'
        
        # Mock de safe_upsert
        with patch('src.registry.repositories.component_repository.safe_upsert', return_value=mock_comp):
            # Mock de resolución de dependencias
            mock_resolve.return_value = [
                {
                    'depends_on_component_id': 2,
                    'depends_on_name': 'Button',
                    'from_path': './Button',
                    'import_type': 'named',
                    'is_external': False
                }
            ]
            
            components = [
                {
                    'name': 'TestComponent',
                    'file_path': 'components/TestComponent.tsx',
                    'props': [],
                    'native_hooks_used': [],
                    'custom_hooks_used': [],
                    'imports': [],
                    'component_imports': [
                        {
                            'imported_names': ['Button'],
                            'from_path': './Button',
                            'import_type': 'named'
                        }
                    ],
                    'exports': [],
                    'component_type': 'component',
                    'description': None,
                    'jsdoc': None
                }
            ]
            
            result = await component_repo.save(components, 'test-project')
            
            assert result == 1
            # Verificar que se llamó resolve_imports_to_components
            mock_resolve.assert_called_once()
            # Verificar que se intentó guardar dependencias
            assert mock_session.add.called or mock_dep_query.first.called

