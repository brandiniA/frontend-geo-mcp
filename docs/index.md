# Frontend GPS Documentation

Complete documentation for the Frontend GPS MCP server.

## 📚 Documentation Index

### Getting Started
- **[Setup Guide](SETUP.md)** - Installation, configuration, and database setup
  - Install dependencies with uv
  - Setup PostgreSQL with Docker
  - Configure Alembic migrations
  - Test database connection
  - Sync your first project

### Core Documentation

#### [Database Reference](database/DATABASE.md)
Complete database documentation including:
- Schema design (projects, components tables)
- Exploration tools (Adminer, pgAdmin, CLI)
- Useful SQL queries
- Data management strategies
- Alembic migration management

#### [Tools Reference](tools/TOOLS.md)
Complete MCP tools documentation:
- Search tools (find_component, search_by_hook, search_by_jsdoc)
- Detail tools (get_component_details, get_component_docs)
- Browse tools (list_components, list_projects)
- Admin tools (sync_project, get_stats)
- Tool parameters and examples

#### [Architecture Guide](architecture/ARCHITECTURE.md)
Technical documentation:
- System architecture overview
- Component interactions
- Data flow diagrams
- Design patterns
- Key technologies

#### [Parser Validation Guide](parser/VALIDATION.md)
Component naming and validation rules:
- Component naming conventions
- Validation rules and criteria
- What gets indexed vs rejected
- Directory structure recommendations
- Best practices

### Quick Reference

**Tech Stack:**
- FastMCP 2.13.0+ - MCP server framework
- SQLAlchemy 2.0+ - Database ORM
- Pydantic 2.0+ - Data validation
- Alembic - Database migrations
- PostgreSQL 15 - Database engine
- Python 3.12+ - Runtime

**Key Features:**
- 🔍 Component search across multiple projects
- 📚 JSDoc documentation extraction
- 📦 Props and hooks detection
- 🔄 Automatic GitHub sync
- 💾 PostgreSQL backend with ORM
- 🚀 Cursor AI integration

## 🗂️ Project Structure

```
frontend-geo-mcp/
├── src/
│   ├── server.py              # MCP server entry point
│   ├── models.py              # SQLAlchemy + Pydantic models
│   ├── tools/navigator.py     # Search and navigation
│   ├── registry/database_client.py  # Database ORM
│   └── utils/parser.py        # Component parser
├── migrations/                # Alembic database versions
│   ├── env.py                 # Migration environment
│   └── versions/001_initial_schema.py
├── scripts/
│   ├── setup_local_db.sh      # Database initialization
│   ├── test_local_db.py       # Connection test
│   ├── sync_projects.py       # Project sync
│   └── explore_db.py          # Database explorer
├── docs/
│   ├── index.md               # This file
│   ├── SETUP.md               # Setup guide
│   ├── database/DATABASE.md   # Database reference
│   ├── tools/TOOLS.md         # Tools documentation
│   └── architecture/ARCHITECTURE.md
└── database/
    └── README.md              # Database folder info
```

## 🚀 Quick Start Commands

```bash
# 1. Install
git clone <repo>
cd frontend-geo-mcp
uv sync

# 2. Setup database
./scripts/setup_local_db.sh

# 3. Configure
cp config.env.example .env

# 4. Test
uv run python scripts/test_local_db.py

# 5. Sync projects
uv run python scripts/sync_projects.py --all

# 6. Run server
fastmcp dev src/server.py:mcp
```

## 📖 Documentation by Task

### I want to...

**Install and setup the project**
→ Read [Setup Guide](SETUP.md)

**Understand the database**
→ Read [Database Reference](database/DATABASE.md)

**Learn about MCP tools**
→ Read [Tools Reference](tools/TOOLS.md)

**Understand the architecture**
→ Read [Architecture Guide](architecture/ARCHITECTURE.md)

**Manage database migrations**
→ See [SETUP.md - Database Migrations](SETUP.md#database-migrations-with-alembic)

**Add a new project**
→ Edit `.mcp-config.json` and run sync command

**Query components**
→ Use tools in Cursor or read [Tools Reference](tools/TOOLS.md)

**Deploy to production**
→ See [SETUP.md - Deployment](SETUP.md#troubleshooting)

**Troubleshoot issues**
→ See [SETUP.md - Troubleshooting](SETUP.md#troubleshooting)

**Understand component validation**
→ Read [Parser Validation Guide](parser/VALIDATION.md)

## 🔗 External Resources

- **FastMCP Documentation** - https://gofastmcp.com
- **SQLAlchemy Documentation** - https://docs.sqlalchemy.org
- **Alembic Documentation** - https://alembic.sqlalchemy.org
- **PostgreSQL Documentation** - https://www.postgresql.org/docs
- **Pydantic Documentation** - https://docs.pydantic.dev

## 💡 Common Tasks

### View Database
```bash
# Web UI (easiest)
# Go to http://localhost:8080 (Adminer)

# Command line
docker exec -it frontend-mcp-db psql -U postgres
```

### Sync Projects
```bash
uv run python scripts/sync_projects.py --project <name>
```

### Check Migrations
```bash
uv run alembic current
uv run alembic history
```

### Search Components in Cursor
```
@frontend-gps find_component("Button")
@frontend-gps search_by_jsdoc("click handler")
```

### Test MCP Tools
```bash
fastmcp inspect src/server.py:mcp
# Then open browser and test tools
```

## 📝 File Descriptions

| File | Purpose |
|------|---------|
| `README.md` | Project overview and quick start |
| `SETUP.md` | Detailed installation and setup guide |
| `database/DATABASE.md` | Database schema and queries |
| `tools/TOOLS.md` | MCP tools reference |
| `architecture/ARCHITECTURE.md` | System design and components |
| `database/README.md` | Database folder information |
| `pyproject.toml` | Python dependencies |
| `alembic.ini` | Alembic configuration |
| `.mcp-config.json` | Project configuration |
| `docker-compose.yml` | Docker services |

## 🆘 Need Help?

1. **Check the relevant documentation page** - Each guide covers specific topics
2. **Review examples** - Each tool documentation includes examples
3. **Check troubleshooting** - [SETUP.md](SETUP.md#troubleshooting) has common issues
4. **Explore database** - Use Adminer to inspect data structure
5. **Test tools** - Use `fastmcp inspect` to test tools interactively

## 📞 Support

For issues:
1. Check the appropriate documentation page
2. Review troubleshooting section
3. Open a GitHub issue with error details

---

**Last Updated:** October 2025
**Version:** 1.0.0
**Status:** Production Ready ✅

Start with [Setup Guide](SETUP.md) →
