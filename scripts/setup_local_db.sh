#!/bin/bash

echo "🚀 Setting up local PostgreSQL database..."

# Verificar que Docker está corriendo
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker no está corriendo. Por favor inicia Docker Desktop."
    exit 1
fi

# Detectar el comando correcto de docker-compose
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    echo "❌ docker-compose o docker compose no encontrados. Por favor instala Docker Compose."
    exit 1
fi

# Iniciar PostgreSQL con docker-compose
echo "📦 Starting PostgreSQL container..."
$DOCKER_COMPOSE_CMD up -d

# Esperar a que PostgreSQL esté listo
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Verificar conexión
until docker exec frontend-mcp-db pg_isready -U postgres > /dev/null 2>&1; do
    echo "⏳ Waiting for database..."
    sleep 2
done

echo "✅ PostgreSQL is ready!"

# Ejecutar Alembic migrations
echo "📝 Running Alembic migrations..."
if ! uv run alembic upgrade head > /dev/null 2>&1; then
    echo "⚠️  Warning: Alembic migrations may have issues"
    echo "   Try running manually: uv run alembic upgrade head"
else
    echo "✅ Alembic migrations executed successfully!"
fi

echo ""
echo "✅ Database setup complete!"
echo ""
echo "📊 Database Info:"
echo "   Host: localhost"
echo "   Port: 5432"
echo "   Database: frontend_mcp"
echo "   User: postgres"
echo "   Password: postgres"
echo ""
echo "🔗 Connection string:"
echo "   postgresql://postgres:postgres@localhost:5432/frontend_mcp"
echo ""
echo "📝 Next steps:"
echo "   1. Copy .env.example to .env (if not already done)"
echo "   2. Run: uv run python scripts/test_local_db.py"
echo ""
echo "📚 Alembic commands:"
echo "   uv run alembic upgrade head       # Apply migrations"
echo "   uv run alembic downgrade -1       # Rollback last migration"
echo "   uv run alembic current            # Show current revision"
echo "   uv run alembic history            # Show all revisions"
