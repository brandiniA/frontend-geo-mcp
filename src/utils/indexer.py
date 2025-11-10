"""
Indexador de proyectos React desde repositorios remotos.
Clona repositorios, escanea archivos y extrae componentes.
"""

import os
import shutil
from pathlib import Path
from typing import List, Dict, Optional
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
        get_relative_path,
    )
    from utils.feature_flag_parser import FeatureFlagParser
    from utils.feature_flag_detector import FeatureFlagUsageDetector
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
        get_relative_path,
    )
    from src.utils.feature_flag_parser import FeatureFlagParser  # type: ignore
    from src.utils.feature_flag_detector import FeatureFlagUsageDetector  # type: ignore


class ProjectIndexer:
    """Indexador de proyectos React desde repositorios remotos."""
    
    def __init__(self, database_client: DatabaseClient):
        self.db = database_client
        self.parser = ReactParser()
        self.feature_flag_parser = FeatureFlagParser()
        self.feature_flag_detector = FeatureFlagUsageDetector()
        self.temp_dir = os.getenv("TEMP_DIR", "/tmp/mcp-repos")
        
        # Crear directorio temporal si no existe
        Path(self.temp_dir).mkdir(parents=True, exist_ok=True)
    
    async def index_project(self, project_id: str, repo_url: str, branch: str = "main") -> Dict:
        """
        Indexa un proyecto completo desde un repositorio remoto.
        Implementa indexación en múltiples fases:
        0. Indexar feature flags (si existen)
        1. Indexar todos los custom hooks primero
        2. Indexar componentes (separando hooks nativos y custom)
        2.5. Detectar uso de feature flags en componentes
        
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
            # FASE 0: Indexar Feature Flags
            # ============================================
            print(f"🔍 Fase 0: Buscando archivo de feature flags en {project_id}...")
            feature_flags = await self._scan_feature_flags(repo_path)
            
            if feature_flags:
                print(f"✅ Encontrados {len(feature_flags)} feature flags")
                print(f"💾 Guardando {len(feature_flags)} feature flags en BD...")
                await self.db.save_feature_flags(feature_flags, project_id)
                print(f"✅ Guardados {len(feature_flags)} feature flags en BD")
                # Guardar nombres de flags para uso posterior
                flag_names = [f['name'] for f in feature_flags]
            else:
                print(f"⚠️  No se encontró archivo de feature flags en {project_id}")
                flag_names = []
            
            # ============================================
            # FASE 1: Indexar Custom Hooks
            # ============================================
            print(f"🔍 Fase 1: Escaneando custom hooks en {project_id}...")
            hooks = await self._scan_hooks(repo_path)
            
            if hooks:
                print(f"✅ Encontrados {len(hooks)} custom hooks")
                print(f"💾 Guardando {len(hooks)} custom hooks en BD...")
                await self.db.save_hooks(hooks, project_id)
                print(f"✅ Guardados {len(hooks)} hooks en BD")
            else:
                print(f"⚠️  No se encontraron custom hooks en {project_id}")
            
            # ============================================
            # FASE 2: Indexar Componentes
            # ============================================
            print(f"🔍 Fase 2: Escaneando componentes en {project_id}...")
            print(f"   Esto puede tardar unos minutos dependiendo del tamaño del proyecto...")
            components = await self._scan_components(repo_path)
            
            if not components:
                print(f"⚠️  No se encontraron componentes en {project_id}")
                result = {
                    "project_id": project_id,
                    "feature_flags_found": len(feature_flags) if feature_flags else 0,
                    "feature_flags_saved": len(feature_flags) if feature_flags else 0,
                    "hooks_found": len(hooks) if hooks else 0,
                    "hooks_saved": len(hooks) if hooks else 0,
                    "components_found": 0,
                    "components_saved": 0,
                    "status": "no_components"
                }
                # Limpiar repositorio
                await self._cleanup_repo(repo_path)
                return result
            
            print(f"✅ Encontrados {len(components)} componentes")
            # Guardar en base de datos
            print(f"💾 Guardando {len(components)} componentes en BD...")
            await self.db.save_components(components, project_id)
            print(f"✅ Guardados {len(components)} componentes en BD")
            
            # ============================================
            # FASE 2.5: Detectar uso de Feature Flags en Componentes
            # ============================================
            if flag_names:
                print(f"🔍 Fase 2.5: Detectando uso de {len(flag_names)} feature flags en {len(components)} componentes...")
                print(f"   Analizando código de componentes para detectar uso de flags...")
                await self._detect_feature_flag_usage(repo_path, project_id, flag_names)
            
            # ============================================
            # FASE 2.6: Detectar uso de Feature Flags en Hooks
            # ============================================
            if flag_names:
                hooks = await self.db.get_hooks_by_project(project_id)
                if hooks:
                    print(f"🔍 Fase 2.6: Detectando uso de {len(flag_names)} feature flags en {len(hooks)} hooks...")
                    print(f"   Analizando código de hooks para detectar uso de flags...")
                    await self._detect_feature_flag_usage_in_hooks(repo_path, project_id, flag_names)
            
            # ============================================
            # FASE 2.7: Detectar Containers y Feature Flags en Containers
            # ============================================
            print(f"🔍 Fase 2.7: Detectando containers de Redux y feature flags en containers...")
            await self._detect_containers_and_flags(repo_path, project_id, flag_names if flag_names else [])
            
            # Limpiar repositorio clonado
            await self._cleanup_repo(repo_path)
            
            # Resumen final
            print(f"\n{'='*60}")
            print(f"📊 Resumen de indexación para '{project_id}':")
            print(f"{'='*60}")
            print(f"   🚩 Feature Flags: {len(feature_flags) if feature_flags else 0}")
            print(f"   🪝 Custom Hooks: {len(hooks) if hooks else 0}")
            print(f"   ⚛️  Componentes: {len(components)}")
            print(f"{'='*60}\n")
            
            return {
                "project_id": project_id,
                "feature_flags_found": len(feature_flags) if feature_flags else 0,
                "feature_flags_saved": len(feature_flags) if feature_flags else 0,
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
        
        def progress_callback(count: int, current_file: str) -> None:
            """Callback para mostrar progreso."""
            if count == 1:
                print(f"   📄 Procesando archivos... (empezando con {current_file})")
            elif count % 50 == 0:
                print(f"   📄 Procesados {count} archivos... (último: {current_file})")
        
        # Combinar directorios base con los específicos de componentes
        ignore_dirs = BASE_IGNORE_DIRS | COMPONENT_IGNORE_DIRS
        
        return scan_files(
            repo_path=repo_path,
            file_filter=is_component_file,
            ignore_dirs=ignore_dirs,
            process_file=process_component_file,
            progress_callback=progress_callback
        )
    
    async def _scan_feature_flags(self, repo_path: str) -> List[Dict]:
        """Escanea y parsea el archivo de feature flags."""
        # Buscar archivo de feature flags
        flags_file = self.feature_flag_parser.find_feature_flags_file(repo_path)
        
        if not flags_file:
            print(f"   ⚠️  No se encontró archivo defaultFeatures.js en {repo_path}")
            return []
        
        print(f"   ✅ Archivo encontrado: {flags_file}")
        
        # Leer y parsear archivo
        content = read_file_safe(flags_file)
        if not content:
            print(f"   ⚠️  No se pudo leer contenido del archivo: {flags_file}")
            return []
        
        relative_path = get_relative_path(flags_file, repo_path)
        flags = self.feature_flag_parser.extract_feature_flags(content, relative_path)
        
        print(f"   📋 Flags extraídos del archivo: {len(flags)}")
        
        # Mostrar algunos flags extraídos
        if flags:
            print(f"   📝 Primeros 5 flags: {', '.join([f['name'] for f in flags[:5]])}")
        
        # Agregar file_path a cada flag
        for flag in flags:
            flag['file_path'] = relative_path
        
        return flags
    
    async def _detect_feature_flag_usage(
        self, repo_path: str, project_id: str, flag_names: List[str]
    ):
        """Detecta uso de feature flags en componentes ya indexados."""
        # Obtener todos los componentes del proyecto desde BD
        components = await self.db.get_components_by_project(project_id)
        
        if not components:
            print(f"   ⚠️  No hay componentes para analizar")
            return
        
        print(f"   📋 Analizando {len(components)} componentes...")
        
        # Obtener mapeo de nombres de flags a IDs
        print(f"   🔑 Obteniendo IDs de {len(flag_names)} feature flags...")
        flag_id_map = {}
        for idx, flag_name in enumerate(flag_names, 1):
            flag = await self.db.get_feature_flag_by_name(flag_name, project_id)
            if flag:
                flag_id_map[flag_name] = flag['id']
            if idx % 20 == 0:
                print(f"      Procesados {idx}/{len(flag_names)} flags...")
        
        print(f"   ✅ {len(flag_id_map)} flags encontrados en BD")
        
        # Para cada componente, leer archivo y detectar uso de flags
        usage_count = 0
        components_analyzed = 0
        
        for idx, component in enumerate(components, 1):
            component_file = os.path.join(repo_path, component['file_path'])
            
            if not os.path.exists(component_file):
                # Intentar buscar el archivo con diferentes variaciones de path
                # A veces el file_path puede tener diferencias menores
                file_name = os.path.basename(component['file_path'])
                # Buscar recursivamente el archivo por nombre
                found_file = None
                for root, dirs, files in os.walk(repo_path):
                    if file_name in files:
                        found_file = os.path.join(root, file_name)
                        break
                
                if not found_file:
                    continue
                else:
                    component_file = found_file
            
            content = read_file_safe(component_file)
            if not content:
                continue
            
            # Mostrar progreso cada 50 componentes
            if idx % 50 == 0 or idx == 1:
                print(f"   🔍 Analizando componente {idx}/{len(components)}: {component['name']}")
            
            # Detectar flags usados
            detected_usages = self.feature_flag_detector.detect_flag_usage(content, flag_names)
            
            # Guardar relaciones
            for usage in detected_usages:
                flag_name = usage['flag_name']
                if flag_name in flag_id_map:
                    await self.db.save_component_feature_flag_usage(
                        component_id=component['id'],
                        feature_flag_id=flag_id_map[flag_name],
                        usage_pattern=usage.get('pattern'),
                        usage_location='component'  # Explícitamente marcar como uso en componente
                    )
                    usage_count += 1
            
            components_analyzed += 1
        
        print(f"   ✅ Analizados {components_analyzed} componentes")
        if usage_count > 0:
            print(f"✅ Detectado uso de feature flags en {usage_count} relaciones componente-flag")
        else:
            print(f"   ℹ️  No se encontró uso de feature flags en los componentes")
    
    async def _detect_feature_flag_usage_in_hooks(
        self, repo_path: str, project_id: str, flag_names: List[str]
    ):
        """Detecta uso de feature flags en hooks ya indexados."""
        # Obtener todos los hooks del proyecto desde BD
        hooks = await self.db.get_hooks_by_project(project_id)
        
        if not hooks:
            print(f"   ⚠️  No hay hooks para analizar")
            return
        
        print(f"   📋 Analizando {len(hooks)} hooks...")
        
        # Obtener mapeo de nombres de flags a IDs
        print(f"   🔑 Obteniendo IDs de {len(flag_names)} feature flags...")
        flag_id_map = {}
        for idx, flag_name in enumerate(flag_names, 1):
            flag = await self.db.get_feature_flag_by_name(flag_name, project_id)
            if flag:
                flag_id_map[flag_name] = flag['id']
            if idx % 20 == 0:
                print(f"      Procesados {idx}/{len(flag_names)} flags...")
        
        print(f"   ✅ {len(flag_id_map)} flags encontrados en BD")
        
        # Para cada hook, leer archivo y detectar uso de flags
        usage_count = 0
        hooks_analyzed = 0
        
        for idx, hook in enumerate(hooks, 1):
            hook_file = os.path.join(repo_path, hook['file_path'])
            
            if not os.path.exists(hook_file):
                # Intentar buscar el archivo con diferentes variaciones de path
                file_name = os.path.basename(hook['file_path'])
                # Buscar recursivamente el archivo por nombre
                found_file = None
                for root, dirs, files in os.walk(repo_path):
                    if file_name in files:
                        found_file = os.path.join(root, file_name)
                        break
                
                if not found_file:
                    continue
                else:
                    hook_file = found_file
            
            content = read_file_safe(hook_file)
            if not content:
                continue
            
            # Mostrar progreso cada 50 hooks
            if idx % 50 == 0 or idx == 1:
                print(f"   🔍 Analizando hook {idx}/{len(hooks)}: {hook['name']}")
            
            # Detectar flags usados
            detected_usages = self.feature_flag_detector.detect_flag_usage(content, flag_names)
            
            # Guardar relaciones
            for usage in detected_usages:
                flag_name = usage['flag_name']
                if flag_name in flag_id_map:
                    await self.db.save_hook_feature_flag_usage(
                        hook_id=hook['id'],
                        feature_flag_id=flag_id_map[flag_name],
                        usage_pattern=usage.get('pattern')
                    )
                    usage_count += 1
            
            hooks_analyzed += 1
        
        print(f"   ✅ Analizados {hooks_analyzed} hooks")
        if usage_count > 0:
            print(f"✅ Detectado uso de feature flags en {usage_count} relaciones hook-flag")
        else:
            print(f"   ℹ️  No se encontró uso de feature flags en los hooks")
    
    async def _detect_containers_and_flags(
        self, repo_path: str, project_id: str, flag_names: List[str]
    ):
        """
        Detecta containers de Redux, actualiza componentes con container_file_path,
        y detecta feature flags usados en containers asociándolos al componente presentacional.
        """
        # scan_files y read_file_safe ya están importados al inicio del archivo
        
        def is_component_file(filename: str) -> bool:
            """Filtro para archivos de componentes."""
            return filename.endswith(REACT_EXTENSIONS)
        
        # Escanear todos los archivos para detectar containers
        print(f"   📋 Escaneando archivos para detectar containers...")
        ignore_dirs = BASE_IGNORE_DIRS | COMPONENT_IGNORE_DIRS
        
        containers_found = []
        files_scanned = 0
        
        def process_file_for_containers(content: str, relative_path: str) -> List[Dict]:
            """Procesa un archivo para detectar si es container."""
            container_info = self.parser._detect_redox_container(content, relative_path)
            if container_info:
                return [container_info]
            return []
        
        def progress_callback(count: int, current_file: str) -> None:
            """Callback para mostrar progreso."""
            nonlocal files_scanned
            files_scanned = count
            if count % 50 == 0:
                print(f"   📄 Escaneados {count} archivos... (último: {current_file})")
        
        # Escanear archivos
        all_results = scan_files(
            repo_path=repo_path,
            file_filter=is_component_file,
            ignore_dirs=ignore_dirs,
            process_file=process_file_for_containers,
            progress_callback=progress_callback
        )
        
        # all_results ya es una lista de dicts (los containers encontrados)
        containers_found = all_results
        
        if not containers_found:
            print(f"   ℹ️  No se encontraron containers de Redux")
            return
        
        print(f"   ✅ Encontrados {len(containers_found)} containers")
        
        # Obtener mapeo de nombres de flags a IDs si hay flags
        flag_id_map = {}
        if flag_names:
            print(f"   🔑 Obteniendo IDs de {len(flag_names)} feature flags...")
            for idx, flag_name in enumerate(flag_names, 1):
                flag = await self.db.get_feature_flag_by_name(flag_name, project_id)
                if flag:
                    flag_id_map[flag_name] = flag['id']
                if idx % 20 == 0:
                    print(f"      Procesados {idx}/{len(flag_names)} flags...")
            print(f"   ✅ {len(flag_id_map)} flags encontrados en BD")
        
        # Procesar cada container
        containers_processed = 0
        components_updated = 0
        flags_detected = 0
        
        for idx, container_info in enumerate(containers_found, 1):
            container_file_path = container_info['file_path']
            wrapped_component_name = container_info['wrapped_component']
            
            # Buscar componente presentacional en BD
            components = await self.db.search_components(wrapped_component_name, project_id)
            
            # Buscar coincidencia exacta por nombre
            component = None
            for comp in components:
                if comp.get('name') == wrapped_component_name:
                    component = comp
                    break
            
            if not component:
                # Componente no encontrado, puede que no esté indexado aún
                if idx % 10 == 0:
                    print(f"   ⚠️  Container {idx}/{len(containers_found)}: Componente '{wrapped_component_name}' no encontrado en BD")
                continue
            
            # Actualizar componente con container_file_path
            updated = await self.db.update_component_container_file_path(
                wrapped_component_name, project_id, container_file_path
            )
            if updated:
                components_updated += 1
            
            # Detectar feature flags en el container
            if flag_names and flag_id_map:
                container_full_path = os.path.join(repo_path, container_file_path)
                if os.path.exists(container_full_path):
                    content = read_file_safe(container_full_path)
                    if content:
                        # Detectar flags usados
                        detected_usages = self.feature_flag_detector.detect_flag_usage(content, flag_names)
                        
                        # Para cada flag detectado, extraer metadata de contexto
                        for usage in detected_usages:
                            flag_name = usage['flag_name']
                            if flag_name in flag_id_map:
                                # Extraer metadata de contexto
                                context_metadata = self.parser._extract_usage_context(content, flag_name)
                                
                                # Guardar relación con metadata rica
                                await self.db.save_component_feature_flag_usage(
                                    component_id=component['id'],
                                    feature_flag_id=flag_id_map[flag_name],
                                    usage_pattern=usage.get('pattern'),
                                    usage_location='container',
                                    usage_context=context_metadata.get('usage_context'),
                                    container_file_path=container_file_path,
                                    usage_type=context_metadata.get('usage_type'),
                                    combined_with=context_metadata.get('combined_with'),
                                    logic=context_metadata.get('logic')
                                )
                                flags_detected += 1
            
            containers_processed += 1
            if idx % 10 == 0:
                print(f"   🔍 Procesados {idx}/{len(containers_found)} containers...")
        
        print(f"   ✅ Procesados {containers_processed} containers")
        print(f"   ✅ Actualizados {components_updated} componentes con container_file_path")
        if flags_detected > 0:
            print(f"✅ Detectado uso de feature flags en {flags_detected} relaciones container-flag")
        else:
            print(f"   ℹ️  No se encontró uso de feature flags en los containers")
    
    async def _cleanup_repo(self, repo_path: str):
        """Limpia el directorio temporal del repositorio."""
        try:
            if os.path.exists(repo_path):
                shutil.rmtree(repo_path)
                print(f"🧹 Limpiado directorio temporal: {repo_path}")
        except Exception as e:
            print(f"⚠️  Error limpiando {repo_path}: {str(e)}")
