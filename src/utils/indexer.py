"""
Indexador de proyectos React desde repositorios remotos.
Clona repositorios, escanea archivos y extrae componentes.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict
import git
from utils.parser import ReactParser
from registry.database_client import DatabaseClient


class ProjectIndexer:
    """Indexador de proyectos React desde repositorios remotos."""
    
    def __init__(self, database_client: DatabaseClient):
        self.db = database_client
        self.parser = ReactParser()
        self.temp_dir = os.getenv("TEMP_DIR", "/tmp/mcp-repos")
        
        # Crear directorio temporal si no existe
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
        
        # Directorios a excluir del escaneo
        self.exclude_dirs = {
            'node_modules', 
            '.git', 
            'dist', 
            'build', 
            '.next', 
            'out',
            'coverage',
            '.cache',
            'public',
            'static',
        }
        
        # Extensiones de archivos React
        self.react_extensions = {'.tsx', '.jsx'}
    
    async def index_remote_repository(
        self, 
        project_id: str, 
        repo_url: str, 
        branch: str = "main"
    ):
        """
        Clona e indexa un repositorio remoto.
        
        Args:
            project_id: ID del proyecto
            repo_url: URL del repositorio
            branch: Rama a clonar
        """
        print(f"\n🔄 Indexing project: {project_id}")
        print(f"📍 Repository: {repo_url}")
        print(f"🌿 Branch: {branch}")
        
        # Preparar directorio de clonado
        repo_path = Path(self.temp_dir) / project_id
        
        # Limpiar si existe
        if repo_path.exists():
            print(f"🧹 Cleaning existing directory...")
            shutil.rmtree(repo_path)
        
        try:
            # Clonar repositorio (shallow clone para velocidad)
            print(f"📥 Cloning repository...")
            
            # Configurar opciones de clonado
            clone_options = {
                'depth': 1,
                'branch': branch,
                'single_branch': True,
            }
            
            # Agregar token de GitHub si está disponible
            github_token = os.getenv("GITHUB_TOKEN")
            if github_token and 'github.com' in repo_url:
                # Insertar token en la URL
                if repo_url.startswith('https://'):
                    repo_url = repo_url.replace(
                        'https://', 
                        f'https://{github_token}@'
                    )
            
            git.Repo.clone_from(repo_url, repo_path, **clone_options)
            print(f"✅ Repository cloned successfully")
            
            # Escanear archivos React
            print(f"🔍 Scanning React files...")
            components = await self._scan_directory(repo_path, project_id)
            
            if not components:
                print(f"⚠️  No components found in repository")
                return
            
            # Guardar en database
            print(f"💾 Saving {len(components)} components to database...")
            await self.db.save_components(components, project_id)
            
            # Actualizar timestamp de sincronización
            await self.db.update_project_sync_time(project_id)
            
            print(f"✅ Indexing complete! Found {len(components)} components")
            
        except git.GitCommandError as e:
            print(f"❌ Git error: {e}")
            raise Exception(f"Failed to clone repository: {e}")
        except Exception as e:
            print(f"❌ Error during indexing: {e}")
            raise
        finally:
            # Limpiar directorio temporal
            if repo_path.exists():
                print(f"🧹 Cleaning up temporary files...")
                shutil.rmtree(repo_path)
    
    async def _scan_directory(self, directory: Path, project_id: str) -> List[Dict]:
        """
        Escanea un directorio recursivamente en busca de archivos React.
        
        Args:
            directory: Directorio a escanear
            project_id: ID del proyecto
            
        Returns:
            Lista de componentes encontrados
        """
        components = []
        files_scanned = 0
        
        # Buscar archivos .tsx y .jsx
        for file_path in directory.rglob('*'):
            # Verificar si está en directorio excluido
            if any(excluded in file_path.parts for excluded in self.exclude_dirs):
                continue
            
            # Solo archivos React
            if file_path.suffix not in self.react_extensions:
                continue
            
            files_scanned += 1
            
            try:
                content = file_path.read_text(encoding='utf-8')
                
                # Extraer componentes
                relative_path = str(file_path.relative_to(directory))
                file_components = self.parser.extract_component_info(
                    content,
                    relative_path
                )
                
                if file_components:
                    components.extend(file_components)
                    print(f"  ✓ {relative_path}: {len(file_components)} component(s)")
                
            except UnicodeDecodeError:
                print(f"  ⚠️  Skipping {file_path}: encoding error")
            except Exception as e:
                print(f"  ⚠️  Error parsing {file_path}: {e}")
        
        print(f"\n📊 Scan summary:")
        print(f"   Files scanned: {files_scanned}")
        print(f"   Components found: {len(components)}")
        
        return components
    
    async def reindex_project(self, project_id: str):
        """
        Re-indexa un proyecto existente.
        
        Args:
            project_id: ID del proyecto
        """
        # Obtener información del proyecto
        project = await self.db.get_project(project_id)
        
        if not project:
            raise ValueError(f"Project '{project_id}' not found in database")
        
        # Indexar
        await self.index_remote_repository(
            project_id,
            project['repository_url'],
            project['branch']
        )
    
    async def index_local_directory(self, directory: str, project_id: str):
        """
        Indexa un directorio local (útil para testing).
        
        Args:
            directory: Ruta al directorio
            project_id: ID del proyecto
        """
        print(f"\n🔄 Indexing local directory: {directory}")
        
        dir_path = Path(directory)
        if not dir_path.exists():
            raise ValueError(f"Directory not found: {directory}")
        
        # Escanear directorio
        print(f"🔍 Scanning React files...")
        components = await self._scan_directory(dir_path, project_id)
        
        if not components:
            print(f"⚠️  No components found")
            return
        
        # Guardar en database
        print(f"💾 Saving {len(components)} components to database...")
        await self.db.save_components(components, project_id)
        
        # Actualizar timestamp
        await self.db.update_project_sync_time(project_id)
        
        print(f"✅ Indexing complete! Found {len(components)} components")


# Función de utilidad para testing
async def test_indexer():
    """Prueba el indexador con un proyecto de ejemplo."""
    from dotenv import load_dotenv
    load_dotenv()
    
    db = DatabaseClient()
    indexer = ProjectIndexer(db)
    
    # Proyecto de prueba (React oficial)
    test_project = {
        'id': 'react-examples',
        'repository': 'https://github.com/facebook/react',
        'branch': 'main'
    }
    
    try:
        await indexer.index_remote_repository(
            test_project['id'],
            test_project['repository'],
            test_project['branch']
        )
    finally:
        db.close()


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_indexer())

