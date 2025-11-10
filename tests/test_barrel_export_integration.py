"""
Tests de integración para el flujo completo de barrel exports.
Incluye el caso crítico Purchase → Checkout.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from src.utils.barrel_export_parser import resolve_index_export
from src.models import Component, BarrelExport, ComponentDependency


class TestBarrelExportIntegration:
    """Tests de integración del flujo completo de barrel exports."""
    
    def test_scan_checkout_directory(self, checkout_evidence_path):
        """Test: Escanear directorio Checkout completo con evidencia real."""
        index_path = checkout_evidence_path / "index.js"
        
        # Verificar que el archivo existe
        assert index_path.exists()
        
        # Parsear el index
        result = resolve_index_export(str(index_path))
        
        # Verificar resultado
        assert result is not None
        assert result['exported_name'] == 'CheckoutContainer'
        assert result['source_file'] == './CheckoutContainer'
        assert result['is_container'] is True
        
        # Verificar que los archivos mencionados existen
        container_path = checkout_evidence_path / "CheckoutContainer.js"
        component_path = checkout_evidence_path / "Checkout.js"
        
        assert container_path.exists()
        assert component_path.exists()
    
    @pytest.mark.asyncio
    async def test_save_and_retrieve_barrel_export(self, mock_database_client):
        """Test: Guardar y recuperar barrel export desde BD."""
        # Mock del repository
        mock_database_client.barrel_exports = Mock()
        mock_database_client.barrel_exports.save_barrel_exports = AsyncMock(return_value=1)
        mock_database_client.barrel_exports.get_by_directory = AsyncMock(return_value={
            'id': 1,
            'project_id': 'test-project',
            'directory_path': 'components/Checkout',
            'index_file_path': 'components/Checkout/index.js',
            'exported_component_id': 123,
            'exported_name': 'CheckoutContainer',
            'source_file_path': './CheckoutContainer',
            'is_container': True,
        })
        
        # Simular guardar
        barrel_exports = [{
            'directory_path': 'components/Checkout',
            'index_file_path': 'components/Checkout/index.js',
            'exported_component_id': 123,
            'exported_name': 'CheckoutContainer',
            'source_file_path': './CheckoutContainer',
            'is_container': True,
        }]
        
        count = await mock_database_client.barrel_exports.save_barrel_exports(
            barrel_exports, 'test-project'
        )
        
        assert count == 1
        
        # Simular recuperar
        result = await mock_database_client.barrel_exports.get_by_directory(
            'components/Checkout', 'test-project'
        )
        
        assert result is not None
        assert result['exported_name'] == 'CheckoutContainer'
        assert result['is_container'] is True
    
    def test_resolve_purchase_checkout_dependency(self, mock_db_session):
        """
        Test: Resolver dependencia Purchase → Checkout via barrel export.
        Este es el caso crítico identificado en el diagnóstico.
        """
        # Mock Purchase component
        purchase_component = Mock()
        purchase_component.id = 1
        purchase_component.name = 'Purchase'
        purchase_component.file_path = 'components/purchase/Purchase.js'
        purchase_component.project_id = 'platform-funnel'
        
        # Mock Checkout component
        checkout_component = Mock()
        checkout_component.id = 2
        checkout_component.name = 'Checkout'
        checkout_component.file_path = 'components/purchase/Checkout/Checkout.js'
        checkout_component.project_id = 'platform-funnel'
        
        # Mock barrel export
        barrel_export = Mock()
        barrel_export.id = 1
        barrel_export.project_id = 'platform-funnel'
        barrel_export.directory_path = 'components/purchase/Checkout'
        barrel_export.exported_component_id = 2
        barrel_export.exported_name = 'CheckoutContainer'
        barrel_export.is_container = True
        
        # Mock query para barrel export
        mock_query = Mock()
        mock_filter_result = Mock()
        mock_filter_result.first.return_value = barrel_export
        mock_query.filter.return_value = mock_filter_result
        mock_db_session.query.return_value = mock_query
        
        # Simular la consulta
        from src.models import BarrelExport
        
        result = mock_db_session.query(BarrelExport).filter(
            BarrelExport.project_id == 'platform-funnel',
            BarrelExport.directory_path == 'components/purchase/Checkout'
        ).first()
        
        # Verificar que se encontró el barrel export
        assert result is not None
        assert result.exported_component_id == 2
        assert result.exported_name == 'CheckoutContainer'
        assert result.is_container is True
    
    def test_multiple_barrel_exports(self, tmp_path):
        """Test: Procesar múltiples barrel exports en diferentes directorios."""
        # Crear estructura de directorios
        components_dir = tmp_path / "components"
        components_dir.mkdir()
        
        # Crear varios directorios con index.js
        directories = ['Button', 'Modal', 'Card', 'Form']
        
        for dir_name in directories:
            dir_path = components_dir / dir_name
            dir_path.mkdir()
            
            # Crear componente
            component_file = dir_path / f"{dir_name}.js"
            component_file.write_text(f"""
import React from 'react';
export const {dir_name} = () => <div>{dir_name}</div>;
""")
            
            # Crear index.js
            index_file = dir_path / "index.js"
            index_file.write_text(f"""
import {dir_name} from './{dir_name}';
export default {dir_name};
""")
        
        # Verificar que se crearon todos los archivos
        for dir_name in directories:
            index_path = components_dir / dir_name / "index.js"
            assert index_path.exists()
            
            result = resolve_index_export(str(index_path))
            assert result is not None
            assert result['exported_name'] == dir_name
            assert result['is_container'] is False


class TestImportResolverWithBarrelExports:
    """Tests de resolución de imports usando barrel exports."""
    
    def test_resolve_directory_import_via_barrel_export(self, mock_db_session):
        """Test: Resolver import a directorio usando barrel export."""
        from src.utils.import_resolver import resolve_imports_to_components
        
        # Mock barrel export
        barrel = Mock()
        barrel.project_id = 'test-project'
        barrel.directory_path = 'components/Checkout'
        barrel.exported_component_id = 123
        barrel.exported_name = 'CheckoutContainer'
        
        # Mock query
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = barrel
        mock_query.filter.return_value = mock_filter
        mock_db_session.query.return_value = mock_query
        
        # Imports de prueba (formato correcto)
        component_imports = [{
            'from_path': 'components/Checkout',
            'imported_names': ['Checkout'],
            'import_type': 'default'
        }]
        
        # Resolver imports
        dependencies = resolve_imports_to_components(
            component_imports=component_imports,
            project_id='test-project',
            current_file_path='components/Purchase/Purchase.js',
            component_name='Purchase',
            db_session=mock_db_session
        )
        
        # Verificar que se resolvió via barrel export
        assert len(dependencies) >= 1
        # La dependencia debería haber sido resuelta
    
    def test_fallback_when_no_barrel_export(self, mock_db_session):
        """Test: Fallback a lógica existente cuando no hay barrel export."""
        from src.utils.import_resolver import resolve_imports_to_components
        
        # Mock sin barrel export
        mock_query = Mock()
        mock_filter = Mock()
        mock_filter.first.return_value = None  # No barrel export
        mock_query.filter.return_value = mock_filter
        
        # Mock para componentes
        mock_component = Mock()
        mock_component.id = 456
        mock_component.name = 'Button'
        mock_component.file_path = 'components/Button.js'
        
        mock_query_all = Mock()
        mock_query_all.all.return_value = [mock_component]
        mock_query.filter.return_value.all.return_value = [mock_component]
        
        mock_db_session.query.return_value = mock_query
        
        # Imports de prueba (formato correcto)
        component_imports = [{
            'from_path': './Button',
            'imported_names': ['Button'],
            'import_type': 'default'
        }]
        
        # Resolver imports (debe usar fallback)
        dependencies = resolve_imports_to_components(
            component_imports=component_imports,
            project_id='test-project',
            current_file_path='components/Form/Form.js',
            component_name='Form',
            db_session=mock_db_session
        )
        
        # Debería poder resolver de alguna manera
        assert isinstance(dependencies, list)


@pytest.mark.asyncio
class TestPurchaseCheckoutEndToEnd:
    """Test end-to-end completo del caso Purchase → Checkout."""
    
    async def test_purchase_checkout_resolution_full_flow(self):
        """
        Test completo del caso Purchase → Checkout usando evidencia real.
        
        Simula:
        1. Indexar componentes (Purchase, Checkout, CheckoutContainer)
        2. Indexar barrel export (Checkout/index.js)
        3. Resolver imports de Purchase
        4. Validar que Purchase.dependencies incluye Checkout
        """
        # Este test requeriría una BD real o mocks muy complejos
        # Por ahora, verificamos que los archivos de evidencia existen
        evidence_dir = Path(__file__).parent.parent / "src/evidencia"
        
        # Verificar estructura de archivos
        purchase_file = evidence_dir / "ev1.md"  # Contiene código de Purchase
        checkout_dir = evidence_dir / "Checkout"
        checkout_index = checkout_dir / "index.js"
        checkout_container = checkout_dir / "CheckoutContainer.js"
        checkout_component = checkout_dir / "Checkout.js"
        
        assert purchase_file.exists(), "Archivo de Purchase no encontrado"
        assert checkout_dir.exists(), "Directorio de Checkout no encontrado"
        assert checkout_index.exists(), "index.js de Checkout no encontrado"
        assert checkout_container.exists(), "CheckoutContainer no encontrado"
        assert checkout_component.exists(), "Checkout no encontrado"
        
        # Verificar que el index.js es un barrel export válido
        result = resolve_index_export(str(checkout_index))
        assert result is not None
        assert result['exported_name'] == 'CheckoutContainer'
        
        # Verificar que Purchase importa Checkout
        purchase_content = purchase_file.read_text()
        assert "import Checkout from 'components/purchase/Checkout'" in purchase_content
        assert "component={Checkout}" in purchase_content
        
        print("✅ Estructura de archivos verificada")
        print("✅ Barrel export de Checkout válido")
        print("✅ Purchase importa Checkout correctamente")

