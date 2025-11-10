"""
Tests para detección de feature flags en containers en el indexer.
"""

import pytest
import os
import tempfile
import shutil
from pathlib import Path
from src.utils.indexer import ProjectIndexer
from src.registry.database_client import DatabaseClient


@pytest.fixture
def temp_repo():
    """Crea un repositorio temporal para testing."""
    repo_path = tempfile.mkdtemp()
    yield repo_path
    shutil.rmtree(repo_path)


@pytest.fixture
def indexer():
    """Fixture para crear un indexer."""
    db_client = DatabaseClient()
    return ProjectIndexer(db_client)


def test_detect_container_file(temp_repo, indexer):
    """Test para detectar archivos que son containers."""
    # Crear archivo container
    container_file = Path(temp_repo) / "Container.js"
    container_file.write_text("""
import { connect } from 'react-redux';
import Component from './Component';

const mapStateToProps = (state) => ({});
const mapDispatchToProps = {};

export default connect(mapStateToProps, mapDispatchToProps)(Component);
""")
    
    # Crear archivo componente
    component_file = Path(temp_repo) / "Component.js"
    component_file.write_text("""
import React from 'react';

const Component = () => <div>Test</div>;
export default Component;
""")
    
    # Verificar que el parser detecta el container
    parser = indexer.parser
    content = container_file.read_text()
    result = parser._detect_redox_container(content, str(container_file.relative_to(temp_repo)))
    
    assert result is not None
    assert result['wrapped_component'] == 'Component'


def test_extract_feature_flag_context(temp_repo, indexer):
    """Test para extraer contexto de feature flags en containers."""
    container_file = Path(temp_repo) / "Container.js"
    container_file.write_text("""
import { connect } from 'react-redux';
import Component from './Component';

const mapStateToProps = (state) => {
  const { features } = state.whitelabelConfig;
  return {
    showField: features.SHOW_FIELD === 'true',
    keys: [
      'field1',
      features.ANOTHER_FIELD && 'field2'
    ].filter(Boolean)
  };
};

const mapDispatchToProps = {};

export default connect(mapStateToProps, mapDispatchToProps)(Component);
""")
    
    parser = indexer.parser
    content = container_file.read_text()
    
    # Test SHOW_FIELD
    result1 = parser._extract_usage_context(content, 'SHOW_FIELD')
    assert result1['usage_context'] == 'mapStateToProps'
    assert result1['usage_type'] == 'conditional_logic'
    
    # Test ANOTHER_FIELD
    result2 = parser._extract_usage_context(content, 'ANOTHER_FIELD')
    assert result2['usage_type'] == 'array_construction'


def test_detect_combined_flags(temp_repo, indexer):
    """Test para detectar flags combinados en containers."""
    container_file = Path(temp_repo) / "Container.js"
    container_file.write_text("""
import { connect } from 'react-redux';
import Component from './Component';

const mapStateToProps = (state) => {
  const { features } = state.whitelabelConfig;
  if (features.FLAG1 && features.FLAG2) {
    return { combined: true };
  }
  return { combined: false };
};

export default connect(mapStateToProps)(Component);
""")
    
    parser = indexer.parser
    content = container_file.read_text()
    
    result = parser._extract_usage_context(content, 'FLAG1')
    
    assert 'FLAG2' in (result.get('combined_with') or [])
    assert result.get('logic') == 'AND'

