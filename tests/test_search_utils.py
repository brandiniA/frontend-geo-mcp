"""
Tests para utilidades de búsqueda en JSDoc (search_utils).
"""

import pytest
from src.tools.utils.search_utils import (
    match_in_description,
    match_in_params,
    match_in_returns,
    match_in_examples,
    search_in_jsdoc,
)


class TestMatchInDescription:
    """Tests para match_in_description."""
    
    def test_match_found(self):
        """Test cuando encuentra coincidencia."""
        jsdoc = {'description': 'Button component for actions'}
        
        result = match_in_description(jsdoc, 'button')
        
        assert result is True
    
    def test_match_not_found(self):
        """Test cuando no encuentra coincidencia."""
        jsdoc = {'description': 'Card component'}
        
        result = match_in_description(jsdoc, 'button')
        
        assert result is False
    
    def test_case_insensitive(self):
        """Test case-insensitive."""
        jsdoc = {'description': 'BUTTON COMPONENT'}
        
        result = match_in_description(jsdoc, 'button')
        
        assert result is True
    
    def test_partial_match(self):
        """Test coincidencia parcial."""
        jsdoc = {'description': 'A button-like component'}
        
        result = match_in_description(jsdoc, 'button')
        
        assert result is True
    
    def test_no_description(self):
        """Test sin descripción."""
        jsdoc = {}
        
        result = match_in_description(jsdoc, 'button')
        
        assert result is False


class TestMatchInParams:
    """Tests para match_in_params."""
    
    def test_match_in_param_name(self):
        """Test coincidencia en nombre de parámetro."""
        jsdoc = {
            'params': [
                {'name': 'onClick', 'description': 'Click handler'}
            ]
        }
        
        result = match_in_params(jsdoc, 'onclick')
        
        assert result == 'onClick'
    
    def test_match_in_param_description(self):
        """Test coincidencia en descripción de parámetro."""
        jsdoc = {
            'params': [
                {'name': 'onClick', 'description': 'Click handler function'}
            ]
        }
        
        result = match_in_params(jsdoc, 'handler')
        
        assert result == 'onClick'
    
    def test_match_in_param_type(self):
        """Test coincidencia en tipo de parámetro."""
        jsdoc = {
            'params': [
                {'name': 'onClick', 'type': 'function', 'description': 'Handler'}
            ]
        }
        
        result = match_in_params(jsdoc, 'function')
        
        assert result == 'onClick'
    
    def test_no_match(self):
        """Test sin coincidencias."""
        jsdoc = {
            'params': [
                {'name': 'onClick', 'description': 'Click handler'}
            ]
        }
        
        result = match_in_params(jsdoc, 'button')
        
        assert result is None
    
    def test_no_params(self):
        """Test sin parámetros."""
        jsdoc = {}
        
        result = match_in_params(jsdoc, 'onClick')
        
        assert result is None
    
    def test_multiple_params(self):
        """Test con múltiples parámetros."""
        jsdoc = {
            'params': [
                {'name': 'label', 'description': 'Button label'},
                {'name': 'onClick', 'description': 'Click handler'},
                {'name': 'disabled', 'description': 'Disabled state'}
            ]
        }
        
        result = match_in_params(jsdoc, 'disabled')
        
        assert result == 'disabled'


class TestMatchInReturns:
    """Tests para match_in_returns."""
    
    def test_match_in_type(self):
        """Test coincidencia en tipo de retorno."""
        jsdoc = {
            'returns': {
                'type': 'JSX.Element',
                'description': 'Rendered component'
            }
        }
        
        result = match_in_returns(jsdoc, 'jsx')
        
        assert result is True
    
    def test_match_in_description(self):
        """Test coincidencia en descripción de retorno."""
        jsdoc = {
            'returns': {
                'type': 'void',
                'description': 'Rendered button element'
            }
        }
        
        result = match_in_returns(jsdoc, 'button')
        
        assert result is True
    
    def test_no_match(self):
        """Test sin coincidencias."""
        jsdoc = {
            'returns': {
                'type': 'void',
                'description': 'No return value'
            }
        }
        
        result = match_in_returns(jsdoc, 'button')
        
        assert result is False
    
    def test_no_returns(self):
        """Test sin returns."""
        jsdoc = {}
        
        result = match_in_returns(jsdoc, 'button')
        
        assert result is False
    
    def test_case_insensitive(self):
        """Test case-insensitive."""
        jsdoc = {
            'returns': {
                'type': 'JSX.Element',
                'description': 'Rendered component'
            }
        }
        
        result = match_in_returns(jsdoc, 'JSX')
        
        assert result is True


class TestMatchInExamples:
    """Tests para match_in_examples."""
    
    def test_match_found(self):
        """Test cuando encuentra coincidencia."""
        jsdoc = {
            'examples': [
                '<Button onClick={handleClick} />'
            ]
        }
        
        result = match_in_examples(jsdoc, 'onclick')
        
        assert result is True
    
    def test_no_match(self):
        """Test sin coincidencias."""
        jsdoc = {
            'examples': [
                '<Button label="Click me" />'
            ]
        }
        
        result = match_in_examples(jsdoc, 'onclick')
        
        assert result is False
    
    def test_multiple_examples(self):
        """Test con múltiples ejemplos."""
        jsdoc = {
            'examples': [
                '<Button label="Click" />',
                '<Button onClick={handler} disabled />'
            ]
        }
        
        result = match_in_examples(jsdoc, 'disabled')
        
        assert result is True
    
    def test_no_examples(self):
        """Test sin ejemplos."""
        jsdoc = {}
        
        result = match_in_examples(jsdoc, 'button')
        
        assert result is False
    
    def test_case_insensitive(self):
        """Test case-insensitive."""
        jsdoc = {
            'examples': [
                '<BUTTON ONCLICK={HANDLER} />'
            ]
        }
        
        result = match_in_examples(jsdoc, 'onclick')
        
        assert result is True


class TestSearchInJSDoc:
    """Tests para search_in_jsdoc."""
    
    def test_match_in_description(self):
        """Test coincidencia en descripción."""
        components = [
            {
                'name': 'Button',
                'jsdoc': {'description': 'A button component'}
            },
            {
                'name': 'Card',
                'jsdoc': {'description': 'A card component'}
            }
        ]
        
        result = search_in_jsdoc(components, 'button')
        
        assert len(result) == 1
        assert result[0][0]['name'] == 'Button'
        assert result[0][1] == 'description'
    
    def test_match_in_params(self):
        """Test coincidencia en parámetros."""
        components = [
            {
                'name': 'Button',
                'jsdoc': {
                    'params': [{'name': 'onClick', 'description': 'Click handler'}]
                }
            }
        ]
        
        result = search_in_jsdoc(components, 'onclick')
        
        assert len(result) == 1
        assert result[0][1] == 'param: onClick'
    
    def test_match_in_returns(self):
        """Test coincidencia en returns."""
        components = [
            {
                'name': 'Button',
                'jsdoc': {
                    'returns': {'type': 'JSX.Element', 'description': 'Rendered button'}
                }
            }
        ]
        
        result = search_in_jsdoc(components, 'jsx')
        
        assert len(result) == 1
        assert result[0][1] == 'returns'
    
    def test_match_in_examples(self):
        """Test coincidencia en ejemplos."""
        components = [
            {
                'name': 'Button',
                'jsdoc': {
                    'examples': ['<Button onClick={handler} />']
                }
            }
        ]
        
        result = search_in_jsdoc(components, 'onclick')
        
        assert len(result) == 1
        assert result[0][1] == 'example'
    
    def test_no_jsdoc(self):
        """Test con componentes sin JSDoc."""
        components = [
            {
                'name': 'Button'
            },
            {
                'name': 'Card',
                'jsdoc': {'description': 'A card'}
            }
        ]
        
        result = search_in_jsdoc(components, 'card')
        
        assert len(result) == 1
        assert result[0][0]['name'] == 'Card'
    
    def test_multiple_matches(self):
        """Test con múltiples coincidencias."""
        components = [
            {
                'name': 'Button',
                'jsdoc': {'description': 'A button component'}
            },
            {
                'name': 'Card',
                'jsdoc': {'description': 'A card component'}
            },
            {
                'name': 'Link',
                'jsdoc': {'description': 'A link component'}
            }
        ]
        
        result = search_in_jsdoc(components, 'component')
        
        assert len(result) == 3
    
    def test_priority_order(self):
        """Test que description tiene prioridad sobre otros matches."""
        components = [
            {
                'name': 'Button',
                'jsdoc': {
                    'description': 'button component',
                    'params': [{'name': 'onClick', 'description': 'button handler'}]
                }
            }
        ]
        
        result = search_in_jsdoc(components, 'button')
        
        assert len(result) == 1
        assert result[0][1] == 'description'  # Debe priorizar description
    
    def test_empty_list(self):
        """Test con lista vacía."""
        result = search_in_jsdoc([], 'button')
        
        assert result == []

