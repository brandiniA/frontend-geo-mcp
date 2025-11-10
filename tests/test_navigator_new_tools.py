"""
Tests para las nuevas tools del Navigator:
- get_barrel_exports
- find_circular_dependencies
- get_unresolved_imports
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch, MagicMock
from tools.navigator import ComponentNavigator


class TestGetBarrelExports:
    """Tests para get_barrel_exports."""
    
    @pytest.fixture
    def mock_db_with_barrel_exports(self, mock_database_client):
        """Fixture que agrega barrel_exports al mock."""
        mock_barrel_exports = Mock()
        mock_barrel_exports.get_all_by_project = AsyncMock()
        mock_database_client.barrel_exports = mock_barrel_exports
        return mock_database_client
    
    @pytest.mark.asyncio
    async def test_get_barrel_exports_no_barrels(self, mock_db_with_barrel_exports):
        """Test cuando no hay barrel exports."""
        navigator = ComponentNavigator(mock_db_with_barrel_exports)
        mock_db_with_barrel_exports.barrel_exports.get_all_by_project.return_value = []
        
        result = await navigator.get_barrel_exports("test-project")
        
        assert "No barrel exports found" in result
        assert "test-project" in result
    
    @pytest.mark.asyncio
    async def test_get_barrel_exports_with_resolved(self, mock_db_with_barrel_exports):
        """Test con barrel exports resueltos."""
        navigator = ComponentNavigator(mock_db_with_barrel_exports)
        
        barrels = [
            {
                'directory_path': 'src/components/Button',
                'exported_component_id': 1,
                'exported_name': 'Button',
                'is_container': False,
                'source_file_path': 'src/components/Button/Button.js',
                'index_file_path': 'src/components/Button/index.js'
            },
            {
                'directory_path': 'src/components/Checkout',
                'exported_component_id': 2,
                'exported_name': 'CheckoutContainer',
                'is_container': True,
                'source_file_path': 'src/components/Checkout/CheckoutContainer.js',
                'index_file_path': 'src/components/Checkout/index.js'
            }
        ]
        
        mock_db_with_barrel_exports.barrel_exports.get_all_by_project.return_value = barrels
        
        result = await navigator.get_barrel_exports("test-project")
        
        assert "Barrel Exports" in result
        assert "**Total:** 2" in result
        assert "**Resolved:** 2" in result
        assert "Button" in result
        assert "CheckoutContainer" in result
        assert "(Container)" in result
        assert "100.0%" in result
    
    @pytest.mark.asyncio
    async def test_get_barrel_exports_with_unresolved(self, mock_db_with_barrel_exports):
        """Test con barrel exports no resueltos."""
        navigator = ComponentNavigator(mock_db_with_barrel_exports)
        
        barrels = [
            {
                'directory_path': 'src/components/Unknown',
                'exported_component_id': None,
                'exported_name': None,
                'is_container': False,
                'source_file_path': 'src/components/Unknown/Unknown.js',
                'index_file_path': 'src/components/Unknown/index.js',
                'notes': 'Component not found'
            }
        ]
        
        mock_db_with_barrel_exports.barrel_exports.get_all_by_project.return_value = barrels
        
        result = await navigator.get_barrel_exports("test-project")
        
        assert "Barrel Exports" in result
        assert "**Total:** 1" in result
        assert "**Unresolved:** 1" in result
        assert "src/components/Unknown" in result
        assert "Component not found" in result
    
    @pytest.mark.asyncio
    async def test_get_barrel_exports_mixed(self, mock_db_with_barrel_exports):
        """Test con barrel exports resueltos y no resueltos."""
        navigator = ComponentNavigator(mock_db_with_barrel_exports)
        
        barrels = [
            {
                'directory_path': 'src/components/Button',
                'exported_component_id': 1,
                'exported_name': 'Button',
                'is_container': False,
                'source_file_path': 'src/components/Button/Button.js',
                'index_file_path': 'src/components/Button/index.js'
            },
            {
                'directory_path': 'src/components/Unknown',
                'exported_component_id': None,
                'exported_name': None,
                'is_container': False,
                'source_file_path': 'src/components/Unknown/Unknown.js',
                'index_file_path': 'src/components/Unknown/index.js'
            }
        ]
        
        mock_db_with_barrel_exports.barrel_exports.get_all_by_project.return_value = barrels
        
        result = await navigator.get_barrel_exports("test-project")
        
        assert "**Total:** 2" in result
        assert "**Resolved:** 1" in result
        assert "**Unresolved:** 1" in result
        assert "50.0%" in result
        assert "✅ Resolved" in result
        assert "⚠️ Unresolved" in result


class TestFindCircularDependencies:
    """Tests para find_circular_dependencies."""
    
    @pytest.fixture
    def mock_db_with_dependencies(self, mock_database_client):
        """Fixture que agrega dependencies al mock."""
        mock_dependencies = Mock()
        mock_dependencies.get_dependencies = AsyncMock()
        mock_database_client.dependencies = mock_dependencies
        mock_database_client.get_components_by_project = AsyncMock()
        return mock_database_client
    
    @pytest.mark.asyncio
    async def test_find_circular_dependencies_no_components(self, mock_db_with_dependencies):
        """Test cuando no hay componentes."""
        navigator = ComponentNavigator(mock_db_with_dependencies)
        mock_db_with_dependencies.get_components_by_project.return_value = []
        
        result = await navigator.find_circular_dependencies("test-project")
        
        assert "No components found" in result
    
    @pytest.mark.asyncio
    async def test_find_circular_dependencies_no_cycles(self, mock_db_with_dependencies):
        """Test cuando no hay ciclos."""
        navigator = ComponentNavigator(mock_db_with_dependencies)
        
        components = [
            {'id': 1, 'name': 'ComponentA', 'file_path': 'ComponentA.js'},
            {'id': 2, 'name': 'ComponentB', 'file_path': 'ComponentB.js'}
        ]
        
        mock_db_with_dependencies.get_components_by_project.return_value = components
        
        # Mock dependencies - ComponentA depende de ComponentB, pero no hay ciclo
        mock_db_with_dependencies.dependencies.get_dependencies.side_effect = [
            [{'id': 2}],  # ComponentA depende de ComponentB
            []  # ComponentB no depende de nadie
        ]
        
        result = await navigator.find_circular_dependencies("test-project")
        
        assert "No circular dependencies found" in result
    
    @pytest.mark.asyncio
    async def test_find_circular_dependencies_simple_cycle(self, mock_db_with_dependencies):
        """Test con un ciclo simple A → B → A."""
        navigator = ComponentNavigator(mock_db_with_dependencies)
        
        components = [
            {'id': 1, 'name': 'ComponentA', 'file_path': 'ComponentA.js'},
            {'id': 2, 'name': 'ComponentB', 'file_path': 'ComponentB.js'}
        ]
        
        mock_db_with_dependencies.get_components_by_project.return_value = components
        
        # Crear ciclo: A → B → A
        mock_db_with_dependencies.dependencies.get_dependencies.side_effect = [
            [{'id': 2}],  # ComponentA depende de ComponentB
            [{'id': 1}]   # ComponentB depende de ComponentA
        ]
        
        result = await navigator.find_circular_dependencies("test-project")
        
        assert "Circular Dependencies Found" in result
        assert "ComponentA" in result
        assert "ComponentB" in result
    
    @pytest.mark.asyncio
    async def test_find_circular_dependencies_self_reference(self, mock_db_with_dependencies):
        """Test con auto-referencia (A → A)."""
        navigator = ComponentNavigator(mock_db_with_dependencies)
        
        components = [
            {'id': 1, 'name': 'ComponentA', 'file_path': 'ComponentA.js'}
        ]
        
        mock_db_with_dependencies.get_components_by_project.return_value = components
        
        # Auto-referencia: A → A
        mock_db_with_dependencies.dependencies.get_dependencies.return_value = [
            {'id': 1}  # ComponentA depende de sí mismo
        ]
        
        result = await navigator.find_circular_dependencies("test-project")
        
        assert "Circular Dependencies Found" in result
        assert "ComponentA" in result
        assert "ComponentA → ComponentA" in result or "ComponentA" in result
    
    @pytest.mark.asyncio
    async def test_find_circular_dependencies_complex_cycle(self, mock_db_with_dependencies):
        """Test con ciclo complejo A → B → C → A."""
        navigator = ComponentNavigator(mock_db_with_dependencies)
        
        components = [
            {'id': 1, 'name': 'ComponentA', 'file_path': 'ComponentA.js'},
            {'id': 2, 'name': 'ComponentB', 'file_path': 'ComponentB.js'},
            {'id': 3, 'name': 'ComponentC', 'file_path': 'ComponentC.js'}
        ]
        
        mock_db_with_dependencies.get_components_by_project.return_value = components
        
        # Ciclo: A → B → C → A
        mock_db_with_dependencies.dependencies.get_dependencies.side_effect = [
            [{'id': 2}],  # A depende de B
            [{'id': 3}],  # B depende de C
            [{'id': 1}]   # C depende de A
        ]
        
        result = await navigator.find_circular_dependencies("test-project")
        
        assert "Circular Dependencies Found" in result
        assert "ComponentA" in result
        assert "ComponentB" in result
        assert "ComponentC" in result


class TestGetUnresolvedImports:
    """Tests para get_unresolved_imports."""
    
    @pytest.mark.asyncio
    @patch('tools.navigator.asyncio.to_thread')
    async def test_get_unresolved_imports_all_resolved(self, mock_to_thread, mock_database_client):
        """Test cuando todos los imports están resueltos."""
        navigator = ComponentNavigator(mock_database_client)
        
        # Mock retorna lista vacía (todos resueltos)
        mock_to_thread.return_value = []
        
        result = await navigator.get_unresolved_imports("test-project", limit=50)
        
        assert "All imports resolved" in result
        assert "test-project" in result
    
    @pytest.mark.asyncio
    @patch('tools.navigator.asyncio.to_thread')
    async def test_get_unresolved_imports_with_unresolved(self, mock_to_thread, mock_database_client):
        """Test con imports no resueltos."""
        navigator = ComponentNavigator(mock_database_client)
        
        unresolved_imports = [
            {
                'component_name': 'ComponentA',
                'component_path': 'src/components/ComponentA.js',
                'import_name': 'UnknownComponent',
                'from_path': './UnknownComponent',
                'import_type': 'default'
            },
            {
                'component_name': 'ComponentB',
                'component_path': 'src/components/ComponentB.js',
                'import_name': 'AnotherUnknown',
                'from_path': '../utils/AnotherUnknown',
                'import_type': 'named'
            }
        ]
        
        mock_to_thread.return_value = unresolved_imports
        
        result = await navigator.get_unresolved_imports("test-project", limit=50)
        
        assert "Unresolved Imports" in result
        assert "ComponentA" in result
        assert "ComponentB" in result
        assert "UnknownComponent" in result
        assert "AnotherUnknown" in result
        assert "./UnknownComponent" in result
        assert "../utils/AnotherUnknown" in result
    
    @pytest.mark.asyncio
    @patch('tools.navigator.asyncio.to_thread')
    async def test_get_unresolved_imports_limit(self, mock_to_thread, mock_database_client):
        """Test que el límite funciona correctamente."""
        navigator = ComponentNavigator(mock_database_client)
        
        # Crear muchos imports no resueltos
        unresolved_imports = [
            {
                'component_name': f'Component{i}',
                'component_path': f'src/components/Component{i}.js',
                'import_name': f'Unknown{i}',
                'from_path': f'./Unknown{i}',
                'import_type': 'default'
            }
            for i in range(100)
        ]
        
        mock_to_thread.return_value = unresolved_imports
        
        result = await navigator.get_unresolved_imports("test-project", limit=10)
        
        assert "Unresolved Imports" in result
        assert "100" in result  # Total
        assert "Showing 10" in result or "10 of 100" in result
    
    @pytest.mark.asyncio
    @patch('tools.navigator.asyncio.to_thread')
    async def test_get_unresolved_imports_grouped_by_component(self, mock_to_thread, mock_database_client):
        """Test que los imports se agrupan por componente."""
        navigator = ComponentNavigator(mock_database_client)
        
        unresolved_imports = [
            {
                'component_name': 'ComponentA',
                'component_path': 'src/components/ComponentA.js',
                'import_name': 'Unknown1',
                'from_path': './Unknown1',
                'import_type': 'default'
            },
            {
                'component_name': 'ComponentA',
                'component_path': 'src/components/ComponentA.js',
                'import_name': 'Unknown2',
                'from_path': './Unknown2',
                'import_type': 'named'
            },
            {
                'component_name': 'ComponentB',
                'component_path': 'src/components/ComponentB.js',
                'import_name': 'Unknown3',
                'from_path': './Unknown3',
                'import_type': 'default'
            }
        ]
        
        mock_to_thread.return_value = unresolved_imports
        
        result = await navigator.get_unresolved_imports("test-project", limit=50)
        
        assert "ComponentA" in result
        assert "ComponentB" in result
        # Verificar que ComponentA aparece solo una vez como encabezado
        assert result.count("### 📦 ComponentA") == 1
        assert result.count("### 📦 ComponentB") == 1

