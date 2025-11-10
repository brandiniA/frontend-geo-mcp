"""
Tests para detección de containers de Redux en el parser.
"""

import pytest
from src.utils.parser import ReactParser


@pytest.fixture
def parser():
    """Fixture para crear un parser."""
    return ReactParser()


def test_detect_container_with_connect(parser):
    """Test para detectar container con connect."""
    content = """
import { connect } from 'react-redux';
import Purchase from './Purchase';

const mapStateToProps = (state) => ({});
const mapDispatchToProps = {};

export default connect(mapStateToProps, mapDispatchToProps)(Purchase);
"""
    result = parser._detect_redox_container(content, "test/path.js")
    
    assert result is not None
    assert result['is_container'] is True
    assert result['wrapped_component'] == 'Purchase'
    assert 'connect' in result['hocs_used']


def test_detect_container_with_compose(parser):
    """Test para detectar container con compose."""
    content = """
import { compose } from 'redux';
import { connect } from 'react-redux';
import { reduxForm } from 'redux-form';
import Passengers from './Passengers';

const mapStateToProps = (state) => ({});
const mapDispatchToProps = {};

export default compose(
  connect(mapStateToProps, mapDispatchToProps),
  reduxForm({ form: 'passengers' })
)(Passengers);
"""
    result = parser._detect_redox_container(content, "test/path.js")
    
    assert result is not None
    assert result['is_container'] is True
    assert result['wrapped_component'] == 'Passengers'
    assert 'compose' in result['hocs_used']
    assert 'connect' in result['hocs_used']


def test_detect_hocs(parser):
    """Test para detectar HOCs usados."""
    content = """
import { compose } from 'redux';
import { connect } from 'react-redux';
import { reduxForm } from 'redux-form';
import { withTranslation } from 'react-i18next';
import Component from './Component';

export default compose(
  connect(() => ({}), {}),
  reduxForm({ form: 'test' }),
  withTranslation('namespace')
)(Component);
"""
    result = parser._detect_redox_container(content, "test/path.js")
    
    assert result is not None
    assert 'reduxForm' in result['hocs_used']
    assert 'withTranslation' in result['hocs_used']


def test_detect_merge_props(parser):
    """Test para detectar mergeProps."""
    content = """
import { connect } from 'react-redux';
import Component from './Component';

const mapStateToProps = () => ({});
const mapDispatchToProps = {};
const mergeProps = (stateProps, dispatchProps, ownProps) => ({});

export default connect(mapStateToProps, mapDispatchToProps, mergeProps)(Component);
"""
    result = parser._detect_redox_container(content, "test/path.js")
    
    assert result is not None
    assert result['has_merge_props'] is True


def test_not_a_container(parser):
    """Test para verificar que un componente normal no se detecta como container."""
    content = """
import React from 'react';

const Component = () => {
  return <div>Hello</div>;
};

export default Component;
"""
    result = parser._detect_redox_container(content, "test/path.js")
    
    assert result is None


def test_extract_usage_context_map_state(parser):
    """Test para extraer contexto de uso en mapStateToProps."""
    content = """
const mapStateToProps = (state) => {
  const { features } = state.whitelabelConfig;
  return {
    showField: features.SHOW_FIELD === 'true'
  };
};
"""
    result = parser._extract_usage_context(content, 'SHOW_FIELD')
    
    assert result['usage_context'] == 'mapStateToProps'
    assert result['usage_type'] == 'conditional_logic'


def test_extract_usage_context_array_construction(parser):
    """Test para detectar construcción de array."""
    content = """
const mapStateToProps = (state) => {
  const { features } = state.whitelabelConfig;
  const keys = [
    'field1',
    features.SHOW_FIELD && 'field2',
    'field3'
  ].filter(Boolean);
  return { keys };
};
"""
    result = parser._extract_usage_context(content, 'SHOW_FIELD')
    
    assert result['usage_type'] == 'array_construction'


def test_extract_combined_flags(parser):
    """Test para detectar flags combinados."""
    content = """
const mapStateToProps = (state) => {
  const { features } = state.whitelabelConfig;
  if (features.FLAG1 === 'value' && features.FLAG2) {
    return { show: true };
  }
  return { show: false };
};
"""
    result1 = parser._extract_usage_context(content, 'FLAG1')
    result2 = parser._extract_usage_context(content, 'FLAG2')
    
    assert 'FLAG2' in (result1.get('combined_with') or [])
    assert result1.get('logic') == 'AND'


def test_detect_container_in_variable(parser):
    """Test para detectar container cuando connect está en una variable (caso CheckoutContainer)."""
    content = """
import { connect } from 'react-redux';
import Checkout from './Checkout';

const mapStateToProps = (state) => ({});
const mapDispatchToProps = {};

const CheckoutContainer = connect(mapStateToProps, mapDispatchToProps)(Checkout);

const CheckoutWithPaymentProviders = (routerProps) => {
  return <CheckoutContainer {...routerProps} />;
};

export default CheckoutWithPaymentProviders;
"""
    result = parser._detect_redox_container(content, "test/CheckoutContainer.js")
    
    assert result is not None
    assert result['is_container'] is True
    assert result['wrapped_component'] == 'Checkout'
    assert 'connect' in result['hocs_used']

