"""
Navigator tool para búsqueda y exploración de componentes React.
"""

from typing import List, Dict, Optional, Any
from registry.database_client import DatabaseClient
from .utils import (
    format_relative_time,
    is_new_component,
    group_by_project,
    search_in_jsdoc,
    generate_import_path,
    format_component_summary,
    format_project_header,
    format_jsdoc_section,
    format_hooks_section,
    format_components_by_type,
    truncate_description,
    format_usage_example,
    get_component_type_icon,
    find_exact_or_first_component,
    normalize_components_to_dicts,
)
from .utils.hierarchy_utils import build_dependency_tree, format_tree


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
        
        # Formatear respuesta usando utilidades
        for pid, comps in by_project.items():
            project = await self.db.get_project(pid)
            response += format_project_header(project, pid) + "\n\n"
            
            for comp in comps:
                response += format_component_summary(
                    comp,
                    include_props=True,
                    include_hooks=True,
                    include_description=True,
                    include_import=True,
                    max_items=5
                ) + "\n\n"
        
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
        comp = find_exact_or_first_component(components, component_name)
        
        if not comp:
            return f"❌ Component '{component_name}' not found in project '{project_id}'"
        
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
            response += format_jsdoc_section(jsdoc)
        
        # Props (si no están en JSDoc)
        if comp['props'] and not (jsdoc and jsdoc.get('params')):
            response += "### 📦 Props\n"
            for prop in comp['props']:
                response += f"- `{prop}`\n"
            response += "\n"
        
        # Hooks - mostrar separados (native y custom)
        hooks_section = format_hooks_section(comp, max_hooks=10)
        if hooks_section:
            response += hooks_section
        
        # Dependencies
        if comp['imports']:
            response += "### 📚 Dependencies\n"
            for imp in comp['imports'][:10]:
                response += f"- `{imp}`\n"
            if len(comp['imports']) > 10:
                response += f"- ... and {len(comp['imports']) - 10} more\n"
            response += "\n"
        
        # Feature Flags
        component_id = comp.get('id')
        if component_id:
            try:
                flags = await self.db.get_flags_for_component(component_id, project_id)
                if flags:
                    response += "### 🚩 Feature Flags\n"
                    for flag in flags:
                        flag_name = flag.get('name', 'Unknown')
                        flag_type = flag.get('value_type', '')
                        default_value = flag.get('default_value')
                        usage_pattern = flag.get('usage_pattern', '')
                        
                        flag_line = f"- **`{flag_name}`**"
                        if flag_type:
                            flag_line += f" (`{flag_type}`)"
                        if default_value is not None:
                            flag_line += f" - Default: `{default_value}`"
                        if usage_pattern:
                            flag_line += f" - Pattern: `{usage_pattern}`"
                        response += flag_line + "\n"
                    response += "\n"
            except Exception as e:
                # Silently fail if there's an error getting flags
                # This prevents breaking the component details if flags aren't available
                pass
        
        # Usage example (si no hay en JSDoc)
        if not (jsdoc and jsdoc.get('examples')):
            response += format_usage_example(comp, include_props=True, max_props=3)
        
        return response
    
    async def find_hook(
        self,
        query: str,
        project_id: Optional[str] = None
    ) -> str:
        """
        Busca hooks por nombre.
        
        Args:
            query: Término de búsqueda
            project_id: Filtrar por proyecto (opcional)
            
        Returns:
            Respuesta formateada en markdown
        """
        hooks = await self.db.search_hooks(query, project_id)
        
        if not hooks:
            return f"❌ No hooks found matching '{query}'"
        
        response = f"📍 Found {len(hooks)} hook(s) matching '{query}':\n\n"
        
        # Agrupar por proyecto
        by_project = group_by_project(hooks)
        
        for pid, hook_list in by_project.items():
            project = await self.db.get_project(pid)
            response += format_project_header(project, pid) + "\n\n"
            
            for hook in hook_list:
                response += f"**{hook['name']}**\n"
                response += f"- 📂 Path: `{hook['file_path']}`\n"
                if hook.get('description'):
                    response += f"- 📝 {hook['description']}\n"
                if hook.get('return_type'):
                    response += f"- 🔄 Returns: `{hook['return_type']}`\n"
                if hook.get('parameters'):
                    params = hook['parameters']
                    if isinstance(params, list) and len(params) > 0:
                        param_str = ", ".join([p.get('name', '') if isinstance(p, dict) else str(p) for p in params[:3]])
                        response += f"- 📥 Parameters: `{param_str}`"
                        if len(params) > 3:
                            response += f" (+{len(params) - 3} more)"
                        response += "\n"
                response += f"- 🔗 Import: `import {{ {hook['name']} }} from '{hook['file_path']}'`\n"
                response += "\n"
        
        return response
    
    async def get_hook_details(
        self,
        hook_name: str,
        project_id: str
    ) -> str:
        """
        Obtiene detalles específicos de un hook.
        Incluye información de cuándo fue creado y modificado.
        
        Args:
            hook_name: Nombre del hook
            project_id: ID del proyecto
            
        Returns:
            Detalles formateados en markdown con JSDoc completo
        """
        hook = await self.db.get_hook_by_name(hook_name, project_id)
        
        if not hook:
            return f"❌ Hook '{hook_name}' not found in project '{project_id}'"
        
        response = f"## 🪝 Hook Details: {hook['name']}\n\n"
        
        # Información del proyecto
        project = await self.db.get_project(project_id)
        if project:
            response += f"**Project:** {project['name']} ({project['type']})\n"
        
        response += f"**Path:** `{hook['file_path']}`\n"
        response += f"**Type:** {hook.get('hook_type', 'custom')}\n"
        
        # Información de fechas
        if hook.get('created_at'):
            response += f"**Added:** {format_relative_time(hook['created_at'])}\n"
        
        if hook.get('updated_at'):
            response += f"**Modified:** {format_relative_time(hook['updated_at'])}\n"
        
        if hook.get('description'):
            response += f"**Description:** {hook['description']}\n"
        
        response += "\n"
        
        # JSDoc completo si está disponible
        jsdoc = hook.get('jsdoc')
        if jsdoc:
            response += format_jsdoc_section(jsdoc)
        
        # Parameters
        if hook.get('parameters'):
            params = hook['parameters']
            if isinstance(params, list) and len(params) > 0:
                response += "### 📥 Parameters\n"
                for param in params:
                    if isinstance(param, dict):
                        param_name = param.get('name', 'Unknown')
                        param_type = param.get('type', '')
                        param_desc = param.get('description', '')
                        param_line = f"- **`{param_name}`**"
                        if param_type:
                            param_line += f" (`{param_type}`)"
                        if param_desc:
                            param_line += f": {param_desc}"
                        response += param_line + "\n"
                    else:
                        response += f"- `{param}`\n"
                response += "\n"
        
        # Return type
        if hook.get('return_type'):
            response += f"### 📤 Returns\n"
            response += f"**Type:** `{hook['return_type']}`\n\n"
        
        # Hooks - mostrar separados (native y custom)
        if hook.get('native_hooks_used') or hook.get('custom_hooks_used'):
            response += "### 🪝 Hooks Used\n"
            if hook.get('native_hooks_used'):
                response += "**Native Hooks:**\n"
                for h in hook['native_hooks_used']:
                    response += f"- `{h}`\n"
            if hook.get('custom_hooks_used'):
                response += "**Custom Hooks:**\n"
                for h in hook['custom_hooks_used']:
                    response += f"- `{h}`\n"
            response += "\n"
        
        # Dependencies
        if hook.get('imports'):
            response += "### 📚 Dependencies\n"
            for imp in hook['imports'][:10]:
                response += f"- `{imp}`\n"
            if len(hook['imports']) > 10:
                response += f"- ... and {len(hook['imports']) - 10} more\n"
            response += "\n"
        
        # Feature Flags
        hook_id = hook.get('id')
        if hook_id:
            try:
                flags = await self.db.get_flags_for_hook(hook_id, project_id)
                if flags:
                    response += "### 🚩 Feature Flags\n"
                    for flag in flags:
                        flag_name = flag.get('name', 'Unknown')
                        flag_type = flag.get('value_type', '')
                        default_value = flag.get('default_value')
                        usage_pattern = flag.get('usage_pattern', '')
                        
                        flag_line = f"- **`{flag_name}`**"
                        if flag_type:
                            flag_line += f" (`{flag_type}`)"
                        if default_value is not None:
                            flag_line += f" - Default: `{default_value}`"
                        if usage_pattern:
                            flag_line += f" - Pattern: `{usage_pattern}`"
                        response += flag_line + "\n"
                    response += "\n"
            except Exception as e:
                pass
        
        # Usage example
        response += "### 💡 Basic Usage\n"
        response += f"```tsx\n"
        response += f"import {{ {hook['name']} }} from '{hook['file_path']}';\n\n"
        if hook.get('parameters'):
            params = hook['parameters']
            if isinstance(params, list) and len(params) > 0:
                param_names = [p.get('name', 'param') if isinstance(p, dict) else str(p) for p in params[:3]]
                response += f"const result = {hook['name']}({', '.join(param_names)});\n"
            else:
                response += f"const result = {hook['name']}();\n"
        else:
            response += f"const result = {hook['name']}();\n"
        response += "```\n"
        
        return response
    
    async def list_all_hooks(
        self,
        project_id: Optional[str] = None
    ) -> str:
        """
        Lista todos los hooks (con filtros opcionales).
        
        Args:
            project_id: Filtrar por proyecto
            
        Returns:
            Lista formateada en markdown
        """
        hooks = await self.db.search_hooks("", project_id)
        
        if not hooks:
            if project_id:
                return f"❌ No hooks found in project '{project_id}'"
            return "❌ No hooks found"
        
        response = f"🪝 **Hooks** ({len(hooks)} total)\n\n"
        
        # Agrupar por proyecto si no está filtrado
        if not project_id:
            by_project = group_by_project(hooks)
            for pid, hook_list in by_project.items():
                project = await self.db.get_project(pid)
                response += format_project_header(project, pid) + "\n\n"
                for hook in hook_list[:20]:
                    response += f"- **{hook['name']}** (`{hook['file_path']}`)\n"
                if len(hook_list) > 20:
                    response += f"- ... and {len(hook_list) - 20} more\n"
                response += "\n"
        else:
            for hook in hooks[:50]:
                response += f"- **{hook['name']}** (`{hook['file_path']}`)\n"
            if len(hooks) > 50:
                response += f"- ... and {len(hooks) - 50} more\n"
        
        return response
    
    async def get_hook_docs(
        self,
        hook_name: str,
        project_id: str
    ) -> str:
        """
        Obtiene la documentación JSDoc completa de un hook.
        
        Args:
            hook_name: Nombre del hook
            project_id: ID del proyecto
            
        Returns:
            Documentación JSDoc formateada
        """
        hook = await self.db.get_hook_by_name(hook_name, project_id)
        
        if not hook:
            return f"❌ Hook '{hook_name}' not found in project '{project_id}'"
        
        jsdoc = hook.get('jsdoc')
        if not jsdoc:
            return f"⚠️ Hook '{hook_name}' has no JSDoc documentation"
        
        response = f"## 📚 Hook Documentation: {hook['name']}\n\n"
        response += f"**File:** `{hook['file_path']}`\n"
        response += f"**Project:** {project_id}\n\n"
        
        response += format_jsdoc_section(jsdoc)
        
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
        response += format_components_by_type(components, show_new_badge=True, max_per_type=20)
        
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
        response += format_components_by_type(components, show_new_badge=True)
        
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
        components_list = normalize_components_to_dicts(components)
        
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
            except Exception as e:
                project = None
                print(f"Error getting project {pid}: {e}")  # Debug
            
            response += format_project_header(project, pid) + "\n\n"
            
            for comp in comps[:20]:  # Limitar visualización a 20
                response += format_component_summary(
                    comp,
                    include_props=False,
                    include_hooks=False,
                    include_description=True,
                    include_import=False,
                    max_items=5
                ) + "\n\n"
            
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
        
        # Tomar el primer match exacto o el más cercano
        comp = find_exact_or_first_component(components, component_name)
        
        if not comp:
            return f"❌ Component '{component_name}' not found in project '{project_id}'"
        
        jsdoc = comp.get('jsdoc')
        
        if not jsdoc:
            return f"⚠️  No JSDoc documentation found for '{component_name}'\n\nTry to add JSDoc comments to your component."
        
        response = f"## 📚 Documentation: {comp['name']}\n\n"
        response += f"**File:** `{comp['file_path']}`\n"
        response += f"**Project:** {project_id}\n\n"
        
        # Usar utilidad para formatear JSDoc
        response += format_jsdoc_section(jsdoc)
        
        return response
    
    async def get_component_hierarchy(
        self,
        component_name: str,
        project_id: str,
        direction: str = 'down',
        max_depth: int = 5
    ) -> str:
        """
        Obtiene el árbol de jerarquía de un componente.
        
        Args:
            component_name: Nombre del componente
            project_id: ID del proyecto
            direction: 'down' (dependencias), 'up' (dependientes), 'both'
            max_depth: Profundidad máxima del árbol (default: 5)
            
        Returns:
            Respuesta formateada en markdown con el árbol
        """
        # Buscar componente
        components = await self.db.search_components(component_name, project_id)
        
        if not components:
            return f"❌ Component '{component_name}' not found in project '{project_id}'"
        
        # Usar el primer componente encontrado
        component = components[0]
        component_id = component.get('id')
        
        if not component_id:
            return f"❌ Component '{component_name}' has no ID"
        
        # Validar dirección
        if direction not in ['down', 'up', 'both']:
            return f"❌ Invalid direction '{direction}'. Must be 'down', 'up', or 'both'"
        
        # Obtener árbol de dependencias
        try:
            tree_data = await self.db.dependencies.get_dependency_tree(
                component_id=component_id,
                direction=direction,
                max_depth=max_depth
            )
            
            if not tree_data:
                return f"❌ Could not build hierarchy tree for '{component_name}'"
            
            # Construir árbol con estadísticas
            tree = build_dependency_tree(tree_data, direction)
            
            # Formatear árbol
            formatted = format_tree(tree, max_depth=max_depth)
            
            return formatted
            
        except Exception as e:
            return f"❌ Error building hierarchy: {str(e)}"
    
    async def get_feature_flag_impact(
        self,
        flag_name: str,
        project_id: str
    ) -> str:
        """
        Analiza el impacto de cambiar o eliminar un feature flag.
        
        Args:
            flag_name: Nombre del feature flag
            project_id: ID del proyecto
            
        Returns:
            Análisis de impacto formateado
        """
        flag = await self.db.get_feature_flag_by_name(flag_name, project_id)
        
        if not flag:
            return f"❌ Feature flag '{flag_name}' not found in project '{project_id}'"
        
        components = await self.db.get_components_using_flag(flag_name, project_id)
        hooks = await self.db.get_hooks_using_flag(flag_name, project_id)
        
        response = f"## 🚩 Feature Flag Impact Analysis: `{flag_name}`\n\n"
        response += f"**Project:** {project_id}\n"
        response += f"**Default Value:** `{flag.get('default_value', 'N/A')}`\n"
        response += f"**Type:** {flag.get('value_type', 'N/A')}\n\n"
        
        total_usage = len(components) + len(hooks)
        
        if total_usage == 0:
            response += "✅ **Safe to remove** - This flag is not used anywhere.\n"
            return response
        
        response += f"⚠️ **Impact Level: {'HIGH' if total_usage > 10 else 'MEDIUM' if total_usage > 5 else 'LOW'}**\n\n"
        response += f"**Total Usage:** {total_usage} entity(ies)\n\n"
        
        if components:
            response += f"### 📦 Components Affected ({len(components)})\n\n"
            for comp in components:
                response += f"- **{comp['name']}** (`{comp['file_path']}`)\n"
            response += "\n"
        
        if hooks:
            response += f"### 🪝 Hooks Affected ({len(hooks)})\n\n"
            for hook in hooks:
                response += f"- **{hook['name']}** (`{hook['file_path']}`)\n"
            response += "\n"
        
        response += "### 📋 Migration Steps\n\n"
        response += "1. Review all affected components and hooks\n"
        response += "2. Understand current flag behavior and default value\n"
        response += "3. Plan migration strategy:\n"
        response += "   - If removing: Replace flag checks with default behavior\n"
        response += "   - If changing default: Update all usages accordingly\n"
        response += "4. Test each affected component/hook\n"
        response += "5. Remove flag definition after migration\n"
        
        return response
    
    async def get_unused_hooks(
        self,
        project_id: str
    ) -> str:
        """
        Obtiene hooks que están definidos pero no se usan en ningún componente u otro hook.
        
        Args:
            project_id: ID del proyecto
            
        Returns:
            Lista de hooks no usados
        """
        all_hooks = await self.db.get_hooks_by_project(project_id)
        
        if not all_hooks:
            return f"❌ No hooks found in project '{project_id}'"
        
        # Obtener todos los componentes y hooks para buscar referencias
        all_components = await self.db.get_components_by_project(project_id)
        
        # Crear set de hooks usados
        used_hooks = set()
        
        # Buscar en componentes
        for comp in all_components:
            custom_hooks = comp.get('custom_hooks_used', [])
            if custom_hooks:
                used_hooks.update(custom_hooks)
        
        # Buscar en otros hooks
        for hook in all_hooks:
            custom_hooks = hook.get('custom_hooks_used', [])
            if custom_hooks:
                used_hooks.update(custom_hooks)
        
        # Filtrar hooks no usados
        unused_hooks = [
            hook for hook in all_hooks
            if hook['name'] not in used_hooks
        ]
        
        if not unused_hooks:
            return f"✅ All hooks in project '{project_id}' are being used!"
        
        response = f"⚠️ **Unused Hooks in '{project_id}':** ({len(unused_hooks)})\n\n"
        
        for hook in unused_hooks:
            response += f"- **{hook['name']}** (`{hook['file_path']}`)"
            if hook.get('description'):
                response += f" - {hook['description']}"
            response += "\n"
        
        response += f"\n💡 **Recommendation:** Consider removing these hooks or documenting why they exist.\n"
        
        return response
    
    async def get_hook_usage_stats(
        self,
        project_id: Optional[str] = None
    ) -> str:
        """
        Obtiene estadísticas de uso de hooks.
        
        Args:
            project_id: Filtrar por proyecto (opcional)
            
        Returns:
            Estadísticas formateadas
        """
        if project_id:
            components = await self.db.get_components_by_project(project_id)
            hooks = await self.db.get_hooks_by_project(project_id)
        else:
            components = await self.db.get_all_components()
            hooks = await self.db.search_hooks("", None)
        
        # Contar uso de hooks nativos
        native_hook_usage = {}
        for comp in components:
            native_hooks = comp.get('native_hooks_used', [])
            for hook in native_hooks:
                native_hook_usage[hook] = native_hook_usage.get(hook, 0) + 1
        
        # Contar uso de hooks custom
        custom_hook_usage = {}
        for comp in components:
            custom_hooks = comp.get('custom_hooks_used', [])
            for hook in custom_hooks:
                custom_hook_usage[hook] = custom_hook_usage.get(hook, 0) + 1
        
        # También contar en otros hooks
        for hook in hooks:
            custom_hooks = hook.get('custom_hooks_used', [])
            for ch in custom_hooks:
                custom_hook_usage[ch] = custom_hook_usage.get(ch, 0) + 1
        
        response = f"📊 **Hook Usage Statistics**\n\n"
        
        if project_id:
            response += f"**Project:** {project_id}\n\n"
        
        # Hooks nativos más usados
        if native_hook_usage:
            response += "### 🪝 Most Used Native Hooks\n\n"
            sorted_native = sorted(native_hook_usage.items(), key=lambda x: x[1], reverse=True)
            for hook_name, count in sorted_native[:10]:
                response += f"- `{hook_name}`: {count} component(s)\n"
            response += "\n"
        
        # Hooks custom más usados
        if custom_hook_usage:
            response += "### 🎣 Most Used Custom Hooks\n\n"
            sorted_custom = sorted(custom_hook_usage.items(), key=lambda x: x[1], reverse=True)
            for hook_name, count in sorted_custom[:10]:
                response += f"- `{hook_name}`: {count} usage(s)\n"
            response += "\n"
        
        response += f"**Total Components Analyzed:** {len(components)}\n"
        response += f"**Total Custom Hooks:** {len(hooks)}\n"
        
        return response


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

