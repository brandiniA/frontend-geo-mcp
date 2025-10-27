# Frontend GPS - Database Documentation

Complete reference for the Frontend GPS database schema and management.

## 📋 Schema Overview

### Tables

#### Projects Table
Stores configuration information for React projects to be indexed.

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

**Fields:**
- `id` - Unique project identifier (used in `.mcp-config.json`)
- `name` - Human-readable project name
- `repository_url` - GitHub/GitLab repository URL
- `branch` - Git branch to index (default: main)
- `type` - Project type: 'application' or 'library'
- `is_active` - Whether project is active
- `last_sync` - When project was last indexed
- `created_at` - When project was added

#### Components Table
Stores indexed React components from projects.

```sql
CREATE TABLE components (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
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

**Fields:**
- `id` - Auto-increment unique identifier
- `name` - Component name (e.g., "Button", "Card")
- `project_id` - Reference to projects table
- `file_path` - Relative path to file in repository
- `props` - JSON array of component props
- `hooks` - JSON array of React hooks used
- `imports` - JSON array of dependencies imported
- `exports` - JSON array of named exports
- `component_type` - Type: 'component', 'page', 'layout', 'hook'
- `description` - Component description from JSDoc comments
- `created_at` - When component was first indexed
- `updated_at` - When component was last updated

## 🔍 Exploring the Database

### Option 1: Adminer Web UI (Recommended)

Lightweight browser-based database tool - **no installation required**.

**URL:** `http://localhost:8080`

**Credentials:**
- System: PostgreSQL
- Server: `host.docker.internal` (WSL) or `postgres` (Linux)
- Username: `postgres`
- Password: `postgres`
- Database: `frontend_mcp`

**Features:**
- Browse tables and rows
- Execute custom SQL queries
- Export/import data
- Simple, intuitive interface

### Option 2: pgAdmin Web UI

Full-featured PostgreSQL management tool.

**URL:** `http://localhost:5050`

**Credentials:**
- Email: `admin@example.com`
- Password: `admin`

Create a new server connection with PostgreSQL credentials.

### Option 3: Command Line - psql

Direct terminal access to database.

```bash
# Connect to database
docker exec -it frontend-mcp-db psql -U postgres -d frontend_mcp
```

### Option 4: Python Explorer Script

Interactive command-line tool.

```bash
python scripts/explore_db.py
```

## 📝 Useful SQL Queries

### View All Tables
```sql
\dt
```

### View Projects
```sql
SELECT id, name, type, is_active, last_sync 
FROM projects 
ORDER BY name;
```

### View Components
```sql
SELECT name, project_id, file_path, component_type 
FROM components 
ORDER BY name;
```

### Count Components by Project
```sql
SELECT project_id, COUNT(*) as count 
FROM components 
GROUP BY project_id 
ORDER BY count DESC;
```

### Count Components by Type
```sql
SELECT component_type, COUNT(*) as count 
FROM components 
GROUP BY component_type 
ORDER BY count DESC;
```

### Find Component by Name
```sql
SELECT name, project_id, file_path, props, hooks 
FROM components 
WHERE name ILIKE '%Button%'
ORDER BY name;
```

### View Component Details
```sql
SELECT * FROM components 
WHERE name = 'Button' 
LIMIT 1;
```

### Get Props of a Component
```sql
SELECT name, props 
FROM components 
WHERE name = 'Button' 
LIMIT 1;
```

### Find Components Using Specific Hook
```sql
SELECT name, project_id 
FROM components 
WHERE hooks @> '["useState"]'
ORDER BY name;
```

### Get Recent Components
```sql
SELECT name, project_id, created_at 
FROM components 
ORDER BY created_at DESC 
LIMIT 10;
```

### Total Statistics
```sql
SELECT 
  (SELECT COUNT(*) FROM projects) as total_projects,
  (SELECT COUNT(*) FROM components) as total_components;
```

## 🔄 Data Management

### Add a New Project
```python
# Via .mcp-config.json
{
  "projects": {
    "my-project": {
      "name": "My Project",
      "repository": "https://github.com/user/my-project",
      "branch": "main",
      "type": "application"
    }
  }
}

# Then sync via MCP tool
@frontend-gps sync_project("my-project")
```

### Manual Database Insert
```sql
INSERT INTO projects (id, name, repository_url, branch, type)
VALUES ('my-project', 'My Project', 'https://github.com/user/my-project', 'main', 'application');
```

### Update Project Last Sync
```sql
UPDATE projects 
SET last_sync = NOW() 
WHERE id = 'my-project';
```

### Delete Project and Its Components
```sql
DELETE FROM projects 
WHERE id = 'my-project';
-- Components are automatically deleted due to CASCADE
```

## 🧹 Database Maintenance

### Reset Entire Database
```bash
# Stop and remove containers with volumes
docker-compose down -v

# Restart fresh
docker-compose up -d

# Run migrations
./scripts/setup_local_db.sh
```

### Clear All Components (Keep Projects)
```sql
DELETE FROM components;
```

### Clear All Data
```sql
DELETE FROM components;
DELETE FROM projects;
```

### Backup Database
```bash
# Export to SQL file
docker exec -i frontend-mcp-db pg_dump -U postgres frontend_mcp > backup.sql

# Restore from backup
docker exec -i frontend-mcp-db psql -U postgres frontend_mcp < backup.sql
```

## 📊 Database Statistics

### Storage Usage
```sql
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname NOT IN ('pg_catalog', 'information_schema')
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Slow Queries (if slow_query_log is enabled)
```sql
SELECT query, calls, total_time 
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
```

## ❌ Troubleshooting

### Connection Refused
**Problem:** Cannot connect to database in Adminer
**Solution:** 
- Use `host.docker.internal` in WSL (not localhost)
- Use `postgres` service name on native Linux
- Ensure PostgreSQL container is running: `docker-compose ps`

### Database Not Found
**Problem:** `frontend_mcp` database doesn't exist
**Solution:**
```bash
docker-compose down -v
./scripts/setup_local_db.sh
```

### Permission Denied
**Problem:** Permission error when accessing database
**Solution:**
- Verify username/password are correct (postgres/postgres)
- Check user permissions in pgAdmin

### Out of Disk Space
**Problem:** Database volume is full
**Solution:**
```bash
# Clean old data
DELETE FROM components WHERE created_at < NOW() - INTERVAL '30 days';

# Or reset everything
docker-compose down -v
```

## 📚 See Also

- [TOOLS.md](../tools/TOOLS.md) - MCP Tools documentation
- [SETUP.md](../SETUP.md) - Setup and installation
- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) - System architecture

