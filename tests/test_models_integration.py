"""
Tests de integración para modelos SQLAlchemy.
Verifica que los métodos críticos como to_dict() funcionen correctamente.
"""

import pytest
from datetime import datetime
from src.models import Project, Component, Hook


class TestProjectModelIntegration:
    """Tests de integración para el modelo Project."""
    
    def test_project_to_dict(self):
        """Test que Project.to_dict() funciona correctamente."""
        project = Project(
            id="test-project-1",
            name="Test Project",
            repository_url="https://github.com/test/repo",
            branch="main",
            type="application",
            is_active="true",
            last_sync=datetime(2024, 1, 1, 12, 0, 0),
            created_at=datetime(2024, 1, 1, 10, 0, 0)
        )
        result = project.to_dict()
        
        # Verificar estructura básica
        assert isinstance(result, dict)
        assert result['id'] == "test-project-1"
        assert result['name'] == "Test Project"
        assert result['repository_url'] == "https://github.com/test/repo"
        assert result['branch'] == "main"
        assert result['type'] == "application"
        
        # Verificar conversión de is_active de string a bool
        assert result['is_active'] is True
        
        # Verificar fechas
        assert result['last_sync'] == datetime(2024, 1, 1, 12, 0, 0)
        assert result['created_at'] == datetime(2024, 1, 1, 10, 0, 0)
    
    def test_project_to_dict_with_false_active(self):
        """Test que Project.to_dict() convierte is_active="false" a False."""
        project = Project(
            id="test-project-2",
            name="Inactive Project",
            repository_url="https://github.com/test/repo2",
            branch="main",
            type="application",
            is_active="false"
        )
        result = project.to_dict()
        
        assert result['is_active'] is False
    
    def test_project_to_dict_with_none_values(self):
        """Test que Project.to_dict() maneja valores None correctamente."""
        project = Project(
            id="test-project-3",
            name="Project Without Sync",
            repository_url="https://github.com/test/repo3",
            branch="main",
            type="library",
            is_active="true",
            last_sync=None,
            created_at=None  # En memoria, los defaults no se aplican hasta insertar en BD
        )
        result = project.to_dict()
        
        assert result['last_sync'] is None
        # Nota: created_at será None en memoria, pero se genera automáticamente al insertar en BD
        assert result['created_at'] is None or isinstance(result['created_at'], datetime)


class TestComponentModelIntegration:
    """Tests de integración para el modelo Component."""
    
    def test_component_to_dict(self):
        """Test que Component.to_dict() funciona correctamente."""
        component = Component(
            name="TestButton",
            project_id="test-project-1",
            file_path="src/components/TestButton.js",
            props=["onClick", "text", "variant"],
            native_hooks_used=["useState", "useEffect"],
            custom_hooks_used=["useAuth"],
            imports=["react", "prop-types"],
            exports=["TestButton"],
            component_type="component",
            description="A test button component",
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 2, 15, 30, 0)
        )
        result = component.to_dict()
        
        # Verificar estructura básica
        assert isinstance(result, dict)
        assert result['name'] == "TestButton"
        assert result['project_id'] == "test-project-1"
        assert result['file_path'] == "src/components/TestButton.js"
        
        # Verificar arrays JSON
        assert result['props'] == ["onClick", "text", "variant"]
        assert result['native_hooks_used'] == ["useState", "useEffect"]
        assert result['custom_hooks_used'] == ["useAuth"]
        assert result['imports'] == ["react", "prop-types"]
        assert result['exports'] == ["TestButton"]
        
        # Verificar campos opcionales
        assert result['component_type'] == "component"
        assert result['description'] == "A test button component"
        
        # Verificar fechas
        assert result['created_at'] == datetime(2024, 1, 1, 10, 0, 0)
        assert result['updated_at'] == datetime(2024, 1, 2, 15, 30, 0)
    
    def test_component_to_dict_with_empty_arrays(self):
        """Test que Component.to_dict() maneja arrays vacíos correctamente."""
        component = Component(
            name="SimpleComponent",
            project_id="test-project-1",
            file_path="src/SimpleComponent.js",
            props=[],
            native_hooks_used=[],
            custom_hooks_used=[],
            imports=[],
            exports=[]
        )
        result = component.to_dict()
        
        assert result['props'] == []
        assert result['native_hooks_used'] == []
        assert result['custom_hooks_used'] == []
        assert result['imports'] == []
        assert result['exports'] == []
    
    def test_component_to_dict_with_jsdoc(self):
        """Test que Component.to_dict() incluye JSDoc si está presente."""
        jsdoc_data = {
            "description": "A button component",
            "params": [
                {"name": "onClick", "type": "function", "description": "Click handler"}
            ],
            "returns": {"type": "JSX.Element"}
        }
        
        component = Component(
            name="DocumentedButton",
            project_id="test-project-1",
            file_path="src/DocumentedButton.js",
            jsdoc=jsdoc_data
        )
        result = component.to_dict()
        
        assert result['jsdoc'] == jsdoc_data
        assert result['jsdoc']['description'] == "A button component"
    
    def test_component_to_dict_with_none_values(self):
        """Test que Component.to_dict() maneja valores None correctamente."""
        component = Component(
            name="MinimalComponent",
            project_id="test-project-1",
            file_path="src/MinimalComponent.js",
            component_type=None,
            description=None,
            jsdoc=None
        )
        result = component.to_dict()
        
        assert result['component_type'] is None
        assert result['description'] is None
        assert result['jsdoc'] is None


class TestHookModelIntegration:
    """Tests de integración para el modelo Hook."""
    
    def test_hook_to_dict(self):
        """Test que Hook.to_dict() funciona correctamente."""
        hook = Hook(
            name="useTest",
            project_id="test-project-1",
            file_path="src/hooks/useTest.js",
            hook_type="custom",
            description="A test hook",
            return_type="string",
            parameters=[{"name": "param1", "type": "string"}],
            imports=["react"],
            exports=["useTest"],
            native_hooks_used=["useState"],
            custom_hooks_used=[],
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 2, 15, 30, 0)
        )
        result = hook.to_dict()
        
        # Verificar estructura básica
        assert isinstance(result, dict)
        assert result['name'] == "useTest"
        assert result['project_id'] == "test-project-1"
        assert result['file_path'] == "src/hooks/useTest.js"
        assert result['hook_type'] == "custom"
        
        # Verificar campos opcionales
        assert result['description'] == "A test hook"
        assert result['return_type'] == "string"
        assert result['parameters'] == [{"name": "param1", "type": "string"}]
        
        # Verificar arrays JSON
        assert result['imports'] == ["react"]
        assert result['exports'] == ["useTest"]
        assert result['native_hooks_used'] == ["useState"]
        assert result['custom_hooks_used'] == []
        
        # Verificar fechas
        assert result['created_at'] == datetime(2024, 1, 1, 10, 0, 0)
        assert result['updated_at'] == datetime(2024, 1, 2, 15, 30, 0)
    
    def test_hook_to_dict_with_default_type(self):
        """Test que Hook.to_dict() incluye hook_type (default se aplica al insertar en BD)."""
        # Nota: Los defaults de SQLAlchemy solo se aplican al insertar en BD
        # En memoria, debemos especificar el valor explícitamente
        hook = Hook(
            name="useDefault",
            project_id="test-project-1",
            file_path="src/hooks/useDefault.js",
            hook_type="custom"  # Especificamos explícitamente para el test
        )
        result = hook.to_dict()
        
        assert result['hook_type'] == "custom"
        
        # Test alternativo: verificar que si no se especifica, puede ser None en memoria
        hook_no_type = Hook(
            name="useNoType",
            project_id="test-project-1",
            file_path="src/hooks/useNoType.js"
        )
        result_no_type = hook_no_type.to_dict()
        # En memoria sin especificar, puede ser None, pero al insertar en BD será "custom"
        assert result_no_type['hook_type'] is None or result_no_type['hook_type'] == "custom"
    
    def test_hook_to_dict_with_empty_arrays(self):
        """Test que Hook.to_dict() maneja arrays vacíos correctamente."""
        hook = Hook(
            name="useEmpty",
            project_id="test-project-1",
            file_path="src/hooks/useEmpty.js",
            parameters=[],
            imports=[],
            exports=[],
            native_hooks_used=[],
            custom_hooks_used=[]
        )
        result = hook.to_dict()
        
        assert result['parameters'] == []
        assert result['imports'] == []
        assert result['exports'] == []
        assert result['native_hooks_used'] == []
        assert result['custom_hooks_used'] == []
    
    def test_hook_to_dict_with_jsdoc(self):
        """Test que Hook.to_dict() incluye JSDoc si está presente."""
        jsdoc_data = {
            "description": "A custom hook",
            "params": [
                {"name": "value", "type": "any", "description": "Input value"}
            ],
            "returns": {"type": "string", "description": "Processed value"}
        }
        
        hook = Hook(
            name="useDocumented",
            project_id="test-project-1",
            file_path="src/hooks/useDocumented.js",
            jsdoc=jsdoc_data
        )
        result = hook.to_dict()
        
        assert result['jsdoc'] == jsdoc_data
        assert result['jsdoc']['description'] == "A custom hook"

