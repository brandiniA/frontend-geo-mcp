# Hook Model

Represents an indexed custom React hook from a project.

## 📋 Schema

### Database Table
```sql
CREATE TABLE hooks (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
  file_path TEXT NOT NULL,
  hook_type TEXT DEFAULT 'custom',
  description TEXT,
  return_type TEXT,
  parameters JSONB DEFAULT '[]',
  imports JSONB DEFAULT '[]',
  exports JSONB DEFAULT '[]',
  native_hooks_used JSONB DEFAULT '[]',
  custom_hooks_used JSONB DEFAULT '[]',
  jsdoc JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🏷️ Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | SERIAL | Auto-increment unique identifier |
| `name` | TEXT | Hook name (use* prefix: useUserData, useAuth) |
| `project_id` | TEXT FK | Reference to projects table |
| `file_path` | TEXT | Relative path: src/hooks/useUserData.ts |
| `hook_type` | TEXT | Type: custom (default) |
| `description` | TEXT | Short description from JSDoc |
| `return_type` | TEXT | Return type: UserData or UserData \| null |
| `parameters` | JSONB | Hook parameters with types |
| `imports` | JSONB | Import statements/modules |
| `exports` | JSONB | Named exports |
| `native_hooks_used` | JSONB | React hooks: ["useState", "useEffect"] |
| `custom_hooks_used` | JSONB | Other custom hooks used |
| `jsdoc` | JSONB | Complete JSDoc documentation |
| `created_at` | TIMESTAMP | When hook was first indexed |
| `updated_at` | TIMESTAMP | When hook was last updated |

## 🐍 Pydantic Models

### HookBase
```python
class HookBase(BaseModel):
    name: str
    file_path: str
    hook_type: str = "custom"
    description: Optional[str] = None
    return_type: Optional[str] = None
    parameters: List[Dict[str, Any]] = []
    imports: List[str] = []
    exports: List[str] = []
    native_hooks_used: List[str] = []
    custom_hooks_used: List[str] = []
    jsdoc: Optional[Dict[str, Any]] = None
```

### HookCreate
```python
class HookCreate(HookBase):
    project_id: str
```

**Example:**
```python
hook = HookCreate(
    name="useUserData",
    file_path="src/hooks/useUserData.ts",
    project_id="my-project",
    return_type="UserData | null",
    parameters=[
        {
            "name": "userId",
            "type": "string",
            "description": "User ID to fetch"
        }
    ],
    native_hooks_used=["useState", "useEffect"],
    custom_hooks_used=[],
    description="Hook to fetch user data from API",
    jsdoc={
        "description": "Fetches user data and manages loading state",
        "params": [
            {"name": "userId", "type": "string", "description": "User ID"}
        ],
        "returns": {"type": "UserData | null", "description": "User data"}
    }
)
```

### HookResponse
```python
class HookResponse(HookBase):
    id: int
    project_id: str
    created_at: datetime
    updated_at: datetime
```

## 📝 JSDoc Structure

Complete JSDoc documentation as JSON:

```json
{
  "description": "Fetches user data and manages loading state",
  "params": [
    {
      "name": "userId",
      "type": "string",
      "description": "User ID to fetch from API"
    }
  ],
  "returns": {
    "type": "UserData | null",
    "description": "User data object or null if loading/error"
  },
  "examples": [
    "const user = useUserData('123');"
  ],
  "deprecated": false,
  "author": "John Doe",
  "version": "1.0.0"
}
```

## 🔗 Relationships

### Many-to-One: Project
```python
hook.project  # Reference to parent Project
```

### Many-to-Many: Hooks
```python
hook.custom_hooks_used  # Other custom hooks this hook uses
hook.native_hooks_used  # React hooks this hook uses
```

## 📝 Common Operations

### Create a Hook
```python
from models import HookCreate

hook = HookCreate(
    name="useUserData",
    file_path="src/hooks/useUserData.ts",
    project_id="my-project",
    return_type="UserData | null",
    parameters=[
        {"name": "userId", "type": "string"}
    ],
    native_hooks_used=["useState", "useEffect"],
    description="Fetch user data from API",
    hook_type="custom"
)

db_hook = Hook(**hook.dict())
session.add(db_hook)
session.commit()
```

### Query Hooks
```python
# Find specific hook
hook = session.query(Hook).filter_by(name="useUserData", project_id="my-project").first()

# Find all hooks in project
hooks = session.query(Hook).filter_by(project_id="my-project").all()

# Find hooks using specific React hook
hooks_with_state = session.query(Hook)\
    .filter(Hook.native_hooks_used.contains(["useState"]))\
    .all()

# Find hooks without documentation
undocumented = session.query(Hook)\
    .filter(Hook.jsdoc == None)\
    .all()
```

### Update Hook
```python
# Update return type
hook.return_type = "User | undefined"

# Update parameters
hook.parameters = [
    {"name": "userId", "type": "string"},
    {"name": "options", "type": "Object"}
]

# Update JSDoc
hook.jsdoc = {"description": "Updated description", ...}

session.commit()
```

### Delete Hook
```python
session.delete(hook)
session.commit()
```

## 🔍 Useful Queries

### Find Hooks by Name
```sql
SELECT name, project_id, file_path, return_type 
FROM hooks 
WHERE name ILIKE '%UserData%'
ORDER BY name;
```

### Find All Hooks in Project
```sql
SELECT name, return_type, description
FROM hooks 
WHERE project_id = 'my-project'
ORDER BY name;
```

### Find Hooks Using Specific Native Hook
```sql
SELECT name, project_id 
FROM hooks 
WHERE native_hooks_used @> '["useState"]'
ORDER BY name;
```

### Find Hooks Using Custom Hooks
```sql
SELECT name, custom_hooks_used
FROM hooks 
WHERE custom_hooks_used @> '["useAuth"]'
ORDER BY name;
```

### Count Hooks per Project
```sql
SELECT project_id, COUNT(*) as hook_count 
FROM hooks 
GROUP BY project_id 
ORDER BY hook_count DESC;
```

### Find Undocumented Hooks
```sql
SELECT name, project_id, file_path 
FROM hooks 
WHERE jsdoc IS NULL OR description IS NULL
ORDER BY name;
```

### Find Hook Dependencies
```sql
SELECT 
  h.name,
  unnest(h.custom_hooks_used) as uses_hook
FROM hooks h
WHERE h.project_id = 'my-project'
ORDER BY h.name, uses_hook;
```

### Most Used Custom Hooks
```sql
SELECT 
  unnest(custom_hooks_used) as hook_name,
  COUNT(*) as usage_count
FROM (
  SELECT custom_hooks_used FROM components
  UNION ALL
  SELECT custom_hooks_used FROM hooks
)
GROUP BY hook_name
ORDER BY usage_count DESC;
```

## 🎯 Naming Convention

Custom hooks must follow the `use` prefix pattern:
- ✅ `useUserData` - ✅ `useAuth` - ✅ `useLocalStorage`
- ❌ `userData` - ❌ `auth` - ❌ `localStorage`

This is a JavaScript convention and helps distinguish hooks from regular functions.

## ⚠️ Important Notes

- Hook names must start with `use` (case-sensitive)
- Only custom hooks should be in this table (not React built-ins)
- `native_hooks_used` contains React built-in hooks only
- `custom_hooks_used` should reference actual hooks in this table
- `return_type` is helpful for IDE integration and discovery
- `parameters` should include type information
- JSDoc is optional but recommended
- `updated_at` is automatically updated on every change

## 📊 Hook Types

Currently only `custom` is used, representing user-defined React hooks.

Future expansion could include:
- `async` - For hooks that handle async operations
- `state` - For hooks managing state
- `effect` - For hooks managing side effects
- `context` - For hooks consuming context

## 🔗 See Also

- [PROJECT.md](PROJECT.md) - Project model
- [COMPONENT.md](COMPONENT.md) - Component model
- [DATABASE.md](../DATABASE.md) - Database queries
