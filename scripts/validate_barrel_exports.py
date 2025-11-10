"""
Script para validar la implementación de barrel exports.
Ejecutar después de re-indexar un proyecto para medir la mejora.
"""

import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Agregar src al path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

from src.models import (
    Base, Project, Component, ComponentDependency, BarrelExport
)

load_dotenv()


class BarrelExportValidator:
    """Validador de barrel exports y mejoras en resolución de dependencias."""
    
    def __init__(self):
        """Inicializa conexión a la base de datos."""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def print_header(self, title: str):
        """Imprime un encabezado formateado."""
        print(f"\n{'=' * 70}")
        print(f"  {title}")
        print(f"{'=' * 70}")
    
    def print_section(self, title: str):
        """Imprime un título de sección."""
        print(f"\n{'-' * 70}")
        print(f"  {title}")
        print(f"{'-' * 70}")
    
    def validate_barrel_exports(self, project_id: str = None):
        """
        Valida los barrel exports indexados y su impacto en resolución.
        
        Args:
            project_id: ID del proyecto (opcional, si no se provee analiza todos)
        """
        session = self.SessionLocal()
        
        try:
            self.print_header("VALIDACIÓN DE BARREL EXPORTS")
            
            # Proyectos a analizar
            if project_id:
                projects = session.query(Project).filter(Project.id == project_id).all()
            else:
                projects = session.query(Project).all()
            
            if not projects:
                print("⚠️  No se encontraron proyectos")
                return
            
            print(f"\n📊 Analizando {len(projects)} proyecto(s)...")
            
            total_barrel_exports = 0
            total_resolved = 0
            total_dependencies = 0
            
            for project in projects:
                self.print_section(f"Proyecto: {project.name} ({project.id})")
                
                # Stats de barrel exports
                barrel_count = session.query(BarrelExport).filter(
                    BarrelExport.project_id == project.id
                ).count()
                
                barrel_resolved = session.query(BarrelExport).filter(
                    BarrelExport.project_id == project.id,
                    BarrelExport.exported_component_id.isnot(None)
                ).count()
                
                barrel_unresolved = barrel_count - barrel_resolved
                
                print(f"\n📦 Barrel Exports:")
                print(f"   Total indexados: {barrel_count}")
                print(f"   ✅ Resueltos (con componente): {barrel_resolved}")
                print(f"   ❌ No resueltos: {barrel_unresolved}")
                
                if barrel_count > 0:
                    resolution_rate = (barrel_resolved / barrel_count) * 100
                    print(f"   📈 Tasa de resolución: {resolution_rate:.1f}%")
                
                # Stats de componentes y dependencias
                component_count = session.query(Component).filter(
                    Component.project_id == project.id
                ).count()
                
                dependency_count = session.query(ComponentDependency).join(
                    Component, ComponentDependency.component_id == Component.id
                ).filter(
                    Component.project_id == project.id
                ).count()
                
                print(f"\n⚛️  Componentes:")
                print(f"   Total: {component_count}")
                
                print(f"\n🔗 Dependencias:")
                print(f"   Total resueltas: {dependency_count}")
                
                # Buscar casos específicos: Purchase → Checkout
                self._check_specific_cases(session, project.id)
                
                # Mostrar algunos ejemplos de barrel exports
                self._show_barrel_export_examples(session, project.id)
                
                total_barrel_exports += barrel_count
                total_resolved += barrel_resolved
                total_dependencies += dependency_count
            
            # Resumen global
            self.print_section("RESUMEN GLOBAL")
            print(f"\n📦 Total Barrel Exports: {total_barrel_exports}")
            print(f"✅ Total Resueltos: {total_resolved}")
            
            if total_barrel_exports > 0:
                global_rate = (total_resolved / total_barrel_exports) * 100
                print(f"📈 Tasa de resolución global: {global_rate:.1f}%")
            
            print(f"\n🔗 Total Dependencias: {total_dependencies}")
            
            self._print_recommendations(total_barrel_exports, total_resolved)
            
        finally:
            session.close()
    
    def _check_specific_cases(self, session, project_id: str):
        """Verifica casos específicos importantes."""
        print(f"\n🔍 Casos específicos:")
        
        # Caso Purchase → Checkout
        purchase = session.query(Component).filter(
            Component.project_id == project_id,
            Component.name == 'Purchase'
        ).first()
        
        checkout = session.query(Component).filter(
            Component.project_id == project_id,
            Component.name == 'Checkout'
        ).first()
        
        if purchase and checkout:
            dependency = session.query(ComponentDependency).filter(
                ComponentDependency.component_id == purchase.id,
                ComponentDependency.depends_on_component_id == checkout.id
            ).first()
            
            if dependency:
                print(f"   ✅ Purchase → Checkout: RESUELTO")
            else:
                print(f"   ❌ Purchase → Checkout: NO RESUELTO")
                
                # Verificar si existe barrel export
                barrel = session.query(BarrelExport).filter(
                    BarrelExport.project_id == project_id,
                    BarrelExport.directory_path.like('%Checkout%')
                ).first()
                
                if barrel:
                    print(f"      📦 Barrel export encontrado: {barrel.directory_path}")
                    if barrel.exported_component_id:
                        print(f"      🔗 Apunta a componente ID: {barrel.exported_component_id}")
                    else:
                        print(f"      ⚠️  Barrel export no resuelto a componente")
        else:
            if not purchase:
                print(f"   ⚠️  Componente 'Purchase' no encontrado")
            if not checkout:
                print(f"   ⚠️  Componente 'Checkout' no encontrado")
    
    def _show_barrel_export_examples(self, session, project_id: str):
        """Muestra ejemplos de barrel exports."""
        barrels = session.query(BarrelExport).filter(
            BarrelExport.project_id == project_id
        ).limit(5).all()
        
        if barrels:
            print(f"\n📝 Ejemplos de barrel exports (primeros 5):")
            for barrel in barrels:
                status = "✅" if barrel.exported_component_id else "❌"
                print(f"   {status} {barrel.directory_path}")
                print(f"      → Exporta: {barrel.exported_name}")
                print(f"      → Container: {'Sí' if barrel.is_container else 'No'}")
                if barrel.exported_component_id:
                    component = session.query(Component).filter(
                        Component.id == barrel.exported_component_id
                    ).first()
                    if component:
                        print(f"      → Componente: {component.name}")
    
    def _print_recommendations(self, total_barrel_exports: int, total_resolved: int):
        """Imprime recomendaciones basadas en los resultados."""
        self.print_section("RECOMENDACIONES")
        
        if total_barrel_exports == 0:
            print("\n⚠️  No se encontraron barrel exports.")
            print("   - Verifica que el proyecto usa el patrón index.js")
            print("   - Ejecuta una sincronización del proyecto")
        elif total_resolved == 0:
            print("\n❌ Ningún barrel export fue resuelto.")
            print("   - Verifica que los componentes estén indexados")
            print("   - Revisa el mapeo en resolve_barrel_component()")
        elif total_resolved < total_barrel_exports:
            resolution_rate = (total_resolved / total_barrel_exports) * 100
            print(f"\n📊 Tasa de resolución: {resolution_rate:.1f}%")
            
            if resolution_rate < 50:
                print("   ⚠️  Tasa baja. Posibles causas:")
                print("      - Componentes no indexados")
                print("      - Containers no vinculados correctamente")
            elif resolution_rate < 80:
                print("   📈 Tasa aceptable. Áreas de mejora:")
                print("      - Revisar casos no resueltos")
                print("      - Verificar nombres de componentes")
            else:
                print("   ✅ Tasa buena. Sistema funcionando correctamente.")
        else:
            print("\n🎉 ¡Todos los barrel exports resueltos correctamente!")
    
    def compare_with_baseline(self, project_id: str, baseline_rate: float = 15.5):
        """
        Compara la tasa de resolución actual con la baseline.
        
        Args:
            project_id: ID del proyecto
            baseline_rate: Tasa de resolución baseline (default: 15.5%)
        """
        session = self.SessionLocal()
        
        try:
            self.print_header(f"COMPARACIÓN CON BASELINE ({baseline_rate}%)")
            
            # Calcular tasa actual
            total_imports = session.query(ComponentDependency).join(
                Component, ComponentDependency.component_id == Component.id
            ).filter(
                Component.project_id == project_id
            ).count()
            
            total_components = session.query(Component).filter(
                Component.project_id == project_id
            ).count()
            
            if total_components == 0:
                print("⚠️  No hay componentes indexados")
                return
            
            # Estimar imports totales (cada componente tiene ~3 imports en promedio)
            estimated_total_imports = total_components * 3
            
            current_rate = (total_imports / estimated_total_imports) * 100 if estimated_total_imports > 0 else 0
            
            print(f"\n📊 Estadísticas:")
            print(f"   Componentes: {total_components}")
            print(f"   Dependencias resueltas: {total_imports}")
            print(f"   Imports estimados: {estimated_total_imports}")
            print(f"\n📈 Tasas de resolución:")
            print(f"   Baseline (antes): {baseline_rate:.1f}%")
            print(f"   Actual (ahora): {current_rate:.1f}%")
            
            improvement = current_rate - baseline_rate
            
            if improvement > 0:
                print(f"\n✅ Mejora: +{improvement:.1f} puntos porcentuales")
                
                if improvement >= 50:
                    print(f"   🎉 ¡Excelente! Mejora significativa.")
                elif improvement >= 20:
                    print(f"   👍 Buena mejora.")
                else:
                    print(f"   📈 Mejora moderada.")
            elif improvement < 0:
                print(f"\n❌ Disminución: {improvement:.1f} puntos porcentuales")
                print(f"   ⚠️  Investigar causas de la regresión")
            else:
                print(f"\n➖ Sin cambio significativo")
            
        finally:
            session.close()


def main():
    """Función principal."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Valida la implementación de barrel exports"
    )
    parser.add_argument(
        '--project',
        type=str,
        help='ID del proyecto a validar (opcional)'
    )
    parser.add_argument(
        '--compare',
        action='store_true',
        help='Comparar con baseline'
    )
    parser.add_argument(
        '--baseline',
        type=float,
        default=15.5,
        help='Tasa baseline para comparación (default: 15.5)'
    )
    
    args = parser.parse_args()
    
    validator = BarrelExportValidator()
    
    print("\n" + "="*70)
    print("  🔍 VALIDADOR DE BARREL EXPORTS")
    print("="*70)
    print(f"\nFecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Validación básica
    validator.validate_barrel_exports(args.project)
    
    # Comparación con baseline si se solicita
    if args.compare:
        if args.project:
            validator.compare_with_baseline(args.project, args.baseline)
        else:
            print("\n⚠️  Para comparar con baseline, especifica --project")
    
    print("\n" + "="*70)
    print("  ✅ Validación completada")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()

