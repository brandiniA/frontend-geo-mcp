"""
Frontend GPS MCP Server
Navigator and Code Reviewer for React projects
"""

from fastmcp import FastMCP
from typing import Optional, Annotated, Dict, Any, Union
import os
import json
from pathlib import Path
from dotenv import load_dotenv

# Importar módulos
from registry.database_client import DatabaseClient
from tools.navigator import ComponentNavigator
from utils.indexer import ProjectIndexer

# Cargar variables de entorno
load_dotenv()

# Inicializar MCP Server
mcp = FastMCP("Frontend GPS 🚀")

# Inicializar servicios
db_client = DatabaseClient()
navigator = ComponentNavigator(db_client)
indexer = ProjectIndexer(db_client)

# Cargar configuración de proyectos
config_path = Path(".mcp-config.json")
if config_path.exists():
    with open(config_path) as f:
        project_config = json.load(f)
else:
    project_config = {"projects": {}}


# ============================================
# 🔍 NAVIGATOR TOOLS
# ============================================

@mcp.tool
async def find_component(
    query: Annotated[str, "Component name to search"],
    project_id: Annotated[Optional[str], "Filter by specific project"] = None
) -> str:
    """
    Find React components by name across all indexed projects.
    Returns location, props, hooks, and usage examples.
    
    Example: find_component("Button")
    Example: find_component("Card", project_id="ui-library")
    """
    return await navigator.find_component(query, project_id)


@mcp.tool
async def get_component_details(
    component_name: Annotated[str, "Component name"],
    project_id: Annotated[str, "Project ID"]
) -> str:
    """
    Get detailed information about a specific component.
    Includes props, hooks, dependencies, and usage examples.
    
    Example: get_component_details("Button", "main-app")
    """
    return await navigator.get_component_details(component_name, project_id)


@mcp.tool
async def list_components(
    project_id: Annotated[Optional[str], "Filter by project"] = None,
    component_type: Annotated[Optional[str], "Filter by type (page, component, layout, hook)"] = None
) -> str:
    """
    List all components in the catalog.
    Optionally filter by project or component type.
    
    Example: list_components()
    Example: list_components(project_id="ui-library")
    Example: list_components(component_type="page")
    """
    return await navigator.list_all_components(project_id, component_type)


@mcp.tool
async def list_components_in_path(
    path: Annotated[str, "Directory path (e.g., 'src/components/purchase')"],
    project_id: Annotated[str, "Project ID"]
) -> str:
    """
    List all components in a specific directory path.
    Returns all components without pagination limit.
    
    Example: list_components_in_path("src/components/purchase", "platform-funnel")
    Example: list_components_in_path("src/ui/atoms", "ui-library")
    """
    return await navigator.list_components_in_path(path, project_id)


@mcp.tool
async def search_by_hook(
    hook_name: Annotated[str, "Hook name (e.g., useState, useEffect)"],
    project_id: Annotated[Optional[str], "Filter by specific project"] = None
) -> str:
    """
    Find components that use a specific React hook.
    
    Example: search_by_hook("useState")
    Example: search_by_hook("useEffect")
    Example: search_by_hook("useState", project_id="craftitapp")
    """
    return await navigator.search_by_hook(hook_name, project_id)


@mcp.tool
async def search_by_jsdoc(
    query: Annotated[str, "Search term in JSDoc documentation"],
    project_id: Annotated[Optional[str], "Filter by project"] = None
) -> str:
    """
    Find components by searching their JSDoc documentation.
    Searches in descriptions, parameters, return types, and examples.
    
    Example: search_by_jsdoc("click handler")
    Example: search_by_jsdoc("form validation", project_id="ui-library")
    """
    return await navigator.search_by_jsdoc(query, project_id)


@mcp.tool
async def search_components_semantic(
    query: Annotated[str, "Search term"] = "",
    project_id: Annotated[Optional[str], "Filter by project"] = None,
    filters: Annotated[Optional[Dict[str, Any]], "Advanced filters"] = None
) -> str:
    """
    Search components by meaning with optional filters.
    Searches in names, descriptions, file paths, and JSDoc.
    
    Example: search_components_semantic("price breakdown")
    Example: search_components_semantic("button", filters={"type": "atom"})
    Example: search_components_semantic("form", filters={"path": "src/components", "contains_hook": "useState"})
    """
    # Convertir string vacío a None para consistencia
    query_param = query if query else None
    return await navigator.search_components_semantic(query_param, project_id, filters)


@mcp.tool
async def get_component_docs(
    component_name: Annotated[str, "Component name"],
    project_id: Annotated[str, "Project ID"]
) -> str:
    """
    Get the complete JSDoc documentation for a component.
    Includes parameters, return types, examples, author, version, deprecation status.
    
    Example: get_component_docs("Button", "ui-library")
    Example: get_component_docs("Header", "main-app")
    """
    return await navigator.get_component_docs(component_name, project_id)


@mcp.tool
async def get_component_hierarchy(
    component_name: Annotated[str, "Name of the component"],
    project_id: Annotated[str, "Project ID"],
    direction: Annotated[Optional[str], "Direction: 'down' (dependencies), 'up' (dependents), 'both' (default: 'down')"] = 'down',
    max_depth: Annotated[Optional[Union[int, float, str]], "Maximum depth of the tree (default: 5). Accepts integer, number, or numeric string."] = 5
) -> str:
    """
    Get the component hierarchy tree showing dependencies and dependents.
    
    Shows what components a component uses (dependencies) and what components use it (dependents).
    Useful for understanding component relationships and impact analysis.
    
    Args:
        component_name: Name of the component to analyze
        project_id: Project ID where the component exists
        direction: 
            - 'down': Show dependencies (components this uses)
            - 'up': Show dependents (components that use this)
            - 'both': Show both dependencies and dependents
        max_depth: Maximum depth to traverse (default: 5). Accepts both integer and number types.
    
    Returns:
        Formatted markdown tree showing component hierarchy
    
    Example:
        get_component_hierarchy("HomePage", "my-app", direction="down", max_depth=3)
    """
    # Convert max_depth to int if it's a float or string (from MCP clients that send number/string type)
    if max_depth is not None:
        max_depth_int = int(float(max_depth))  # Handles int, float, and numeric strings
    else:
        max_depth_int = None
    return await navigator.get_component_hierarchy(component_name, project_id, direction, max_depth_int)


# ============================================
# 🪝 HOOK TOOLS
# ============================================

@mcp.tool
async def find_hook(
    query: Annotated[str, "Hook name to search"],
    project_id: Annotated[Optional[str], "Filter by specific project"] = None
) -> str:
    """
    Find React hooks by name across all indexed projects.
    Returns location, parameters, return type, and usage examples.
    
    Example: find_hook("useAuth")
    Example: find_hook("usePricing", project_id="platform-funnel")
    """
    return await navigator.find_hook(query, project_id)


@mcp.tool
async def get_hook_details(
    hook_name: Annotated[str, "Hook name"],
    project_id: Annotated[str, "Project ID"]
) -> str:
    """
    Get detailed information about a specific hook.
    Includes parameters, return type, hooks used, dependencies, feature flags, and usage examples.
    
    Example: get_hook_details("useAuth", "main-app")
    Example: get_hook_details("usePricingBeforeCheckout", "platform-funnel")
    """
    return await navigator.get_hook_details(hook_name, project_id)


@mcp.tool
async def list_hooks(
    project_id: Annotated[Optional[str], "Filter by project"] = None
) -> str:
    """
    List all hooks in the catalog.
    Optionally filter by project.
    
    Example: list_hooks()
    Example: list_hooks(project_id="platform-funnel")
    """
    return await navigator.list_all_hooks(project_id)


@mcp.tool
async def get_hook_docs(
    hook_name: Annotated[str, "Hook name"],
    project_id: Annotated[str, "Project ID"]
) -> str:
    """
    Get the complete JSDoc documentation for a hook.
    Includes parameters, return types, examples, author, version, deprecation status.
    
    Example: get_hook_docs("useAuth", "main-app")
    Example: get_hook_docs("usePricingBeforeCheckout", "platform-funnel")
    """
    return await navigator.get_hook_docs(hook_name, project_id)


# ============================================
# 🚩 FEATURE FLAG TOOLS
# ============================================

@mcp.tool
async def get_feature_flag_usage(
    flag_name: Annotated[str, "Feature flag name to search"],
    project_id: Annotated[str, "Project ID"],
    entity_type: Annotated[str, "Type of entities to search: 'components', 'hooks', or 'all'"] = "all"
) -> str:
    """
    Find all entities (components, hooks, or both) that use a specific feature flag.
    
    Args:
        flag_name: Name of the feature flag to search
        project_id: Project ID where to search
        entity_type: Type of entities to search:
            - 'components': Search only in components
            - 'hooks': Search only in hooks
            - 'all': Search in both components and hooks (default)
    
    Example: get_feature_flag_usage("SHOW_PURCHASE_FOOTER", "platform-funnel", "all")
    Example: get_feature_flag_usage("USE_NEW_CARD_INPUT", "platform-funnel", "components")
    Example: get_feature_flag_usage("PRICING_BEFORE_CHECKOUT", "platform-funnel", "hooks")
    """
    if entity_type not in ["components", "hooks", "all"]:
        return f"❌ Invalid entity_type '{entity_type}'. Must be 'components', 'hooks', or 'all'"
    
    response = f"🚩 **Feature Flag Usage: `{flag_name}`**\n\n"
    response += f"**Project:** {project_id}\n"
    response += f"**Search scope:** {entity_type}\n\n"
    
    found_any = False
    
    # Search in components
    if entity_type in ["components", "all"]:
        components = await db_client.get_components_using_flag(flag_name, project_id)
        if components:
            found_any = True
            response += f"### 📦 Components ({len(components)})\n\n"
            for comp in components:
                usage_location = comp.get('usage_location', 'component')
                usage_context = comp.get('usage_context')
                container_path = comp.get('container_file_path')
                usage_type = comp.get('usage_type')
                
                comp_line = f"- **{comp['name']}** (`{comp['file_path']}`)"
                if usage_location == 'container':
                    comp_line += f" - Used in container"
                    if container_path:
                        comp_line += f" (`{container_path}`)"
                if usage_context:
                    comp_line += f" - Context: `{usage_context}`"
                if usage_type:
                    comp_line += f" - Type: `{usage_type}`"
                response += comp_line + "\n"
            response += "\n"
        elif entity_type == "components":
            response += f"### 📦 Components\n\n"
            response += f"⚠️ No components found using this feature flag.\n\n"
    
    # Search in hooks
    if entity_type in ["hooks", "all"]:
        hooks = await db_client.get_hooks_using_flag(flag_name, project_id)
        if hooks:
            found_any = True
            response += f"### 🪝 Hooks ({len(hooks)})\n\n"
            for hook in hooks:
                response += f"- **{hook['name']}** (`{hook['file_path']}`)\n"
            response += "\n"
        elif entity_type == "hooks":
            response += f"### 🪝 Hooks\n\n"
            response += f"⚠️ No hooks found using this feature flag.\n\n"
    
    if not found_any:
        if entity_type == "all":
            return f"🔍 No components or hooks found using feature flag '{flag_name}' in project '{project_id}'"
        elif entity_type == "components":
            return f"🔍 No components found using feature flag '{flag_name}' in project '{project_id}'"
        else:
            return f"🔍 No hooks found using feature flag '{flag_name}' in project '{project_id}'"
    
    return response


@mcp.tool
async def list_feature_flags(
    project_id: Annotated[Optional[str], "Filter by project"] = None
) -> str:
    """
    List all feature flags in a project.
    
    Example: list_feature_flags(project_id="main-app")
    """
    if not project_id:
        return "❌ project_id is required"
    
    flags = await db_client.get_feature_flags_by_project(project_id)
    
    if not flags:
        return f"🚩 No feature flags found in project '{project_id}'"
    
    response = f"🚩 **Feature Flags in '{project_id}':**\n\n"
    for flag in flags:
        response += f"- **{flag['name']}**\n"
        if flag.get('description'):
            response += f"  - Description: {flag['description']}\n"
        if flag.get('default_value') is not None:
            response += f"  - Default: {flag['default_value']}\n"
        if flag.get('value_type'):
            response += f"  - Type: {flag['value_type']}\n"
        if flag.get('possible_values'):
            response += f"  - Possible values: {', '.join(flag['possible_values'])}\n"
        response += "\n"
    
    return response


@mcp.tool
async def get_feature_flag_details(
    flag_name: Annotated[str, "Feature flag name"],
    project_id: Annotated[str, "Project ID"]
) -> str:
    """
    Get detailed information about a specific feature flag.
    Includes default value, type, description, and components that use it.
    
    Example: get_feature_flag_details("SHOW_PURCHASE_FOOTER", "main-app")
    """
    flag = await db_client.get_feature_flag_by_name(flag_name, project_id)
    
    if not flag:
        return f"❌ Feature flag '{flag_name}' not found in project '{project_id}'"
    
    response = f"🚩 **Feature Flag: {flag_name}**\n\n"
    
    if flag.get('description'):
        response += f"**Description:** {flag['description']}\n\n"
    
    if flag.get('default_value') is not None:
        response += f"**Default Value:** {flag['default_value']}\n"
    
    if flag.get('value_type'):
        response += f"**Type:** {flag['value_type']}\n"
    
    if flag.get('possible_values'):
        response += f"**Possible Values:** {', '.join(flag['possible_values'])}\n"
    
    if flag.get('file_path'):
        response += f"**File:** `{flag['file_path']}`\n"
    
    # Obtener componentes que usan este flag
    components = await db_client.get_components_using_flag(flag_name, project_id)
    hooks = await db_client.get_hooks_using_flag(flag_name, project_id)
    
    if components or hooks:
        response += "\n**Usage:**\n"
        
        if components:
            response += f"\n📦 **Components ({len(components)}):**\n"
            for comp in components:
                response += f"- {comp['name']} (`{comp['file_path']}`)\n"
        
        if hooks:
            response += f"\n🪝 **Hooks ({len(hooks)}):**\n"
            for hook in hooks:
                response += f"- {hook['name']} (`{hook['file_path']}`)\n"
    else:
        response += "\n⚠️ **Not used in any component or hook**\n"
    
    return response


@mcp.tool
async def get_unused_feature_flags(
    project_id: Annotated[str, "Project ID"]
) -> str:
    """
    Get feature flags that are defined but not used in any component or hook.
    
    Example: get_unused_feature_flags("main-app")
    """
    unused_flags = await db_client.get_unused_feature_flags(project_id)
    
    if not unused_flags:
        return f"✅ All feature flags in project '{project_id}' are being used!"
    
    response = f"⚠️ **Unused Feature Flags in '{project_id}':**\n\n"
    for flag in unused_flags:
        response += f"- **{flag['name']}**"
        if flag.get('description'):
            response += f" - {flag['description']}"
        response += "\n"
    
    return response


@mcp.tool
async def get_feature_flag_impact(
    flag_name: Annotated[str, "Feature flag name"],
    project_id: Annotated[str, "Project ID"]
) -> str:
    """
    Analyze the impact of changing or removing a feature flag.
    Shows all affected components and hooks, and provides migration steps.
    
    Example: get_feature_flag_impact("SHOW_PURCHASE_FOOTER", "platform-funnel")
    """
    return await navigator.get_feature_flag_impact(flag_name, project_id)


@mcp.tool
async def get_unused_hooks(
    project_id: Annotated[str, "Project ID"]
) -> str:
    """
    Get hooks that are defined but not used in any component or other hook.
    
    Example: get_unused_hooks("platform-funnel")
    """
    return await navigator.get_unused_hooks(project_id)


@mcp.tool
async def get_hook_usage_stats(
    project_id: Annotated[Optional[str], "Filter by project"] = None
) -> str:
    """
    Get statistics about hook usage.
    Shows most used native hooks and custom hooks.
    
    Example: get_hook_usage_stats()
    Example: get_hook_usage_stats(project_id="platform-funnel")
    """
    return await navigator.get_hook_usage_stats(project_id)


@mcp.tool
async def map_feature_flags_file(
    project_id: Annotated[str, "Project ID"]
) -> str:
    """
    Map and show all feature flags extracted from defaultFeatures.js file.
    Useful for debugging if flags are being parsed correctly.
    
    Example: map_feature_flags_file("main-app")
    """
    flags = await db_client.get_feature_flags_by_project(project_id)
    
    if not flags:
        return f"❌ No feature flags found in project '{project_id}'. Make sure the project has been synced."
    
    # Agrupar por archivo
    flags_by_file = {}
    for flag in flags:
        file_path = flag.get('file_path', 'unknown')
        if file_path not in flags_by_file:
            flags_by_file[file_path] = []
        flags_by_file[file_path].append(flag)
    
    response = f"📋 **Feature Flags Mapped from defaultFeatures.js**\n\n"
    response += f"**Total flags:** {len(flags)}\n\n"
    
    for file_path, file_flags in flags_by_file.items():
        response += f"**File:** `{file_path}` ({len(file_flags)} flags)\n\n"
        
        # Ordenar alfabéticamente
        file_flags_sorted = sorted(file_flags, key=lambda x: x['name'])
        
        for flag in file_flags_sorted:
            response += f"- **{flag['name']}**"
            if flag.get('default_value') is not None:
                response += f" = `{flag['default_value']}`"
            if flag.get('value_type'):
                response += f" ({flag['value_type']})"
            if flag.get('description'):
                response += f" // {flag['description']}"
            if flag.get('possible_values'):
                response += f" [Values: {', '.join(flag['possible_values'])}]"
            response += "\n"
        response += "\n"
    
    return response


# ============================================
# 🔄 SYNC TOOLS
# ============================================

@mcp.tool
async def sync_project(
    project_id: Annotated[str, "Project ID to sync from config"]
) -> str:
    """
    Sync a project from GitHub repository.
    Clones the repo, scans for React components, and indexes them.
    
    Example: sync_project("main-app")
    """
    if project_id not in project_config["projects"]:
        return f"❌ Project '{project_id}' not found in .mcp-config.json"
    
    project = project_config["projects"][project_id]
    repo_url = project["repository"]
    branch = project.get("branch", "main")
    
    try:
        # Asegurar que el proyecto existe en la DB
        await db_client.upsert_project(project_id, {
            'name': project.get('name', project_id),
            'repository_url': repo_url,
            'branch': branch,
            'type': project.get('type', 'application')
        })
        
        # Indexar
        await indexer.index_project(project_id, repo_url, branch)
        
        # Obtener conteo
        count = await db_client.get_component_count(project_id)
        
        return f"✅ Project '{project_id}' synced successfully!\n\n📊 Total components indexed: {count}"
    except Exception as e:
        return f"❌ Error syncing project: {str(e)}"


@mcp.tool
async def list_projects() -> str:
    """
    List all configured projects and their sync status.
    
    Example: list_projects()
    """
    projects = await db_client.list_projects()
    
    if not projects:
        return "📂 No projects configured yet.\n\nAdd projects to .mcp-config.json and run sync_project"
    
    response = "📂 **Configured Projects:**\n\n"
    
    for project in projects:
        response += f"**{project['name']}** (`{project['id']}`)\n"
        response += f"- Repository: {project['repository_url']}\n"
        response += f"- Branch: {project['branch']}\n"
        response += f"- Type: {project['type']}\n"
        
        # Obtener conteo de componentes
        count = await db_client.get_component_count(project['id'])
        response += f"- Components: {count}\n"
        response += "\n"
    
    return response


# ============================================
# 📊 STATS TOOLS
# ============================================

@mcp.tool
async def list_prompts() -> str:
    """
    List all available MCP prompts in this server.
    Useful for verifying that prompts are correctly exposed.
    
    Example: list_prompts()
    """
    prompts = await mcp.get_prompts()
    
    if not prompts:
        return "❌ No prompts found in this MCP server"
    
    response = f"🎯 **Available MCP Prompts ({len(prompts)}):**\n\n"
    
    for name, prompt_obj in prompts.items():
        response += f"### {prompt_obj.name}\n"
        response += f"**Description:** {prompt_obj.description}\n"
        
        if prompt_obj.arguments:
            response += f"**Arguments ({len(prompt_obj.arguments)}):**\n"
            for arg in prompt_obj.arguments:
                required = "✅ Required" if arg.required else "⚪ Optional"
                description = arg.description.split('\n')[0]  # Solo primera línea
                response += f"- `{arg.name}` ({required}): {description}\n"
        else:
            response += "**Arguments:** None\n"
        
        response += "\n"
    
    return response


@mcp.tool
async def get_stats() -> str:
    """
    Get detailed statistics about indexed components.
    Includes totals, breakdown by type and path.
    
    Example: get_stats()
    """
    stats = await db_client.get_component_index_stats()
    projects = await db_client.list_projects()
    
    response = "📊 **Frontend GPS Statistics**\n\n"
    response += f"- **Total Projects:** {len(projects)}\n"
    response += f"- **Total Components:** {stats['total']}\n\n"
    
    if stats['byType']:
        response += "**By Type:**\n"
        for comp_type, count in sorted(stats['byType'].items()):
            response += f"- {comp_type}: {count}\n"
        response += "\n"
    
    if stats['byPath']:
        response += "**Top Paths:**\n"
        for path, count in list(stats['byPath'].items())[:10]:
            response += f"- `{path}`: {count} components\n"
        response += "\n"
    
    if stats['lastUpdated']:
        response += f"**Last Updated:** {stats['lastUpdated']}\n"
    
    response += f"**Index Coverage:** {stats['indexCoverage']}%\n"
    
    return response


# ============================================
# 📦 BARREL EXPORT TOOLS
# ============================================

@mcp.tool
async def get_barrel_exports(
    project_id: Annotated[str, "Project ID"]
) -> str:
    """
    Get all barrel exports in a project with their resolution status.
    Shows resolved and unresolved barrel exports, including containers.
    
    Example: get_barrel_exports("platform-funnel")
    """
    return await navigator.get_barrel_exports(project_id)


# ============================================
# 🔄 DEPENDENCY ANALYSIS TOOLS
# ============================================

@mcp.tool
async def find_circular_dependencies(
    project_id: Annotated[str, "Project ID"]
) -> str:
    """
    Detect circular dependencies between components.
    Useful for identifying architectural issues and potential infinite loops.
    
    Example: find_circular_dependencies("platform-funnel")
    """
    return await navigator.find_circular_dependencies(project_id)


@mcp.tool
async def get_unresolved_imports(
    project_id: Annotated[str, "Project ID"],
    limit: Annotated[Optional[int], "Maximum number of results to show (default: 50)"] = 50
) -> str:
    """
    Get imports that could not be resolved to components.
    Helps identify missing components, indexing issues, or barrel export problems.
    
    Example: get_unresolved_imports("platform-funnel")
    Example: get_unresolved_imports("platform-funnel", limit=100)
    """
    return await navigator.get_unresolved_imports(project_id, limit)


# ============================================
# 🎯 PROMPTS - Ejecución Automática de Tools
# ============================================

@mcp.prompt(
    name="analyze_component",
    description="Análisis completo de un componente React incluyendo detalles, jerarquía y documentación"
)
async def analyze_component_prompt(
    component_name: Annotated[str, "Nombre del componente a analizar"],
    project_id: Annotated[str, "ID del proyecto donde existe el componente"]
) -> str:
    """
    Analiza un componente React de forma completa ejecutando automáticamente múltiples tools.
    """
    return f"""Please perform a comprehensive analysis of the React component '{component_name}' in project '{project_id}':

1. First, find the component using find_component tool with query="{component_name}" and project_id="{project_id}"
2. Get detailed information using get_component_details with component_name="{component_name}" and project_id="{project_id}"
3. Get the complete JSDoc documentation using get_component_docs with component_name="{component_name}" and project_id="{project_id}"
4. Get the component hierarchy (dependencies and dependents) using get_component_hierarchy with component_name="{component_name}", project_id="{project_id}", direction="both", max_depth=3

After gathering all information, provide a comprehensive summary including:
- Component location and structure
- Props and their types
- Hooks used
- Dependencies (what components it uses)
- Dependents (what components use it)
- Documentation quality
- Code quality recommendations
- Potential optimizations
- Testing suggestions"""


@mcp.prompt(
    name="explore_project",
    description="Explora un proyecto listando componentes, estadísticas y estructura"
)
async def explore_project_prompt(
    project_id: Annotated[str, "ID del proyecto a explorar"]
) -> str:
    """
    Explora un proyecto de forma completa listando componentes y obteniendo estadísticas.
    """
    return f"""Please explore the project '{project_id}' comprehensively:

1. List all components in the project using list_components with project_id="{project_id}"
2. Get project statistics using get_stats
3. List components by type (pages, components, layouts, hooks) using list_components with project_id="{project_id}" and component_type="page", then "component", then "layout", then "hook"

After gathering all information, provide:
- Project overview
- Component breakdown by type
- Most common component paths
- Project structure insights
- Recommendations for organization"""


@mcp.prompt(
    name="find_hook_usage",
    description="Encuentra todos los componentes que usan un hook específico de React"
)
async def find_hook_usage_prompt(
    hook_name: Annotated[str, "Nombre del hook de React (ej: useState, useEffect, useContext)"],
    project_id: Annotated[Optional[str], "Filtrar por proyecto específico"] = None
) -> str:
    """
    Encuentra todos los componentes que usan un hook específico y analiza sus patrones de uso.
    """
    project_filter = f' and project_id="{project_id}"' if project_id else ""
    return f"""Please find all components that use the React hook '{hook_name}'{project_filter}:

1. Search for components using the hook using search_by_hook with hook_name="{hook_name}"{project_filter}
2. For each component found, get its details to understand how the hook is being used
3. Analyze usage patterns and provide recommendations

After analysis, provide:
- List of all components using this hook
- Common usage patterns
- Potential issues or anti-patterns
- Recommendations for hook usage
- Opportunities for custom hooks"""


@mcp.prompt(
    name="search_component_by_feature",
    description="Busca componentes por funcionalidad usando búsqueda semántica"
)
async def search_component_by_feature_prompt(
    query: Annotated[str, "Funcionalidad a buscar (ej: 'validación de formularios', 'mostrar precio', 'autenticación de usuario')"],
    project_id: Annotated[Optional[str], "Filtrar por proyecto específico"] = None
) -> str:
    """
    Busca componentes por funcionalidad usando búsqueda semántica.
    """
    project_filter = f' and project_id="{project_id}"' if project_id else ""
    return f"""Please search for components related to '{query}'{project_filter}:

1. Perform semantic search using search_components_semantic with query="{query}"{project_filter}
2. Also search in JSDoc documentation using search_by_jsdoc with query="{query}"{project_filter}
3. For relevant results, get component details to understand their functionality

After searching, provide:
- List of relevant components
- How each component relates to the feature
- Component locations and usage
- Recommendations for using or modifying these components"""


@mcp.prompt(
    name="explore_directory",
    description="Explora todos los componentes en una ruta de directorio específica"
)
async def explore_directory_prompt(
    path: Annotated[str, "Ruta del directorio a explorar (ej: 'src/components/purchase')"],
    project_id: Annotated[str, "ID del proyecto"]
) -> str:
    """
    Explora todos los componentes en un directorio específico y analiza sus relaciones.
    """
    return f"""Please explore the directory '{path}' in project '{project_id}':

1. List all components in the path using list_components_in_path with path="{path}" and project_id="{project_id}"
2. For each component found, get its details using get_component_details
3. Get the hierarchy for key components to understand dependencies

After exploration, provide:
- Complete list of components in the directory
- Component relationships and dependencies
- Directory structure insights
- Recommendations for organization
- Potential refactoring opportunities"""


@mcp.prompt(
    name="component_impact_analysis",
    description="Analiza el impacto de modificar un componente revisando sus dependientes"
)
async def component_impact_analysis_prompt(
    component_name: Annotated[str, "Nombre del componente a analizar"],
    project_id: Annotated[str, "ID del proyecto"]
) -> str:
    """
    Analiza el impacto de modificar un componente revisando qué depende de él.
    """
    return f"""Please perform an impact analysis for component '{component_name}' in project '{project_id}':

1. Get component details using get_component_details with component_name="{component_name}" and project_id="{project_id}"
2. Get component hierarchy showing dependents (what uses this component) using get_component_hierarchy with component_name="{component_name}", project_id="{project_id}", direction="up", max_depth=5
3. Also get dependencies (what this component uses) using get_component_hierarchy with component_name="{component_name}", project_id="{project_id}", direction="down", max_depth=3

After analysis, provide:
- Complete dependency tree
- List of all components that depend on this component
- Impact assessment if this component is modified
- Breaking change risks
- Migration recommendations"""


@mcp.prompt(
    name="onboard_new_developer",
    description="Ayuda a un nuevo desarrollador a entender la estructura del proyecto y los componentes"
)
async def onboard_new_developer_prompt() -> str:
    """
    Proporciona una guía completa de onboarding para nuevos desarrolladores.
    """
    return """Please help onboard a new developer to this project:

1. List all projects using list_projects
2. Get overall statistics using get_stats
3. For each project, list components by type (pages, components, layouts, hooks)
4. Show the most common component paths to understand the structure

After gathering information, provide:
- Project overview and structure
- Component organization patterns
- Key directories and their purposes
- Common component types and their usage
- Quick start guide
- Best practices for this codebase
- Where to find specific types of components"""


# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        # Modo HTTP para Railway/Render
        port = int(os.getenv("PORT", 8080))
        print(f"🚀 Starting Frontend GPS MCP Server on port {port}")
        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=port
        )
    else:
        # Modo stdio para Cursor local
        print("🚀 Starting Frontend GPS MCP Server (stdio mode)")
        mcp.run()