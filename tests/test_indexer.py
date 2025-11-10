"""
Tests para ProjectIndexer (indexer.py).
"""

import pytest
import os
import tempfile
import shutil
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from pathlib import Path
from src.utils.indexer import ProjectIndexer


class TestProjectIndexer:
    """Tests para ProjectIndexer."""
    
    @pytest.fixture
    def mock_db_client(self):
        """Fixture para DatabaseClient mock."""
        db = Mock()
        db.save_hooks = AsyncMock(return_value=5)
        db.save_components = AsyncMock(return_value=10)
        db.save_feature_flags = AsyncMock(return_value=3)
        db.resolve_all_dependencies = AsyncMock(return_value=10)
        db.get_components_by_project = AsyncMock(return_value=[
            {'id': 1, 'name': 'Button', 'file_path': 'src/components/Button.jsx'},
            {'id': 2, 'name': 'Footer', 'file_path': 'src/components/Footer.jsx'},
        ])
        db.get_hooks_by_project = AsyncMock(return_value=[])
        db.get_feature_flag_by_name = AsyncMock(return_value={'id': 1, 'name': 'SHOW_FOOTER'})
        db.save_component_feature_flag_usage = AsyncMock()
        db.save_hook_feature_flag_usage = AsyncMock()
        db.search_components = AsyncMock(return_value=[])
        db.update_component_container_file_path = AsyncMock(return_value=True)
        # Nuevos métodos para barrel exports
        db.barrel_exports = Mock()
        db.barrel_exports.save_barrel_exports = AsyncMock(return_value=0)
        db.upsert_project = AsyncMock()
        return db
    
    @pytest.fixture
    def indexer(self, mock_db_client):
        """Fixture para ProjectIndexer."""
        with patch.dict(os.environ, {'TEMP_DIR': '/tmp/test-mcp-repos'}):
            return ProjectIndexer(mock_db_client)
    
    @pytest.fixture
    def temp_repo(self):
        """Fixture para crear un repositorio temporal."""
        temp_dir = tempfile.mkdtemp()
        repo_path = os.path.join(temp_dir, 'test-repo')
        os.makedirs(repo_path, exist_ok=True)
        
        # Crear estructura de directorios
        os.makedirs(os.path.join(repo_path, 'src', 'components'), exist_ok=True)
        os.makedirs(os.path.join(repo_path, 'src', 'hooks'), exist_ok=True)
        
        yield repo_path
        
        # Limpiar
        shutil.rmtree(temp_dir)
    
    def test_init(self, mock_db_client):
        """Test inicialización."""
        with patch.dict(os.environ, {'TEMP_DIR': '/tmp/test-mcp-repos'}):
            indexer = ProjectIndexer(mock_db_client)
            
            assert indexer.db == mock_db_client
            assert indexer.temp_dir == '/tmp/test-mcp-repos'
            assert indexer.parser is not None
    
    @pytest.mark.asyncio
    async def test_cleanup_repo(self, indexer, temp_repo):
        """Test limpieza de repositorio."""
        # Crear un archivo en el repo
        test_file = os.path.join(temp_repo, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        
        assert os.path.exists(temp_repo)
        
        await indexer._cleanup_repo(temp_repo)
        
        assert not os.path.exists(temp_repo)
    
    @pytest.mark.asyncio
    async def test_cleanup_repo_nonexistent(self, indexer):
        """Test limpieza de repositorio inexistente."""
        # No debería lanzar error
        await indexer._cleanup_repo('/nonexistent/path')
    
    @pytest.mark.asyncio
    async def test_scan_components_empty(self, indexer, temp_repo):
        """Test escaneo de componentes en directorio vacío."""
        result = await indexer._scan_components(temp_repo)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_scan_components_with_file(self, indexer, temp_repo):
        """Test escaneo de componentes con archivo."""
        component_file = os.path.join(temp_repo, 'src', 'components', 'Button.jsx')
        os.makedirs(os.path.dirname(component_file), exist_ok=True)
        
        with open(component_file, 'w') as f:
            f.write("""
            export function Button({ onClick, text }) {
                return <button onClick={onClick}>{text}</button>;
            }
            """)
        
        result = await indexer._scan_components(temp_repo)
        
        assert len(result) > 0
        assert any(c['name'] == 'Button' for c in result)
    
    @pytest.mark.asyncio
    async def test_scan_components_ignores_node_modules(self, indexer, temp_repo):
        """Test que ignora node_modules."""
        # Crear archivo en node_modules
        node_modules_path = os.path.join(temp_repo, 'node_modules', 'package', 'Component.jsx')
        os.makedirs(os.path.dirname(node_modules_path), exist_ok=True)
        
        with open(node_modules_path, 'w') as f:
            f.write("export function Component() { return <div />; }")
        
        result = await indexer._scan_components(temp_repo)
        
        # No debería encontrar el componente en node_modules
        assert not any('node_modules' in c['file_path'] for c in result)
    
    @pytest.mark.asyncio
    async def test_scan_hooks_empty(self, indexer, temp_repo):
        """Test escaneo de hooks en directorio vacío."""
        result = await indexer._scan_hooks(temp_repo)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_scan_hooks_with_file(self, indexer, temp_repo):
        """Test escaneo de hooks con archivo."""
        hook_file = os.path.join(temp_repo, 'src', 'hooks', 'useAuth.js')
        os.makedirs(os.path.dirname(hook_file), exist_ok=True)
        
        with open(hook_file, 'w') as f:
            f.write("""
            export function useAuth() {
                const [user, setUser] = useState(null);
                return { user, setUser };
            }
            """)
        
        result = await indexer._scan_hooks(temp_repo)
        
        assert len(result) > 0
        assert any(h['name'] == 'useAuth' for h in result)
    
    @pytest.mark.asyncio
    async def test_scan_hooks_only_starts_with_use(self, indexer, temp_repo):
        """Test que solo escanea archivos que empiezan con 'use'."""
        # Crear archivo que NO empieza con 'use'
        other_file = os.path.join(temp_repo, 'src', 'hooks', 'auth.js')
        os.makedirs(os.path.dirname(other_file), exist_ok=True)
        
        with open(other_file, 'w') as f:
            f.write("export function useAuth() { return {}; }")
        
        result = await indexer._scan_hooks(temp_repo)
        
        # No debería encontrar nada porque el archivo no empieza con 'use'
        assert len(result) == 0
    
    @pytest.mark.asyncio
    @patch('src.utils.indexer.git.Repo')
    async def test_clone_repo(self, mock_git_repo, indexer):
        """Test clonado de repositorio."""
        mock_repo_instance = Mock()
        mock_git_repo.clone_from.return_value = mock_repo_instance
        
        repo_path = await indexer._clone_repo(
            'https://github.com/test/repo',
            'test-project',
            'main'
        )
        
        assert repo_path == os.path.join(indexer.temp_dir, 'test-project')
        mock_git_repo.clone_from.assert_called_once()
    
    @pytest.mark.asyncio
    @patch('src.utils.indexer.git.Repo')
    async def test_clone_repo_cleans_existing(self, mock_git_repo, indexer):
        """Test que limpia repositorio existente antes de clonar."""
        # Asegurar que el directorio temporal existe
        os.makedirs(indexer.temp_dir, exist_ok=True)
        
        repo_path = os.path.join(indexer.temp_dir, 'test-project')
        os.makedirs(repo_path, exist_ok=True)
        
        # Crear archivo para verificar que se limpia
        test_file = os.path.join(repo_path, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        
        mock_repo_instance = Mock()
        mock_git_repo.clone_from.return_value = mock_repo_instance
        
        result_path = await indexer._clone_repo(
            'https://github.com/test/repo',
            'test-project',
            'main'
        )
        
        # Verificar que se retorna el path correcto
        assert result_path == repo_path
        # El archivo test.txt debería haber sido eliminado antes del clone
        # (aunque el mock no crea realmente el directorio)
    
    @pytest.mark.asyncio
    @patch('src.utils.indexer.git.Repo')
    async def test_clone_repo_error(self, mock_git_repo, indexer):
        """Test manejo de error al clonar."""
        mock_git_repo.clone_from.side_effect = Exception("Clone failed")
        
        with pytest.raises(Exception) as exc_info:
            await indexer._clone_repo(
                'https://github.com/test/repo',
                'test-project',
                'main'
            )
        
        assert "Failed to clone repository" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('src.utils.indexer.detect_project_aliases')
    @patch.object(ProjectIndexer, '_scan_barrel_exports')
    @patch.object(ProjectIndexer, '_clone_repo')
    @patch.object(ProjectIndexer, '_scan_hooks')
    @patch.object(ProjectIndexer, '_scan_components')
    @patch.object(ProjectIndexer, '_cleanup_repo')
    async def test_index_project_success(
        self,
        mock_cleanup,
        mock_scan_components,
        mock_scan_hooks,
        mock_clone,
        mock_scan_barrel_exports,
        mock_detect_aliases,
        indexer,
        mock_db_client
    ):
        """Test indexación exitosa de proyecto."""
        mock_clone.return_value = '/tmp/test-repo'
        mock_detect_aliases.return_value = {}
        mock_scan_barrel_exports.return_value = []
        mock_scan_hooks.return_value = [
            {'name': 'useAuth', 'file_path': 'hooks/useAuth.js'}
        ]
        mock_scan_components.return_value = [
            {'name': 'Button', 'file_path': 'components/Button.jsx'}
        ]
        
        result = await indexer.index_project(
            'test-project',
            'https://github.com/test/repo',
            'main'
        )
        
        assert result['status'] == 'success'
        assert result['hooks_found'] == 1
        assert result['components_found'] == 1
        assert result['components_saved'] == 1
        mock_db_client.save_hooks.assert_called_once()
        mock_db_client.save_components.assert_called_once()
        mock_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    @patch.object(ProjectIndexer, '_clone_repo')
    @patch.object(ProjectIndexer, '_scan_hooks')
    @patch.object(ProjectIndexer, '_scan_components')
    @patch.object(ProjectIndexer, '_cleanup_repo')
    async def test_index_project_no_components(
        self,
        mock_cleanup,
        mock_scan_components,
        mock_scan_hooks,
        mock_clone,
        indexer
    ):
        """Test indexación sin componentes."""
        mock_clone.return_value = '/tmp/test-repo'
        mock_scan_hooks.return_value = []
        mock_scan_components.return_value = []
        
        result = await indexer.index_project(
            'test-project',
            'https://github.com/test/repo',
            'main'
        )
        
        assert result['status'] == 'no_components'
        assert result['components_found'] == 0
        mock_cleanup.assert_called_once()
    
    @pytest.mark.asyncio
    @patch.object(ProjectIndexer, '_clone_repo')
    async def test_index_project_clone_error(self, mock_clone, indexer):
        """Test manejo de error al clonar."""
        mock_clone.side_effect = Exception("Clone failed")
        
        result = await indexer.index_project(
            'test-project',
            'https://github.com/test/repo',
            'main'
        )
        
        assert result['status'] == 'failed'
        assert 'error' in result
    
    @pytest.mark.asyncio
    async def test_scan_feature_flags_found(self, indexer, temp_repo):
        """Test escaneo de feature flags cuando se encuentra el archivo."""
        # Crear directorio config
        config_dir = os.path.join(temp_repo, 'config')
        os.makedirs(config_dir, exist_ok=True)
        
        # Crear archivo defaultFeatures.js
        flags_file = os.path.join(config_dir, 'defaultFeatures.js')
        with open(flags_file, 'w') as f:
            f.write("""
            const defaultFeatures = {
              SHOW_FOOTER: true, // If true, shows the footer
              ENABLE_DARK_MODE: false,
              MAX_ITEMS: 10,
            };
            
            export default defaultFeatures;
            """)
        
        result = await indexer._scan_feature_flags(temp_repo)
        
        assert len(result) == 3
        assert result[0]['name'] == 'SHOW_FOOTER'
        assert result[0]['default_value'] is True
        assert result[0]['description'] == 'If true, shows the footer'
        assert result[0]['file_path'] == 'config/defaultFeatures.js'
    
    @pytest.mark.asyncio
    async def test_scan_feature_flags_not_found(self, indexer, temp_repo):
        """Test escaneo de feature flags cuando NO se encuentra el archivo."""
        result = await indexer._scan_feature_flags(temp_repo)
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_detect_feature_flag_usage(self, indexer, temp_repo, mock_db_client):
        """Test detección de uso de feature flags en componentes."""
        # Crear componente que usa feature flags
        component_file = os.path.join(temp_repo, 'src', 'components', 'Footer.jsx')
        os.makedirs(os.path.dirname(component_file), exist_ok=True)
        
        with open(component_file, 'w') as f:
            f.write("""
            import useWhitelabelFeatures from '../hooks/useWhitelabelFeatures';
            
            const Footer = () => {
              const { SHOW_FOOTER } = useWhitelabelFeatures();
              
              if (SHOW_FOOTER) {
                return <footer>Footer</footer>;
              }
              
              return null;
            };
            """)
        
        flag_names = ['SHOW_FOOTER', 'ENABLE_DARK_MODE']
        
        await indexer._detect_feature_flag_usage(temp_repo, 'test-project', flag_names)
        
        # Verificar que se llamó save_component_feature_flag_usage
        assert mock_db_client.save_component_feature_flag_usage.called
    
    @pytest.mark.asyncio
    @patch('src.utils.indexer.detect_project_aliases')
    @patch.object(ProjectIndexer, '_scan_barrel_exports')
    @patch.object(ProjectIndexer, '_clone_repo')
    @patch.object(ProjectIndexer, '_scan_feature_flags')
    @patch.object(ProjectIndexer, '_scan_hooks')
    @patch.object(ProjectIndexer, '_scan_components')
    @patch.object(ProjectIndexer, '_detect_feature_flag_usage')
    @patch.object(ProjectIndexer, '_cleanup_repo')
    async def test_index_project_with_feature_flags(
        self,
        mock_cleanup,
        mock_detect_flags,
        mock_scan_components,
        mock_scan_hooks,
        mock_scan_feature_flags,
        mock_clone,
        mock_scan_barrel_exports,
        mock_detect_aliases,
        indexer,
        mock_db_client
    ):
        """Test indexación completa con feature flags."""
        mock_clone.return_value = '/tmp/test-repo'
        mock_detect_aliases.return_value = {}
        mock_scan_barrel_exports.return_value = []
        mock_scan_feature_flags.return_value = [
            {'name': 'SHOW_FOOTER', 'file_path': 'config/defaultFeatures.js', 'default_value': True}
        ]
        mock_scan_hooks.return_value = []
        mock_scan_components.return_value = [
            {'name': 'Button', 'file_path': 'components/Button.jsx'}
        ]
        
        result = await indexer.index_project(
            'test-project',
            'https://github.com/test/repo',
            'main'
        )
        
        assert result['status'] == 'success'
        assert result['feature_flags_found'] == 1
        assert result['feature_flags_saved'] == 1
        mock_db_client.save_feature_flags.assert_called_once()
        mock_detect_flags.assert_called_once()
        mock_cleanup.assert_called_once()

