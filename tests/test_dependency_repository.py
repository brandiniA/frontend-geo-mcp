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
    
    @pytest.mark.asyncio
    @patch('src.registry.repositories.dependency_repository.db_session')
    async def test_get_dependency_tree_both_direction(self, mock_db_session, dependency_repo):
        """Test árbol de dependencias con direction='both' (dependencias y dependientes)"""
        mock_session = MagicMock()
        mock_db_session.return_value.__enter__.return_value = mock_session
        mock_db_session.return_value.__exit__.return_value = None
        
        # Mock componente raíz
        mock_comp = Mock()
        mock_comp.to_dict.return_value = {
            'id': 1,
            'name': 'Button',
            'file_path': 'components/Button.tsx'
        }
        
        # Mock componente dependiente (que Button usa)
        mock_dep_comp = Mock()
        mock_dep_comp.to_dict.return_value = {
            'id': 2,
            'name': 'Icon',
            'file_path': 'components/Icon.tsx'
        }
        
        # Mock componente que usa Button (dependiente)
        mock_dependent_comp = Mock()
        mock_dependent_comp.to_dict.return_value = {
            'id': 3,
            'name': 'HomePage',
            'file_path': 'pages/HomePage.tsx'
        }
        
        # Mock dependencia (Button usa Icon)
        mock_dep = Mock()
        mock_dep.depends_on_component_id = 2
        mock_dep.import_type = 'named'
        mock_dep.from_path = './Icon'
        
        # Mock dependiente (HomePage usa Button)
        mock_dependent = Mock()
        mock_dependent.component_id = 3
        mock_dependent.import_type = 'default'
        mock_dependent.from_path = './Button'
        
        mock_query = Mock()
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.isnot.return_value = mock_query
        
        # Configurar respuestas según la query
        def query_side_effect(model):
            if model == Component:
                query_mock = Mock()
                query_mock.filter.return_value = query_mock
                # Retornar el componente apropiado según el ID
                def first_side_effect():
                    comp_id = query_mock.filter.call_args[0][0].left.key == 'id'
                    # Simplificado: retornar según el contexto
                    if hasattr(mock_query, '_return_comp'):
                        return mock_query._return_comp
                    return mock_comp
                query_mock.first = first_side_effect
                return query_mock
            elif model == ComponentDependency:
                query_mock = Mock()
                query_mock.filter.return_value = query_mock
                query_mock.isnot.return_value = query_mock
                # Dependencias (down): Button usa Icon
                if mock_query._query_type == 'deps':
                    query_mock.all.return_value = [mock_dep]
                    # Configurar para retornar Icon cuando se busca
                    mock_query._return_comp = mock_dep_comp
                # Dependientes (up): HomePage usa Button
                elif mock_query._query_type == 'dependents':
                    query_mock.all.return_value = [mock_dependent]
                    mock_query._return_comp = mock_dependent_comp
                else:
                    query_mock.all.return_value = []
                return query_mock
            return mock_query
        
        mock_session.query.side_effect = query_side_effect
        
        # Simular que primero busca dependencias, luego dependientes
        mock_query._query_type = 'deps'
        result = await dependency_repo.get_dependency_tree(
            component_id=1,
            direction='both',
            max_depth=3
        )
        
        assert result is not None
        assert 'component' in result
        # Debería tener children con hierarchy_direction marcado
        children = result.get('children', [])
        # Verificar que los children tienen hierarchy_direction
        for child in children:
            assert 'hierarchy_direction' in child
            assert child['hierarchy_direction'] in ['down', 'up']

