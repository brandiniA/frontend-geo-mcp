# Testing Guide

Este proyecto usa **pytest** como framework de testing, similar a Jest en JavaScript.

## 🚀 Quick Start

```bash
# Instalar dependencias de desarrollo
uv sync --dev

# Ejecutar todas las pruebas
uv run pytest

# O usar el script
./scripts/test.sh
```

## 📁 Estructura de Tests

```
tests/
├── __init__.py          # Inicialización del paquete
├── conftest.py          # Fixtures compartidas
├── test_tools.py        # Tests para ComponentNavigator
├── test_repositories.py # Tests para repositorios
└── test_utils.py        # Tests para utilidades
```

## 🧪 Comandos Útiles

### Ejecutar todas las pruebas
```bash
uv run pytest
```

### Ejecutar con cobertura
```bash
uv run pytest --cov=src --cov-report=html
# Abre htmlcov/index.html para ver el reporte
```

### Ejecutar pruebas específicas
```bash
# Por archivo
uv run pytest tests/test_tools.py

# Por clase
uv run pytest tests/test_tools.py::TestComponentNavigator

# Por función
uv run pytest tests/test_tools.py::TestComponentNavigator::test_find_component
```

### Filtrar por marcadores
```bash
# Solo tests unitarios
uv run pytest -m "unit"

# Excluir tests de integración
uv run pytest -m "not integration"

# Excluir tests lentos
uv run pytest -m "not slow"
```

### Modo verbose
```bash
uv run pytest -v          # Más detallado
uv run pytest -vv         # Muy detallado
uv run pytest -s          # Mostrar prints
```

## 📝 Escribir Tests

### Estructura básica

```python
import pytest
from tools.navigator import ComponentNavigator

class TestComponentNavigator:
    @pytest.mark.asyncio
    async def test_find_component(self, mock_database_client):
        """Test description."""
        navigator = ComponentNavigator(mock_database_client)
        # ... tu código de test
        assert result == expected
```

### Fixtures disponibles

- `mock_database_client`: Mock de DatabaseClient
- `sample_component`: Componente de ejemplo
- `sample_project`: Proyecto de ejemplo
- `sample_hook`: Hook de ejemplo
- `mock_db_session`: Mock de sesión SQLAlchemy

### Marcadores

```python
@pytest.mark.unit          # Test unitario
@pytest.mark.integration   # Test de integración
@pytest.mark.slow          # Test lento
```

## 🔧 Configuración

La configuración de pytest está en `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
asyncio_mode = "auto"
```

## 📊 Cobertura de Código

```bash
# Generar reporte HTML
uv run pytest --cov=src --cov-report=html

# Ver reporte en terminal
uv run pytest --cov=src --cov-report=term-missing
```

## 🐛 Debugging

```bash
# Ejecutar con pdb (debugger)
uv run pytest --pdb

# Ejecutar con prints visibles
uv run pytest -s

# Ejecutar solo el primer test que falla
uv run pytest -x
```

## 📚 Recursos

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)

