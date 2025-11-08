.PHONY: test test-cov test-unit test-integration install-dev help

# Instalar dependencias de desarrollo
install-dev:
	uv sync --dev

# Ejecutar todas las pruebas
test:
	uv run pytest

# Ejecutar pruebas con cobertura
test-cov:
	uv run pytest --cov=src --cov-report=html --cov-report=term-missing

# Ejecutar solo tests unitarios
test-unit:
	uv run pytest -m "unit"

# Ejecutar solo tests de integración
test-integration:
	uv run pytest -m "integration"

# Ejecutar tests en modo watch (requiere pytest-watch)
test-watch:
	uv run ptw

# Ejecutar tests con verbose
test-verbose:
	uv run pytest -vv

# Limpiar archivos temporales de pytest
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete

# Ayuda
help:
	@echo "Comandos disponibles:"
	@echo "  make install-dev      - Instalar dependencias de desarrollo"
	@echo "  make test            - Ejecutar todas las pruebas"
	@echo "  make test-cov        - Ejecutar pruebas con cobertura"
	@echo "  make test-unit       - Ejecutar solo tests unitarios"
	@echo "  make test-integration - Ejecutar solo tests de integración"
	@echo "  make test-verbose    - Ejecutar tests con output detallado"
	@echo "  make clean           - Limpiar archivos temporales"

