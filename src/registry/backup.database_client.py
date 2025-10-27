"""
Cliente de base de datos para operaciones con PostgreSQL.
Soporta PostgreSQL local y remoto (Supabase, Railway, Render, etc).
"""

import os
import json
import psycopg2
from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()


class DatabaseClient:
    """Cliente genérico para interactuar con PostgreSQL."""
    
    def __init__(self):
        self.database_url = os.getenv("DATABASE_URL")
        if not self.database_url:
            raise ValueError("DATABASE_URL environment variable is required")
        
        self.conn = None
        self._connect()
    
    def _connect(self):
        """Establece conexión con la base de datos."""
        try:
            self.conn = psycopg2.connect(self.database_url)
            self.conn.autocommit = True
            print("✅ Connected to database successfully")
        except Exception as e:
            print(f"❌ Error connecting to database: {e}")
            raise
    
    async def search_components(
        self, 
        query: str, 
        project_id: Optional[str] = None
    ) -> List[Dict]:
        """
        Busca componentes por nombre.
        
        Args:
            query: Término de búsqueda
            project_id: Filtrar por proyecto específico (opcional)
            
        Returns:
            Lista de componentes encontrados
        """
        cursor = self.conn.cursor()
        
        try:
            if project_id:
                sql = """
                    SELECT id, name, project_id, file_path, props, hooks, 
                           imports, exports, component_type, description, jsdoc
                    FROM components
                    WHERE name ILIKE %s AND project_id = %s
                    ORDER BY name
                    LIMIT 20
                """
                cursor.execute(sql, (f'%{query}%', project_id))
            else:
                sql = """
                    SELECT id, name, project_id, file_path, props, hooks, 
                           imports, exports, component_type, description, jsdoc
                    FROM components
                    WHERE name ILIKE %s
                    ORDER BY name
                    LIMIT 20
                """
                cursor.execute(sql, (f'%{query}%',))
            
            rows = cursor.fetchall()
            
            components = []
            for row in rows:
                # Parsear jsdoc si es string
                jsdoc = row[10] if len(row) > 10 else None
                if jsdoc and isinstance(jsdoc, str):
                    try:
                        jsdoc = json.loads(jsdoc)
                    except:
                        jsdoc = None
                
                components.append({
                    'id': row[0],
                    'name': row[1],
                    'project_id': row[2],
                    'file_path': row[3],
                    'props': row[4] if row[4] else [],
                    'hooks': row[5] if row[5] else [],
                    'imports': row[6] if row[6] else [],
                    'exports': row[7] if row[7] else [],
                    'component_type': row[8],
                    'description': row[9],
                    'jsdoc': jsdoc,
                })
            
            return components
            
        finally:
            cursor.close()
    
    async def save_components(self, components: List[Dict], project_id: str):
        """
        Guarda componentes en la base de datos.
        
        Args:
            components: Lista de componentes a guardar
            project_id: ID del proyecto
        """
        if not components:
            return
        
        cursor = self.conn.cursor()
        
        try:
            for component in components:
                # Convertir listas a JSON
                props_json = json.dumps(component.get('props', []))
                hooks_json = json.dumps(component.get('hooks', []))
                imports_json = json.dumps(component.get('imports', []))
                exports_json = json.dumps(component.get('exports', []))
                
                sql = """
                    INSERT INTO components 
                    (name, project_id, file_path, props, hooks, imports, exports, component_type, description)
                    VALUES (%s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s)
                    ON CONFLICT (name, project_id, file_path) 
                    DO UPDATE SET 
                        props = EXCLUDED.props,
                        hooks = EXCLUDED.hooks,
                        imports = EXCLUDED.imports,
                        exports = EXCLUDED.exports,
                        component_type = EXCLUDED.component_type,
                        description = EXCLUDED.description,
                        updated_at = NOW()
                """
                
                cursor.execute(sql, (
                    component['name'],
                    project_id,
                    component['file_path'],
                    props_json,
                    hooks_json,
                    imports_json,
                    exports_json,
                    component.get('component_type', 'component'),
                    component.get('description')
                ))
            
            print(f"✅ Saved {len(components)} components to database")
            
        except Exception as e:
            print(f"❌ Error saving components: {e}")
            raise
        finally:
            cursor.close()
    
    async def get_project(self, project_id: str) -> Optional[Dict]:
        """Obtiene información de un proyecto."""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute(
                "SELECT id, name, repository_url, branch, type, is_active, last_sync FROM projects WHERE id = %s",
                (project_id,)
            )
            row = cursor.fetchone()
            
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'repository_url': row[2],
                    'branch': row[3],
                    'type': row[4],
                    'is_active': row[5],
                    'last_sync': row[6],
                }
            return None
            
        finally:
            cursor.close()
    
    async def list_projects(self) -> List[Dict]:
        """Lista todos los proyectos activos."""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute(
                "SELECT id, name, repository_url, branch, type FROM projects WHERE is_active = true"
            )
            rows = cursor.fetchall()
            
            projects = []
            for row in rows:
                projects.append({
                    'id': row[0],
                    'name': row[1],
                    'repository_url': row[2],
                    'branch': row[3],
                    'type': row[4],
                })
            
            return projects
            
        finally:
            cursor.close()
    
    async def upsert_project(self, project_id: str, project_data: Dict):
        """
        Inserta o actualiza un proyecto.
        
        Args:
            project_id: ID del proyecto
            project_data: Datos del proyecto (name, repository_url, branch, type)
        """
        cursor = self.conn.cursor()
        
        try:
            sql = """
                INSERT INTO projects (id, name, repository_url, branch, type)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (id) 
                DO UPDATE SET 
                    name = EXCLUDED.name,
                    repository_url = EXCLUDED.repository_url,
                    branch = EXCLUDED.branch,
                    type = EXCLUDED.type
            """
            
            cursor.execute(sql, (
                project_id,
                project_data.get('name', project_id),
                project_data['repository_url'],
                project_data.get('branch', 'main'),
                project_data.get('type', 'application')
            ))
            
        finally:
            cursor.close()
    
    async def update_project_sync_time(self, project_id: str):
        """Actualiza el timestamp de última sincronización."""
        cursor = self.conn.cursor()
        
        try:
            cursor.execute(
                "UPDATE projects SET last_sync = NOW() WHERE id = %s",
                (project_id,)
            )
        finally:
            cursor.close()
    
    async def get_component_count(self, project_id: Optional[str] = None) -> int:
        """Obtiene el conteo de componentes."""
        cursor = self.conn.cursor()
        
        try:
            if project_id:
                cursor.execute(
                    "SELECT COUNT(*) FROM components WHERE project_id = %s",
                    (project_id,)
                )
            else:
                cursor.execute("SELECT COUNT(*) FROM components")
            
            return cursor.fetchone()[0]
            
        finally:
            cursor.close()
    
    async def get_components_by_project(self, project_id: str) -> List[Dict]:
        """
        Obtiene todos los componentes de un proyecto específico.
        
        Args:
            project_id: ID del proyecto
            
        Returns:
            Lista de componentes del proyecto
        """
        cursor = self.conn.cursor()
        
        try:
            sql = "SELECT * FROM components WHERE project_id = %s"
            cursor.execute(sql, (project_id,))
            
            columns = [desc[0] for desc in cursor.description]
            components = []
            
            for row in cursor.fetchall():
                component = dict(zip(columns, row))
                # Parsear JSON fields
                component['props'] = json.loads(component.get('props', '[]'))
                component['hooks'] = json.loads(component.get('hooks', '[]'))
                component['imports'] = json.loads(component.get('imports', '[]'))
                component['exports'] = json.loads(component.get('exports', '[]'))
                if component.get('jsdoc'):
                    component['jsdoc'] = json.loads(component['jsdoc'])
                components.append(component)
            
            return components
            
        except Exception as e:
            print(f"❌ Error fetching components by project: {e}")
            return []
        finally:
            cursor.close()
    
    async def get_all_components(self) -> List[Dict]:
        """
        Obtiene todos los componentes indexados.
        
        Returns:
            Lista de todos los componentes
        """
        cursor = self.conn.cursor()
        
        try:
            sql = "SELECT * FROM components"
            cursor.execute(sql)
            
            columns = [desc[0] for desc in cursor.description]
            components = []
            
            for row in cursor.fetchall():
                component = dict(zip(columns, row))
                # Parsear JSON fields
                component['props'] = json.loads(component.get('props', '[]'))
                component['hooks'] = json.loads(component.get('hooks', '[]'))
                component['imports'] = json.loads(component.get('imports', '[]'))
                component['exports'] = json.loads(component.get('exports', '[]'))
                if component.get('jsdoc'):
                    component['jsdoc'] = json.loads(component['jsdoc'])
                components.append(component)
            
            return components
            
        except Exception as e:
            print(f"❌ Error fetching all components: {e}")
            return []
        finally:
            cursor.close()
    
    def close(self):
        """Cierra la conexión."""
        if self.conn:
            self.conn.close()
            print("✅ Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


# Función de utilidad para testing
def test_connection():
    """Prueba la conexión a la base de datos."""
    try:
        client = DatabaseClient()
        print("✅ Database connection test successful!")
        client.close()
        return True
    except Exception as e:
        print(f"❌ Database connection test failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()

