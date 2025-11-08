"""
Tests para utilidades de archivos (file_utils).
"""

import pytest
import os
import tempfile
import shutil
from src.utils.file_utils import (
    REACT_EXTENSIONS,
    BASE_IGNORE_DIRS,
    COMPONENT_IGNORE_DIRS,
    filter_ignore_dirs,
    read_file_safe,
    get_relative_path,
    get_file_name_without_ext,
    scan_files,
)


class TestFileUtils:
    """Tests para utilidades de archivos."""
    
    def test_react_extensions(self):
        """Test que REACT_EXTENSIONS contiene las extensiones correctas."""
        assert '.tsx' in REACT_EXTENSIONS
        assert '.ts' in REACT_EXTENSIONS
        assert '.jsx' in REACT_EXTENSIONS
        assert '.js' in REACT_EXTENSIONS
    
    def test_base_ignore_dirs(self):
        """Test que BASE_IGNORE_DIRS contiene directorios comunes."""
        assert 'node_modules' in BASE_IGNORE_DIRS
        assert '.git' in BASE_IGNORE_DIRS
        assert 'dist' in BASE_IGNORE_DIRS
    
    def test_component_ignore_dirs(self):
        """Test que COMPONENT_IGNORE_DIRS contiene directorios adicionales."""
        assert 'tests' in COMPONENT_IGNORE_DIRS
        assert 'types' in COMPONENT_IGNORE_DIRS
        assert 'assets' in COMPONENT_IGNORE_DIRS
    
    def test_filter_ignore_dirs(self):
        """Test filtrado de directorios ignorados."""
        dirs = ['src', 'node_modules', '.git', 'components', 'dist']
        filter_ignore_dirs(dirs, BASE_IGNORE_DIRS)
        
        assert 'src' in dirs
        assert 'components' in dirs
        assert 'node_modules' not in dirs
        assert '.git' not in dirs
        assert 'dist' not in dirs
    
    def test_filter_ignore_dirs_dot_prefix(self):
        """Test que filtra directorios que empiezan con punto."""
        dirs = ['src', '.next', '.storybook', 'components']
        filter_ignore_dirs(dirs, set())
        
        assert 'src' in dirs
        assert 'components' in dirs
        assert '.next' not in dirs
        assert '.storybook' not in dirs
    
    def test_read_file_safe_success(self):
        """Test lectura exitosa de archivo."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write('test content')
            temp_path = f.name
        
        try:
            content = read_file_safe(temp_path)
            assert content == 'test content'
        finally:
            os.unlink(temp_path)
    
    def test_read_file_safe_nonexistent(self):
        """Test lectura de archivo inexistente."""
        content = read_file_safe('/nonexistent/file.txt')
        assert content is None
    
    def test_get_relative_path(self):
        """Test obtención de ruta relativa."""
        result = get_relative_path('/tmp/repo/src/components/Button.jsx', '/tmp/repo')
        assert result == 'src/components/Button.jsx'
    
    def test_get_relative_path_same_level(self):
        """Test ruta relativa al mismo nivel."""
        result = get_relative_path('/tmp/repo/Button.jsx', '/tmp/repo')
        assert result == 'Button.jsx'
    
    def test_get_file_name_without_ext(self):
        """Test obtención de nombre sin extensión."""
        result = get_file_name_without_ext('hooks/useAuth.ts')
        assert result == 'useAuth'
    
    def test_get_file_name_without_ext_complex(self):
        """Test con ruta compleja."""
        result = get_file_name_without_ext('src/components/Button.jsx')
        assert result == 'Button'
    
    def test_get_file_name_without_ext_no_ext(self):
        """Test sin extensión."""
        result = get_file_name_without_ext('README')
        assert result == 'README'


class TestScanFiles:
    """Tests para scan_files."""
    
    @pytest.fixture
    def temp_repo(self):
        """Fixture para crear repositorio temporal."""
        temp_dir = tempfile.mkdtemp()
        repo_path = os.path.join(temp_dir, 'test-repo')
        os.makedirs(repo_path, exist_ok=True)
        
        # Crear estructura
        os.makedirs(os.path.join(repo_path, 'src', 'components'), exist_ok=True)
        os.makedirs(os.path.join(repo_path, 'src', 'hooks'), exist_ok=True)
        os.makedirs(os.path.join(repo_path, 'node_modules'), exist_ok=True)
        
        yield repo_path
        
        shutil.rmtree(temp_dir)
    
    def test_scan_files_with_filter(self, temp_repo):
        """Test escaneo con filtro de archivos."""
        # Crear archivos
        component_file = os.path.join(temp_repo, 'src', 'components', 'Button.jsx')
        hook_file = os.path.join(temp_repo, 'src', 'hooks', 'useAuth.js')
        
        with open(component_file, 'w') as f:
            f.write('export function Button() {}')
        with open(hook_file, 'w') as f:
            f.write('export function useAuth() {}')
        
        def is_hook_file(filename: str) -> bool:
            return filename.startswith('use') and filename.endswith(REACT_EXTENSIONS)
        
        results = scan_files(temp_repo, file_filter=is_hook_file)
        
        # Debe encontrar solo el hook
        assert len(results) == 1
        assert 'useAuth.js' in results[0] or 'hooks/useAuth.js' in results[0]
    
    def test_scan_files_ignores_node_modules(self, temp_repo):
        """Test que ignora node_modules."""
        # Crear archivo en node_modules
        nm_file = os.path.join(temp_repo, 'node_modules', 'package', 'Component.jsx')
        os.makedirs(os.path.dirname(nm_file), exist_ok=True)
        
        with open(nm_file, 'w') as f:
            f.write('export function Component() {}')
        
        def is_component_file(filename: str) -> bool:
            return filename.endswith(REACT_EXTENSIONS)
        
        results = scan_files(temp_repo, file_filter=is_component_file)
        
        # No debe encontrar el archivo en node_modules
        assert not any('node_modules' in str(r) for r in results)
    
    def test_scan_files_with_process_file(self, temp_repo):
        """Test escaneo con función de procesamiento."""
        component_file = os.path.join(temp_repo, 'src', 'components', 'Button.jsx')
        
        with open(component_file, 'w') as f:
            f.write('export function Button() {}')
        
        def is_component_file(filename: str) -> bool:
            return filename.endswith(REACT_EXTENSIONS)
        
        def process_file(content: str, relative_path: str):
            return [{'name': 'Button', 'path': relative_path}]
        
        results = scan_files(
            temp_repo,
            file_filter=is_component_file,
            process_file=process_file
        )
        
        assert len(results) == 1
        assert results[0]['name'] == 'Button'
    
    def test_scan_files_empty_repo(self, temp_repo):
        """Test escaneo de repositorio vacío."""
        def is_component_file(filename: str) -> bool:
            return filename.endswith(REACT_EXTENSIONS)
        
        results = scan_files(temp_repo, file_filter=is_component_file)
        
        assert results == []

