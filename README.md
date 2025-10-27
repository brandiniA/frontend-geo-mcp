# Frontend GPS 🚀

**Navigator and Code Reviewer for React Projects**

MCP (Model Context Protocol) server that indexes React components from GitHub repositories and provides intelligent search and navigation capabilities through Cursor AI.

## ✨ Features

- 🔍 **Component Search**: Find React components across multiple projects
- 📦 **Props & Hooks Detection**: Automatically extract component props and hooks
- 🏢 **Multi-Project Support**: Index and search across multiple repositories
- 🔄 **Auto-Sync**: Clone and index repositories from GitHub
- 💾 **PostgreSQL Backend**: Fast and reliable component database
- 🚀 **MCP Integration**: Native integration with Cursor AI

## 📋 Requirements

- Python 3.12+
- Docker Desktop (for local PostgreSQL)
- [uv](https://github.com/astral-sh/uv) package manager
- Git

## Estructura del Proyecto

```
frontend-geo-mcp/
├── src/
│   ├── __init__.py
│   ├── server.py           # Entry point principal
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── navigator.py    # Herramientas de navegación
│   │   ├── validator.py    # Validación de código
│   │   └── guide.py        # Guía de proyecto
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── indexer.py      # Indexación de componentes
│   │   ├── cache.py        # Sistema de cache
│   │   └── parser.py       # Parser de código React
│   └── config/
│       └── rules.py        # Reglas de validación
├── pyproject.toml
├── uv.lock
├── README.md
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

# Run database setup
./scripts/setup_local_db.sh
```

### 3. Configure Environment

```bash
# Copy example config
cp config.env.example .env

# Edit .env with your values (defaults work for local development)
```

### 4. Test Connection

```bash
python scripts/test_local_db.py
```

### 5. Sync a Project

```bash
# Edit .mcp-config.json with your projects
# Then sync:
python scripts/sync_projects.py --project test-project
```

### 6. Run MCP Server

```bash
# Development mode with hot-reload
fastmcp dev src/server.py:mcp

# Visual inspector for testing tools
fastmcp inspect src/server.py:mcp

# For Cursor integration (stdio mode)
python src/server.py

# For HTTP testing
python src/server.py --http
```

## 📖 Full Documentation

- **[Complete Setup Guide](docs/SETUP.md)** - Detailed installation and configuration
- **[Custom Commands](docs/COMANDOS_PERSONALIZADOS.md)** - Helper commands for development

## 🔧 Configuration for Cursor

Add to your Cursor MCP settings:

```json
{
  "mcpServers": {
    "frontend-gps": {
      "command": "python",
      "args": ["/absolute/path/to/frontend-geo-mcp/src/server.py"],
      "env": {
        "DATABASE_URL": "postgresql://postgres:postgres@localhost:5432/frontend_mcp",
        "API_KEY": "local-dev-key"
      }
    }
  }
}
```

## 💡 Usage Examples

Once configured in Cursor:

```
@frontend-gps find_component("Button")
@frontend-gps get_component_details("Button", "ui-library")
@frontend-gps list_components(component_type="page")
@frontend-gps search_by_hook("useState")
@frontend-gps sync_project("my-app")
@frontend-gps get_stats()
```

## 🛠️ Available Tools

- `find_component(query, project_id?)` - Search for components
- `get_component_details(name, project_id)` - Get detailed component info
- `list_components(project_id?, type?)` - List all components
- `search_by_hook(hook_name)` - Find components using a specific hook
- `sync_project(project_id)` - Sync a project from GitHub
- `list_projects()` - List all configured projects
- `get_stats()` - Get indexing statistics

## 🐳 Docker Commands

```bash
# Start database and tools
docker-compose up -d

# Stop database
docker-compose down

# Reset database (delete all data)
docker-compose down -v && ./scripts/setup_local_db.sh

# View logs
docker-compose logs -f postgres
```

## 📊 Explore Database

### Web UI - Adminer (Recommended for WSL/Linux)

```
http://localhost:8080
```

**Login credentials:**
- System: PostgreSQL
- Server: `host.docker.internal` (or `postgres` if on Linux)
- Username: `postgres`
- Password: `postgres`
- Database: `frontend_mcp`

### Web UI - pgAdmin

```
http://localhost:5050
```

**Login credentials:**
- Email: `admin@example.com`
- Password: `admin`

### Command Line - psql

```bash
docker exec -it frontend-mcp-db psql -U postgres -d frontend_mcp

# Useful commands:
\dt                      # List tables
SELECT * FROM projects;  # View projects
SELECT * FROM components LIMIT 5; # View components
\q                      # Exit
```

### Python Script - Interactive Explorer

```bash
python scripts/explore_db.py
```

## 🚀 Deployment

See [SETUP.md](docs/SETUP.md) for deployment instructions to Railway or Render.

## 📁 Project Structure

```
frontend-geo-mcp/
├── src/
│   ├── server.py              # MCP Server entry point
│   ├── tools/
│   │   └── navigator.py       # Component navigation tools
│   ├── utils/
│   │   ├── parser.py          # React component parser
│   │   └── indexer.py         # Repository indexer
│   └── registry/
│       └── database_client.py # PostgreSQL client
├── scripts/
│   ├── setup_local_db.sh      # Database setup script
│   ├── test_local_db.py       # Connection test
│   └── sync_projects.py       # Manual sync script
├── database/migrations/       # Database schema
├── docker-compose.yml         # Local PostgreSQL
├── Dockerfile                 # Production deployment
└── .mcp-config.json          # Project configuration
```

## 🤝 Contributing

Contributions are welcome! Please read the setup guide and ensure all tests pass before submitting a PR.

## 📄 License

MIT License - see LICENSE file for details
