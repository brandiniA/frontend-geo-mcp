"""
Configuración de pytest con fixtures compartidas.
"""

import pytest
import os
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, MagicMock
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

# Agregar src al PYTHONPATH para imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Configurar variables de entorno para testing
os.environ.setdefault("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/frontend_mcp_test")
os.environ.setdefault("TEMP_DIR", "/tmp/mcp-repos-test")


@pytest.fixture
def mock_db_session():
    """Fixture para mock de sesión de base de datos."""
    session = Mock(spec=Session)
    session.query = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.rollback = Mock()
    session.close = Mock()
    return session


@pytest.fixture
def mock_database_client():
    """Fixture para mock de DatabaseClient."""
    from src.registry.database_client import DatabaseClient
    
    client = Mock(spec=DatabaseClient)
    client.search_components = AsyncMock(return_value=[])
    client.get_project = AsyncMock(return_value=None)
    client.get_component_index_stats = AsyncMock(return_value={
        "total": 0,
        "byType": {},
        "byPath": {},
        "lastUpdated": None,
        "indexCoverage": 0.0
    })
    client.list_projects = AsyncMock(return_value=[])
    client.list_components_in_path = AsyncMock(return_value=[])
    client.search_components_semantic = AsyncMock(return_value=[])
    client.search_by_hook = AsyncMock(return_value=[])
    client.get_all_components = AsyncMock(return_value=[])
    client.get_component_by_name = AsyncMock(return_value=None)
    client.get_component_docs = AsyncMock(return_value=None)
    client.search_by_jsdoc = AsyncMock(return_value=[])
    
    return client


@pytest.fixture
def sample_component():
    """Fixture para componente de ejemplo."""
    return {
        "id": "test-component-1",
        "name": "TestButton",
        "project_id": "test-project",
        "file_path": "src/components/TestButton.js",
        "component_type": "component",
        "props": ["onClick", "text", "variant"],
        "native_hooks_used": ["useState", "useEffect"],
        "custom_hooks_used": ["useAuth"],
        "imports": ["react"],
        "exports": ["TestButton"],
        "description": "A test button component",
        "jsdoc": None,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00",
    }


@pytest.fixture
def sample_project():
    """Fixture para proyecto de ejemplo."""
    return {
        "id": "test-project",
        "name": "Test Project",
        "repository": "https://github.com/test/test-project",
        "branch": "main",
        "type": "application",
        "last_sync": "2024-01-01T00:00:00",
    }


@pytest.fixture
def sample_hook():
    """Fixture para hook de ejemplo."""
    return {
        "id": "test-hook-1",
        "name": "useTest",
        "project_id": "test-project",
        "file_path": "src/hooks/useTest.js",
        "hook_type": "custom",
        "description": "A test hook",
        "return_type": "string",
        "parameters": ["param1"],
        "jsdoc": None,
    }


@pytest.fixture
def checkout_evidence_path():
    """Fixture para la ruta de evidencia de Checkout."""
    return Path(__file__).parent.parent / "src/evidencia/Checkout"

