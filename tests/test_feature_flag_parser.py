"""
Tests para FeatureFlagParser.
"""

import pytest
from src.utils.feature_flag_parser import FeatureFlagParser
import tempfile
import os


class TestFeatureFlagParser:
    """Tests para FeatureFlagParser."""
    
    @pytest.fixture
    def parser(self):
        """Fixture para FeatureFlagParser."""
        return FeatureFlagParser()
    
    def test_extract_feature_flags_simple(self, parser):
        """Test extracción de flags simples."""
        content = """
        const defaultFeatures = {
          SHOW_FOOTER: true,
          ENABLE_DARK_MODE: false,
          MAX_ITEMS: 10,
        };
        
        export default defaultFeatures;
        """
        
        flags = parser.extract_feature_flags(content, "config/defaultFeatures.js")
        
        assert len(flags) == 3
        assert flags[0]['name'] == 'SHOW_FOOTER'
        assert flags[0]['default_value'] is True
        assert flags[0]['value_type'] == 'boolean'
        
        assert flags[1]['name'] == 'ENABLE_DARK_MODE'
        assert flags[1]['default_value'] is False
        
        assert flags[2]['name'] == 'MAX_ITEMS'
        assert flags[2]['default_value'] == 10
        assert flags[2]['value_type'] == 'number'
    
    def test_extract_feature_flags_with_descriptions(self, parser):
        """Test extracción de flags con descripciones."""
        content = """
        const defaultFeatures = {
          SHOW_FOOTER: true, // If true, shows the footer
          ENABLE_DARK_MODE: false, // Enables dark mode
        };
        
        export default defaultFeatures;
        """
        
        flags = parser.extract_feature_flags(content, "config/defaultFeatures.js")
        
        assert len(flags) == 2
        assert flags[0]['description'] == 'If true, shows the footer'
        assert flags[1]['description'] == 'Enables dark mode'
    
    def test_extract_feature_flags_with_enum_values(self, parser):
        """Test extracción de flags con valores posibles (enums)."""
        content = """
        const defaultFeatures = {
          FUNNEL_STYLE: 'CLASSIC', // CLASSIC | FLAT
          HOUR_FORMAT: '12', // 12 | 24
        };
        
        export default defaultFeatures;
        """
        
        flags = parser.extract_feature_flags(content, "config/defaultFeatures.js")
        
        assert len(flags) == 2
        assert flags[0]['name'] == 'FUNNEL_STYLE'
        assert flags[0]['default_value'] == 'CLASSIC'
        assert flags[0]['value_type'] == 'string'
        assert 'CLASSIC' in flags[0]['possible_values']
        assert 'FLAT' in flags[0]['possible_values']
        
        assert flags[1]['name'] == 'HOUR_FORMAT'
        assert '12' in flags[1]['possible_values']
        assert '24' in flags[1]['possible_values']
    
    def test_extract_feature_flags_with_arrays(self, parser):
        """Test extracción de flags con arrays."""
        content = """
        const defaultFeatures = {
          VALID_CATEGORIES: [],
          SPECIAL_CATEGORIES: [],
        };
        
        export default defaultFeatures;
        """
        
        flags = parser.extract_feature_flags(content, "config/defaultFeatures.js")
        
        assert len(flags) == 2
        assert flags[0]['default_value'] == []
        assert flags[0]['value_type'] == 'array'
    
    def test_extract_feature_flags_with_strings(self, parser):
        """Test extracción de flags con strings."""
        content = """
        const defaultFeatures = {
          OPENPAY_REGION: 'mexico',
          TICKETS_REFERENCE: 'transporter-key', // transporter-key | purchase-token
        };
        
        export default defaultFeatures;
        """
        
        flags = parser.extract_feature_flags(content, "config/defaultFeatures.js")
        
        assert len(flags) == 2
        assert flags[0]['default_value'] == 'mexico'
        assert flags[0]['value_type'] == 'string'
        
        assert flags[1]['default_value'] == 'transporter-key'
        assert 'transporter-key' in flags[1]['possible_values']
        assert 'purchase-token' in flags[1]['possible_values']
    
    def test_find_feature_flags_file_exact_name(self, parser):
        """Test búsqueda de archivo con nombre exacto."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = os.path.join(tmpdir, 'config')
            os.makedirs(config_dir)
            
            flags_file = os.path.join(config_dir, 'defaultFeatures.js')
            with open(flags_file, 'w') as f:
                f.write("const defaultFeatures = { FLAG: true }; export default defaultFeatures;")
            
            found = parser.find_feature_flags_file(tmpdir)
            assert found == flags_file
    
    def test_find_feature_flags_file_pattern(self, parser):
        """Test búsqueda de archivo con patrón."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_dir = os.path.join(tmpdir, 'config')
            os.makedirs(config_dir)
            
            flags_file = os.path.join(config_dir, 'features.js')
            with open(flags_file, 'w') as f:
                f.write("const defaultFeatures = { FLAG1: true, FLAG2: false, FLAG3: 10 }; export default defaultFeatures;")
            
            found = parser.find_feature_flags_file(tmpdir)
            assert found == flags_file
    
    def test_find_feature_flags_file_not_found(self, parser):
        """Test cuando no se encuentra archivo."""
        with tempfile.TemporaryDirectory() as tmpdir:
            found = parser.find_feature_flags_file(tmpdir)
            assert found is None
    
    def test_is_feature_flags_file(self, parser):
        """Test detección de archivo de feature flags."""
        valid_content = """
        const defaultFeatures = {
          FLAG1: true,
          FLAG2: false,
          FLAG3: 'value',
        };
        export default defaultFeatures;
        """
        
        assert parser._is_feature_flags_file(valid_content) is True
        
        invalid_content = "const x = 5;"
        assert parser._is_feature_flags_file(invalid_content) is False

