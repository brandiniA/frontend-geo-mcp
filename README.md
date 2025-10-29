# Frontend GPS 🚀

**Navigator and Code Reviewer for React Projects**

MCP (Model Context Protocol) server that indexes React components from GitHub repositories and provides intelligent search and navigation capabilities through Cursor AI.

## ✨ Features

- 🔍 **Component Search**: Find React components across multiple projects by name
- 📚 **JSDoc Documentation**: Extract and search component documentation
- 📦 **Props & Hooks Detection**: Automatically extract component props and React hooks
- 🏢 **Multi-Project Support**: Index and search across multiple repositories simultaneously
- 🔄 **Auto-Sync**: Clone and index repositories from GitHub
- 💾 **PostgreSQL Backend**: Fast and reliable component database with SQLAlchemy ORM
- 🚀 **MCP Integration**: Native integration with Cursor AI
- 📝 **Version Control**: Database migrations with Alembic

## 📋 Requirements

- Python 3.12+
- Docker Desktop (for local PostgreSQL)
- [uv](https://github.com/astral-sh/uv) package manager
- Git

## 📦 Tech Stack

- **FastMCP 2.13.0+** - MCP server framework
- **SQLAlchemy 2.0+** - ORM for database operations
- **Pydantic 2.0+** - Data validation
- **Alembic** - Database migrations
- **PostgreSQL 15** - Database engine
- **Python 3.12** - Runtime

## Estructura del Proyecto

```
frontend-geo-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py              # MCP Server entry point
│   ├── models.py              # SQLAlchemy + Pydantic models
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── navigator.py       # Component search and navigation
│   │   ├── validator.py       # Code validation tools
│   │   └── guide.py           # Project guidance
│   ├── registry/
│   │   ├── __init__.py
│   │   ├── database_client.py # Database ORM client
│   │   └── backup.database_client.py # Legacy backup
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── indexer.py         # Repository indexing
│   │   ├── parser.py          # React component parser
│   │   └── cache.py           # Caching system
│   └── config/
│       └── rules.py           # Validation rules
├── scripts/
│   ├── setup_local_db.sh      # Database initialization
│   ├── test_local_db.py       # Connection test
│   ├── sync_projects.py       # Manual project sync
│   └── explore_db.py          # Database explorer
├── migrations/                # Alembic database migrations
│   ├── env.py                 # Migration environment config
│   ├── versions/
│   │   └── 001_initial_schema.py
│   └── README
├── database/                  # Database configuration
│   └── README.md
├── docs/                      # Documentation
│   ├── index.md               # Documentation portal
│   ├── SETUP.md               # Setup guide
│   ├── database/
│   │   └── DATABASE.md        # Database reference
│   ├── tools/
│   │   └── TOOLS.md           # Tools documentation
│   └── architecture/
│       └── ARCHITECTURE.md    # Architecture guide
├── pyproject.toml             # Python dependencies
├── alembic.ini                # Alembic config
├── docker-compose.yml         # Docker services
├── Dockerfile                 # Production Docker image
├── fastmcp.json               # FastMCP configuration
└── .mcp-config.json           # Project configuration
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Clone the repository
git clone https://github.com/your-org/frontend-geo-mcp
cd frontend-geo-mcp

# Install dependencies with UV
uv sync
```

### 2. Setup Local Database

```bash
# Make setup script executable
chmod +x scripts/setup_local_db.sh

# Run database setup (starts PostgreSQL, applies Alembic migrations)
./scripts/setup_local_db.sh
```

This will:
- Start PostgreSQL container
- Apply Alembic migrations automatically
- Create all necessary tables
- Start Adminer and pgAdmin services

### 3. Configure Environment

```bash
# Copy example config
cp config.env.example .env

# Edit .env with your values (defaults work for local development)
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/frontend_mcp
```

### 4. Test Connection

```bash
uv run python scripts/test_local_db.py
```

### 5. Configure Projects

Edit `.mcp-config.json`:

```json
{
  "projects": {
    "my-app": {
      "repository": "https://github.com/user/my-app",
      "branch": "main",
      "type": "application"
    },
    "ui-library": {
      "repository": "https://github.com/user/ui-library",
      "branch": "main",
      "type": "library"
    }
  }
}
```

### 6. Sync Projects

```bash
# Sync specific project
uv run python scripts/sync_projects.py --project my-app

# Sync all projects
uv run python scripts/sync_projects.py --all
```

### 7. Run MCP Server

```bash
# Development mode with hot-reload
fastmcp dev src/server.py:mcp

# Visual inspector for testing tools
fastmcp inspect src/server.py:mcp

# Production mode (HTTP)
uv run python src/server.py --http
```

## 🗄️ Database Management

### Adminer Web UI (Recommended)

```
http://localhost:8080
```

**Login credentials:**
- System: PostgreSQL
- Server: `postgres`
- Username: `postgres`
- Password: `postgres`
- Database: `frontend_mcp`

### CLI Access

```bash
docker exec -it frontend-mcp-db psql -U postgres -d frontend_mcp
```

## 🔄 Database Migrations (Alembic)

### View Migration Status

```bash
# Show current revision
uv run alembic current

# Show all revisions
uv run alembic history
```

### Apply Migrations

```bash
# Apply all pending migrations
uv run alembic upgrade head

# Apply specific migration
uv run alembic upgrade +1
```

### Rollback Migrations

```bash
# Rollback last migration
uv run alembic downgrade -1

# Rollback to specific revision
uv run alembic downgrade 001
```

### Create New Migration

When you modify `src/models.py`:

```bash
# Auto-generate migration
uv run alembic revision --autogenerate -m "Add new_field to Component"

# Review the generated migration file in migrations/versions/

# Apply it
uv run alembic upgrade head
```

## 📚 MCP Tools

### Search Tools

- **`find_component`** - Find components by name
  ```
  @frontend-gps find_component("Button")
  @frontend-gps find_component("Button", project_id="ui-library")
  ```

- **`search_by_hook`** - Find components using specific hooks
  ```
  @frontend-gps search_by_hook("useState")
  @frontend-gps search_by_hook("useEffect")
  ```

- **`search_by_jsdoc`** - Search documentation
  ```
  @frontend-gps search_by_jsdoc("click handler")
  @frontend-gps search_by_jsdoc("validation", project_id="ui-library")
  ```

### Detail Tools

- **`get_component_details`** - Get component metadata
  ```
  @frontend-gps get_component_details("Button", "ui-library")
  ```

- **`get_component_docs`** - Get full JSDoc documentation
  ```
  @frontend-gps get_component_docs("Button", "ui-library")
  ```

### Browse Tools

- **`list_components`** - List all indexed components
  ```
  @frontend-gps list_components()
  @frontend-gps list_components(project_id="ui-library")
  ```

- **`list_projects`** - Show all configured projects
  ```
  @frontend-gps list_projects()
  ```

### Admin Tools

- **`sync_project`** - Manually sync a project
  ```
  @frontend-gps sync_project("my-app")
  ```

- **`get_stats`** - View indexing statistics
  ```
  @frontend-gps get_stats()
  ```

## 🐳 Docker

### Local Development

```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f postgres

# Stop services
docker-compose down

# Reset everything (careful!)
docker-compose down -v
```

### Database Container

The PostgreSQL container:
- Persists data in `postgres_data` volume
- Exposes port 5432
- Includes health checks
- Auto-applies Alembic migrations on startup

## 🚢 Deployment

### Railway/Render

1. Create PostgreSQL database
2. Set `DATABASE_URL` environment variable
3. Deploy with:
   ```bash
   uv run python src/server.py --http
   ```

### Dockerfile

```bash
docker build -t frontend-geo-mcp:latest .
docker run -e DATABASE_URL=... frontend-geo-mcp:latest
```

## 📖 Documentation

See the comprehensive guides in `/docs`:

- **[Setup Guide](docs/SETUP.md)** - Detailed installation and configuration
- **[Database Reference](docs/database/DATABASE.md)** - Schema and queries
- **[Tools Documentation](docs/tools/TOOLS.md)** - Complete tools reference
- **[Architecture Guide](docs/architecture/ARCHITECTURE.md)** - System design
- **[Documentation Index](docs/index.md)** - All documentation

## 🛠️ Development

### Project Structure

**ORM & Models:**
- `src/models.py` - SQLAlchemy models with Pydantic validation

**Database:**
- `src/registry/database_client.py` - Async-compatible database client using SQLAlchemy
- `migrations/` - Alembic version control for schema changes

**Indexing:**
- `src/utils/parser.py` - React component JSDoc parser
- `src/utils/indexer.py` - Repository cloning and component extraction

**Tools:**
- `src/tools/navigator.py` - Search and navigation tools
- `src/server.py` - FastMCP server with tool definitions

### Testing

```bash
# Test database connection
uv run python scripts/test_local_db.py

# Explore database
uv run python scripts/explore_db.py

# Test MCP tools
fastmcp inspect src/server.py:mcp
```

## 🐛 Troubleshooting

### Database Connection Failed

```bash
# Check if PostgreSQL is running
docker ps | grep frontend-mcp-db

# Check logs
docker-compose logs postgres

# Restart containers
docker-compose restart
```

### Migration Issues

```bash
# Check migration status
uv run alembic current

# View migration history
uv run alembic history

# Rollback if needed
uv run alembic downgrade -1
```

### MCP Not Loading Tools

```bash
# Restart MCP server
fastmcp dev src/server.py:mcp

# Check for import errors
uv run python -c "from src.server import mcp; print(mcp)"
```

## 📝 Environment Variables

```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/frontend_mcp

# Temporary directory for cloned repos
TEMP_DIR=/tmp/mcp-repos

# API Key (local development)
API_KEY=local-dev-key

# GitHub (optional, for private repos)
GITHUB_TOKEN=

# Server
PORT=8080
```

