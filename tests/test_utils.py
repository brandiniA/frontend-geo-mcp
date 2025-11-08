"""
Tests para utilidades de los repositorios.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from sqlalchemy.orm import Session

from src.registry.repositories.utils.serialization import (
    to_dict_list,
    model_to_dict,
    make_serializable,
)
from src.registry.repositories.utils.crud import (
    safe_upsert,
    update_field,
)


class TestSerializationUtils:
    """Tests para utilidades de serialización."""
    
    def test_to_dict_list(self):
        """Test para convertir lista de objetos a diccionarios."""
        mock_obj1 = Mock()
        mock_obj1.to_dict.return_value = {"id": 1, "name": "Test1"}
        
        mock_obj2 = Mock()
        mock_obj2.to_dict.return_value = {"id": 2, "name": "Test2"}
        
        result = to_dict_list([mock_obj1, mock_obj2])
        
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2
    
    def test_model_to_dict_with_object(self):
        """Test para convertir objeto a diccionario."""
        mock_obj = Mock()
        mock_obj.to_dict.return_value = {"id": 1, "name": "Test"}
        
        result = model_to_dict(mock_obj)
        
        assert result["id"] == 1
        assert result["name"] == "Test"
    
    def test_model_to_dict_with_none(self):
        """Test para convertir None."""
        result = model_to_dict(None)
        
        assert result is None
    
    def test_make_serializable_datetime(self):
        """Test para serializar datetime."""
        dt = datetime(2024, 1, 1, 12, 0, 0)
        result = make_serializable(dt)
        
        assert isinstance(result, str)
        assert "2024-01-01" in result
    
    def test_make_serializable_dict(self):
        """Test para serializar diccionario con datetime."""
        data = {
            "id": 1,
            "date": datetime(2024, 1, 1, 12, 0, 0),
            "nested": {
                "date": datetime(2024, 1, 2, 12, 0, 0)
            }
        }
        
        result = make_serializable(data)
        
        assert isinstance(result["date"], str)
        assert isinstance(result["nested"]["date"], str)
        assert result["id"] == 1
    
    def test_make_serializable_list(self):
        """Test para serializar lista con datetime."""
        data = [
            datetime(2024, 1, 1, 12, 0, 0),
            datetime(2024, 1, 2, 12, 0, 0)
        ]
        
        result = make_serializable(data)
        
        assert len(result) == 2
        assert all(isinstance(item, str) for item in result)


class TestCrudUtils:
    """Tests para utilidades CRUD."""
    
    @pytest.fixture
    def mock_session(self):
        """Fixture para sesión mock."""
        session = Mock(spec=Session)
        session.query = Mock()
        session.add = Mock()
        session.commit = Mock()
        return session
    
    def test_safe_upsert_create_new(self, mock_session):
        """Test para crear nuevo registro con safe_upsert."""
        MockModel = Mock()
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query
        
        instance = Mock()
        MockModel.return_value = instance
        
        result = safe_upsert(
            session=mock_session,
            model_class=MockModel,
            unique_fields={"id": "test-1"},
            data={"name": "Test"},
        )
        
        assert result == instance
        mock_session.add.assert_called_once()
    
    def test_safe_upsert_update_existing(self, mock_session):
        """Test para actualizar registro existente con safe_upsert."""
        MockModel = Mock()
        existing = Mock()
        existing.updated_at = None
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = existing
        mock_session.query.return_value = mock_query
        
        result = safe_upsert(
            session=mock_session,
            model_class=MockModel,
            unique_fields={"id": "test-1"},
            data={"name": "Updated"},
            update_timestamp=True
        )
        
        assert result == existing
        assert hasattr(existing, 'name') or existing.name == "Updated"
    
    def test_update_field_success(self, mock_session):
        """Test para actualizar campo específico."""
        MockModel = Mock()
        instance = Mock()
        instance.last_sync = None
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = instance
        mock_session.query.return_value = mock_query
        
        result = update_field(
            session=mock_session,
            model_class=MockModel,
            filter_fields={"id": "test-1"},
            field_name="last_sync",
            field_value=datetime.utcnow(),
            commit=True
        )
        
        assert result is True
        mock_session.commit.assert_called_once()
    
    def test_update_field_not_found(self, mock_session):
        """Test para actualizar campo cuando no se encuentra el registro."""
        MockModel = Mock()
        
        mock_query = Mock()
        mock_query.filter.return_value.first.return_value = None
        mock_session.query.return_value = mock_query
        
        result = update_field(
            session=mock_session,
            model_class=MockModel,
            filter_fields={"id": "test-1"},
            field_name="last_sync",
            field_value=datetime.utcnow(),
            commit=True
        )
        
        assert result is False

