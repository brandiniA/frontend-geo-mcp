"""
Tests para FeatureFlagUsageDetector.
"""

import pytest
from src.utils.feature_flag_detector import FeatureFlagUsageDetector


class TestFeatureFlagUsageDetector:
    """Tests para FeatureFlagUsageDetector."""
    
    @pytest.fixture
    def detector(self):
        """Fixture para FeatureFlagUsageDetector."""
        return FeatureFlagUsageDetector()
    
    def test_detect_features_dot_pattern(self, detector):
        """Test detección de patrón features.FLAG_NAME."""
        content = """
        const MyComponent = () => {
          const features = useWhitelabelFeatures();
          
          if (features.SHOW_FOOTER) {
            return <Footer />;
          }
          
          return <div>Content</div>;
        };
        """
        
        flag_names = ['SHOW_FOOTER', 'ENABLE_DARK_MODE']
        detected = detector.detect_flag_usage(content, flag_names)
        
        assert len(detected) > 0
        assert any(d['flag_name'] == 'SHOW_FOOTER' for d in detected)
        assert any('features.SHOW_FOOTER' in d['pattern'] for d in detected)
    
    def test_detect_features_bracket_pattern(self, detector):
        """Test detección de patrón features['FLAG_NAME']."""
        content = """
        const MyComponent = () => {
          const features = useWhitelabelFeatures();
          
          if (features['SHOW_FOOTER']) {
            return <Footer />;
          }
        };
        """
        
        flag_names = ['SHOW_FOOTER']
        detected = detector.detect_flag_usage(content, flag_names)
        
        assert len(detected) > 0
        assert any(d['flag_name'] == 'SHOW_FOOTER' for d in detected)
    
    def test_detect_useWhitelabelFeatures_pattern(self, detector):
        """Test detección de patrón const { FLAG_NAME } = useWhitelabelFeatures()."""
        content = """
        import useWhitelabelFeatures from './hooks/useWhitelabelFeatures';
        
        const MyComponent = () => {
          const { SHOW_FOOTER, ENABLE_DARK_MODE } = useWhitelabelFeatures();
          
          return (
            <div>
              {SHOW_FOOTER && <Footer />}
            </div>
          );
        };
        """
        
        flag_names = ['SHOW_FOOTER', 'ENABLE_DARK_MODE']
        detected = detector.detect_flag_usage(content, flag_names)
        
        assert len(detected) > 0
        assert any(d['flag_name'] == 'SHOW_FOOTER' for d in detected)
        assert any(d['flag_name'] == 'ENABLE_DARK_MODE' for d in detected)
    
    def test_detect_useSelector_pattern(self, detector):
        """Test detección de patrón const { features } = useSelector(...)."""
        content = """
        import { useSelector } from 'react-redux';
        
        const MyComponent = () => {
          const { features } = useSelector((state) => state.whitelabelConfig);
          
          if (features.SHOW_FOOTER) {
            return <Footer />;
          }
        };
        """
        
        flag_names = ['SHOW_FOOTER']
        detected = detector.detect_flag_usage(content, flag_names)
        
        assert len(detected) > 0
        assert any(d['flag_name'] == 'SHOW_FOOTER' for d in detected)
    
    def test_detect_whitelabelConfig_pattern(self, detector):
        """Test detección de patrón whitelabelConfig.features.FLAG_NAME."""
        content = """
        const mapStateToProps = (state) => {
          const { whitelabelConfig } = state;
          
          return {
            showFooter: whitelabelConfig.features.SHOW_FOOTER,
          };
        };
        """
        
        flag_names = ['SHOW_FOOTER']
        detected = detector.detect_flag_usage(content, flag_names)
        
        assert len(detected) > 0
        assert any(d['flag_name'] == 'SHOW_FOOTER' for d in detected)
    
    def test_detect_mapStateToProps_destructuring(self, detector):
        """Test detección en mapStateToProps con destructuring."""
        content = """
        const mapStateToProps = (state) => {
          const {
            whitelabelConfig: { features, env },
          } = state;
          
          return {
            showFooter: features.SHOW_FOOTER,
          };
        };
        """
        
        flag_names = ['SHOW_FOOTER']
        detected = detector.detect_flag_usage(content, flag_names)
        
        assert len(detected) > 0
        assert any(d['flag_name'] == 'SHOW_FOOTER' for d in detected)
    
    def test_detect_multiple_flags(self, detector):
        """Test detección de múltiples flags."""
        content = """
        const MyComponent = () => {
          const { SHOW_FOOTER, ENABLE_DARK_MODE, MAX_ITEMS } = useWhitelabelFeatures();
          
          return (
            <div>
              {SHOW_FOOTER && <Footer />}
              {ENABLE_DARK_MODE && <DarkModeToggle />}
              <Items max={MAX_ITEMS} />
            </div>
          );
        };
        """
        
        flag_names = ['SHOW_FOOTER', 'ENABLE_DARK_MODE', 'MAX_ITEMS']
        detected = detector.detect_flag_usage(content, flag_names)
        
        assert len(detected) >= 3
        detected_names = {d['flag_name'] for d in detected}
        assert 'SHOW_FOOTER' in detected_names
        assert 'ENABLE_DARK_MODE' in detected_names
        assert 'MAX_ITEMS' in detected_names
    
    def test_detect_no_flags(self, detector):
        """Test cuando no hay flags usados."""
        content = """
        const MyComponent = () => {
          return <div>No flags here</div>;
        };
        """
        
        flag_names = ['SHOW_FOOTER', 'ENABLE_DARK_MODE']
        detected = detector.detect_flag_usage(content, flag_names)
        
        assert len(detected) == 0
    
    def test_detect_orphaned_flags(self, detector):
        """Test detección de flags huérfanos (usados pero no definidos)."""
        content = """
        const MyComponent = () => {
          const { UNKNOWN_FLAG, ANOTHER_UNKNOWN } = useWhitelabelFeatures();
          
          if (features.MISSING_FLAG) {
            return <div>Test</div>;
          }
        };
        """
        
        defined_flags = {'SHOW_FOOTER', 'ENABLE_DARK_MODE'}
        orphaned = detector.detect_orphaned_flags(content, defined_flags)
        
        assert len(orphaned) > 0
        assert 'UNKNOWN_FLAG' in orphaned or 'ANOTHER_UNKNOWN' in orphaned or 'MISSING_FLAG' in orphaned

