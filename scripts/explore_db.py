#!/usr/bin/env python
"""
Script para explorar la base de datos de componentes.
Muestra proyectos, componentes, props, hooks, etc.
"""

import os
import sys
from pathlib import Path
import json

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from dotenv import load_dotenv
import psycopg2

load_dotenv()


def explore_database():
    """Explora la base de datos de componentes."""
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL not found")
        return
    
    try:
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        print("\n" + "="*60)
        print("📊 EXPLORADOR DE BASE DE DATOS - Frontend GPS")
        print("="*60 + "\n")
        
        # 1. Mostrar proyectos
        print("📂 PROYECTOS CONFIGURADOS:")
        print("-" * 60)
        cursor.execute("SELECT id, name, repository_url, branch, type, is_active FROM projects ORDER BY name")
        projects = cursor.fetchall()
        
        if projects:
            for project in projects:
                print(f"\n  ID: {project[0]}")
                print(f"  Nombre: {project[1]}")
                print(f"  Repositorio: {project[2]}")
                print(f"  Rama: {project[3]}")
                print(f"  Tipo: {project[4]}")
                print(f"  Activo: {'✅' if project[5] else '❌'}")
        else:
            print("  (Sin proyectos configurados)")
        
        # 2. Estadísticas de componentes
        print("\n\n📦 ESTADÍSTICAS DE COMPONENTES:")
        print("-" * 60)
        
        cursor.execute("SELECT COUNT(*) FROM components")
        total_components = cursor.fetchone()[0]
        print(f"  Total componentes indexados: {total_components}")
        
        if total_components > 0:
            cursor.execute("""
                SELECT project_id, COUNT(*) as count 
                FROM components 
                GROUP BY project_id 
                ORDER BY count DESC
            """)
            by_project = cursor.fetchall()
            print("\n  Por proyecto:")
            for project_id, count in by_project:
                print(f"    - {project_id}: {count} componentes")
            
            # Tipos de componentes
            cursor.execute("""
                SELECT component_type, COUNT(*) as count 
                FROM components 
                GROUP BY component_type 
                ORDER BY count DESC
            """)
            by_type = cursor.fetchall()
            print("\n  Por tipo:")
            for comp_type, count in by_type:
                print(f"    - {comp_type}: {count}")
        
        # 3. Mostrar componentes recientes
        print("\n\n🆕 COMPONENTES RECIENTES:")
        print("-" * 60)
        cursor.execute("""
            SELECT name, project_id, file_path, component_type, array_length(props, 1) as prop_count
            FROM components
            ORDER BY created_at DESC
            LIMIT 10
        """)
        components = cursor.fetchall()
        
        if components:
            for comp in components:
                props_count = comp[4] if comp[4] else 0
                print(f"\n  • {comp[0]}")
                print(f"    Proyecto: {comp[1]}")
                print(f"    Ruta: {comp[2]}")
                print(f"    Tipo: {comp[3]}")
                print(f"    Props: {props_count}")
        else:
            print("  (Sin componentes indexados)")
        
        # 4. Búsqueda de componentes
        print("\n\n🔍 BÚSQUEDA DE COMPONENTES:")
        print("-" * 60)
        query = input("  Ingresa parte del nombre del componente (o presiona Enter para omitir): ").strip()
        
        if query:
            cursor.execute("""
                SELECT name, project_id, file_path, component_type
                FROM components
                WHERE name ILIKE %s
                ORDER BY name
                LIMIT 20
            """, (f"%{query}%",))
            
            results = cursor.fetchall()
            if results:
                print(f"\n  Encontrados {len(results)} componentes:")
                for comp in results:
                    print(f"\n    • {comp[0]}")
                    print(f"      Proyecto: {comp[1]}")
                    print(f"      Ruta: {comp[2]}")
                    print(f"      Tipo: {comp[3]}")
            else:
                print("  No se encontraron componentes")
        
        # 5. Ver detalles de un componente
        print("\n\n🔎 DETALLES DE COMPONENTE:")
        print("-" * 60)
        comp_name = input("  Ingresa nombre exacto de componente para ver detalles (o presiona Enter para omitir): ").strip()
        
        if comp_name:
            cursor.execute("""
                SELECT name, project_id, file_path, props, hooks, imports, component_type, description
                FROM components
                WHERE name = %s
                LIMIT 1
            """, (comp_name,))
            
            result = cursor.fetchone()
            if result:
                print(f"\n  📋 {result[0]}")
                print(f"     Proyecto: {result[1]}")
                print(f"     Ruta: {result[2]}")
                print(f"     Tipo: {result[6]}")
                
                if result[3]:
                    props = json.loads(result[3])
                    print(f"     Props ({len(props)}): {', '.join(props[:5])}")
                
                if result[4]:
                    hooks = json.loads(result[4])
                    print(f"     Hooks ({len(hooks)}): {', '.join(hooks)}")
                
                if result[5]:
                    imports = json.loads(result[5])
                    print(f"     Imports: {', '.join(imports[:3])}")
                
                if result[7]:
                    print(f"     Descripción: {result[7]}")
            else:
                print(f"  ❌ Componente '{comp_name}' no encontrado")
        
        print("\n" + "="*60 + "\n")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    explore_database()
