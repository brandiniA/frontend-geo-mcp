#!/bin/bash

echo "🚀 Setting up local PostgreSQL database..."

# Verificar que Docker está corriendo
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker no está corriendo. Por favor inicia Docker Desktop."
    exit 1
fi

# Iniciar PostgreSQL con docker-compose
echo "📦 Starting PostgreSQL container..."
docker-compose up -d

# Esperar a que PostgreSQL esté listo
echo "⏳ Waiting for PostgreSQL to be ready..."
sleep 5

# Verificar conexión
until docker exec frontend-mcp-db pg_isready -U postgres > /dev/null 2>&1; do
    echo "⏳ Waiting for database..."
    sleep 2
done

echo "✅ PostgreSQL is ready!"

# Ejecutar migrations
echo "📝 Running migrations..."
if [ -f "database/migrations/001_initial_schema.sql" ]; then
    docker exec -i frontend-mcp-db psql -U postgres -d frontend_mcp < database/migrations/001_initial_schema.sql
    echo "✅ Migrations executed successfully!"
else
    echo "⚠️  Migration file not found. Please create database/migrations/001_initial_schema.sql"
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
echo "   1. Copy .env.example to .env"
echo "   2. Update DATABASE_URL in .env"
echo "   3. Run: python scripts/test_local_db.py"

