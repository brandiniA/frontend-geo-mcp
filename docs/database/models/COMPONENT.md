# Component Model

Represents an indexed React component from a project.

## 📋 Schema

### Database Table
```sql
CREATE TABLE components (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
  file_path TEXT NOT NULL,
  props JSONB DEFAULT '[]',
  native_hooks_used JSONB DEFAULT '[]',
  custom_hooks_used JSONB DEFAULT '[]',
  imports JSONB DEFAULT '[]',
  exports JSONB DEFAULT '[]',
  component_type TEXT,
  description TEXT,
  jsdoc JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

## 🏷️ Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | SERIAL | Auto-increment unique identifier |
| `name` | TEXT | Component name (PascalCase: Button, UserCard) |
| `project_id` | TEXT FK | Reference to projects table |
| `file_path` | TEXT | Relative path: src/components/Button.tsx |
| `props` | JSONB | Component props array: ["onClick", "disabled"] |
| `native_hooks_used` | JSONB | React hooks: ["useState", "useEffect"] |
| `custom_hooks_used` | JSONB | Custom hooks used: ["useTheme", "useAuth"] |
| `imports` | JSONB | Import statements/modules |
| `exports` | JSONB | Named exports |
| `component_type` | TEXT | Type: component, page, layout, hook |
| `description` | TEXT | Short description from JSDoc |
| `jsdoc` | JSONB | Complete JSDoc documentation (see below) |
| `created_at` | TIMESTAMP | When component was first indexed |
| `updated_at` | TIMESTAMP | When component was last updated |

## 🐍 Pydantic Models

### ComponentBase
```python
class ComponentBase(BaseModel):
    name: str
    file_path: str
    props: List[str] = []
    hooks: List[str] = []
    imports: List[str] = []
    exports: List[str] = []
    component_type: Optional[str] = None
    description: Optional[str] = None
    jsdoc: Optional[Dict[str, Any]] = None
```

### ComponentCreate
```python
class ComponentCreate(ComponentBase):
    project_id: str
```

**Example:**
```python
component = ComponentCreate(
    name="Button",
    file_path="src/components/Button.tsx",
    project_id="my-project",
    props=["onClick", "disabled", "children"],
    native_hooks_used=["useState"],
    custom_hooks_used=["useTheme"],
    description="Reusable button component",
    jsdoc={
        "description": "A flexible button component",
        "params": [
            {"name": "onClick", "type": "Function", "description": "Click handler"}
        ]
    }
)
```

### ComponentResponse
```python
class ComponentResponse(ComponentBase):
    id: int
    project_id: str
    created_at: datetime
    updated_at: datetime
```

## 📝 JSDoc Structure

Complete JSDoc documentation as JSON:

```json
{
  "description": "Reusable button component with multiple variants",
  "params": [
    {
      "name": "onClick",
      "type": "Function",
      "description": "Callback when button is clicked"
    },
    {
      "name": "disabled",
      "type": "boolean",
      "description": "Disable the button"
    }
  ],
  "returns": {
    "type": "JSX.Element",
    "description": "Rendered button element"
  },
  "examples": [
    "<Button onClick={() => alert('clicked')}>Click me</Button>"
  ],
  "deprecated": false,
  "author": "John Doe",
  "version": "1.0.0"
}
```

## 🔗 Relationships

### Many-to-One: Project
```python
component.project  # Reference to parent Project
```

### Many-to-Many: Hooks (via custom_hooks_used)
```python
component.custom_hooks_used  # ["useUserData", "useAuth"]
# These reference Hook objects in the hooks table
```

## 📝 Common Operations

### Create a Component
```python
from models import ComponentCreate

button = ComponentCreate(
    name="Button",
    file_path="src/components/Button.tsx",
    project_id="my-project",
    props=["onClick", "children"],
    native_hooks_used=["useState"],
    component_type="component",
    description="Reusable button"
)

db_button = Component(**button.dict())
session.add(db_button)
session.commit()
```

### Query Components
```python
# Find specific component
button = session.query(Component).filter_by(name="Button", project_id="my-project").first()

# Find all components in project
components = session.query(Component).filter_by(project_id="my-project").all()

# Find components using specific hook
components_with_state = session.query(Component)\
    .filter(Component.native_hooks_used.contains(["useState"]))\
    .all()
```

### Update Component
```python
# Update props
component.props = ["onClick", "disabled", "variant"]

# Update custom hooks used
component.custom_hooks_used = ["useTheme", "useAuth"]

# Update JSDoc
component.jsdoc = {"description": "Updated description", ...}

session.commit()
```

### Delete Component
```python
session.delete(component)
session.commit()
```

## 🔍 Useful Queries

### Find Components by Name
```sql
SELECT name, project_id, file_path 
FROM components 
WHERE name ILIKE '%Button%'
ORDER BY name;
```

### Find Components Using Specific Native Hook
```sql
SELECT name, project_id 
FROM components 
WHERE native_hooks_used @> '["useState"]'
ORDER BY name;
```

### Find Components Using Custom Hooks
```sql
SELECT name, project_id, custom_hooks_used
FROM components 
WHERE custom_hooks_used @> '["useUserData"]'
ORDER BY name;
```

### Count Components by Type
```sql
SELECT component_type, COUNT(*) as count 
FROM components 
GROUP BY component_type 
ORDER BY count DESC;
```

### Find Recently Updated Components
```sql
SELECT name, project_id, updated_at 
FROM components 
ORDER BY updated_at DESC 
LIMIT 10;
```

### Find Components Without JSDoc
```sql
SELECT name, project_id, file_path 
FROM components 
WHERE jsdoc IS NULL 
ORDER BY name;
```

## 📊 Component Types

- `component` - Regular component (default)
- `page` - Page component (route level)
- `layout` - Layout wrapper component
- `hook` - Custom hook (use* prefix)

## ⚠️ Important Notes

- Component names must follow PascalCase convention (see validation rules)
- `file_path` should be relative to repository root
- `native_hooks_used` contains React built-in hooks only
- `custom_hooks_used` should reference actual hooks in the hooks table
- JSDoc is fully optional but recommended for discovery
- `updated_at` is automatically updated on every change

## 🔗 See Also

- [PROJECT.md](PROJECT.md) - Project model
- [HOOK.md](HOOK.md) - Hook model  
- [DATABASE.md](../DATABASE.md) - Database queries
- [VALIDATION.md](../../parser/VALIDATION.md) - Component naming rules
