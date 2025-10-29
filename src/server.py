"""
Frontend GPS MCP Server
Navigator and Code Reviewer for React projects
"""

from fastmcp import FastMCP
from typing import Optional, Annotated
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
async def get_stats() -> str:
    """
    Get statistics about indexed components.
    
    Example: get_stats()
    """
    total_components = await db_client.get_component_count()
    projects = await db_client.list_projects()
    
    response = "📊 **Frontend GPS Statistics**\n\n"
    response += f"- Total Projects: {len(projects)}\n"
    response += f"- Total Components: {total_components}\n\n"
    
    if projects:
        response += "**By Project:**\n"
        for project in projects:
            count = await db_client.get_component_count(project['id'])
            response += f"- {project['name']}: {count} components\n"
    
    return response


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