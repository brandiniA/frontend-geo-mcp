"""
Navigator tool para búsqueda y exploración de componentes React.
"""

from typing import List, Dict, Optional, Any
from registry.database_client import DatabaseClient
from .utils import (
    format_relative_time,
    get_all_hooks,
    is_new_component,
    group_components_by_type,
    group_by_project,
    search_in_jsdoc,
)


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
        
        # Agrupar por proyecto usando utilidad
        by_project = group_by_project(components)
        
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
                
                # Mostrar hooks nativos de React
                native_hooks = comp.get('native_hooks_used', [])
                if native_hooks:
                    native_list = ', '.join(native_hooks[:5])
                    if len(native_hooks) > 5:
                        native_list += f" (+{len(native_hooks) - 5} more)"
                    response += f"- 🪝 Native Hooks: {native_list}\n"
                
                # Mostrar custom hooks
                custom_hooks = comp.get('custom_hooks_used', [])
                if custom_hooks:
                    custom_list = ', '.join(custom_hooks[:5])
                    if len(custom_hooks) > 5:
                        custom_list += f" (+{len(custom_hooks) - 5} more)"
                    response += f"- 🎣 Custom Hooks: {custom_list}\n"
                
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
        Incluye información de cuándo fue creado y modificado.
        
        Args:
            component_name: Nombre del componente
            project_id: ID del proyecto
            
        Returns:
            Detalles formateados en markdown con JSDoc completo
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
        
        # Información de fechas (usando utilidad)
        if comp.get('created_at'):
            response += f"**Added:** {format_relative_time(comp['created_at'])}\n"
        
        if comp.get('updated_at'):
            response += f"**Modified:** {format_relative_time(comp['updated_at'])}\n"
        
        if comp['description']:
            response += f"**Description:** {comp['description']}\n"
        
        response += "\n"
        
        # JSDoc completo si está disponible
        jsdoc = comp.get('jsdoc')
        if jsdoc:
            # Descripción extendida
            if jsdoc.get('description'):
                response += f"### 📝 Overview\n{jsdoc['description']}\n\n"
            
            # Parámetros
            if jsdoc.get('params'):
                response += "### 📥 Parameters\n"
                for param in jsdoc['params']:
                    response += f"- **`{param['name']}`** (`{param['type']}`): {param['description']}\n"
                response += "\n"
            
            # Returns
            if jsdoc.get('returns'):
                returns = jsdoc['returns']
                response += f"### 📤 Returns\n**Type:** `{returns['type']}`\n"
                if returns['description']:
                    response += f"**Description:** {returns['description']}\n"
                response += "\n"
            
            # Ejemplos
            if jsdoc.get('examples'):
                response += "### 💡 Examples\n"
                for i, example in enumerate(jsdoc['examples'], 1):
                    response += f"**Example {i}:**\n```tsx\n{example}\n```\n"
                response += "\n"
            
            # Información adicional
            if jsdoc.get('deprecated'):
                response += "⚠️ **DEPRECATED** - This component is deprecated\n\n"
            
            if jsdoc.get('author'):
                response += f"👤 **Author:** {jsdoc['author']}\n"
            
            if jsdoc.get('version'):
                response += f"📌 **Version:** {jsdoc['version']}\n"
        
        # Props (si no están en JSDoc)
        if comp['props'] and not (jsdoc and jsdoc.get('params')):
            response += "### 📦 Props\n"
            for prop in comp['props']:
                response += f"- `{prop}`\n"
            response += "\n"
        
        # Hooks - mostrar separados (native y custom)
        native_hooks = comp.get('native_hooks_used', [])
        custom_hooks = comp.get('custom_hooks_used', [])
        
        if native_hooks or custom_hooks:
            response += "### 🪝 Hooks Used\n"
            
            if native_hooks:
                response += "**Native Hooks:**\n"
                for hook in native_hooks[:10]:
                    response += f"- `{hook}`\n"
                if len(native_hooks) > 10:
                    response += f"- ... and {len(native_hooks) - 10} more\n"
            
            if custom_hooks:
                response += "**Custom Hooks:**\n"
                for hook in custom_hooks[:10]:
                    response += f"- `{hook}`\n"
                if len(custom_hooks) > 10:
                    response += f"- ... and {len(custom_hooks) - 10} more\n"
            
            response += "\n"
        
        # Dependencies
        if comp['imports']:
            response += "### 📚 Dependencies\n"
            for imp in comp['imports'][:10]:
                response += f"- `{imp}`\n"
            if len(comp['imports']) > 10:
                response += f"- ... and {len(comp['imports']) - 10} more\n"
            response += "\n"
        
        # Usage example (si no hay en JSDoc)
        if not (jsdoc and jsdoc.get('examples')):
            response += "### 💡 Basic Usage\n"
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
        Muestra 🆕 para componentes creados en los últimos 7 días.
        
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
        
        # Agrupar por tipo usando utilidad
        by_type = group_components_by_type(components)
        
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
                # Usar is_new_component para determinar si mostrar badge
                new_badge = " 🆕" if is_new_component(comp) else ""
                response += f"- **{comp['name']}** - `{comp['file_path']}`{new_badge}\n"
            
            if len(comps) > 20:
                response += f"- ... and {len(comps) - 20} more\n"
            
            response += "\n"
        
        return response
    
    async def list_components_in_path(
        self, 
        path: str, 
        project_id: str
    ) -> str:
        """
        Lista componentes en una ruta específica.
        
        Args:
            path: Ruta del directorio
            project_id: ID del proyecto
            
        Returns:
            Lista formateada en markdown
        """
        components = await self.db.list_components_in_path(path, project_id)
        
        if not components:
            return f"❌ No components found in path '{path}'"
        
        response = f"📂 **Components in `{path}`** ({len(components)} total)\n\n"
        
        # Agrupar por tipo
        by_type = group_components_by_type(components)
        
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
            
            for comp in sorted(comps, key=lambda x: x['name']):
                new_badge = " 🆕" if is_new_component(comp) else ""
                response += f"- **{comp['name']}** - `{comp['file_path']}`{new_badge}\n"
            
            response += "\n"
        
        return response
    
    async def search_components_semantic(
        self,
        query: Optional[str] = None,
        project_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Búsqueda semántica avanzada de componentes.
        
        Args:
            query: Término de búsqueda
            project_id: Filtrar por proyecto (opcional)
            filters: Filtros adicionales
            
        Returns:
            Lista formateada en markdown
        """
    async def search_components_semantic(
        self,
        query: Optional[str] = None,
        project_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Búsqueda semántica avanzada de componentes.
        
        Args:
            query: Término de búsqueda
            project_id: Filtrar por proyecto (opcional)
            filters: Filtros adicionales
            
        Returns:
            Lista formateada en markdown
        """
        try:
            components = await self.db.search_components_semantic(query, project_id, filters)
        except Exception as e:
            import traceback
            error_msg = f"❌ Error in search_components_semantic: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)  # Debug
            return error_msg
        
        if not components:
            filter_str = f" with filters {filters}" if filters else ""
            query_str = f"'{query}'" if query else "empty query"
            return f"❌ No components found matching {query_str}{filter_str}"
        
        # Asegurar que todos los componentes son diccionarios
        components_list = []
        for comp in components:
            if isinstance(comp, dict):
                components_list.append(comp)
            elif hasattr(comp, 'to_dict'):
                components_list.append(comp.to_dict())
            else:
                # Fallback: crear diccionario manualmente
                components_list.append({
                    'id': getattr(comp, 'id', None),
                    'name': getattr(comp, 'name', ''),
                    'project_id': getattr(comp, 'project_id', ''),
                    'file_path': getattr(comp, 'file_path', ''),
                    'props': getattr(comp, 'props', []),
                    'component_type': getattr(comp, 'component_type', None),
                    'description': getattr(comp, 'description', None),
                })
        
        query_display = query if query else "all components"
        response = f"🔍 Found {len(components_list)} component(s) matching '{query_display}'"
        if filters:
            response += f" with filters: {filters}"
        response += ":\n\n"
        
        # Agrupar por proyecto
        by_project = group_by_project(components_list)
        
        for pid, comps in by_project.items():
            try:
                project = await self.db.get_project(pid)
                project_name = project['name'] if project else pid
            except Exception as e:
                project_name = pid
                print(f"Error getting project {pid}: {e}")  # Debug
            
            response += f"### 🏢 {project_name.upper()}\n\n"
            
            for comp in comps[:20]:  # Limitar visualización a 20
                response += f"**{comp.get('name', 'Unknown')}**\n"
                response += f"- 📂 Path: `{comp.get('file_path', '')}`\n"
                response += f"- 🏷️  Type: {comp.get('component_type', 'unknown')}\n"
                
                if comp.get('description'):
                    desc = comp['description'][:100]
                    if len(comp['description']) > 100:
                        desc += "..."
                    response += f"- 📝 Description: {desc}\n"
                
                response += "\n"
            
            if len(comps) > 20:
                response += f"- ... and {len(comps) - 20} more\n"
            
            response += "\n"
        
        return response
    
    async def search_by_hook(self, hook_name: str, project_id: Optional[str] = None) -> str:
        """
        Busca componentes que usan un hook específico.
        
        Args:
            hook_name: Nombre del hook (ej: useState, useEffect)
            project_id: Filtrar por proyecto (opcional). Si es None, busca en todos los proyectos
            
        Returns:
            Lista de componentes que usan el hook
        """
        # Usar el método especializado de búsqueda en la BD (más eficiente)
        matching = await self.db.search_by_hook(hook_name, project_id)
        
        if not matching:
            if project_id:
                return f"❌ No components found using hook '{hook_name}' in project '{project_id}'"
            else:
                return f"❌ No components found using hook '{hook_name}'"
        
        response = f"🪝 Found {len(matching)} component(s) using `{hook_name}`"
        if project_id:
            response += f" in project `{project_id}`"
        response += ":\n\n"
        
        # Agrupar por proyecto si no está filtrado (usando utilidad)
        if not project_id:
            by_project = group_by_project(matching)
            
            for pid, comps in by_project.items():
                response += f"### 📦 {pid}\n\n"
                for comp in comps[:15]:
                    response += f"- **{comp['name']}** in `{comp['file_path']}`\n"
                
                if len(comps) > 15:
                    response += f"- ... and {len(comps) - 15} more\n"
                
                response += "\n"
        else:
            # Mostrar resultados sin agrupar si está filtrado por proyecto
            for comp in matching[:20]:
                response += f"- **{comp['name']}** in `{comp['file_path']}`\n"
            
            if len(matching) > 20:
                response += f"\n... and {len(matching) - 20} more\n"
        
        return response
    
    async def search_by_jsdoc(self, query: str, project_id: Optional[str] = None) -> str:
        """
        Busca componentes por términos en su JSDoc.
        
        Args:
            query: Término de búsqueda (ej: description, param name, return type)
            project_id: Filtrar por proyecto (opcional)
            
        Returns:
            Lista de componentes que coinciden con el término
        """
        # Obtener componentes (todos o de un proyecto específico)
        if project_id:
            components = await self.db.get_components_by_project(project_id)
        else:
            components = await self.db.get_all_components()
        
        # Usar utilidad de búsqueda en JSDoc
        matching = search_in_jsdoc(components, query)
        
        if not matching:
            return f"❌ No components found with JSDoc matching '{query}'"
        
        response = f"🔍 Found {len(matching)} component(s) with '{query}' in documentation:\n\n"
        
        # Agrupar por proyecto (usando utilidad)
        by_project_with_match = {}
        for comp, match_type in matching:
            pid = comp['project_id']
            if pid not in by_project_with_match:
                by_project_with_match[pid] = []
            by_project_with_match[pid].append((comp, match_type))
        
        # Formatear respuesta
        for pid, comps in by_project_with_match.items():
            response += f"### 📦 {pid}\n"
            
            for comp, match_type in comps[:10]:
                response += f"- **{comp['name']}** ({match_type})\n"
                response += f"  📄 `{comp['file_path']}`\n"
            
            if len(comps) > 10:
                response += f"- ... and {len(comps) - 10} more\n"
            
            response += "\n"
        
        return response
    
    async def get_component_docs(
        self,
        component_name: str,
        project_id: str
    ) -> str:
        """
        Obtiene la documentación JSDoc completa de un componente.
        Muestra parámetros, returns, ejemplos, autor, versión, deprecated.
        
        Args:
            component_name: Nombre del componente
            project_id: ID del proyecto
            
        Returns:
            Documentación formateada en markdown
        """
        components = await self.db.search_components(component_name, project_id)
        
        if not components:
            return f"❌ Component '{component_name}' not found in project '{project_id}'"
        
        # Tomar el primer match exacto
        comp = None
        for c in components:
            if c['name'] == component_name:
                comp = c
                break
        
        if not comp:
            comp = components[0]
        
        jsdoc = comp.get('jsdoc')
        
        if not jsdoc:
            return f"⚠️  No JSDoc documentation found for '{component_name}'\n\nTry to add JSDoc comments to your component."
        
        response = f"## 📚 Documentation: {comp['name']}\n\n"
        response += f"**File:** `{comp['file_path']}`\n"
        response += f"**Project:** {project_id}\n\n"
        
        # Descripción principal
        if jsdoc.get('description'):
            response += f"### 📝 Overview\n{jsdoc['description']}\n\n"
        
        # Parámetros
        if jsdoc.get('params'):
            response += "### 📥 Parameters\n"
            for param in jsdoc['params']:
                response += f"- **`{param['name']}`** (`{param['type']}`)\n"
                if param.get('description'):
                    response += f"  {param['description']}\n"
            response += "\n"
        
        # Returns
        if jsdoc.get('returns'):
            returns = jsdoc['returns']
            response += "### 📤 Returns\n"
            response += f"**Type:** `{returns['type']}`\n"
            if returns.get('description'):
                response += f"**Description:** {returns['description']}\n"
            response += "\n"
        
        # Ejemplos
        if jsdoc.get('examples'):
            response += "### 💡 Examples\n"
            for i, example in enumerate(jsdoc['examples'], 1):
                response += f"**Example {i}:**\n```tsx\n{example}\n```\n"
            response += "\n"
        
        # Información adicional
        if jsdoc.get('deprecated'):
            response += "⚠️ **DEPRECATED** - This component is deprecated\n\n"
        
        if jsdoc.get('author'):
            response += f"👤 **Author:** {jsdoc['author']}\n"
        
        if jsdoc.get('version'):
            response += f"📌 **Version:** {jsdoc['version']}\n"
        
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
        # Test 1: Buscar componentes por nombre
        print("=" * 60)
        print("Test 1: Buscar componentes por nombre 'Button'")
        print("=" * 60)
        result = await navigator.find_component("Button")
        print(result)
        
        # Test 2: Buscar componentes por hook (nuevo método)
        print("\n" + "=" * 60)
        print("Test 2: Buscar componentes que usan 'useState' (BD optimizada)")
        print("=" * 60)
        result = await navigator.search_by_hook("useState")
        print(result)
        
        # Test 3: Buscar componentes por hook en proyecto específico
        print("\n" + "=" * 60)
        print("Test 3: Buscar componentes que usan 'useEffect' en proyecto")
        print("=" * 60)
        result = await navigator.search_by_hook("useEffect")
        print(result)
        
    finally:
        db.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_navigator())

