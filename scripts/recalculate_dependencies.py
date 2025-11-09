#!/usr/bin/env python3
"""
Script para recalcular dependencias de componentes existentes.

Este script recorre todos los componentes de un proyecto y recalcula
sus dependencias basándose en los imports guardados en component_imports.
"""

import asyncio
import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.registry.database_client import DatabaseClient
from src.utils.import_resolver import resolve_imports_to_components
from src.models import Component


async def recalculate_dependencies(project_id: str):
    """
    Recalcula las dependencias de todos los componentes de un proyecto.
    
    Args:
        project_id: ID del proyecto
    """
    db = DatabaseClient()
    
    def _recalculate():
        with db.SessionLocal() as session:
            # Obtener todos los componentes del proyecto
            components = session.query(Component).filter(
                Component.project_id == project_id
            ).all()
            
            print(f"📦 Encontrados {len(components)} componentes en proyecto '{project_id}'")
            
            recalculated = 0
            errors = 0
            
            for comp in components:
                try:
                    # Obtener imports estructurados
                    component_imports = comp.component_imports
                    
                    if not component_imports:
                        continue
                    
                    # Resolver imports a dependencias
                    dependencies = resolve_imports_to_components(
                        component_imports=component_imports,
                        project_id=project_id,
                        current_file_path=comp.file_path,
                        component_name=comp.name,
                        db_session=session
                    )
                    
                    if dependencies:
                        # Guardar dependencias usando el repositorio
                        # Primero eliminar dependencias existentes para evitar duplicados
                        from src.models import ComponentDependency
                        session.query(ComponentDependency).filter(
                            ComponentDependency.component_id == comp.id
                        ).delete()
                        
                        # Guardar nuevas dependencias
                        for dep in dependencies:
                            dep_obj = ComponentDependency(
                                component_id=comp.id,
                                depends_on_component_id=dep.get('depends_on_component_id'),
                                depends_on_name=dep['depends_on_name'],
                                from_path=dep['from_path'],
                                import_type=dep['import_type'],
                                is_external=dep.get('is_external', False),
                                project_id=project_id
                            )
                            session.add(dep_obj)
                        
                        recalculated += 1
                        if recalculated % 10 == 0:
                            print(f"  ✅ Recalculadas {recalculated} dependencias...")
                            session.commit()
                
                except Exception as e:
                    errors += 1
                    print(f"  ❌ Error procesando componente {comp.name} ({comp.file_path}): {e}")
                    session.rollback()
                    continue
            
            # Commit final
            session.commit()
            print(f"\n✅ Proceso completado:")
            print(f"   - Componentes procesados: {recalculated}")
            print(f"   - Errores: {errors}")
    
    await asyncio.to_thread(_recalculate)


async def main():
    """Función principal."""
    if len(sys.argv) < 2:
        print("Uso: python scripts/recalculate_dependencies.py <project_id>")
        print("\nEjemplo:")
        print("  python scripts/recalculate_dependencies.py craftitapp")
        sys.exit(1)
    
    project_id = sys.argv[1]
    
    print(f"🔄 Recalculando dependencias para proyecto '{project_id}'...")
    print("=" * 60)
    
    await recalculate_dependencies(project_id)
    
    print("=" * 60)
    print("✅ ¡Listo!")


if __name__ == "__main__":
    asyncio.run(main())

