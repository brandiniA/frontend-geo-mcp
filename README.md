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

## 📁 Project Structure

```
frontend-geo-mcp/
├── src/
│   ├── server.py              # MCP Server entry point
│   ├── models.py              # SQLAlchemy + Pydantic models
│   ├── tools/
│   │   ├── navigator.py       # Component search and navigation
│   │   ├── validator.py       # Code validation tools
│   │   └── guide.py           # Project guidance
│   ├── registry/
│   │   └── database_client.py # Database ORM client
│   └── utils/
│       ├── indexer.py         # Repository indexing
│       ├── parser.py          # React component parser
│       └── cache.py           # Caching system
├── scripts/
│   ├── setup_local_db.sh      # Database initialization
│   ├── test_local_db.py       # Connection test
│   ├── sync_projects.py       # Manual project sync
│   └── explore_db.py          # Database explorer
├── migrations/                # Alembic database migrations
├── docs/                      # Documentation
├── pyproject.toml             # Python dependencies
├── docker-compose.yml         # Docker services
└── Dockerfile                 # Production Docker image
```

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/your-org/frontend-geo-mcp
cd frontend-geo-mcp
uv sync
```

### 2. Setup Database

```bash
chmod +x scripts/setup_local_db.sh
./scripts/setup_local_db.sh
```

This starts PostgreSQL, applies migrations, and creates necessary tables.

### 3. Configure & Test

```bash
# Copy environment template
cp config.env.example .env

# Test database connection
uv run python scripts/test_local_db.py
```

### 4. Configure Projects

Edit `.mcp-config.json` with your repositories:

```json
{
  "projects": {
    "my-app": {
      "repository": "https://github.com/user/my-app",
      "branch": "main",
      "type": "application"
    }
  }
}
```

### 5. Sync & Run

```bash
# Sync projects
uv run python scripts/sync_projects.py --all

# Start MCP server
fastmcp dev src/server.py:mcp
```

**For detailed setup instructions, see [📖 SETUP.md](docs/SETUP.md)**

---

## 📚 MCP Tools

### Search Tools

- **`find_component`** - Find components by name
- **`search_by_hook`** - Find components using specific hooks
- **`search_by_jsdoc`** - Search component documentation

### Detail Tools

- **`get_component_details`** - Get component metadata
- **`get_component_docs`** - Get full JSDoc documentation

### Browse Tools

- **`list_components`** - List all indexed components
- **`list_projects`** - Show all configured projects

### Admin Tools

- **`sync_project`** - Manually sync a project
- **`get_stats`** - View indexing statistics

**For complete tools reference, see [📖 Tools Documentation](docs/tools/TOOLS.md)**

---

## 🗄️ Database Management

### Web UI (Adminer)
```
http://localhost:8080
```

### CLI Access
```bash
docker exec -it frontend-mcp-db psql -U postgres -d frontend_mcp
```

**For database migrations and detailed management, see [📖 SETUP.md](docs/SETUP.md#database-migrations-with-alembic)**

---

## 🐳 Docker

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# View logs
docker-compose logs -f postgres
```

---

## 🚢 Deployment

### Railway/Render

```bash
# Set DATABASE_URL environment variable
uv run python src/server.py --http
```

### Docker Build

```bash
docker build -t frontend-geo-mcp:latest .
docker run -e DATABASE_URL=... frontend-geo-mcp:latest
```

---

## 📖 Documentation

Complete guides available in `/docs`:

| Document | Purpose |
|----------|---------|
| [**Setup Guide**](docs/SETUP.md) | Detailed installation, configuration, migrations |
| [**Tools Reference**](docs/tools/TOOLS.md) | Complete tools documentation |
| [**Database Reference**](docs/database/DATABASE.md) | Schema and queries |
| [**Architecture Guide**](docs/architecture/ARCHITECTURE.md) | System design |
| [**Documentation Index**](docs/index.md) | All documentation portal |

---

## 🛠️ Development

### Testing

```bash
# Test database connection
uv run python scripts/test_local_db.py

# Explore database interactively
uv run python scripts/explore_db.py

# Test MCP tools with visual inspector
fastmcp inspect src/server.py:mcp
```

### Key Files

- `src/models.py` - SQLAlchemy models
- `src/registry/database_client.py` - Database client
- `src/tools/navigator.py` - Search tools
- `src/server.py` - FastMCP server

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Database connection failed | Check [SETUP.md troubleshooting](docs/SETUP.md#troubleshooting) |
| Migration issues | See [Alembic section](docs/SETUP.md#database-migrations-with-alembic) |
| MCP tools not loading | See [MCP issues](docs/SETUP.md#mcp-issues) |

---

## 📝 Environment Variables

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/frontend_mcp
TEMP_DIR=/tmp/mcp-repos
API_KEY=local-dev-key
GITHUB_TOKEN=          # Optional
PORT=8080
```

See [SETUP.md](docs/SETUP.md#4-environment-configuration) for detailed configuration.

---

## 📞 Support

- Check the [Setup Guide](docs/SETUP.md)
- Review the [Architecture Guide](docs/architecture/ARCHITECTURE.md)
- See the [Database Reference](docs/database/DATABASE.md)
- Open a GitHub issue with details

