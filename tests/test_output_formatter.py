"""
Tests para utilidades de formateo de output (output_formatter).
"""

import pytest
from src.tools.utils.output_formatter import (
    group_by_project,
    format_list_with_more,
)


class TestGroupByProject:
    """Tests para group_by_project."""
    
    def test_group_by_project(self):
        """Test agrupación por project_id."""
        items = [
            {'name': 'Button', 'project_id': 'ui-library'},
            {'name': 'Card', 'project_id': 'ui-library'},
            {'name': 'HomePage', 'project_id': 'main-app'},
        ]
        
        result = group_by_project(items)
        
        assert 'ui-library' in result
        assert 'main-app' in result
        assert len(result['ui-library']) == 2
        assert len(result['main-app']) == 1
    
    def test_with_missing_project_id(self):
        """Test con items sin project_id."""
        items = [
            {'name': 'Button', 'project_id': 'ui-library'},
            {'name': 'Card'},  # Sin project_id
        ]
        
        result = group_by_project(items)
        
        assert 'ui-library' in result
        assert None in result  # Los items sin project_id se agrupan bajo None
        assert len(result['ui-library']) == 1
        assert len(result[None]) == 1
    
    def test_empty_list(self):
        """Test con lista vacía."""
        result = group_by_project([])
        
        assert result == {}
    
    def test_single_project(self):
        """Test con un solo proyecto."""
        items = [
            {'name': 'Button', 'project_id': 'ui-library'},
            {'name': 'Card', 'project_id': 'ui-library'},
        ]
        
        result = group_by_project(items)
        
        assert len(result) == 1
        assert 'ui-library' in result
        assert len(result['ui-library']) == 2


class TestFormatListWithMore:
    """Tests para format_list_with_more."""
    
    def test_within_limit(self):
        """Test con items dentro del límite."""
        items = ['useState', 'useEffect', 'useContext']
        
        result = format_list_with_more(items, max_items=5)
        
        assert result == 'useState, useEffect, useContext'
    
    def test_exceeds_limit(self):
        """Test con items que exceden el límite."""
        items = ['useState', 'useEffect', 'useContext', 'useReducer', 'useMemo', 'useCallback']
        
        result = format_list_with_more(items, max_items=3)
        
        assert 'useState' in result
        assert 'useEffect' in result
        assert 'useContext' in result
        assert '(+3 more)' in result
    
    def test_exactly_at_limit(self):
        """Test con exactamente el límite de items."""
        items = ['useState', 'useEffect', 'useContext', 'useReducer', 'useMemo']
        
        result = format_list_with_more(items, max_items=5)
        
        assert result == 'useState, useEffect, useContext, useReducer, useMemo'
        assert '(+' not in result
    
    def test_empty_list(self):
        """Test con lista vacía."""
        result = format_list_with_more([])
        
        assert result == ""
    
    def test_custom_separator(self):
        """Test con separador personalizado."""
        items = ['useState', 'useEffect', 'useContext']
        
        result = format_list_with_more(items, max_items=5, separator=' | ')
        
        assert result == 'useState | useEffect | useContext'
    
    def test_custom_max_items(self):
        """Test con max_items personalizado."""
        items = ['a', 'b', 'c', 'd', 'e', 'f']
        
        result = format_list_with_more(items, max_items=2)
        
        assert 'a' in result
        assert 'b' in result
        assert '(+4 more)' in result
    
    def test_single_item(self):
        """Test con un solo item."""
        result = format_list_with_more(['useState'])
        
        assert result == 'useState'

