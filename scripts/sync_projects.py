#!/usr/bin/env python
"""
Script para sincronizar proyectos manualmente desde GitHub.
Usage: python scripts/sync_projects.py --project test-project
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.registry.database_client import DatabaseClient
from src.utils.indexer import ProjectIndexer
import json
from dotenv import load_dotenv

load_dotenv()


async def sync_project(project_id: str):
    """Sincroniza un proyecto específico."""
    
    # Cargar config
    config_path = Path(".mcp-config.json")
    if not config_path.exists():
        print("❌ .mcp-config.json not found")
        print("   Please create it with your project configuration")
        return False
    
    with open(config_path) as f:
        config = json.load(f)
    
    if project_id not in config['projects']:
        print(f"❌ Project '{project_id}' not found in config")
        print(f"\n📂 Available projects:")
        for pid in config['projects'].keys():
            print(f"   - {pid}")
        return False
    
    project = config['projects'][project_id]
    
    print(f"🔄 Syncing project: {project_id}")
    print(f"📍 Repository: {project['repository']}")
    print(f"🌿 Branch: {project.get('branch', 'main')}")
    print()
    
    # Inicializar servicios
    db = DatabaseClient()
    indexer = ProjectIndexer(db)
    
    try:
        # Asegurar que el proyecto existe en la DB
        await db.upsert_project(project_id, {
            'name': project.get('name', project_id),
            'repository_url': project['repository'],
            'branch': project.get('branch', 'main'),
            'type': project.get('type', 'application')
        })
        
        # Sincronizar
        await indexer.index_remote_repository(
            project_id,
            project['repository'],
            project.get('branch', 'main')
        )
        
        # Mostrar estadísticas
        count = await db.get_component_count(project_id)
        print(f"\n📊 Sync complete!")
        print(f"   Total components indexed: {count}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error during sync: {e}")
        return False
    finally:
        db.close()


async def sync_all_projects():
    """Sincroniza todos los proyectos configurados."""
    
    config_path = Path(".mcp-config.json")
    if not config_path.exists():
        print("❌ .mcp-config.json not found")
        return False
    
    with open(config_path) as f:
        config = json.load(f)
    
    projects = config.get('projects', {})
    if not projects:
        print("❌ No projects configured in .mcp-config.json")
        return False
    
    print(f"🔄 Syncing {len(projects)} project(s)...\n")
    
    success_count = 0
    for project_id in projects.keys():
        result = await sync_project(project_id)
        if result:
            success_count += 1
        print()  # Separador
    
    print(f"✅ Sync complete: {success_count}/{len(projects)} projects synced successfully")
    return success_count == len(projects)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Sync React projects from GitHub to database'
    )
    parser.add_argument(
        '--project',
        help='Project ID to sync (from .mcp-config.json)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Sync all configured projects'
    )
    
    args = parser.parse_args()
    
    if args.all:
        asyncio.run(sync_all_projects())
    elif args.project:
        asyncio.run(sync_project(args.project))
    else:
        parser.print_help()
        print("\nExamples:")
        print("  python scripts/sync_projects.py --project test-project")
        print("  python scripts/sync_projects.py --all")


if __name__ == "__main__":
    main()

