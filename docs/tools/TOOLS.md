# Frontend GPS - MCP Tools Documentation

Complete reference for all available MCP tools in Frontend GPS.

## 🔍 Navigator Tools

### find_component

Search for React components by name across all indexed projects.

**Usage in Cursor:**
```
@frontend-gps find_component("Button")
@frontend-gps find_component("Card", project_id="ui-library")
```

**Parameters:**
- `query` (required) - Component name or partial name to search
- `project_id` (optional) - Filter by specific project

**Returns:**
- List of matching components with:
  - Component name and location
  - File path
  - Props and hooks
  - Import statement
  - Project information

**Examples:**
```
@frontend-gps find_component("Button")
# Returns all components with "Button" in the name

@frontend-gps find_component("Card", project_id="main-app")
# Returns Card components only from main-app project

@frontend-gps find_component("Modal")
# Returns Modal, ModalDialog, ModalOverlay, etc.
```

### get_component_details

Get detailed information about a specific component.

**Usage in Cursor:**
```
@frontend-gps get_component_details("Button", "ui-library")
```

**Parameters:**
- `component_name` (required) - Exact component name
- `project_id` (required) - Project ID where component exists

**Returns:**
- Component name and type
- File path
- Props with descriptions
- Hooks used
- Dependencies imported
- Description from JSDoc comments
- Full usage example

**Examples:**
```
@frontend-gps get_component_details("Button", "ui-library")
# Shows: props, hooks, imports, usage example

@frontend-gps get_component_details("useAuth", "main-app")
# Shows custom hook details and usage
```

### list_components

List all indexed components with optional filtering.

**Usage in Cursor:**
```
@frontend-gps list_components()
@frontend-gps list_components(project_id="ui-library")
@frontend-gps list_components(component_type="page")
```

**Parameters:**
- `project_id` (optional) - Filter by project
- `component_type` (optional) - Filter by type: 'component', 'page', 'layout', 'hook'

**Returns:**
- Grouped list of components
- Count per category
- File paths

**Examples:**
```
@frontend-gps list_components()
# Lists all components grouped by type

@frontend-gps list_components(project_id="ui-library")
# Lists only UI library components

@frontend-gps list_components(component_type="page")
# Lists only page components (routes)
```

### search_by_hook

Find components that use a specific React hook.

**Usage in Cursor:**
```
@frontend-gps search_by_hook("useState")
@frontend-gps search_by_hook("useEffect")
```

**Parameters:**
- `hook_name` (required) - React hook name (e.g., useState, useContext)

**Returns:**
- List of components using that hook
- Project information
- File paths

**Examples:**
```
@frontend-gps search_by_hook("useState")
# All components using useState

@frontend-gps search_by_hook("useContext")
# All components using useContext

@frontend-gps search_by_hook("useReducer")
# All components using useReducer
```

## 🔄 Sync Tools

### sync_project

Sync a project from GitHub repository and index all components.

**Usage in Cursor:**
```
@frontend-gps sync_project("main-app")
@frontend-gps sync_project("ui-library")
```

**Parameters:**
- `project_id` (required) - Project ID from `.mcp-config.json`

**Returns:**
- Sync status and results
- Number of components indexed
- Success/error messages

**Before using:**
1. Add project to `.mcp-config.json`:
```json
{
  "projects": {
    "my-app": {
      "name": "My Application",
      "repository": "https://github.com/user/my-app",
      "branch": "main",
      "type": "application"
    }
  }
}
```

**Examples:**
```
@frontend-gps sync_project("main-app")
# Clones, scans, and indexes all components

@frontend-gps sync_project("ui-library")
# Syncs the UI library from GitHub

# After first sync, use to refresh:
@frontend-gps sync_project("main-app")
# Updates index with latest changes
```

### list_projects

List all configured projects and their sync status.

**Usage in Cursor:**
```
@frontend-gps list_projects()
```

**Parameters:**
- None

**Returns:**
- All configured projects
- Project type (application/library)
- Repository URL
- Component count
- Last sync time

**Examples:**
```
@frontend-gps list_projects()
# Shows all configured projects and statistics
```

## 📊 Statistics Tools

### get_stats

Get overall statistics about indexed components.

**Usage in Cursor:**
```
@frontend-gps get_stats()
```

**Parameters:**
- None

**Returns:**
- Total projects configured
- Total components indexed
- Components per project
- Component types breakdown

**Examples:**
```
@frontend-gps get_stats()
# Shows total: 2 projects, 156 components
# Breakdown by project and type
```

## 📋 Common Workflows

### Workflow 1: Find and Understand a Component

```bash
# Step 1: Search for component
@frontend-gps find_component("Button")

# Step 2: Get full details
@frontend-gps get_component_details("Button", "ui-library")

# Step 3: Find similar components
@frontend-gps find_component("Button")
@frontend-gps search_by_hook("useState")
```

### Workflow 2: Add New Project to Index

```bash
# Step 1: Edit .mcp-config.json
# Add your project configuration

# Step 2: Sync the project
@frontend-gps sync_project("my-project")

# Step 3: Verify it was indexed
@frontend-gps list_projects()

# Step 4: Browse components
@frontend-gps list_components(project_id="my-project")
```

### Workflow 3: Check How Many Projects Are Indexed

```bash
# Get overall statistics
@frontend-gps get_stats()

# Get detailed project list
@frontend-gps list_projects()

# Browse all components
@frontend-gps list_components()
```

### Workflow 4: Find Hooks Usage

```bash
# Find all components using a specific hook
@frontend-gps search_by_hook("useState")

# Get details about one component
@frontend-gps get_component_details("UserForm", "main-app")

# See all hooks in use
@frontend-gps list_components(component_type="component")
```

## 🎯 Best Practices

### 1. Before Syncing
- Ensure project is in `.mcp-config.json`
- Verify GitHub URL is correct and accessible
- Check that repository is public or you have access

### 2. Effective Searching
- Use partial names: `find_component("Button")` finds Button, PrimaryButton, etc.
- Filter by project when possible: `find_component("Button", project_id="ui-library")`
- Use `search_by_hook()` to find components by pattern

### 3. Maintaining Index
- Regularly sync projects: `sync_project("my-project")`
- Use `list_projects()` to check project status
- Use `get_stats()` to monitor index growth

### 4. Component Discovery
1. Use `find_component()` to locate components
2. Use `get_component_details()` to understand them
3. Use `search_by_hook()` to find patterns
4. Copy import statements provided by tools

## ❌ Troubleshooting

### "Project not found in config"
**Problem:** Tried to sync non-existent project
**Solution:**
1. Add project to `.mcp-config.json`
2. Verify project ID is correct
3. Check JSON syntax is valid

### "No components found"
**Problem:** Search returned empty results
**Solution:**
- Check spelling and case sensitivity
- Use partial name: "Button" instead of "ButtonComponent"
- Verify project is synced: `list_projects()`
- Use `search_by_hook()` to find by pattern

### "Connection refused during sync"
**Problem:** Cannot clone repository
**Solution:**
- Verify GitHub URL is correct
- Check git is installed
- For private repos, add GITHUB_TOKEN to `.env`
- Verify internet connection

### "Import statement looks wrong"
**Problem:** Import path seems incorrect
**Solution:**
- Check `get_component_details()` for the exact path
- Use exact path shown in tool response
- Paths are relative to src/ directory

## 📚 See Also

- [DATABASE.md](../database/DATABASE.md) - Database schema and queries
- [SETUP.md](../SETUP.md) - Installation and setup
- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) - System design

