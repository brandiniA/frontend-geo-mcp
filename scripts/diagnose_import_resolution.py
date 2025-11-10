#!/usr/bin/env python3
"""
Script de diagnóstico para analizar el estado actual de la resolución de imports.

Analiza:
- Componentes indexados
- Dependencias registradas
- Imports no resueltos
- Casos específicos (Purchase/Checkout)
- Containers
- Estadísticas generales

Uso:
    python scripts/diagnose_import_resolution.py
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import create_engine, func, and_, or_
from sqlalchemy.orm import sessionmaker

from src.models import (
    Base, 
    Project, 
    Component, 
    ComponentDependency
)

# Cargar variables de entorno
load_dotenv()


class ImportResolutionDiagnostic:
    """Diagnóstico completo de resolución de imports."""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL not found in environment")
        
        self.engine = create_engine(self.database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        print("=" * 80)
        print("🔍 IMPORT RESOLUTION DIAGNOSTIC REPORT")
        print("=" * 80)
        print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🗄️  Database: {self.database_url.split('@')[1] if '@' in self.database_url else 'local'}")
        print("=" * 80)
        print()
    
    def run_full_diagnostic(self):
        """Ejecuta diagnóstico completo."""
        with self.SessionLocal() as session:
            self._section_1_projects(session)
            self._section_2_components(session)
            self._section_3_dependencies(session)
            self._section_4_unresolved_imports(session)
            self._section_5_containers(session)
            self._section_6_specific_case_checkout(session)
            self._section_7_directory_analysis(session)
            self._section_8_recommendations(session)
    
    def _section_1_projects(self, session):
        """Análisis de proyectos."""
        print("\n" + "=" * 80)
        print("📦 SECTION 1: PROJECTS")
        print("=" * 80)
        
        projects = session.query(Project).all()
        
        print(f"\n📊 Total Projects: {len(projects)}")
        print()
        
        for project in projects:
            print(f"  • {project.name} ({project.id})")
            print(f"    ├─ URL: {project.repository_url}")
            print(f"    ├─ Branch: {project.branch}")
            print(f"    ├─ Type: {project.type}")
            print(f"    ├─ Active: {project.is_active}")
            print(f"    └─ Last Sync: {project.last_sync or 'Never'}")
            print()
    
    def _section_2_components(self, session):
        """Análisis de componentes."""
        print("\n" + "=" * 80)
        print("🧩 SECTION 2: COMPONENTS")
        print("=" * 80)
        
        total_components = session.query(Component).count()
        
        # Por proyecto
        components_by_project = session.query(
            Component.project_id,
            func.count(Component.id).label('count')
        ).group_by(Component.project_id).all()
        
        # Por tipo
        components_by_type = session.query(
            Component.component_type,
            func.count(Component.id).label('count')
        ).group_by(Component.component_type).all()
        
        # Con container
        with_container = session.query(Component).filter(
            Component.container_file_path.isnot(None)
        ).count()
        
        # Con imports estructurados
        with_structured_imports = session.query(Component).filter(
            Component.component_imports.isnot(None)
        ).count()
        
        print(f"\n📊 Component Statistics:")
        print(f"  • Total Components: {total_components}")
        print(f"  • With Container: {with_container} ({self._percent(with_container, total_components)})")
        print(f"  • With Structured Imports: {with_structured_imports} ({self._percent(with_structured_imports, total_components)})")
        print()
        
        print("📊 Components by Project:")
        for project_id, count in components_by_project:
            print(f"  • {project_id}: {count} components")
        print()
        
        print("📊 Components by Type:")
        for comp_type, count in sorted(components_by_type, key=lambda x: x[1], reverse=True):
            type_name = comp_type or 'unknown'
            print(f"  • {type_name}: {count}")
        print()
    
    def _section_3_dependencies(self, session):
        """Análisis de dependencias."""
        print("\n" + "=" * 80)
        print("🔗 SECTION 3: DEPENDENCIES")
        print("=" * 80)
        
        total_deps = session.query(ComponentDependency).count()
        
        # Resueltas vs no resueltas
        resolved = session.query(ComponentDependency).filter(
            ComponentDependency.depends_on_component_id.isnot(None)
        ).count()
        
        unresolved = session.query(ComponentDependency).filter(
            ComponentDependency.depends_on_component_id.is_(None),
            ComponentDependency.is_external == False
        ).count()
        
        external = session.query(ComponentDependency).filter(
            ComponentDependency.is_external == True
        ).count()
        
        # Por tipo de import
        by_import_type = session.query(
            ComponentDependency.import_type,
            func.count(ComponentDependency.id).label('count')
        ).group_by(ComponentDependency.import_type).all()
        
        print(f"\n📊 Dependency Statistics:")
        print(f"  • Total Dependencies: {total_deps}")
        print(f"  • Resolved (linked to component): {resolved} ({self._percent(resolved, total_deps)})")
        print(f"  • Unresolved (internal, no link): {unresolved} ({self._percent(unresolved, total_deps)})")
        print(f"  • External (libraries): {external} ({self._percent(external, total_deps)})")
        print()
        
        print("📊 Dependencies by Import Type:")
        for import_type, count in sorted(by_import_type, key=lambda x: x[1], reverse=True):
            print(f"  • {import_type}: {count}")
        print()
        
        # Componentes con más dependencias
        print("🔝 Top 10 Components with Most Dependencies:")
        top_with_deps = session.query(
            Component.name,
            Component.file_path,
            func.count(ComponentDependency.id).label('dep_count')
        ).join(
            ComponentDependency,
            ComponentDependency.component_id == Component.id
        ).group_by(
            Component.id
        ).order_by(
            func.count(ComponentDependency.id).desc()
        ).limit(10).all()
        
        for i, (name, path, count) in enumerate(top_with_deps, 1):
            print(f"  {i:2d}. {name} ({count} deps)")
            print(f"      └─ {path}")
        print()
        
        # Componentes más dependidos
        print("🔝 Top 10 Most Depended-On Components:")
        top_depended = session.query(
            Component.name,
            Component.file_path,
            func.count(ComponentDependency.id).label('dependent_count')
        ).join(
            ComponentDependency,
            ComponentDependency.depends_on_component_id == Component.id
        ).group_by(
            Component.id
        ).order_by(
            func.count(ComponentDependency.id).desc()
        ).limit(10).all()
        
        for i, (name, path, count) in enumerate(top_depended, 1):
            print(f"  {i:2d}. {name} ({count} dependents)")
            print(f"      └─ {path}")
        print()
    
    def _section_4_unresolved_imports(self, session):
        """Análisis de imports no resueltos."""
        print("\n" + "=" * 80)
        print("❌ SECTION 4: UNRESOLVED IMPORTS (Internal)")
        print("=" * 80)
        
        # Imports internos no resueltos
        unresolved = session.query(
            ComponentDependency,
            Component
        ).join(
            Component,
            ComponentDependency.component_id == Component.id
        ).filter(
            ComponentDependency.depends_on_component_id.is_(None),
            ComponentDependency.is_external == False
        ).limit(50).all()
        
        if not unresolved:
            print("\n✅ All internal imports are resolved!")
            return
        
        print(f"\n⚠️  Found {len(unresolved)} unresolved internal imports (showing first 50)")
        print()
        
        # Agrupar por patrón de from_path
        patterns = defaultdict(list)
        
        for dep, comp in unresolved:
            # Detectar si es import de directorio
            from_path = dep.from_path
            if not from_path.endswith(('.js', '.jsx', '.ts', '.tsx')):
                pattern = "directory_import"
            elif '../' in from_path:
                pattern = "relative_parent"
            elif './' in from_path:
                pattern = "relative_same"
            elif from_path.startswith('@'):
                pattern = "alias_import"
            else:
                pattern = "absolute_import"
            
            patterns[pattern].append((dep, comp))
        
        print("📊 Unresolved by Pattern:")
        for pattern, items in sorted(patterns.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"\n  📂 {pattern.upper()}: {len(items)} cases")
            for dep, comp in items[:5]:  # Mostrar solo 5 ejemplos por patrón
                print(f"     • {comp.name}")
                print(f"       imports: {dep.depends_on_name}")
                print(f"       from: {dep.from_path}")
                print(f"       type: {dep.import_type}")
            if len(items) > 5:
                print(f"     ... and {len(items) - 5} more")
        print()
    
    def _section_5_containers(self, session):
        """Análisis de containers."""
        print("\n" + "=" * 80)
        print("📦 SECTION 5: CONTAINERS")
        print("=" * 80)
        
        # Componentes con container
        with_container = session.query(Component).filter(
            Component.container_file_path.isnot(None)
        ).all()
        
        print(f"\n📊 Components with Containers: {len(with_container)}")
        print()
        
        if with_container:
            print("🔝 Examples (showing first 10):")
            for i, comp in enumerate(with_container[:10], 1):
                print(f"  {i:2d}. {comp.name}")
                print(f"      ├─ Component: {comp.file_path}")
                print(f"      └─ Container: {comp.container_file_path}")
            
            if len(with_container) > 10:
                print(f"      ... and {len(with_container) - 10} more")
        print()
        
        # Detectar patrones de container
        container_patterns = defaultdict(int)
        for comp in with_container:
            container_path = comp.container_file_path or ""
            if 'Container' in container_path:
                container_patterns['*Container.js'] += 1
            elif 'index.js' in container_path:
                container_patterns['index.js'] += 1
            else:
                container_patterns['other'] += 1
        
        if container_patterns:
            print("📊 Container File Patterns:")
            for pattern, count in sorted(container_patterns.items(), key=lambda x: x[1], reverse=True):
                print(f"  • {pattern}: {count}")
        print()
    
    def _section_6_specific_case_checkout(self, session):
        """Análisis específico del caso Purchase/Checkout."""
        print("\n" + "=" * 80)
        print("🔍 SECTION 6: SPECIFIC CASE - Purchase → Checkout")
        print("=" * 80)
        
        # Buscar Purchase
        purchase = session.query(Component).filter(
            Component.name == 'Purchase'
        ).first()
        
        # Buscar Checkout
        checkout = session.query(Component).filter(
            Component.name == 'Checkout',
            Component.file_path.like('%/Checkout/Checkout.js')
        ).first()
        
        print(f"\n📋 Component: Purchase")
        if purchase:
            print(f"  ✅ Found: {purchase.file_path}")
            print(f"  • ID: {purchase.id}")
            print(f"  • Project: {purchase.project_id}")
            
            # Dependencias de Purchase
            purchase_deps = session.query(ComponentDependency).filter(
                ComponentDependency.component_id == purchase.id
            ).all()
            
            print(f"  • Total Dependencies: {len(purchase_deps)}")
            print(f"  • Resolved: {sum(1 for d in purchase_deps if d.depends_on_component_id)}")
            print(f"  • Unresolved: {sum(1 for d in purchase_deps if not d.depends_on_component_id and not d.is_external)}")
            
            # ¿Depende de Checkout?
            checkout_dep = session.query(ComponentDependency).filter(
                ComponentDependency.component_id == purchase.id,
                or_(
                    ComponentDependency.depends_on_name == 'Checkout',
                    ComponentDependency.from_path.like('%Checkout%')
                )
            ).first()
            
            if checkout_dep:
                print(f"\n  📦 Import of Checkout:")
                print(f"    • Found: YES")
                print(f"    • From: {checkout_dep.from_path}")
                print(f"    • Type: {checkout_dep.import_type}")
                print(f"    • Resolved: {'YES' if checkout_dep.depends_on_component_id else 'NO ❌'}")
                if checkout_dep.depends_on_component_id:
                    linked_comp = session.query(Component).get(checkout_dep.depends_on_component_id)
                    print(f"    • Linked to: {linked_comp.name if linked_comp else 'Unknown'}")
            else:
                print(f"\n  ❌ Import of Checkout: NOT FOUND in dependencies")
        else:
            print(f"  ❌ Not found in database")
        print()
        
        print(f"📋 Component: Checkout")
        if checkout:
            print(f"  ✅ Found: {checkout.file_path}")
            print(f"  • ID: {checkout.id}")
            print(f"  • Project: {checkout.project_id}")
            print(f"  • Container: {checkout.container_file_path or 'None'}")
            
            # Dependientes de Checkout
            checkout_dependents = session.query(ComponentDependency).filter(
                ComponentDependency.depends_on_component_id == checkout.id
            ).all()
            
            print(f"  • Dependents (components using Checkout): {len(checkout_dependents)}")
            
            if checkout_dependents:
                print(f"\n  📦 Used by:")
                for dep in checkout_dependents[:5]:
                    comp = session.query(Component).get(dep.component_id)
                    print(f"    • {comp.name if comp else 'Unknown'}")
                if len(checkout_dependents) > 5:
                    print(f"    ... and {len(checkout_dependents) - 5} more")
            else:
                print(f"\n  ❌ NO DEPENDENTS FOUND")
                print(f"     This means no component is registered as using Checkout")
                print(f"     This is likely the bug we're investigating!")
        else:
            print(f"  ❌ Not found in database")
        print()
        
        # Buscar otros componentes en el directorio Checkout
        print(f"📂 Other components in Checkout directory:")
        checkout_dir_components = session.query(Component).filter(
            Component.file_path.like('%/Checkout/%')
        ).all()
        
        for comp in checkout_dir_components:
            print(f"  • {comp.name}")
            print(f"    └─ {comp.file_path}")
        print()
    
    def _section_7_directory_analysis(self, session):
        """Análisis de imports de directorio."""
        print("\n" + "=" * 80)
        print("📁 SECTION 7: DIRECTORY IMPORTS ANALYSIS")
        print("=" * 80)
        
        # Buscar dependencias que no terminan en extensión de archivo
        potential_directory_imports = session.query(
            ComponentDependency,
            Component
        ).join(
            Component,
            ComponentDependency.component_id == Component.id
        ).filter(
            and_(
                ~ComponentDependency.from_path.like('%.js'),
                ~ComponentDependency.from_path.like('%.jsx'),
                ~ComponentDependency.from_path.like('%.ts'),
                ~ComponentDependency.from_path.like('%.tsx'),
                ComponentDependency.is_external == False
            )
        ).all()
        
        print(f"\n📊 Potential Directory Imports: {len(potential_directory_imports)}")
        print(f"   (Imports without file extension - likely pointing to directories)")
        print()
        
        if potential_directory_imports:
            # Agrupar por patrón
            resolved_dir = []
            unresolved_dir = []
            
            for dep, comp in potential_directory_imports:
                if dep.depends_on_component_id:
                    resolved_dir.append((dep, comp))
                else:
                    unresolved_dir.append((dep, comp))
            
            print(f"  ✅ Resolved: {len(resolved_dir)} ({self._percent(len(resolved_dir), len(potential_directory_imports))})")
            print(f"  ❌ Unresolved: {len(unresolved_dir)} ({self._percent(len(unresolved_dir), len(potential_directory_imports))})")
            print()
            
            if unresolved_dir:
                print("  📋 Unresolved Directory Imports (first 10):")
                for dep, comp in unresolved_dir[:10]:
                    print(f"    • {comp.name}")
                    print(f"      imports: {dep.depends_on_name}")
                    print(f"      from: {dep.from_path}")
                
                if len(unresolved_dir) > 10:
                    print(f"    ... and {len(unresolved_dir) - 10} more")
            print()
    
    def _section_8_recommendations(self, session):
        """Recomendaciones basadas en el diagnóstico."""
        print("\n" + "=" * 80)
        print("💡 SECTION 8: RECOMMENDATIONS")
        print("=" * 80)
        
        total_deps = session.query(ComponentDependency).count()
        resolved = session.query(ComponentDependency).filter(
            ComponentDependency.depends_on_component_id.isnot(None)
        ).count()
        unresolved = session.query(ComponentDependency).filter(
            ComponentDependency.depends_on_component_id.is_(None),
            ComponentDependency.is_external == False
        ).count()
        
        resolution_rate = (resolved / total_deps * 100) if total_deps > 0 else 0
        
        print(f"\n📊 Current Resolution Rate: {resolution_rate:.1f}%")
        print(f"   ({resolved} resolved out of {resolved + unresolved} internal imports)")
        print()
        
        print("🎯 Recommendations:")
        
        if resolution_rate < 60:
            print("\n  🔴 CRITICAL - Very Low Resolution Rate")
            print("     • Priority: Implement Barrel Export resolution immediately")
            print("     • Expected improvement: 30-40%")
            print("     • Recommended approach: Full solution (Phases 1+2+3)")
        elif resolution_rate < 80:
            print("\n  🟠 IMPORTANT - Moderate Resolution Rate")
            print("     • Priority: Implement directory import resolution")
            print("     • Expected improvement: 15-25%")
            print("     • Recommended approach: Phase 2 + 3")
        else:
            print("\n  🟢 GOOD - High Resolution Rate")
            print("     • Priority: Fine-tune edge cases")
            print("     • Expected improvement: 5-10%")
            print("     • Recommended approach: Phase 1 optimizations")
        
        # Detectar si el caso Purchase/Checkout está sin resolver
        purchase = session.query(Component).filter(Component.name == 'Purchase').first()
        checkout = session.query(Component).filter(
            Component.name == 'Checkout',
            Component.file_path.like('%/Checkout/Checkout.js')
        ).first()
        
        if purchase and checkout:
            checkout_dep = session.query(ComponentDependency).filter(
                ComponentDependency.component_id == purchase.id,
                ComponentDependency.depends_on_name == 'Checkout'
            ).first()
            
            if not checkout_dep or not checkout_dep.depends_on_component_id:
                print("\n  ⚠️  SPECIFIC ISSUE DETECTED:")
                print("     • Purchase → Checkout dependency is NOT resolved")
                print("     • This confirms the barrel export bug")
                print("     • Solution: Implement barrel export resolution")
        
        # Contar directory imports no resueltos
        unresolved_dir = session.query(ComponentDependency).filter(
            and_(
                ~ComponentDependency.from_path.like('%.js'),
                ~ComponentDependency.from_path.like('%.jsx'),
                ~ComponentDependency.from_path.like('%.ts'),
                ~ComponentDependency.from_path.like('%.tsx'),
                ComponentDependency.is_external == False,
                ComponentDependency.depends_on_component_id.is_(None)
            )
        ).count()
        
        if unresolved_dir > 0:
            print(f"\n  📁 Directory Import Issues:")
            print(f"     • {unresolved_dir} unresolved directory imports detected")
            print(f"     • This is likely the main cause of low resolution rate")
            print(f"     • Solution: Implement index.js parsing")
        
        print("\n  📚 Next Steps:")
        print("     1. Review BUG_ANALISIS_IMPORT_RESOLUTION_V2.md")
        print("     2. Decide on implementation approach (Phase 1/2/3)")
        print("     3. Create barrel_exports table if going with Phase 3")
        print("     4. Re-run this diagnostic after implementation")
        print()
    
    def _percent(self, part: int, total: int) -> str:
        """Calcula porcentaje."""
        if total == 0:
            return "0%"
        return f"{part / total * 100:.1f}%"
    
    def export_json_report(self, output_file: str = "diagnostic_report.json"):
        """Exporta reporte en JSON para análisis programático."""
        with self.SessionLocal() as session:
            report = {
                'timestamp': datetime.now().isoformat(),
                'database': self.database_url.split('@')[1] if '@' in self.database_url else 'local',
                'statistics': {
                    'projects': session.query(Project).count(),
                    'components': session.query(Component).count(),
                    'dependencies': {
                        'total': session.query(ComponentDependency).count(),
                        'resolved': session.query(ComponentDependency).filter(
                            ComponentDependency.depends_on_component_id.isnot(None)
                        ).count(),
                        'unresolved_internal': session.query(ComponentDependency).filter(
                            ComponentDependency.depends_on_component_id.is_(None),
                            ComponentDependency.is_external == False
                        ).count(),
                        'external': session.query(ComponentDependency).filter(
                            ComponentDependency.is_external == True
                        ).count()
                    },
                    'containers': session.query(Component).filter(
                        Component.container_file_path.isnot(None)
                    ).count()
                }
            }
            
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"\n📄 JSON report exported to: {output_file}")


def main():
    """Main function."""
    try:
        diagnostic = ImportResolutionDiagnostic()
        diagnostic.run_full_diagnostic()
        diagnostic.export_json_report()
        
        print("\n" + "=" * 80)
        print("✅ DIAGNOSTIC COMPLETE")
        print("=" * 80)
        print()
        
    except Exception as e:
        print(f"\n❌ Error running diagnostic: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

