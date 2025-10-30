# Project Model

Represents a React project to be indexed for component discovery.

## 📋 Schema

### Database Table
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

## 🏷️ Fields

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `id` | TEXT | ✅ | - | Unique identifier (used in `.mcp-config.json`) |
| `name` | TEXT | ✅ | - | Human-readable project name |
| `repository_url` | TEXT | ✅ | - | GitHub/GitLab repository URL |
| `branch` | TEXT | ❌ | `main` | Git branch to index |
| `type` | TEXT | ❌ | `application` | `application` or `library` |
| `is_active` | BOOLEAN | ❌ | `true` | Whether project is being indexed |
| `last_sync` | TIMESTAMP | ❌ | NULL | When project was last synced |
| `created_at` | TIMESTAMP | ❌ | NOW() | When project was added |

## 🐍 Pydantic Models

### ProjectBase
Base model with common fields:
```python
class ProjectBase(BaseModel):
    name: str
    repository_url: str
    branch: str = "main"
    type: str = "application"
```

### ProjectCreate
Used for creating new projects:
```python
class ProjectCreate(ProjectBase):
    pass  # Inherits all fields from ProjectBase
```

**Example:**
```python
project = ProjectCreate(
    name="My App",
    repository_url="https://github.com/myorg/my-app",
    branch="main",
    type="application"
)
```

### ProjectUpdate
Used for partial updates:
```python
class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    branch: Optional[str] = None
    type: Optional[str] = None
```

**Example:**
```python
update = ProjectUpdate(branch="develop")  # Only update branch
```

### ProjectResponse
Returned from API/queries:
```python
class ProjectResponse(ProjectBase):
    id: str
    last_sync: Optional[datetime] = None
    created_at: datetime
    is_active: bool = True
```

## 🔗 Relationships

### One-to-Many: Components
```python
# Access components of a project
project.components  # List of Component objects
```

### One-to-Many: Hooks
```python
# Access hooks of a project
project.hooks  # List of Hook objects
```

Both relationships have `cascade="all, delete-orphan"`, meaning:
- Deleting a project automatically deletes its components and hooks
- Updating a project updates its children

## 📝 Common Operations

### Create a Project
```python
from models import ProjectCreate

new_project = ProjectCreate(
    name="UI Components Library",
    repository_url="https://github.com/myorg/ui-library",
    branch="main",
    type="library"
)

# Save to database
db_project = Project(**new_project.dict())
session.add(db_project)
session.commit()
```

### Query a Project
```python
from models import ProjectResponse

# Get from database
db_project = session.query(Project).filter_by(id="my-project").first()

# Convert to response model
response = ProjectResponse.from_orm(db_project)
print(response.name)  # "UI Components Library"
```

### Update a Project
```python
# Update sync timestamp
project.last_sync = datetime.utcnow()
session.commit()

# Change branch
project.branch = "develop"
session.commit()
```

### Deactivate a Project
```python
# Stop indexing a project without deleting it
project.is_active = False
session.commit()
```

### Delete a Project
```python
# Cascade deletes all components and hooks
session.delete(project)
session.commit()
```

## 🔍 Useful Queries

### Get All Projects
```sql
SELECT id, name, type, is_active, last_sync 
FROM projects 
ORDER BY name;
```

### Get Active Projects Only
```sql
SELECT id, name, type, last_sync 
FROM projects 
WHERE is_active = true 
ORDER BY last_sync DESC;
```

### Find by Repository URL
```sql
SELECT * FROM projects 
WHERE repository_url LIKE '%myorg%';
```

### Count Components per Project
```sql
SELECT 
  p.name,
  COUNT(c.id) as component_count
FROM projects p
LEFT JOIN components c ON p.id = c.project_id
GROUP BY p.id, p.name
ORDER BY component_count DESC;
```

### Count Hooks per Project
```sql
SELECT 
  p.name,
  COUNT(h.id) as hook_count
FROM projects p
LEFT JOIN hooks h ON p.id = h.project_id
GROUP BY p.id, p.name
ORDER BY hook_count DESC;
```

### Find Recently Synced Projects
```sql
SELECT id, name, last_sync 
FROM projects 
WHERE last_sync IS NOT NULL
ORDER BY last_sync DESC 
LIMIT 5;
```

## 📚 Configuration

### In `.mcp-config.json`
```json
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
```

The `id` (key in projects object) becomes the database `id`.

## 🔄 Sync Workflow

1. **Add Project** to `.mcp-config.json`
2. **Run Sync** - `sync_project("my-project")`
3. **Fetch Repository** - Clone to temp directory
4. **Parse Components** - Extract components and hooks
5. **Store in DB** - Insert/update project and its entities
6. **Update `last_sync`** - Record sync timestamp
7. **Cleanup** - Delete temp files

## 🎯 Type Values

### Project Type
- `application` - Main app with pages and features
- `library` - Reusable component/hook library

Choose based on what you're indexing.

## ⚠️ Important Notes

- `id` must be unique and is typically lowercase with hyphens: `my-project`
- `repository_url` should be HTTPS (not SSH) for cloning
- `branch` must exist in the repository
- Deleting a project cascades to all components and hooks
- `last_sync` is NULL until first sync

## 🔗 See Also

- [COMPONENT.md](COMPONENT.md) - Component model
- [HOOK.md](HOOK.md) - Hook model
- [DATABASE.md](../DATABASE.md) - Database queries
- [SETUP.md](../../SETUP.md) - Project configuration
