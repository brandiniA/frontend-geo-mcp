# Frontend GPS - Architecture Documentation

Complete technical documentation of the Frontend GPS system architecture, components, and data flows.

## 🏗️ System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Cursor IDE                          │
│              (MCP Client)                            │
└────────────────────┬────────────────────────────────┘
                     │
                     │ MCP Protocol (stdio/HTTP)
                     │
┌────────────────────▼────────────────────────────────┐
│            Frontend GPS MCP Server                   │
│                 (FastMCP)                            │
├────────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────────┐  │
│  │         Request Handler                      │  │
│  └──────────────────────────────────────────────┘  │
│                      │                              │
│  ┌──────────┬────────┼────────┬──────────────────┐ │
│  │          │        │        │                  │ │
│  ▼          ▼        ▼        ▼                  ▼ │
│ ┌──────┐ ┌─────┐ ┌──────┐ ┌─────────┐ ┌──────┐   │
│ │Find  │ │List │ │Search│ │Sync     │ │Stats │   │
│ │Comp. │ │Comp.│ │Hook  │ │Project  │ │      │   │
│ └──────┘ └─────┘ └──────┘ └─────────┘ └──────┘   │
│                      │                              │
│  ┌──────────────────▼──────────────────────────┐  │
│  │      Core Services                          │  │
│  │  • ComponentNavigator                       │  │
│  │  • ProjectIndexer                           │  │
│  │  • ReactParser                              │  │
│  │  • DatabaseClient                           │  │
│  └──────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────┘
                     │
                     │ PostgreSQL Protocol
                     │
┌────────────────────▼────────────────────────────────┐
│        PostgreSQL Database (Local/Remote)           │
│  ┌────────────────┐  ┌──────────────────────────┐  │
│  │   projects     │  │    components            │  │
│  │   table        │  │    table                 │  │
│  └────────────────┘  └──────────────────────────┘  │
└────────────────────────────────────────────────────┘
         │
         │ Git Clone
         │
┌────────▼────────────────────────────────────┐
│    GitHub/GitLab Repositories               │
│  • Main App Project                         │
│  • UI Library                               │
│  • Shared Components                        │
└─────────────────────────────────────────────┘
```

## 🧩 Core Components

### 1. MCP Server (`src/server.py`)

**Responsibility:** Entry point, request routing, tool definitions

**Features:**
- 7 FastMCP tools exposed via Cursor
- Request parsing and validation
- Response formatting
- Error handling
- Configuration loading

**Imports:**
- FastMCP framework
- All tool modules
- Database client

### 2. Navigator Tool (`src/tools/navigator.py`)

**Responsibility:** Component search and discovery

**Key Methods:**
- `find_component()` - Search by name/partial match
- `get_component_details()` - Detailed component info
- `list_all_components()` - Browse all components
- `search_by_hook()` - Find by React hook usage

**Dependencies:**
- DatabaseClient for queries
- Markdown formatting

### 3. React Parser (`src/utils/parser.py`)

**Responsibility:** Extract component metadata from source code

**Features:**
- Component name extraction (regex-based)
- Props parsing (JSDoc + destructuring)
- Hooks detection (`use*` pattern)
- Imports/exports extraction
- Component type determination
- Description extraction from comments

**Regex Patterns Used:**
```python
COMPONENT_PATTERNS = [
    r'export\s+(?:default\s+)?(?:function|const)\s+(\w+)',
    r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>',
    r'function\s+(\w+)\s*\([^)]*\)'
]

PROPS_PATTERN = r'\((?:\s*{\s*([^}]+)\s*}|([^)]+))\)'
HOOKS_PATTERN = r'use[A-Z]\w+'
IMPORT_PATTERN = r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]'
```

### 4. Project Indexer (`src/utils/indexer.py`)

**Responsibility:** Clone repositories and index components

**Process:**
1. Clone repository with `git clone --depth 1`
2. Scan for `.tsx` and `.jsx` files
3. Apply ReactParser to each file
4. Filter out excluded directories (node_modules, dist, etc.)
5. Batch save to database

**Features:**
- Shallow cloning for speed
- Recursive directory traversal
- File encoding handling
- Error recovery per file
- Progress logging

### 5. Database Client (`src/registry/database_client.py`)

**Responsibility:** PostgreSQL operations

**Methods:**
- `search_components()` - Query by name
- `save_components()` - Bulk insert/upsert
- `get_project()` - Project info
- `list_projects()` - All projects
- `upsert_project()` - Insert or update
- `get_component_count()` - Statistics

**Features:**
- Connection pooling (via psycopg2)
- UPSERT for idempotent updates
- JSON handling for complex fields
- Error handling

## 🔄 Data Flow

### Sync Flow

```
User Input: sync_project("main-app")
        │
        ▼
┌─────────────────────┐
│  server.py          │
│  sync_project()     │
└─────────┬───────────┘
          │
          ▼
┌──────────────────────────────┐
│  ProjectIndexer              │
│  index_remote_repository()   │
└─────────┬────────────────────┘
          │
          ├─► Clone repo from GitHub
          │
          ├─► Scan .tsx/.jsx files
          │
          ├─► For each file:
          │   ├─► Read file content
          │   ├─► Parse with ReactParser
          │   └─► Extract metadata
          │
          ▼
┌──────────────────────────────┐
│  DatabaseClient              │
│  save_components()           │
└─────────┬────────────────────┘
          │
          ▼
┌──────────────────────────────┐
│  PostgreSQL Database         │
│  INSERT INTO components      │
└──────────────────────────────┘
```

### Search Flow

```
User Input: find_component("Button")
        │
        ▼
┌─────────────────────┐
│  server.py          │
│  find_component()   │
└─────────┬───────────┘
          │
          ▼
┌──────────────────────────────┐
│  ComponentNavigator          │
│  find_component()            │
└─────────┬────────────────────┘
          │
          ▼
┌──────────────────────────────┐
│  DatabaseClient              │
│  search_components()         │
│  SELECT * FROM components    │
│  WHERE name ILIKE '%Button%' │
└─────────┬────────────────────┘
          │
          ▼
┌──────────────────────────────┐
│  PostgreSQL Database         │
│  Return results              │
└─────────┬────────────────────┘
          │
          ▼
┌──────────────────────────────┐
│  Format Response             │
│  Markdown with imports       │
└─────────┬────────────────────┘
          │
          ▼
User sees: Button component info + import
```

## 📊 Database Schema

### Projects Table
```
id (PK)          | name     | repository_url        | branch | type
─────────────────┼──────────┼──────────────────────┼────────┼──────
"ui-library"     | "UI Lib" | "https://github..." | "main" | "lib"
"main-app"       | "Main"   | "https://github..." | "dev"  | "app"
```

### Components Table
```
id  | name   | project_id   | file_path          | props      | hooks
────┼────────┼──────────────┼────────────────────┼────────────┼──────
1   | Button | ui-library   | Button.tsx         | ["size"]   | []
2   | Form   | main-app     | forms/Form.tsx     | ["fields"] | ["useState"]
```

## 🔐 Security Considerations

### Database
- PostgreSQL with username/password authentication
- No default credentials in production
- Environment variables for secrets

### File System
- Git clone restricted to whitelisted repositories
- Temporary directories cleaned after use
- No shell injection via user input

### API
- FastMCP handles request validation
- Tool parameters are type-checked
- Errors don't expose system internals

## 🚀 Performance Optimizations

### 1. Indexing
- Shallow Git clones (`--depth 1`)
- Regex-based parsing (no full AST compilation)
- Batch database inserts
- UPSERT prevents duplicate processing

### 2. Search
- Database indexes on name and project_id
- Full-text search indexes on component names
- Query limits to first 20 results

### 3. Memory
- Streaming file reading
- Generator-based directory traversal
- Lazy loading of component data

## 📈 Scalability

### Horizontal
- Stateless server design
- Can run multiple instances
- Shared PostgreSQL backend

### Vertical
- Configurable cache TTLs
- Incremental indexing possible
- Database query optimization

### Data
- Supports 10,000+ components
- Efficient JSON storage in PostgreSQL
- Index-based queries scale well

## 🔄 Design Patterns

### 1. Parser Pattern
- Regex-first approach (90% use case)
- Fallback to manual analysis
- Type detection by convention

### 2. Index Pattern
- Initial full scan
- Incremental updates via sync
- Cache-first responses

### 3. Tool Pattern
- FastMCP decorators for tool exposure
- Async/await for I/O operations
- Markdown formatting for responses

### 4. Database Pattern
- Connection pooling
- Parameterized queries (SQL injection safe)
- UPSERT for idempotence

## 🧪 Testing Strategy

### Unit Tests
- ReactParser regex patterns
- Component type detection
- Props extraction

### Integration Tests
- Database CRUD operations
- Search functionality
- Project sync workflow

### End-to-End Tests
- Tool responses from MCP server
- Full search/sync cycle

## 📚 See Also

- [DATABASE.md](../database/DATABASE.md) - Schema and queries
- [TOOLS.md](../tools/TOOLS.md) - Tools reference
- [SETUP.md](../SETUP.md) - Installation guide

