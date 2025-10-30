# Frontend GPS - Database Documentation

Quick reference for database schema, queries, and management tools.

## 📋 Schema Overview

Three main tables store all data:

- **projects** - React projects to be indexed
- **components** - Indexed React components  
- **hooks** - Indexed custom React hooks

For detailed model documentation, see:
- [MODELS.md](MODELS.md) - Models overview and architecture
- [models/PROJECT.md](models/PROJECT.md) - Projects model
- [models/COMPONENT.md](models/COMPONENT.md) - Components model
- [models/HOOK.md](models/HOOK.md) - Hooks model

## 🔍 Exploring the Database

### Option 1: Adminer Web UI (Recommended)

```
http://localhost:8080
Username: postgres | Password: postgres | Database: frontend_mcp
```

### Option 2: Command Line
```bash
docker exec -it frontend-mcp-db psql -U postgres -d frontend_mcp
```

### Option 3: Python Explorer
```bash
python scripts/explore_db.py
```

## 📊 Quick Queries

### Get Statistics
```sql
SELECT 
  (SELECT COUNT(*) FROM projects) as total_projects,
  (SELECT COUNT(*) FROM components) as total_components,
  (SELECT COUNT(*) FROM hooks) as total_hooks;
```

### View All Projects
```sql
SELECT id, name, type, is_active, last_sync FROM projects ORDER BY name;
```

### View All Components
```sql
SELECT name, project_id, file_path, component_type FROM components ORDER BY name;
```

### View All Hooks
```sql
SELECT name, project_id, file_path, return_type FROM hooks ORDER BY name;
```

For more queries, see individual model documentation:
- [PROJECT.md - Queries](models/PROJECT.md#-useful-queries)
- [COMPONENT.md - Queries](models/COMPONENT.md#-useful-queries)
- [HOOK.md - Queries](models/HOOK.md#-useful-queries)

## 🧹 Maintenance

### Reset Entire Database
```bash
docker-compose down -v
docker-compose up -d
./scripts/setup_local_db.sh
```

### Clear All Data
```sql
DELETE FROM components;
DELETE FROM hooks;
DELETE FROM projects;
```

### Backup Database
```bash
docker exec -i frontend-mcp-db pg_dump -U postgres frontend_mcp > backup.sql
```

### Restore from Backup
```bash
docker exec -i frontend-mcp-db psql -U postgres frontend_mcp < backup.sql
```

## ❌ Troubleshooting

**Connection Refused**
- Ensure Docker is running: `docker-compose ps`
- Check credentials: postgres/postgres
- Try `host.docker.internal` instead of `localhost` on WSL

**Database Not Found**
```bash
docker-compose down -v
./scripts/setup_local_db.sh
```

## 📚 See Also

- [MODELS.md](MODELS.md) - Data models overview
- [SETUP.md](../SETUP.md) - Database setup
- [TOOLS.md](../tools/TOOLS.md) - MCP tools