"""
Tests para hierarchy_utils.
"""

import pytest
from src.tools.utils.hierarchy_utils import (
    build_dependency_tree,
    format_tree,
    detect_circular_dependencies,
)


class TestHierarchyUtils:
    """Tests para utilidades de jerarquía."""
    
    def test_build_dependency_tree(self):
        """Test construcción de árbol con estadísticas"""
        tree_data = {
            'component': {
                'id': 1,
                'name': 'Button',
                'file_path': 'components/Button.tsx',
                'component_type': 'component'
            },
            'children': [
                {
                    'component': {
                        'id': 2,
                        'name': 'Icon',
                        'file_path': 'components/Icon.tsx',
                        'component_type': 'component'
                    },
                    'children': [],
                    'depth': 1
                }
            ],
            'depth': 0
        }
        
        result = build_dependency_tree(tree_data, 'down')
        
        assert 'stats' in result
        assert result['stats']['total_dependencies'] == 1
        assert result['direction'] == 'down'
    
    def test_format_tree_basic(self):
        """Test formateo básico de árbol"""
        tree = {
            'component': {
                'name': 'Button',
                'file_path': 'components/Button.tsx',
                'component_type': 'component'
            },
            'children': [
                {
                    'component': {
                        'name': 'Icon',
                        'file_path': 'components/Icon.tsx',
                        'component_type': 'component'
                    },
                    'children': [],
                    'import_type': 'named',
                    'from_path': './Icon'
                }
            ],
            'direction': 'down',
            'stats': {
                'total_dependencies': 1,
                'total_dependents': 0,
                'max_depth': 1,
                'has_circular': False
            }
        }
        
        result = format_tree(tree, max_depth=3)
        
        assert 'Button' in result
        assert 'Icon' in result
        assert 'Dependencies' in result
        assert 'Statistics' in result
    
    def test_format_tree_empty(self):
        """Test formateo de árbol vacío"""
        tree = {
            'component': {
                'name': 'Button',
                'file_path': 'components/Button.tsx',
                'component_type': 'component'
            },
            'children': [],
            'direction': 'down',
            'stats': {
                'total_dependencies': 0,
                'total_dependents': 0,
                'max_depth': 0,
                'has_circular': False
            }
        }
        
        result = format_tree(tree)
        
        assert 'Button' in result
        assert 'No dependencies found' in result
    
    def test_detect_circular_dependencies(self):
        """Test detección de dependencias circulares"""
        tree = {
            'component': {
                'name': 'A',
                'file_path': 'A.tsx',
                'component_type': 'component'
            },
            'children': [
                {
                    'component': {
                        'name': 'B',
                        'file_path': 'B.tsx',
                        'component_type': 'component'
                    },
                    'children': [
                        {
                            'component': {
                                'name': 'A',  # Circular!
                                'file_path': 'A.tsx',
                                'component_type': 'component'
                            },
                            'children': [],
                            'circular': True
                        }
                    ],
                    'depth': 1
                }
            ],
            'depth': 0
        }
        
        cycles = detect_circular_dependencies(tree)
        
        # Debe detectar el ciclo A -> B -> A
        assert len(cycles) > 0
    
    def test_format_tree_with_max_depth(self):
        """Test formateo con límite de profundidad"""
        tree = {
            'component': {
                'name': 'A',
                'file_path': 'A.tsx',
                'component_type': 'component'
            },
            'children': [
                {
                    'component': {
                        'name': 'B',
                        'file_path': 'B.tsx',
                        'component_type': 'component'
                    },
                    'children': [
                        {
                            'component': {
                                'name': 'C',
                                'file_path': 'C.tsx',
                                'component_type': 'component'
                            },
                            'children': [],
                            'max_depth_reached': True
                        }
                    ],
                    'depth': 1
                }
            ],
            'direction': 'down',
            'stats': {
                'total_dependencies': 2,
                'total_dependents': 0,
                'max_depth': 2,
                'has_circular': False
            }
        }
        
        result = format_tree(tree, max_depth=2)
        
        assert 'A' in result
        assert 'B' in result
        # C debería estar truncado o marcado
    
    def test_format_tree_direction_up(self):
        """Test formateo con dirección 'up' (dependientes)"""
        tree = {
            'component': {
                'name': 'Button',
                'file_path': 'components/Button.tsx',
                'component_type': 'component'
            },
            'children': [
                {
                    'component': {
                        'name': 'HomePage',
                        'file_path': 'pages/HomePage.tsx',
                        'component_type': 'page'
                    },
                    'children': [],
                    'import_type': 'default',
                    'from_path': './Button'
                }
            ],
            'direction': 'up',
            'stats': {
                'total_dependencies': 0,
                'total_dependents': 1,
                'max_depth': 1,
                'has_circular': False
            }
        }
        
        result = format_tree(tree)
        
        assert 'Dependents' in result
        assert 'HomePage' in result
    
    def test_format_tree_direction_both(self):
        """Test formateo con dirección 'both' (dependencias y dependientes)"""
        tree = {
            'component': {
                'name': 'Button',
                'file_path': 'components/Button.tsx',
                'component_type': 'component'
            },
            'children': [
                {
                    'component': {
                        'name': 'Icon',
                        'file_path': 'components/Icon.tsx',
                        'component_type': 'component'
                    },
                    'children': [],
                    'import_type': 'named',
                    'from_path': './Icon',
                    'hierarchy_direction': 'down'  # Dependencia
                },
                {
                    'component': {
                        'name': 'HomePage',
                        'file_path': 'pages/HomePage.tsx',
                        'component_type': 'page'
                    },
                    'children': [],
                    'import_type': 'default',
                    'from_path': './Button',
                    'hierarchy_direction': 'up'  # Dependiente
                }
            ],
            'direction': 'both',
            'stats': {
                'total_dependencies': 1,
                'total_dependents': 1,
                'max_depth': 1,
                'has_circular': False
            }
        }
        
        result = format_tree(tree)
        
        # Debe mostrar ambas secciones
        assert 'Full Hierarchy' in result
        assert 'Dependencies' in result
        assert 'Dependents' in result
        assert 'Icon' in result  # Dependencia
        assert 'HomePage' in result  # Dependiente

