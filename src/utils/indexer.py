"""
Indexador de proyectos React desde repositorios remotos.
Clona repositorios, escanea archivos y extrae componentes.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict
import git

# Importar con fallback para diferentes contextos de ejecución
try:
    from utils.parser import ReactParser
    from registry.database_client import DatabaseClient
except ImportError:
    # Si falla, intenta con prefijo src (para ejecución desde scripts)
    from src.utils.parser import ReactParser  # type: ignore
    from src.registry.database_client import DatabaseClient  # type: ignore


class ProjectIndexer:
    """Indexador de proyectos React desde repositorios remotos."""
    
    def __init__(self, database_client: DatabaseClient):
        self.db = database_client
        self.parser = ReactParser()
        self.temp_dir = os.getenv("TEMP_DIR", "/tmp/mcp-repos")
        
        # Crear directorio temporal si no existe
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
    
    async def index_project(self, project_id: str, repo_url: str, branch: str = "main") -> Dict:
        """
        Indexa un proyecto completo desde un repositorio remoto.
        
        Args:
            project_id: ID único del proyecto
            repo_url: URL del repositorio Git
            branch: Rama a indexar (default: main)
            
        Returns:
            Dict con estadísticas de indexación
        """
        try:
            # Clonar repositorio
            print(f"📥 Clonando {repo_url}...")
            repo_path = await self._clone_repo(repo_url, project_id, branch)
            
            # Escanear componentes
            print(f"🔍 Escaneando componentes en {project_id}...")
            components = await self._scan_components(repo_path)
            
            if not components:
                print(f"⚠️  No se encontraron componentes en {project_id}")
                return {
                    "project_id": project_id,
                    "components_found": 0,
                    "components_saved": 0,
                    "status": "no_components"
                }
            
            # Guardar en base de datos
            print(f"💾 Guardando {len(components)} componentes en BD...")
            await self.db.save_components(components, project_id)
            
            # Limpiar repositorio clonado
            await self._cleanup_repo(repo_path)
            
            return {
                "project_id": project_id,
                "components_found": len(components),
                "components_saved": len(components),
                "status": "success"
            }
            
        except Exception as e:
            print(f"❌ Error indexando {project_id}: {str(e)}")
            return {
                "project_id": project_id,
                "error": str(e),
                "status": "failed"
            }
    
    async def _clone_repo(self, repo_url: str, project_id: str, branch: str) -> str:
        """Clona un repositorio Git."""
        repo_path = os.path.join(self.temp_dir, project_id)
        
        # Limpiar si existe
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path)
        
        try:
            git.Repo.clone_from(repo_url, repo_path, branch=branch)
            return repo_path
        except Exception as e:
            raise Exception(f"Failed to clone repository: {str(e)}")
    
    async def _scan_components(self, repo_path: str) -> List[Dict]:
        """Escanea directorio recursivamente buscando componentes React."""
        components = []
        
        # Patrones de archivos a buscar
        extensions = ('.tsx', '.ts', '.jsx', '.js')
        
        # Directorios a ignorar
        ignore_dirs = {'node_modules', '.git', '.next', 'dist', 'build', '.venv', 'venv'}
        
        for root, dirs, files in os.walk(repo_path):
            # Filtrar directorios ignorados
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]
            
            for file in files:
                if file.endswith(extensions):
                    file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(file_path, repo_path)
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            
                            # Parsear componentes
                            parsed = self.parser.extract_component_info(content, relative_path)
                            components.extend(parsed)
                    
                    except Exception as e:
                        print(f"⚠️  Error procesando {relative_path}: {str(e)}")
                        continue
        
        return components
    
    async def _cleanup_repo(self, repo_path: str):
        """Limpia el directorio temporal del repositorio."""
        try:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
                print(f"🧹 Limpiado directorio temporal: {repo_path}")
        except Exception as e:
            print(f"⚠️  Error limpiando {repo_path}: {str(e)}")
