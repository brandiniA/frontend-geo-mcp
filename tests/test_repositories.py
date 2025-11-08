"""
Tests para los repositorios de base de datos.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime
from sqlalchemy.orm import Session

from src.registry.repositories.project_repository import ProjectRepository
from src.registry.repositories.component_repository import ComponentRepository
from src.registry.repositories.hook_repository import HookRepository


class TestProjectRepository:
    """Tests para ProjectRepository."""
    
    @pytest.fixture
    def mock_session_factory(self):
        """Fixture para session factory mock."""
        session = Mock(spec=Session)
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.close = Mock()
        
        factory = Mock()
        factory.return_value = session
        return factory
    
    @pytest.fixture
    def project_repo(self, mock_session_factory):
        """Fixture para ProjectRepository."""
        return ProjectRepository(mock_session_factory)
    
    @pytest.mark.asyncio
    async def test_upsert_project(self, project_repo, mock_session_factory, sample_project):
        """Test para crear/actualizar proyecto."""
        # Mock del modelo Project
        mock_project = Mock()
        mock_project.to_dict.return_value = sample_project
        
        with patch('src.registry.repositories.project_repository.Project') as MockProject:
            MockProject.return_value = mock_project
            
            session = mock_session_factory()
            session.query.return_value.filter.return_value.first.return_value = None
            
            result = await project_repo.upsert("test-project", sample_project)
            
            assert result == sample_project
            session.add.assert_called_once()
            session.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_project(self, project_repo, mock_session_factory, sample_project):
        """Test para obtener proyecto."""
        mock_project = Mock()
        mock_project.to_dict.return_value = sample_project
        
        session = mock_session_factory()
        session.query.return_value.filter.return_value.first.return_value = mock_project
        
        result = await project_repo.get("test-project")
        
        assert result == sample_project


class TestComponentRepository:
    """Tests para ComponentRepository."""
    
    @pytest.fixture
    def mock_session_factory(self):
        """Fixture para session factory mock."""
        session = Mock(spec=Session)
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.close = Mock()
        
        factory = Mock()
        factory.return_value = session
        return factory
    
    @pytest.fixture
    def component_repo(self, mock_session_factory):
        """Fixture para ComponentRepository."""
        return ComponentRepository(mock_session_factory)
    
    @pytest.mark.asyncio
    async def test_search_components(self, component_repo, mock_session_factory, sample_component):
        """Test para buscar componentes."""
        mock_component = Mock()
        mock_component.to_dict.return_value = sample_component
        
        session = mock_session_factory()
        session.query.return_value.filter.return_value.all.return_value = [mock_component]
        
        result = await component_repo.search("TestButton")
        
        assert len(result) == 1
        assert result[0]["name"] == "TestButton"
    
    @pytest.mark.asyncio
    async def test_get_index_stats(self, component_repo, mock_session_factory):
        """Test para obtener estadísticas del índice."""
        mock_component = Mock()
        mock_component.component_type = "component"
        mock_component.file_path = "src/components/Test.js"
        mock_component.updated_at = datetime.utcnow()
        
        session = mock_session_factory()
        session.query.return_value.all.return_value = [mock_component]
        
        result = await component_repo.get_index_stats()
        
        assert "total" in result
        assert "byType" in result
        assert "byPath" in result


class TestHookRepository:
    """Tests para HookRepository."""
    
    @pytest.fixture
    def mock_session_factory(self):
        """Fixture para session factory mock."""
        session = Mock(spec=Session)
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.close = Mock()
        
        factory = Mock()
        factory.return_value = session
        return factory
    
    @pytest.fixture
    def hook_repo(self, mock_session_factory):
        """Fixture para HookRepository."""
        return HookRepository(mock_session_factory)
    
    @pytest.mark.asyncio
    async def test_search_hooks(self, hook_repo, mock_session_factory, sample_hook):
        """Test para buscar hooks."""
        mock_hook = Mock()
        mock_hook.to_dict.return_value = sample_hook
        
        session = mock_session_factory()
        session.query.return_value.filter.return_value.all.return_value = [mock_hook]
        
        result = await hook_repo.search("useTest")
        
        assert len(result) == 1
        assert result[0]["name"] == "useTest"
    
    @pytest.mark.asyncio
    async def test_get_by_project(self, hook_repo, mock_session_factory, sample_hook):
        """Test para obtener hooks por proyecto."""
        mock_hook = Mock()
        mock_hook.to_dict.return_value = sample_hook
        
        session = mock_session_factory()
        session.query.return_value.filter.return_value.all.return_value = [mock_hook]
        
        result = await hook_repo.get_by_project("test-project")
        
        assert len(result) == 1
        assert result[0]["project_id"] == "test-project"

