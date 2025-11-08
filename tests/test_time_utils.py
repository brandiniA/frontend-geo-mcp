"""
Tests para utilidades de tiempo (time_utils).
"""

import pytest
from datetime import datetime, timedelta
from src.tools.utils.time_utils import format_relative_time


class TestFormatRelativeTime:
    """Tests para format_relative_time."""
    
    def test_just_now(self):
        """Test para tiempo muy reciente (< 1 minuto)."""
        now = datetime.now()
        result = format_relative_time(now)
        
        assert result == "just now"
    
    def test_minutes_ago(self):
        """Test para minutos atrás."""
        dt = datetime.now() - timedelta(minutes=5)
        result = format_relative_time(dt)
        
        assert "minute" in result.lower()
        assert "5" in result or "ago" in result
    
    def test_one_minute_ago(self):
        """Test para singular de minuto."""
        dt = datetime.now() - timedelta(minutes=1)
        result = format_relative_time(dt)
        
        assert "minute" in result.lower()
        assert "minute ago" in result.lower()  # Sin 's' para singular
    
    def test_hours_ago(self):
        """Test para horas atrás."""
        dt = datetime.now() - timedelta(hours=3)
        result = format_relative_time(dt)
        
        assert "hour" in result.lower()
        assert "3" in result or "ago" in result
    
    def test_one_hour_ago(self):
        """Test para singular de hora."""
        dt = datetime.now() - timedelta(hours=1)
        result = format_relative_time(dt)
        
        assert "hour ago" in result.lower()  # Sin 's' para singular
    
    def test_days_ago(self):
        """Test para días atrás."""
        dt = datetime.now() - timedelta(days=3)
        result = format_relative_time(dt)
        
        assert "day" in result.lower()
        assert "3" in result or "ago" in result
    
    def test_one_day_ago(self):
        """Test para singular de día."""
        dt = datetime.now() - timedelta(days=1)
        result = format_relative_time(dt)
        
        assert "day ago" in result.lower()  # Sin 's' para singular
    
    def test_weeks_ago(self):
        """Test para semanas atrás."""
        dt = datetime.now() - timedelta(days=14)
        result = format_relative_time(dt)
        
        assert "week" in result.lower()
    
    def test_one_week_ago(self):
        """Test para singular de semana."""
        dt = datetime.now() - timedelta(days=7)
        result = format_relative_time(dt)
        
        assert "week ago" in result.lower()  # Sin 's' para singular
    
    def test_months_ago(self):
        """Test para meses atrás."""
        dt = datetime.now() - timedelta(days=60)
        result = format_relative_time(dt)
        
        assert "month" in result.lower()
    
    def test_one_month_ago(self):
        """Test para singular de mes."""
        dt = datetime.now() - timedelta(days=30)
        result = format_relative_time(dt)
        
        assert "month ago" in result.lower()  # Sin 's' para singular
    
    def test_string_iso_format(self):
        """Test con string ISO format."""
        dt_str = datetime.now().isoformat()
        result = format_relative_time(dt_str)
        
        assert result == "just now" or "minute" in result.lower()
    
    def test_string_iso_with_z(self):
        """Test con string ISO format con Z."""
        dt_str = (datetime.now() - timedelta(days=2)).isoformat() + "Z"
        result = format_relative_time(dt_str)
        
        assert "day" in result.lower() or "week" in result.lower()
    
    def test_invalid_string(self):
        """Test con string inválido."""
        result = format_relative_time("invalid-date")
        
        assert result == "unknown"
    
    def test_none_value(self):
        """Test con None."""
        result = format_relative_time(None)
        
        assert result == "unknown"
    
    def test_invalid_type(self):
        """Test con tipo inválido."""
        result = format_relative_time(12345)
        
        assert result == "unknown"

