# Data Models Overview

Complete reference for Frontend GPS data models (Pydantic + SQLAlchemy).

## 📋 Architecture

The application uses a two-layer model approach:

- **Pydantic Models** - Data validation and serialization (API layer)
- **SQLAlchemy Models** - Database ORM (persistence layer)

Location: `src/models.py`

## 🏗️ Model Layers

### API/Validation Layer (Pydantic)
```
ProjectBase → ProjectCreate/ProjectUpdate → ProjectResponse
ComponentBase → ComponentCreate/ComponentUpdate → ComponentResponse
HookBase → HookCreate/HookUpdate → HookResponse
```

### Database Layer (SQLAlchemy)
```
Project (table: projects)
Component (table: components)
Hook (table: hooks)
```

## 📚 Detailed Model Documentation

### [Projects](models/PROJECT.md)
- Store project configuration
- Link to components and hooks
- Manage sync status and metadata

### [Components](models/COMPONENT.md)
- React components with props, hooks, imports
- Native vs custom hooks tracking
- Full JSDoc documentation

### [Hooks](models/HOOK.md)
- Custom React hooks
- Parameters, return types, documentation
- Hook dependencies and usage

## 🔗 Relationships

```
Projects (1)
  ├─ Components (M) - Indexed components in this project
  │  └─ custom_hooks_used → Hooks table
  │
  └─ Hooks (M) - Indexed custom hooks in this project
     └─ custom_hooks_used → Hooks table (self-reference possible)
```

## 🔄 Data Flow

1. **Indexing Phase**
   - Parser reads React files
   - Extracts component/hook info
   - Creates Pydantic models (validation)

2. **Storage Phase**
   - Pydantic models → SQLAlchemy models
   - Data persisted to PostgreSQL
   - Indexes created for fast queries

3. **Query Phase**
   - SQLAlchemy models → Pydantic models
   - Returned to API/MCP tools
   - JSON serialization for responses

## 📝 JSON Fields

Several models use JSON (JSONB in PostgreSQL) for flexible data:

- `props` - Component props array
- `parameters` - Hook parameter definitions
- `imports` - Import statements
- `exports` - Export names
- `native_hooks_used` - React hooks array
- `custom_hooks_used` - Custom hooks array
- `jsdoc` - Complete JSDoc documentation

Example JSDoc structure:
```json
{
  "description": "Component description",
  "params": [
    {"name": "prop1", "type": "string", "description": "..."}
  ],
  "returns": {"type": "JSX.Element", "description": "..."},
  "examples": ["..."],
  "deprecated": false,
  "author": "...",
  "version": "1.0.0"
}
```

## 🎯 Common Patterns

### Creating a Component
```python
from models import ComponentCreate

component = ComponentCreate(
    name="Button",
    file_path="src/components/Button.tsx",
    project_id="my-project",
    props=["onClick", "disabled"],
    native_hooks_used=["useState"],
    custom_hooks_used=["useTheme"],
    description="Reusable button component"
)
```

### Querying Components
```python
from models import ComponentResponse

# Database returns Component (SQLAlchemy)
db_component = session.query(Component).filter_by(name="Button").first()

# Convert to response (Pydantic)
response = ComponentResponse.from_orm(db_component)
```

### Updating Metadata
```python
# Update JSDoc for a component
component.jsdoc = {
    "description": "Updated description",
    "params": [...]
}
session.commit()
```

## 🔍 See Also

- [PROJECT.md](models/PROJECT.md) - Projects model details
- [COMPONENT.md](models/COMPONENT.md) - Components model details  
- [HOOK.md](models/HOOK.md) - Hooks model details
- [DATABASE.md](DATABASE.md) - Database schema and queries
- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) - System design
