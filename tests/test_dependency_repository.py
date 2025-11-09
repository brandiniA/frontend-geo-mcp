"""
Tests para DependencyRepository.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from contextlib import contextmanager
from src.registry.repositories.dependency_repository import DependencyRepository
from src.models import ComponentDependency, Component


class TestDependencyRepository:
    """Tests para DependencyRepository."""
    
    @pytest.fixture
    def mock_session_factory(self):
        """Fixture para mock de session factory"""
        mock_session = MagicMock()
        mock_session.query = Mock()
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.rollback = Mock()
        mock_session.close = Mock()
        
        # db_session llama a session_factory() y luego usa la sesión como context manager
        # Necesitamos que el factory retorne una sesión que pueda usarse con 'with'
        mock_factory = Mock()
        mock_factory.return_value = mock_session
        return mock_factory
    
    @pytest.fixture
    def dependency_repo(self, mock_session_factory):
        """Fixture para DependencyRepository"""
        repo = DependencyRepository(mock_session_factory)
        repo.SessionLocal = mock_session_factory
        return repo
    
    @pytest.mark.asyncio
    @patch('src.registry.repositories.dependency_repository.db_session')
    async def test_save_dependencies(self, mock_db_session, dependency_repo):
        """Test guardar dependencias"""
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session
        mock_db_session.return_value.__exit__.return_value = None
        
        # Mock query para verificar si existe
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None  # No existe, crear nuevo
        
        dependencies = [
            {
                'depends_on_component_id': 2,
                'depends_on_name': 'Button',
                'from_path': './Button',
                'import_type': 'named',
                'is_external': False
            }
        ]
        
        result = await dependency_repo.save_dependencies(
            component_id=1,
            project_id='test-project',
            dependencies=dependencies
        )
        
        assert result == 1
        assert mock_session.add.called
    
    @pytest.mark.asyncio
    @patch('src.registry.repositories.dependency_repository.db_session')
    async def test_get_dependencies(self, mock_db_session, dependency_repo):
        """Test obtener dependencias"""
        # Mock de componente dependiente
        mock_dep_comp = Mock()
        mock_dep_comp.to_dict.return_value = {
            'id': 2,
            'name': 'Button',
            'file_path': 'components/Button.tsx'
        }
        
        # Mock de dependencia
        mock_dep = Mock()
        mock_dep.depends_on_component = mock_dep_comp
        mock_dep.import_type = 'named'
        mock_dep.from_path = './Button'
        
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session
        mock_db_session.return_value.__exit__.return_value = None
        
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.isnot.return_value = mock_query
        mock_query.all.return_value = [mock_dep]
        
        result = await dependency_repo.get_dependencies(component_id=1)
        
        assert len(result) == 1
        assert result[0]['name'] == 'Button'
        assert result[0]['import_type'] == 'named'
    
    @pytest.mark.asyncio
    @patch('src.registry.repositories.dependency_repository.db_session')
    async def test_get_dependents(self, mock_db_session, dependency_repo):
        """Test obtener dependientes"""
        # Mock de componente que depende
        mock_comp = Mock()
        mock_comp.to_dict.return_value = {
            'id': 3,
            'name': 'HomePage',
            'file_path': 'pages/HomePage.tsx'
        }
        
        # Mock de dependencia
        mock_dep = Mock()
        mock_dep.component = mock_comp
        mock_dep.import_type = 'default'
        mock_dep.from_path = './Button'
        
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session
        mock_db_session.return_value.__exit__.return_value = None
        
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = [mock_dep]
        
        result = await dependency_repo.get_dependents(component_id=2)
        
        assert len(result) == 1
        assert result[0]['name'] == 'HomePage'
    
    @pytest.mark.asyncio
    @patch('src.registry.repositories.dependency_repository.db_session')
    async def test_get_dependency_tree_empty(self, mock_db_session, dependency_repo):
        """Test árbol de dependencias vacío"""
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session
        mock_db_session.return_value.__exit__.return_value = None
        
        # Mock componente sin dependencias
        mock_comp = Mock()
        mock_comp.to_dict.return_value = {
            'id': 1,
            'name': 'Button',
            'file_path': 'components/Button.tsx'
        }
        
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.isnot.return_value = mock_query
        mock_query.first.return_value = mock_comp  # Para el componente raíz
        mock_query.all.return_value = []  # Sin dependencias
        
        result = await dependency_repo.get_dependency_tree(
            component_id=1,
            direction='down',
            max_depth=3
        )
        
        assert result is not None
        assert 'component' in result
        assert len(result.get('children', [])) == 0

