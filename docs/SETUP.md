# Setup Guide

Complete installation and configuration guide for Frontend GPS.

## Prerequisites

- Python 3.12 or higher
- Docker Desktop
- Git
- [uv](https://github.com/astral-sh/uv) package manager

## Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/your-org/frontend-geo-mcp
cd frontend-geo-mcp
```

### 2. Install Dependencies

```bash
# Install all project dependencies with uv
uv sync
```

This installs:
- FastMCP 2.13.0+
- SQLAlchemy 2.0+
- Alembic (database migrations)
- PostgreSQL driver (psycopg2)
- And all other dependencies listed in `pyproject.toml`

### 3. Setup Local Database

```bash
# Make the setup script executable
chmod +x scripts/setup_local_db.sh

# Run the setup script
./scripts/setup_local_db.sh
```

This script will:
1. Start PostgreSQL container (if Docker is running)
2. Wait for database to be ready
3. Apply all Alembic migrations
4. Start Adminer and pgAdmin containers
5. Display connection information

**What gets created:**
- PostgreSQL 15 Alpine container
- Adminer web UI (port 8080)
- pgAdmin web UI (port 5050)
- Database schema with `projects` and `components` tables

### 4. Environment Configuration

```bash
# Copy environment template
cp config.env.example .env
```

Edit `.env` with your settings:

```bash
# Database (defaults work for local dev)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/frontend_mcp

# Temporary directory for cloning repos
TEMP_DIR=/tmp/mcp-repos

# API Key
API_KEY=local-dev-key

# GitHub token (optional, for private repos)
GITHUB_TOKEN=

# Server port
PORT=8080
```

### 5. Test Database Connection

```bash
# Test the connection
uv run python scripts/test_local_db.py
```

Expected output:
```
✅ Connected to database with SQLAlchemy
✅ Database connection test successful!
```

### 6. Configure Projects

Edit `.mcp-config.json`:

```json
{
  "projects": {
    "my-main-app": {
      "repository": "https://github.com/myorg/main-app",
      "branch": "main",
      "type": "application",
      "name": "My Main App"
    },
    "ui-components": {
      "repository": "https://github.com/myorg/ui-library",
      "branch": "main",
      "type": "library",
      "name": "UI Components Library"
    }
  }
}
```

**Project Types:**
- `application` - Main app with pages and features
- `library` - Reusable component library

## Database Management

### Option 1: Adminer Web UI (Recommended for WSL/Linux)

```
http://localhost:8080
```

**Login credentials:**
- System: PostgreSQL
- Server: `postgres`
- Username: `postgres`
- Password: `postgres`
- Database: `frontend_mcp`

**Features:**
- Browse tables and data
- Execute SQL queries
- Export data
- No installation required (runs in browser)

### Option 2: Command Line

```bash
# Connect to database
docker exec -it frontend-geo-mcp-db psql -U postgres -d frontend_mcp

# Common queries
\dt                 # List tables
\d components       # Describe components table
SELECT * FROM components LIMIT 5;  # View data
\q                  # Exit
```

## Database Migrations with Alembic

Alembic manages database schema changes and version control.

### View Migration Status

```bash
# Show current database revision
uv run alembic current

# Show all migrations
uv run alembic history

# Show detailed info
uv run alembic history --verbose
```

### Apply Migrations

```bash
# Apply all pending migrations to latest
uv run alembic upgrade head

# Apply next single migration
uv run alembic upgrade +1

# Apply specific revision
uv run alembic upgrade abc123def456
```

### Rollback Migrations

```bash
# Rollback to previous migration
uv run alembic downgrade -1

# Rollback multiple versions
uv run alembic downgrade -2

# Rollback to specific revision
uv run alembic downgrade abc123def456
```

### Create New Migrations

When you modify `src/models.py`, create a new migration:

```bash
# Generate migration automatically
uv run alembic revision --autogenerate -m "Add new_column to components"
```

This creates a new file in `migrations/versions/` with:
- Upgrade function (applying changes)
- Downgrade function (reverting changes)

Review the migration file, then apply it:

```bash
uv run alembic upgrade head
```

### Manual Migration

For complex changes:

```bash
# Create empty migration
uv run alembic revision -m "Custom migration"

# Edit migrations/versions/xxxxx_custom_migration.py
# Add your SQL operations in upgrade() and downgrade()

# Apply it
uv run alembic upgrade head
```

## Syncing Projects

### Sync Specific Project

```bash
# Sync one project
uv run python scripts/sync_projects.py --project my-main-app

# Output:
# 🔄 Syncing project: my-main-app
# 📍 Repository: https://github.com/myorg/main-app
# 🌿 Branch: main
# ✅ Connected to database with SQLAlchemy
# 📥 Cloning https://github.com/myorg/main-app...
# 🔍 Scanning components...
# 💾 Saving components...
# ✅ Sync completed: 42 components saved
```

### Sync All Projects

```bash
uv run python scripts/sync_projects.py --all
```

### Sync from MCP Tools

```bash
# Using the @frontend-gps sync_project tool
@frontend-gps sync_project("my-main-app")
```

## Running MCP Server

### Development Mode

```bash
# Start with hot-reload
fastmcp dev src/server.py:mcp
```

Features:
- Auto-reloads on code changes
- Direct stdio connection
- Good for development

### Inspection Mode

```bash
# Start with visual inspector
fastmcp inspect src/server.py:mcp
```

Open browser to see:
- Available tools
- Tool parameters
- Test tool calls
- Response formatting

### Production Mode (HTTP)

```bash
# Start HTTP server
uv run python src/server.py --http
```

Then access at:
- `http://localhost:8080` (check actual PORT from logs)

## Testing

### Test Database Connection

```bash
uv run python scripts/test_local_db.py
```

### Explore Database Interactively

```bash
uv run python scripts/explore_db.py
```

Allows browsing:
- All projects
- All components
- Components by project
- Component details

### Test MCP Tools

```bash
# Start inspection mode
fastmcp inspect src/server.py:mcp

# Open browser and test each tool:
# - find_component
# - get_component_details
# - search_by_hook
# - search_by_jsdoc
# etc.
```

## Troubleshooting

### Docker Issues

**Problem:** "Cannot connect to Docker daemon"

```bash
# Make sure Docker Desktop is running
# Then restart:
docker-compose down
docker-compose up -d
```

**Problem:** Port 5432 already in use

```bash
# Check what's using port 5432
lsof -i :5432

# Kill the process or change docker-compose port
```

### Database Issues

**Problem:** "relation 'components' does not exist"

```bash
# Check migration status
uv run alembic current

# Apply migrations
uv run alembic upgrade head

# Or restart setup
./scripts/setup_local_db.sh
```

**Problem:** Connection refused to localhost:5432

```bash
# Make sure PostgreSQL container is running
docker ps | grep frontend-mcp-db

# If not, start it
docker-compose up -d postgres
```

### Migration Issues

**Problem:** "Alembic revision not found"

```bash
# Check available revisions
uv run alembic history

# Make sure you're in project root directory
pwd  # Should end with /frontend-geo-mcp
```

### MCP Issues

**Problem:** "ModuleNotFoundError: No module named 'src'"

```bash
# Make sure you're in project root
cd /path/to/frontend-geo-mcp

# Reinstall dependencies
uv sync

# Try again
fastmcp dev src/server.py:mcp
```

**Problem:** Tools not showing in Cursor

```bash
# Restart MCP server
# Check for import errors:
uv run python -c "from src.server import mcp; print('OK')"

# Check models are valid:
uv run python -c "from src.models import Base; print('OK')"
```

## Next Steps

1. **Configure Projects** - Edit `.mcp-config.json` with your repositories
2. **Sync Components** - Run `uv run python scripts/sync_projects.py --all`
3. **Explore Data** - Use Adminer at `http://localhost:8080`
4. **Test Tools** - Run `fastmcp inspect src/server.py:mcp`
5. **Connect Cursor** - Add MCP server to Cursor's `mcp.json` configuration

## Useful Commands Reference

```bash
# Development
uv sync                                    # Install/update dependencies
fastmcp dev src/server.py:mcp             # Run in development mode
fastmcp inspect src/server.py:mcp         # Run with inspector

# Database
./scripts/setup_local_db.sh                # Initialize database
uv run alembic upgrade head                # Apply migrations
uv run alembic downgrade -1                # Rollback migration
uv run python scripts/test_local_db.py     # Test connection

# Projects
uv run python scripts/sync_projects.py --project <id>  # Sync one project
uv run python scripts/sync_projects.py --all           # Sync all projects
uv run python scripts/explore_db.py                    # Browse database

# Docker
docker-compose up -d                       # Start services
docker-compose down                        # Stop services
docker-compose logs -f postgres            # View logs
docker-compose down -v                     # Reset everything
```

## Support

For issues or questions:
1. Check the [Architecture Guide](architecture/ARCHITECTURE.md)
2. Review the [Database Reference](database/DATABASE.md)
3. Check the [Tools Documentation](tools/TOOLS.md)
4. Open a GitHub issue with details
