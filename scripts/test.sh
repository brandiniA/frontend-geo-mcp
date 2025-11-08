#!/bin/bash
# Script para ejecutar tests con pytest

set -e

echo "🧪 Running tests with pytest..."
echo ""

# Ejecutar pytest con configuración del proyecto
uv run pytest "$@"

