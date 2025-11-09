#!/usr/bin/env python
"""
Script para probar las herramientas MCP de feature flags.
"""

import asyncio
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.registry.database_client import DatabaseClient
from dotenv import load_dotenv

load_dotenv()


async def test_feature_flag_tools():
    """Prueba las herramientas de feature flags."""
    
    db = DatabaseClient()
    
    try:
        # Obtener proyectos disponibles
        projects = await db.list_projects()
        print("📂 Proyectos disponibles:")
        for project in projects:
            print(f"   - {project['id']}: {project.get('name', 'N/A')}")
        print()
        
        if not projects:
            print("❌ No hay proyectos sincronizados")
            return
        
        # Usar el primer proyecto disponible
        project_id = projects[0]['id']
        print(f"🔍 Probando con proyecto: {project_id}\n")
        
        # Test 1: Listar feature flags
        print("=" * 60)
        print("TEST 1: list_feature_flags")
        print("=" * 60)
        flags = await db.get_feature_flags_by_project(project_id)
        if flags:
            print(f"✅ Encontrados {len(flags)} feature flags:\n")
            for flag in flags[:5]:  # Mostrar solo los primeros 5
                print(f"  - {flag['name']}")
                if flag.get('description'):
                    print(f"    Descripción: {flag['description']}")
                if flag.get('default_value') is not None:
                    print(f"    Valor por defecto: {flag['default_value']}")
                print()
            if len(flags) > 5:
                print(f"  ... y {len(flags) - 5} más\n")
        else:
            print("⚠️  No se encontraron feature flags\n")
        
        # Test 2: Obtener detalles de un flag específico
        if flags:
            test_flag = flags[0]['name']
            print("=" * 60)
            print(f"TEST 2: get_feature_flag_details - '{test_flag}'")
            print("=" * 60)
            flag_details = await db.get_feature_flag_by_name(test_flag, project_id)
            if flag_details:
                print(f"✅ Flag encontrado:")
                print(f"  Nombre: {flag_details['name']}")
                print(f"  Tipo: {flag_details.get('value_type', 'N/A')}")
                print(f"  Valor por defecto: {flag_details.get('default_value', 'N/A')}")
                print(f"  Archivo: {flag_details.get('file_path', 'N/A')}")
                if flag_details.get('description'):
                    print(f"  Descripción: {flag_details['description']}")
                if flag_details.get('possible_values'):
                    print(f"  Valores posibles: {', '.join(flag_details['possible_values'])}")
                print()
            else:
                print(f"❌ Flag '{test_flag}' no encontrado\n")
        
        # Test 3: Buscar componentes que usan un flag
        if flags:
            test_flag = flags[0]['name']
            print("=" * 60)
            print(f"TEST 3: search_by_feature_flag - '{test_flag}'")
            print("=" * 60)
            components = await db.get_components_using_flag(test_flag, project_id)
            if components:
                print(f"✅ Encontrados {len(components)} componente(s) que usan '{test_flag}':\n")
                for comp in components[:5]:  # Mostrar solo los primeros 5
                    print(f"  - {comp['name']} ({comp.get('file_path', 'N/A')})")
                if len(components) > 5:
                    print(f"  ... y {len(components) - 5} más\n")
            else:
                print(f"⚠️  No se encontraron componentes que usen '{test_flag}'\n")
        
        # Test 4: Obtener flags no usados
        print("=" * 60)
        print("TEST 4: get_unused_feature_flags")
        print("=" * 60)
        unused_flags = await db.get_unused_feature_flags(project_id)
        if unused_flags:
            print(f"⚠️  Encontrados {len(unused_flags)} flag(s) no usado(s):\n")
            for flag in unused_flags[:10]:  # Mostrar solo los primeros 10
                print(f"  - {flag['name']}")
                if flag.get('description'):
                    print(f"    {flag['description']}")
            if len(unused_flags) > 10:
                print(f"  ... y {len(unused_flags) - 10} más\n")
        else:
            print("✅ Todos los feature flags están siendo usados!\n")
        
        # Test 5: Buscar flags por nombre (search)
        if flags:
            search_term = flags[0]['name'][:5]  # Primeros 5 caracteres
            print("=" * 60)
            print(f"TEST 5: search_feature_flags - '{search_term}'")
            print("=" * 60)
            search_results = await db.search_feature_flags(search_term, project_id, limit=5)
            if search_results:
                print(f"✅ Encontrados {len(search_results)} flag(s) que coinciden con '{search_term}':\n")
                for flag in search_results:
                    print(f"  - {flag['name']}")
            else:
                print(f"⚠️  No se encontraron flags que coincidan con '{search_term}'\n")
        
        print("=" * 60)
        print("✅ Todas las pruebas completadas")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_feature_flag_tools())

