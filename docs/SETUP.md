# Frontend GPS - Setup Guide

Complete guide to set up and run the Frontend GPS MCP Server.

## 📋 Prerequisites

- Python 3.12+
- Docker Desktop (for local PostgreSQL)
- Git
- UV package manager (recommended) or pip

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Install dependencies with UV
uv sync

# Or with pip
pip install -r pyproject.toml
```

### 2. Setup Local Database

```bash
# Make script executable
chmod +x scripts/setup_local_db.sh

# Run setup script
./scripts/setup_local_db.sh
```

This will:
- Start PostgreSQL in Docker
- Create the `frontend_mcp` database
- Run migrations to create tables

### 3. Configure Environment

```bash
# Copy example config
cp config.env.example .env

# Edit .env with your values
# For local development, the defaults should work
```

**`.env` file:**
```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/frontend_mcp
API_KEY=local-dev-key
GITHUB_TOKEN=  # Optional, only for private repos
TEMP_DIR=/tmp/mcp-repos
PORT=8080
```

### 4. Test Database Connection

```bash
python scripts/test_local_db.py
```

You should see:
```
✅ Connected successfully!
📊 Tables found:
   - projects: 1 rows
   - components: 0 rows
```

### 5. Configure Projects

Edit `.mcp-config.json` to add your projects:

```json
{
  "projects": {
    "my-app": {
      "name": "My Application",
      "repository": "https://github.com/user/my-app",
      "branch": "main",
      "type": "application"
    },
    "ui-library": {
      "name": "UI Component Library",
      "repository": "https://github.com/company/ui-library",
      "branch": "main",
      "type": "library"
    }
  }
}
```

### 6. Sync Projects

```bash
# Sync a specific project
python scripts/sync_projects.py --project my-app

# Or sync all projects
python scripts/sync_projects.py --all
```

### 7. Run MCP Server

```bash
# Development mode with hot-reload (recommended during development)
fastmcp dev src/server.py:mcp

# Visual inspector to test tools and debug
fastmcp inspect src/server.py:mcp

# For Cursor integration (stdio mode - production)
python src/server.py

# For HTTP testing
python src/server.py --http
```

## 🔧 FastMCP CLI Commands

The FastMCP CLI provides several useful commands for development:

### Development Mode

```bash
# Start server with hot-reload (automatically restarts on file changes)
fastmcp dev src/server.py:mcp

# Start with verbose logging
fastmcp dev src/server.py:mcp --verbose

# Run with specific port (for HTTP mode)
fastmcp dev src/server.py:mcp --transport http --port 8000
```

### Inspector (Testing UI)

```bash
# Open visual inspector to test your MCP tools
fastmcp inspect src/server.py:mcp

# This opens a web interface where you can:
# - Test each tool with different parameters
# - See tool responses in real-time
# - Debug issues interactively
```

### Direct Python Execution

```bash
# Standard stdio mode (for Cursor integration)
python src/server.py

# HTTP mode (for remote testing)
python src/server.py --http
```

## 📊 Exploring the Database

### Option 1: Adminer Web UI (Recommended for WSL/Linux)

Adminer is a lightweight, browser-based database management tool - no installation needed!

```
http://localhost:8080
```

**Login with these credentials:**
- **System:** PostgreSQL
- **Server:** `postgres`
- **Username:** `postgres`
- **Password:** `postgres`
- **Database:** `frontend_mcp`

**Features:**
- Browse tables and data
- Execute custom SQL queries
- Export/Import data
- Simple and intuitive UI

### Option 2: pgAdmin Web UI

Full-featured PostgreSQL management tool.

```
http://localhost:5050
```

**Login with:**
- **Email:** `admin@example.com`
- **Password:** `admin`

Then create a new server connection with PostgreSQL credentials.

### Option 3: Command Line - psql

Direct database access from terminal:

```bash
# Connect to the database
docker exec -it frontend-mcp-db psql -U postgres -d frontend_mcp

# Useful psql commands:
\dt                              # List all tables
\d components                    # Describe components table structure
SELECT * FROM projects;          # View all projects
SELECT * FROM components LIMIT 5; # View first 5 components
SELECT COUNT(*) FROM components; # Count total components
SELECT name, component_type FROM components GROUP BY component_type; # Count by type
\q                              # Exit psql
```

### Option 4: Python Interactive Explorer

Custom script for easy exploration:

```bash
python scripts/explore_db.py
```

This script provides:
- Interactive menu
- Search components by name
- View component details (props, hooks, imports)
- Project statistics
- Component count by type

## 🔧 Configuration for Cursor

Add to your Cursor settings (`.cursor/mcp_settings.json` or global settings):

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

**Or use the full path from your .env:**

```json
{
  "mcpServers": {
    "frontend-gps": {
      "command": "python",
      "args": ["/home/basr/personal/frontend-geo-mcp/src/server.py"]
    }
  }
}
```

## 📖 Usage Examples

Once configured in Cursor, you can use these commands:

### Find Components

```
@frontend-gps find_component("Button")
@frontend-gps find_component("Card", project_id="ui-library")
```

### Get Component Details

```
@frontend-gps get_component_details("Button", "ui-library")
```

### List Components

```
@frontend-gps list_components()
@frontend-gps list_components(project_id="my-app")
@frontend-gps list_components(component_type="page")
```

### Search by Hook

```
@frontend-gps search_by_hook("useState")
@frontend-gps search_by_hook("useEffect")
```

### Sync Projects

```
@frontend-gps sync_project("my-app")
@frontend-gps list_projects()
@frontend-gps get_stats()
```

## 🐳 Docker Commands

### Start Database

```bash
docker-compose up -d
```

### Stop Database

```bash
docker-compose down
```

### Reset Database (delete all data)

```bash
docker-compose down -v
./scripts/setup_local_db.sh
```

### View Logs

```bash
docker-compose logs -f postgres
```

### Connect to Database

```bash
docker exec -it frontend-mcp-db psql -U postgres -d frontend_mcp
```

## 🔍 Troubleshooting

### Database Connection Failed

1. Check Docker is running:
   ```bash
   docker ps
   ```

2. Restart database:
   ```bash
   docker-compose restart
   ```

3. Check DATABASE_URL in `.env`

### No Components Found

1. Make sure you've synced a project:
   ```bash
   python scripts/sync_projects.py --project test-project
   ```

2. Check project configuration in `.mcp-config.json`

### Import Errors

1. Make sure you're in the project root directory
2. Check Python path:
   ```bash
   python -c "import sys; print(sys.path)"
   ```

### GitHub Clone Failed

1. For private repos, add GITHUB_TOKEN to `.env`:
   ```bash
   GITHUB_TOKEN=ghp_your_token_here
   ```

2. Generate token at: https://github.com/settings/tokens

## 🚀 Deployment to Railway

### 1. Prepare for Deployment

Make sure these files are in your repo:
- `Dockerfile`
- `pyproject.toml`
- `.mcp-config.json`

### 2. Create Railway Project

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository

### 3. Configure Environment Variables

In Railway dashboard, add:

```
DATABASE_URL=postgresql://user:pass@host:5432/dbname
API_KEY=your-production-api-key
GITHUB_TOKEN=ghp_your_token
TEMP_DIR=/tmp/mcp-repos
PORT=8080
```

### 4. Add PostgreSQL Database

1. In Railway, click "New" → "Database" → "PostgreSQL"
2. Railway will automatically set DATABASE_URL

### 5. Deploy

Railway will automatically build and deploy using the Dockerfile.

## 📊 Database Schema

### Projects Table

```sql
CREATE TABLE projects (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  repository_url TEXT NOT NULL,
  branch TEXT DEFAULT 'main',
  type TEXT CHECK (type IN ('application', 'library')),
  is_active BOOLEAN DEFAULT true,
  last_sync TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Components Table

```sql
CREATE TABLE components (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  project_id TEXT REFERENCES projects(id),
  file_path TEXT NOT NULL,
  props JSONB DEFAULT '[]',
  hooks JSONB DEFAULT '[]',
  imports JSONB DEFAULT '[]',
  exports JSONB DEFAULT '[]',
  component_type TEXT,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🔐 Security Notes

- Never commit `.env` file (it's in `.gitignore`)
- Use strong passwords for production databases
- Rotate API keys regularly
- Use GitHub tokens with minimal required permissions

## 📚 Additional Resources

- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [Railway Documentation](https://docs.railway.app)

