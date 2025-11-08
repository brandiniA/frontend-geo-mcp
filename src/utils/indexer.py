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
    from utils.file_utils import (
        REACT_EXTENSIONS,
        BASE_IGNORE_DIRS,
        COMPONENT_IGNORE_DIRS,
        scan_files,
        read_file_safe,
    )
except ImportError:
    # Si falla, intenta con prefijo src (para ejecución desde scripts)
    from src.utils.parser import ReactParser  # type: ignore
    from src.registry.database_client import DatabaseClient  # type: ignore
    from src.utils.file_utils import (  # type: ignore
        REACT_EXTENSIONS,
        BASE_IGNORE_DIRS,
        COMPONENT_IGNORE_DIRS,
        scan_files,
        read_file_safe,
    )


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
        Implementa indexación en dos fases:
        1. Indexar todos los custom hooks primero
        2. Indexar componentes (separando hooks nativos y custom)
        
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
            
            # ============================================
            # FASE 1: Indexar Custom Hooks
            # ============================================
            print(f"🔍 Fase 1: Escaneando custom hooks en {project_id}...")
            hooks = await self._scan_hooks(repo_path)
            
            if hooks:
                print(f"💾 Guardando {len(hooks)} custom hooks en BD...")
                await self.db.save_hooks(hooks, project_id)
            else:
                print(f"⚠️  No se encontraron custom hooks en {project_id}")
            
            # ============================================
            # FASE 2: Indexar Componentes
            # ============================================
            print(f"🔍 Fase 2: Escaneando componentes en {project_id}...")
            components = await self._scan_components(repo_path)
            
            if not components:
                print(f"⚠️  No se encontraron componentes en {project_id}")
                result = {
                    "project_id": project_id,
                    "hooks_found": len(hooks) if hooks else 0,
                    "hooks_saved": len(hooks) if hooks else 0,
                    "components_found": 0,
                    "components_saved": 0,
                    "status": "no_components"
                }
                # Limpiar repositorio
                await self._cleanup_repo(repo_path)
                return result
            
            # Guardar en base de datos
            print(f"💾 Guardando {len(components)} componentes en BD...")
            await self.db.save_components(components, project_id)
            
            # Limpiar repositorio clonado
            await self._cleanup_repo(repo_path)
            
            return {
                "project_id": project_id,
                "hooks_found": len(hooks) if hooks else 0,
                "hooks_saved": len(hooks) if hooks else 0,
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
    
    async def _scan_hooks(self, repo_path: str) -> List[Dict]:
        """Escanea directorio recursivamente buscando custom hooks.
        
        Optimización: SOLO procesa archivos que empiezan con 'use' (convención de hooks).
        Esto reduce significativamente el tiempo de escaneo.
        """
        def is_hook_file(filename: str) -> bool:
            """Filtro para archivos de hooks."""
            return filename.startswith('use') and filename.endswith(REACT_EXTENSIONS)
        
        def process_hook_file(content: str, relative_path: str) -> List[Dict]:
            """Procesa un archivo de hook."""
            return self.parser.extract_hook_info(content, relative_path)
        
        return scan_files(
            repo_path=repo_path,
            file_filter=is_hook_file,
            ignore_dirs=BASE_IGNORE_DIRS,
            process_file=process_hook_file
        )
    
    async def _scan_components(self, repo_path: str) -> List[Dict]:
        """Escanea directorio recursivamente buscando componentes React."""
        def is_component_file(filename: str) -> bool:
            """Filtro para archivos de componentes."""
            return filename.endswith(REACT_EXTENSIONS)
        
        def process_component_file(content: str, relative_path: str) -> List[Dict]:
            """Procesa un archivo de componente."""
            return self.parser.extract_component_info(content, relative_path)
        
        # Combinar directorios base con los específicos de componentes
        ignore_dirs = BASE_IGNORE_DIRS | COMPONENT_IGNORE_DIRS
        
        return scan_files(
            repo_path=repo_path,
            file_filter=is_component_file,
            ignore_dirs=ignore_dirs,
            process_file=process_component_file
        )
    
    async def _cleanup_repo(self, repo_path: str):
        """Limpia el directorio temporal del repositorio."""
        try:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
                print(f"🧹 Limpiado directorio temporal: {repo_path}")
        except Exception as e:
            print(f"⚠️  Error limpiando {repo_path}: {str(e)}")
