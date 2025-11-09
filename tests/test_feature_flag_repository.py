"""
Tests para FeatureFlagRepository.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.registry.repositories.feature_flag_repository import FeatureFlagRepository
from src.models import FeatureFlag, ComponentFeatureFlag, Component


class TestFeatureFlagRepository:
    """Tests para FeatureFlagRepository."""
    
    @pytest.fixture
    def mock_session_factory(self):
        """Fixture para session factory mock."""
        session = Mock()
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        session.rollback = Mock()
        session.close = Mock()
        
        factory = Mock()
        factory.return_value = session
        return factory
    
    @pytest.fixture
    def feature_flag_repo(self, mock_session_factory):
        """Fixture para FeatureFlagRepository."""
        return FeatureFlagRepository(mock_session_factory)
    
    @pytest.fixture
    def sample_flags(self):
        """Fixture para flags de ejemplo."""
        return [
            {
                'name': 'SHOW_FOOTER',
                'file_path': 'config/defaultFeatures.js',
                'default_value': True,
                'value_type': 'boolean',
                'description': 'If true, shows the footer',
                'possible_values': [],
            },
            {
                'name': 'FUNNEL_STYLE',
                'file_path': 'config/defaultFeatures.js',
                'default_value': 'CLASSIC',
                'value_type': 'string',
                'description': 'Funnel style',
                'possible_values': ['CLASSIC', 'FLAT'],
            },
        ]
    
    @pytest.mark.asyncio
    async def test_save_feature_flags(self, feature_flag_repo, mock_session_factory, sample_flags):
        """Test para guardar feature flags."""
        session = mock_session_factory()
        session.query.return_value.filter.return_value.first.return_value = None
        
        with patch('src.registry.repositories.feature_flag_repository.safe_upsert') as mock_upsert:
            result = await feature_flag_repo.save(sample_flags, 'test-project')
            
            assert result == 2
            assert mock_upsert.call_count == 2
            # Verificar que file_path se pasa correctamente
            call_args = mock_upsert.call_args_list[0]
            assert 'file_path' in call_args[1]['data']
            assert call_args[1]['data']['file_path'] == 'config/defaultFeatures.js'
    
    @pytest.mark.asyncio
    async def test_get_by_project(self, feature_flag_repo, mock_session_factory):
        """Test para obtener flags por proyecto."""
        mock_flag1 = Mock()
        mock_flag1.to_dict.return_value = {
            'id': 1,
            'name': 'SHOW_FOOTER',
            'project_id': 'test-project',
            'file_path': 'config/defaultFeatures.js',
        }
        
        mock_flag2 = Mock()
        mock_flag2.to_dict.return_value = {
            'id': 2,
            'name': 'ENABLE_DARK_MODE',
            'project_id': 'test-project',
            'file_path': 'config/defaultFeatures.js',
        }
        
        session = mock_session_factory()
        session.query.return_value.filter.return_value.all.return_value = [mock_flag1, mock_flag2]
        
        result = await feature_flag_repo.get_by_project('test-project')
        
        assert len(result) == 2
        assert result[0]['name'] == 'SHOW_FOOTER'
        assert result[1]['name'] == 'ENABLE_DARK_MODE'
    
    @pytest.mark.asyncio
    async def test_get_by_name(self, feature_flag_repo, mock_session_factory):
        """Test para obtener flag por nombre."""
        mock_flag = Mock()
        mock_flag.to_dict.return_value = {
            'id': 1,
            'name': 'SHOW_FOOTER',
            'project_id': 'test-project',
            'file_path': 'config/defaultFeatures.js',
            'default_value': True,
        }
        
        session = mock_session_factory()
        session.query.return_value.filter.return_value.first.return_value = mock_flag
        
        result = await feature_flag_repo.get_by_name('SHOW_FOOTER', 'test-project')
        
        assert result is not None
        assert result['name'] == 'SHOW_FOOTER'
        assert result['default_value'] is True
    
    @pytest.mark.asyncio
    async def test_get_components_using_flag(self, feature_flag_repo, mock_session_factory):
        """Test para obtener componentes que usan un flag."""
        mock_flag = Mock()
        mock_flag.id = 1
        
        mock_component_flag1 = Mock()
        mock_component_flag1.component_id = 10
        
        mock_component_flag2 = Mock()
        mock_component_flag2.component_id = 20
        
        mock_comp1 = Mock()
        mock_comp1.to_dict.return_value = {'id': 10, 'name': 'Component1'}
        
        mock_comp2 = Mock()
        mock_comp2.to_dict.return_value = {'id': 20, 'name': 'Component2'}
        
        session = mock_session_factory()
        # Mock para buscar el flag
        session.query.return_value.filter.return_value.first.return_value = mock_flag
        # Mock para buscar relaciones
        session.query.return_value.join.return_value.filter.return_value.distinct.return_value.all.return_value = [
            mock_component_flag1, mock_component_flag2
        ]
        # Mock para buscar componentes
        session.query.return_value.filter.return_value.all.return_value = [mock_comp1, mock_comp2]
        
        result = await feature_flag_repo.get_components_using_flag('SHOW_FOOTER', 'test-project')
        
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_get_unused_flags(self, feature_flag_repo, mock_session_factory):
        """Test para obtener flags no usados."""
        mock_flag1 = Mock()
        mock_flag1.id = 1
        mock_flag1.to_dict.return_value = {'id': 1, 'name': 'USED_FLAG'}
        
        mock_flag2 = Mock()
        mock_flag2.id = 2
        mock_flag2.to_dict.return_value = {'id': 2, 'name': 'UNUSED_FLAG'}
        
        session = mock_session_factory()
        # Mock para obtener todos los flags
        session.query.return_value.filter.return_value.all.return_value = [mock_flag1, mock_flag2]
        # Mock para obtener IDs de flags usados (solo flag1)
        session.query.return_value.join.return_value.filter.return_value.distinct.return_value.all.return_value = [
            (1,)  # Solo flag1 está usado
        ]
        
        result = await feature_flag_repo.get_unused_flags('test-project')
        
        assert len(result) == 1
        assert result[0]['name'] == 'UNUSED_FLAG'
    
    @pytest.mark.asyncio
    async def test_save_component_flag_usage(self, feature_flag_repo, mock_session_factory):
        """Test para guardar relación componente-flag."""
        session = mock_session_factory()
        session.query.return_value.filter.return_value.first.return_value = None  # No existe
        
        await feature_flag_repo.save_component_flag_usage(10, 1, 'features.SHOW_FOOTER')
        
        session.add.assert_called_once()
        session.commit.assert_called_once()

