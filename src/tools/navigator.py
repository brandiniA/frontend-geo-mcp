"""
Navigator tool para búsqueda y exploración de componentes React.
"""

from typing import List, Dict, Optional
from registry.database_client import DatabaseClient


class ComponentNavigator:
    """Herramienta de navegación y búsqueda de componentes."""
    
    def __init__(self, database_client: DatabaseClient):
        self.db = database_client
    
    async def find_component(
        self, 
        query: str, 
        project_id: Optional[str] = None
    ) -> str:
        """
        Busca componentes por nombre.
        
        Args:
            query: Término de búsqueda
            project_id: Filtrar por proyecto (opcional)
            
        Returns:
            Respuesta formateada en markdown
        """
        components = await self.db.search_components(query, project_id)
        
        if not components:
            return f"❌ No components found matching '{query}'"
        
        response = f"📍 Found {len(components)} component(s) matching '{query}':\n\n"
        
        # Agrupar por proyecto
        by_project = {}
        for comp in components:
            pid = comp['project_id']
            if pid not in by_project:
                by_project[pid] = []
            by_project[pid].append(comp)
        
        # Formatear respuesta
        for pid, comps in by_project.items():
            project = await self.db.get_project(pid)
            project_name = project['name'] if project else pid
            project_type = project['type'] if project else 'unknown'
            
            response += f"### 🏢 {project_name.upper()} ({project_type})\n\n"
            
            for comp in comps:
                response += f"**{comp['name']}**\n"
                response += f"- 📂 Path: `{comp['file_path']}`\n"
                response += f"- 🏷️  Type: {comp['component_type']}\n"
                
                if comp['props']:
                    props_list = ', '.join(comp['props'][:5])
                    if len(comp['props']) > 5:
                        props_list += f" (+{len(comp['props']) - 5} more)"
                    response += f"- 📦 Props: {props_list}\n"
                
                if comp['hooks']:
                    hooks_list = ', '.join(comp['hooks'][:5])
                    if len(comp['hooks']) > 5:
                        hooks_list += f" (+{len(comp['hooks']) - 5} more)"
                    response += f"- 🪝 Hooks: {hooks_list}\n"
                
                if comp['description']:
                    response += f"- 📝 Description: {comp['description']}\n"
                
                # Generar import statement
                import_path = self._generate_import_path(comp)
                response += f"- 🔗 Import: `import {{ {comp['name']} }} from '{import_path}'`\n"
                response += "\n"
        
        return response
    
    async def get_component_details(
        self, 
        component_name: str, 
        project_id: str
    ) -> str:
        """
        Obtiene detalles específicos de un componente.
        
        Args:
            component_name: Nombre del componente
            project_id: ID del proyecto
            
        Returns:
            Detalles formateados en markdown
        """
        components = await self.db.search_components(component_name, project_id)
        
        if not components:
            return f"❌ Component '{component_name}' not found in project '{project_id}'"
        
        # Tomar el primer match exacto o el más cercano
        comp = None
        for c in components:
            if c['name'] == component_name:
                comp = c
                break
        
        if not comp:
            comp = components[0]
        
        response = f"## 📋 Component Details: {comp['name']}\n\n"
        
        # Información del proyecto
        project = await self.db.get_project(project_id)
        if project:
            response += f"**Project:** {project['name']} ({project['type']})\n"
        
        response += f"**Path:** `{comp['file_path']}`\n"
        response += f"**Type:** {comp['component_type']}\n"
        
        if comp['description']:
            response += f"**Description:** {comp['description']}\n"
        
        response += "\n"
        
        # Props
        if comp['props']:
            response += "### 📦 Props\n"
            for prop in comp['props']:
                response += f"- `{prop}`\n"
            response += "\n"
        
        # Hooks
        if comp['hooks']:
            response += "### 🪝 Hooks Used\n"
            for hook in comp['hooks']:
                response += f"- `{hook}`\n"
            response += "\n"
        
        # Dependencies
        if comp['imports']:
            response += "### 📚 Dependencies\n"
            for imp in comp['imports'][:10]:
                response += f"- `{imp}`\n"
            if len(comp['imports']) > 10:
                response += f"- ... and {len(comp['imports']) - 10} more\n"
            response += "\n"
        
        # Exports
        if comp['exports']:
            response += "### 📤 Exports\n"
            for exp in comp['exports']:
                response += f"- `{exp}`\n"
            response += "\n"
        
        # Usage example
        response += "### 💡 Usage Example\n"
        response += "```tsx\n"
        
        import_path = self._generate_import_path(comp)
        response += f"import {{ {comp['name']} }} from '{import_path}';\n\n"
        
        if comp['props']:
            response += f"<{comp['name']}\n"
            for prop in comp['props'][:3]:
                response += f"  {prop}={{/* value */}}\n"
            if len(comp['props']) > 3:
                response += f"  // ... and {len(comp['props']) - 3} more props\n"
            response += "/>\n"
        else:
            response += f"<{comp['name']} />\n"
        
        response += "```\n"
        
        return response
    
    async def list_all_components(
        self, 
        project_id: Optional[str] = None,
        component_type: Optional[str] = None
    ) -> str:
        """
        Lista todos los componentes (con filtros opcionales).
        
        Args:
            project_id: Filtrar por proyecto
            component_type: Filtrar por tipo (page, component, layout, hook)
            
        Returns:
            Lista formateada en markdown
        """
        # Buscar con query vacío para obtener todos
        components = await self.db.search_components("", project_id)
        
        if component_type:
            components = [c for c in components if c['component_type'] == component_type]
        
        if not components:
            return "📂 No components found"
        
        response = f"📂 **Component Catalog** ({len(components)} total)\n\n"
        
        # Agrupar por tipo
        by_type = {}
        for comp in components:
            comp_type = comp['component_type'] or 'component'
            if comp_type not in by_type:
                by_type[comp_type] = []
            by_type[comp_type].append(comp)
        
        # Mostrar por tipo
        type_icons = {
            'page': '📄',
            'component': '🧩',
            'layout': '📐',
            'hook': '🪝',
        }
        
        for comp_type, comps in sorted(by_type.items()):
            icon = type_icons.get(comp_type, '📦')
            response += f"### {icon} {comp_type.title()}s ({len(comps)})\n\n"
            
            for comp in sorted(comps, key=lambda x: x['name'])[:20]:
                response += f"- **{comp['name']}** - `{comp['file_path']}`\n"
            
            if len(comps) > 20:
                response += f"- ... and {len(comps) - 20} more\n"
            
            response += "\n"
        
        return response
    
    async def search_by_hook(self, hook_name: str) -> str:
        """
        Busca componentes que usan un hook específico.
        
        Args:
            hook_name: Nombre del hook (ej: useState, useEffect)
            
        Returns:
            Lista de componentes que usan el hook
        """
        # Esta es una búsqueda más compleja que requeriría una query SQL especial
        # Por ahora, buscaremos todos los componentes y filtraremos
        components = await self.db.search_components("")
        
        matching = [
            c for c in components 
            if hook_name in c.get('hooks', [])
        ]
        
        if not matching:
            return f"❌ No components found using hook '{hook_name}'"
        
        response = f"🪝 Found {len(matching)} component(s) using `{hook_name}`:\n\n"
        
        for comp in matching[:20]:
            response += f"- **{comp['name']}** in `{comp['file_path']}`\n"
        
        if len(matching) > 20:
            response += f"\n... and {len(matching) - 20} more\n"
        
        return response
    
    def _generate_import_path(self, component: Dict) -> str:
        """
        Genera la ruta de import correcta para un componente.
        
        Args:
            component: Diccionario con información del componente
            
        Returns:
            Ruta de import
        """
        file_path = component['file_path']
        
        # Remover extensión
        import_path = file_path.replace('.tsx', '').replace('.jsx', '')
        
        # Si empieza con src/, removerlo
        if import_path.startswith('src/'):
            import_path = import_path[4:]
        
        # Agregar ./ al inicio si no tiene
        if not import_path.startswith('./') and not import_path.startswith('@'):
            import_path = './' + import_path
        
        return import_path


# Función de utilidad para testing
async def test_navigator():
    """Prueba el navigator con la base de datos."""
    from dotenv import load_dotenv
    load_dotenv()
    
    db = DatabaseClient()
    navigator = ComponentNavigator(db)
    
    try:
        # Buscar componentes
        result = await navigator.find_component("Button")
        print(result)
    finally:
        db.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_navigator())

