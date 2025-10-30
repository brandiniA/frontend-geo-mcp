# Frontend GPS - MCP Tools Documentation

Complete reference for all available MCP tools in Frontend GPS.

## 📋 Quick Reference

| Category | Tool | Purpose |
|----------|------|---------|
| 🔍 Navigator | `find_component` | Search components by name |
| 🔍 Navigator | `get_component_details` | Get component props, hooks, imports |
| 🔍 Navigator | `list_components` | List all components with filters |
| 🔍 Navigator | `search_by_hook` | Find components using specific hooks |
| 🔍 Navigator | `search_by_jsdoc` | Search JSDoc documentation |
| 📚 Navigator | `get_component_docs` | View complete JSDoc documentation |
| 🔄 Sync | `sync_project` | Index components from GitHub |
| 📂 Sync | `list_projects` | View configured projects |
| 📊 Stats | `get_stats` | View overall statistics |

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
- **NEW:** Added date (relative time: "2 days ago", "1 hour ago", etc.)
- **NEW:** Modified date (last update time)
- Props with descriptions
- Hooks used
- Dependencies imported
- Description from JSDoc comments
- Full usage example

**Examples:**
```
@frontend-gps get_component_details("Button", "ui-library")
# Shows: props, hooks, imports, usage example, and creation/modification dates

@frontend-gps get_component_details("useAuth", "main-app")
# Shows custom hook details and usage
```

**Output Format:**

```markdown
## 📋 Component Details: Button

**Project:** UI Library (library)
**Path:** `src/components/Button.tsx`
**Type:** component
**Added:** 5 days ago
**Modified:** 2 hours ago
**Description:** Reusable button component for common actions

### 📝 Overview
[JSDoc description]

### 📥 Parameters
- **`label`** (`string`): Button text
- **`onClick`** (`Function`): Click handler

[... rest of documentation ...]
```

**Understanding Relative Times:**
- "just now" - Less than 1 minute ago
- "5 minutes ago" - Recently created/modified
- "2 hours ago" - Same day
- "3 days ago" - Recent component
- "2 weeks ago" - Older component
- "1 month ago" - Much older

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
- Grouped list of components by type
- Count per category
- File paths
- **NEW:** 🆕 badge for components created in last 7 days

**Examples:**
```
@frontend-gps list_components()
# Lists all components grouped by type, with 🆕 for recent additions

@frontend-gps list_components(project_id="ui-library")
# Lists only UI library components

@frontend-gps list_components(component_type="page")
# Lists only page components (routes)
```

**Understanding the Output:**

```markdown
### 🧩 Components (45)

- **Button** - `src/components/Button.tsx`
- **Card** - `src/components/Card.tsx` 🆕
- **Modal** - `src/components/Modal.tsx`
- **Header** - `src/components/Header.tsx` 🆕
- ... and 41 more
```

The 🆕 badge indicates components created within the last 7 days.

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

### search_by_jsdoc

Find components by searching their JSDoc documentation.

**Usage in Cursor:**
```
@frontend-gps search_by_jsdoc("validation")
@frontend-gps search_by_jsdoc("click handler", project_id="ui-library")
```

**Parameters:**
- `query` (required) - Search term to find in JSDoc (descriptions, param names, return types, examples)
- `project_id` (optional) - Filter by specific project

**Returns:**
- List of matching components
- Why the component matched (description, param, returns, example)
- File paths
- Project information

**Examples:**
```
@frontend-gps search_by_jsdoc("validation")
# Finds all components with "validation" in their documentation

@frontend-gps search_by_jsdoc("click handler")
# Finds components documenting click handlers

@frontend-gps search_by_jsdoc("returns Promise", project_id="main-app")
# Finds async components in specific project
```

**What It Searches:**
- Component descriptions
- Parameter names and descriptions
- Return type descriptions
- Example code
- Author information

### get_component_docs

Get the complete JSDoc documentation for a component.

**Usage in Cursor:**
```
@frontend-gps get_component_docs("Button", "ui-library")
@frontend-gps get_component_docs("useAuth", "main-app")
```

**Parameters:**
- `component_name` (required) - Exact component name
- `project_id` (required) - Project ID where component exists

**Returns:**
- Complete JSDoc documentation including:
  - Overview/description
  - Parameters with types and descriptions
  - Return types and descriptions
  - Code examples
  - Author information
  - Version information
  - Deprecation warnings (if applicable)

**Examples:**
```
@frontend-gps get_component_docs("Button", "ui-library")
# Shows full JSDoc for Button component

@frontend-gps get_component_docs("useForm", "main-app")
# Shows custom hook documentation

@frontend-gps get_component_docs("Modal", "ui-library")
# Shows detailed Modal documentation with examples
```

**Format of Output:**
```markdown
## 📚 Documentation: ComponentName

**File:** `src/components/ComponentName.tsx`
**Project:** project-id

### 📝 Overview
[Component description from JSDoc]

### 📥 Parameters
- **`propName`** (`type`)
  Description of parameter

### 📤 Returns
**Type:** `ReturnType`
**Description:** What it returns

### 💡 Examples
**Example 1:**
[Code example from JSDoc]
```
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

### Workflow 5: Search and Review JSDoc Documentation

```bash
# Find components with specific keywords in documentation
@frontend-gps search_by_jsdoc("validation")

# Get complete documentation for a component
@frontend-gps get_component_docs("FormValidator", "ui-library")

# Find components by specific patterns in documentation
@frontend-gps search_by_jsdoc("async")
```

### Workflow 6: Comprehensive Component Analysis

```bash
# Find component by name
@frontend-gps find_component("UserProfile")

# Get all details including JSDoc
@frontend-gps get_component_details("UserProfile", "main-app")

# Get complete documentation
@frontend-gps get_component_docs("UserProfile", "main-app")

# Find similar components
@frontend-gps search_by_hook("useState")
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

### "No JSDoc documentation found"
**Problem:** `get_component_docs()` returns empty
**Solution:**
- Component may not have JSDoc comments
- Add JSDoc comments to your component files
- Example JSDoc format:
```javascript
/**
 * Button component for common actions.
 * @param {Object} props - Component props
 * @param {string} props.label - Button text
 * @param {Function} props.onClick - Click handler
 * @returns {JSX.Element} Rendered button
 */
export const Button = ({ label, onClick }) => (...)
```
- Re-sync project after adding documentation: `@frontend-gps sync_project("project-id")`

### "JSDoc search returns too many results"
**Problem:** Query is too broad
**Solution:**
- Use more specific search terms
- Combine with `project_id` filter: `search_by_jsdoc("validation", project_id="ui-library")`
- Try searching in `get_component_docs()` instead for exact components

## 📚 See Also

- [DATABASE.md](../database/DATABASE.md) - Database schema and queries
- [SETUP.md](../SETUP.md) - Installation and setup
- [ARCHITECTURE.md](../architecture/ARCHITECTURE.md) - System design
- [VALIDATION.md](../parser/VALIDATION.md) - Parser component validation rules

