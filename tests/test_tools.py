"""
Tests para las tools del MCP (ComponentNavigator).
"""

import pytest
from unittest.mock import AsyncMock, patch
from tools.navigator import ComponentNavigator


class TestComponentNavigator:
    """Tests para ComponentNavigator."""
    
    @pytest.mark.asyncio
    async def test_find_component_no_results(self, mock_database_client):
        """Test cuando no se encuentran componentes."""
        navigator = ComponentNavigator(mock_database_client)
        mock_database_client.search_components.return_value = []
        
        result = await navigator.find_component("NonExistent")
        
        assert "No components found" in result
        assert "NonExistent" in result
    
    @pytest.mark.asyncio
    async def test_find_component_with_results(self, mock_database_client, sample_component, sample_project):
        """Test cuando se encuentran componentes."""
        navigator = ComponentNavigator(mock_database_client)
        mock_database_client.search_components.return_value = [sample_component]
        mock_database_client.get_project.return_value = sample_project
        
        result = await navigator.find_component("TestButton")
        
        assert "Found" in result
        assert "TestButton" in result
        assert sample_component["file_path"] in result
        assert "Props" in result or "props" in result.lower()
    
    @pytest.mark.asyncio
    async def test_get_component_details_not_found(self, mock_database_client):
        """Test cuando no se encuentra un componente específico."""
        navigator = ComponentNavigator(mock_database_client)
        mock_database_client.get_component_by_name.return_value = None
        
        result = await navigator.get_component_details("NonExistent", "test-project")
        
        assert "not found" in result.lower()
    
    @pytest.mark.asyncio
    async def test_get_component_details_found(self, mock_database_client, sample_component, sample_project):
        """Test cuando se encuentra un componente específico."""
        navigator = ComponentNavigator(mock_database_client)
        mock_database_client.search_components.return_value = [sample_component]
        mock_database_client.get_project.return_value = sample_project
        
        result = await navigator.get_component_details("TestButton", "test-project")
        
        assert "TestButton" in result
        assert "Component Details" in result or "component details" in result.lower()
        assert sample_component["file_path"] in result
    
    @pytest.mark.asyncio
    async def test_list_all_components(self, mock_database_client, sample_component):
        """Test para listar todos los componentes."""
        navigator = ComponentNavigator(mock_database_client)
        # list_all_components usa search_components con query vacío
        mock_database_client.search_components.return_value = [sample_component]
        
        result = await navigator.list_all_components()
        
        assert "Component Catalog" in result or "component catalog" in result.lower()
        assert "TestButton" in result
    
    @pytest.mark.asyncio
    async def test_list_components_in_path(self, mock_database_client, sample_component):
        """Test para listar componentes en una ruta."""
        navigator = ComponentNavigator(mock_database_client)
        mock_database_client.list_components_in_path.return_value = [sample_component]
        
        result = await navigator.list_components_in_path("src/components", "test-project")
        
        assert "components" in result.lower()
        assert "src/components" in result
    
    @pytest.mark.asyncio
    async def test_search_components_semantic(self, mock_database_client, sample_component):
        """Test para búsqueda semántica."""
        navigator = ComponentNavigator(mock_database_client)
        mock_database_client.search_components_semantic.return_value = [sample_component]
        
        result = await navigator.search_components_semantic("button", "test-project")
        
        assert "Found" in result or "found" in result.lower()
        assert "button" in result.lower()
    
    @pytest.mark.asyncio
    async def test_search_by_hook(self, mock_database_client, sample_component):
        """Test para buscar componentes por hook."""
        navigator = ComponentNavigator(mock_database_client)
        mock_database_client.search_by_hook.return_value = [sample_component]
        
        result = await navigator.search_by_hook("useState", "test-project")
        
        assert "useState" in result
        assert "Found" in result or "found" in result.lower()
    
    @pytest.mark.asyncio
    async def test_get_component_docs_not_found(self, mock_database_client):
        """Test cuando no hay documentación JSDoc."""
        navigator = ComponentNavigator(mock_database_client)
        mock_database_client.search_components.return_value = []
        
        result = await navigator.get_component_docs("TestButton", "test-project")
        
        assert "not found" in result.lower() or "No JSDoc" in result
    
    @pytest.mark.asyncio
    async def test_search_by_jsdoc(self, mock_database_client, sample_component):
        """Test para buscar en documentación JSDoc."""
        navigator = ComponentNavigator(mock_database_client)
        mock_database_client.search_by_jsdoc.return_value = [sample_component]
        
        result = await navigator.search_by_jsdoc("button", "test-project")
        
        assert "Found" in result or "found" in result.lower()
        assert "button" in result.lower()

