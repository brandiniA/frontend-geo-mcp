"""
Tests para el parser mejorado con extracción de imports estructurados.
"""

import pytest
from src.utils.parser import ReactParser


class TestParserComponentImports:
    """Tests para _extract_component_imports."""
    
    def test_named_imports(self):
        """Test named imports: import { Button, Card } from './components'"""
        parser = ReactParser()
        content = "import { Button, Card } from './components'"
        result = parser._extract_component_imports(content)
        
        assert len(result) == 1
        assert result[0]['import_type'] == 'named'
        assert result[0]['from_path'] == './components'
        assert 'Button' in result[0]['imported_names']
        assert 'Card' in result[0]['imported_names']
    
    def test_default_import(self):
        """Test default import: import Button from './Button'"""
        parser = ReactParser()
        content = "import Button from './Button'"
        result = parser._extract_component_imports(content)
        
        assert len(result) == 1
        assert result[0]['import_type'] == 'default'
        assert result[0]['from_path'] == './Button'
        assert result[0]['imported_names'] == ['Button']
    
    def test_mixed_import(self):
        """Test mixed import: import Button, { Card } from './components'"""
        parser = ReactParser()
        content = "import Button, { Card } from './components'"
        result = parser._extract_component_imports(content)
        
        assert len(result) == 1
        assert result[0]['import_type'] == 'mixed'
        assert result[0]['from_path'] == './components'
        assert 'Button' in result[0]['imported_names']
        assert 'Card' in result[0]['imported_names']
    
    def test_namespace_import(self):
        """Test namespace import: import * as Components from './components'"""
        parser = ReactParser()
        content = "import * as Components from './components'"
        result = parser._extract_component_imports(content)
        
        assert len(result) == 1
        assert result[0]['import_type'] == 'namespace'
        assert result[0]['from_path'] == './components'
        assert result[0]['imported_names'] == ['Components']
    
    def test_multiple_imports(self):
        """Test múltiples imports en el mismo archivo"""
        parser = ReactParser()
        content = """
        import { Button } from './components'
        import Card from './Card'
        import { Header, Footer } from './layout'
        """
        result = parser._extract_component_imports(content)
        
        assert len(result) >= 2
        named_imports = [r for r in result if r['import_type'] == 'named']
        assert len(named_imports) >= 1
    
    def test_import_with_alias(self):
        """Test import con alias: import Button as Btn from './Button'"""
        parser = ReactParser()
        content = "import { Button as Btn, Card } from './components'"
        result = parser._extract_component_imports(content)
        
        assert len(result) == 1
        # Debe usar el nombre original, no el alias
        assert 'Button' in result[0]['imported_names']
        assert 'Btn' not in result[0]['imported_names']
    
    def test_external_imports(self):
        """Test imports externos (librerías npm)"""
        parser = ReactParser()
        content = "import { useState, useEffect } from 'react'"
        result = parser._extract_component_imports(content)
        
        assert len(result) == 1
        assert result[0]['from_path'] == 'react'
        assert 'useState' in result[0]['imported_names']
    
    def test_component_info_includes_imports(self):
        """Test que extract_component_info incluye component_imports"""
        parser = ReactParser()
        content = """
        import { Button } from './components'
        export const MyComponent = () => {
            return <Button />
        }
        """
        result = parser.extract_component_info(content, 'test.tsx')
        
        assert len(result) > 0
        component = result[0]
        assert 'component_imports' in component
        assert isinstance(component['component_imports'], list)
        assert 'imports' in component  # Legacy format también debe estar

