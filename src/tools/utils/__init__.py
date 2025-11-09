"""
Utilidades para las herramientas de Navigator.
"""

from .time_utils import format_relative_time
from .component_utils import get_all_hooks, is_new_component, group_components_by_type
from .output_formatter import group_by_project, format_list_with_more
from .formatter import generate_import_path, format_component_entry, format_component_with_details
from .search_utils import search_in_jsdoc, match_in_description, match_in_params, match_in_returns, match_in_examples
from .navigator_formatter import (
    COMPONENT_TYPE_ICONS,
    get_component_type_icon,
    format_jsdoc_section,
    format_hooks_section,
    format_hooks_inline,
    format_components_by_type,
    format_component_summary,
    format_project_header,
    truncate_description,
    format_usage_example,
)
from .hierarchy_utils import build_dependency_tree, format_tree, detect_circular_dependencies
from .component_search_utils import find_exact_or_first_component, normalize_components_to_dicts

__all__ = [
    'format_relative_time',
    'get_all_hooks',
    'is_new_component',
    'group_components_by_type',
    'group_by_project',
    'format_list_with_more',
    'generate_import_path',
    'format_component_entry',
    'format_component_with_details',
    'search_in_jsdoc',
    'match_in_description',
    'match_in_params',
    'match_in_returns',
    'match_in_examples',
    # Navigator formatter
    'COMPONENT_TYPE_ICONS',
    'get_component_type_icon',
    'format_jsdoc_section',
    'format_hooks_section',
    'format_hooks_inline',
    'format_components_by_type',
    'format_component_summary',
    'format_project_header',
    'truncate_description',
    'format_usage_example',
    # Hierarchy utils
    'build_dependency_tree',
    'format_tree',
    'detect_circular_dependencies',
    # Component search utils
    'find_exact_or_first_component',
    'normalize_components_to_dicts',
]
