"""
Utilidades para formateo de fechas en formato relativo (ej: '2 days ago').
"""

from datetime import datetime
from typing import Union


def format_relative_time(dt: Union[datetime, str]) -> str:
    """
    Convierte un datetime a formato relativo legible.
    
    Soporta múltiples formatos de entrada:
    - datetime objects (naive o timezone-aware)
    - Strings ISO 8601 (con o sin 'Z' para UTC)
    
    Ejemplos de output:
    - "just now" (< 1 minuto)
    - "5 minutes ago"
    - "2 hours ago"
    - "3 days ago"
    - "2 weeks ago"
    - "1 month ago"
    
    Args:
        dt: datetime object o string ISO format a convertir
        
    Returns:
        String con tiempo relativo, o "unknown" si no se puede parsear
        
    Examples:
        >>> format_relative_time(datetime.now())
        'just now'
        
        >>> format_relative_time('2024-10-25T10:30:00Z')
        '5 days ago'
    """
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return "unknown"
    
    if not isinstance(dt, datetime):
        return "unknown"
    
    # Obtener datetime actual (con mismo timezone si es necesario)
    now = datetime.now(dt.tzinfo) if dt.tzinfo else datetime.now()
    diff = now - dt
    
    # Calcular diferencia en diferentes unidades
    seconds = diff.total_seconds()
    minutes = seconds // 60
    hours = minutes // 60
    days = hours // 24
    
    # Retornar según la unidad más apropiada
    if seconds < 60:
        return "just now"
    elif minutes < 60:
        minute_count = int(minutes)
        return f"{minute_count} minute{'s' if minute_count != 1 else ''} ago"
    elif hours < 24:
        hour_count = int(hours)
        return f"{hour_count} hour{'s' if hour_count != 1 else ''} ago"
    elif days < 7:
        day_count = int(days)
        return f"{day_count} day{'s' if day_count != 1 else ''} ago"
    elif days < 30:
        weeks = days // 7
        week_count = int(weeks)
        return f"{week_count} week{'s' if week_count != 1 else ''} ago"
    else:
        months = days // 30
        month_count = int(months)
        return f"{month_count} month{'s' if month_count != 1 else ''} ago"
