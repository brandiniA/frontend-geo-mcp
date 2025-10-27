# MCP Frontend con FastMCP Python: Desarrollo y Hosting

## 🐍 FastMCP Python - La Mejor Opción para MCP

FastMCP es la interfaz principal para el protocolo MCP en Python, proporcionando una manera rápida y elegante de construir servidores MCP con decoradores simples, validación automática y herramientas de desarrollo integradas.

### ¿Por qué FastMCP Python?

**Ventajas principales:**
- ✅ **Mantenimiento activo** y desarrollo continuo
- ✅ **Sintaxis ultra-simple** con decoradores Python
- ✅ **Validación automática** con Pydantic
- ✅ **CLI integrado** para testing y debugging
- ✅ **Soporte nativo** para SSE y Streamable HTTP
- ✅ **Desarrollo 5x más rápido** que el SDK oficial
- ✅ **Documentación excelente** con ejemplos prácticos
- ✅ **Comunidad activa** y soporte oficial de Anthropic

---

## 📦 Instalación y Setup

### Instalación con UV (Recomendado)
```bash
# Instalar UV (gestor de paquetes moderno para Python)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Crear proyecto
uv init frontend-mcp
cd frontend-mcp

# Instalar FastMCP
uv add fastmcp
```

### Instalación con pip tradicional
```bash
# Crear proyecto
mkdir frontend-mcp && cd frontend-mcp
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar FastMCP
pip install fastmcp
```

---

## 💻 Servidor MCP Completo para Frontend GPS

### Estructura del Proyecto
```
frontend-mcp/
├── src/
│   ├── server.py           # Entry point principal
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── navigator.py    # Herramientas de navegación
│   │   ├── validator.py    # Validación de código
│   │   └── guide.py        # Guía de proyecto
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── indexer.py      # Indexación de componentes
│   │   ├── cache.py        # Sistema de cache
│   │   └── parser.py       # Parser de código React
│   └── config/
│       └── rules.py        # Reglas de validación
├── .env
├── pyproject.toml
└── README.md
```

### Código Principal del Servidor

```python
# src/server.py
from fastmcp import FastMCP
from fastmcp.resources import FileResource
from typing import Dict, List, Optional, Annotated
import os
import json
import re
from pathlib import Path
from datetime import datetime
import asyncio

# Importar herramientas personalizadas
from tools.navigator import ComponentNavigator
from tools.validator import CodeValidator
from tools.guide import ProjectGuide
from utils.indexer import ProjectIndexer
from utils.cache import CacheManager

# Inicializar MCP Server
mcp = FastMCP(
    name="Frontend GPS 🚀",
    description="Navigator and Code Reviewer for Frontend Projects"
)

# Inicializar servicios
navigator = ComponentNavigator()
validator = CodeValidator()
guide = ProjectGuide()
indexer = ProjectIndexer()
cache = CacheManager()

# ============================================
# 🔍 NAVIGATOR TOOLS
# ============================================

@mcp.tool
async def find_component(
    query: Annotated[str, "Component name or functionality to search"],
    project_path: Annotated[Optional[str], "Project root path"] = None
) -> str:
    """
    Find React components by name or functionality.
    Returns location, type, and usage examples.
    """
    project_path = project_path or os.getcwd()
    
    # Verificar cache primero
    cache_key = f"find_{query}_{project_path}"
    cached = await cache.get(cache_key)
    if cached:
        return cached
    
    # Indexar proyecto si no está en cache
    if not await indexer.is_indexed(project_path):
        await indexer.index_project(project_path)
    
    # Buscar componentes
    results = await navigator.find_components(query, project_path)
    
    # Formatear respuesta
    if not results:
        return f"No components found matching '{query}'"
    
    response = f"📍 Found {len(results)} component(s) matching '{query}':\n\n"
    for component in results:
        response += f"""
**{component['name']}**
- 📂 Path: `{component['path']}`
- 🏷️ Type: {component['type']}
- 📦 Exports: {', '.join(component['exports'])}
- 🔗 Imports: {', '.join(component['imports'][:3])}...
"""
        if component.get('props'):
            response += f"- 🎯 Props: {', '.join(component['props'])}\n"
        if component.get('hooks'):
            response += f"- 🪝 Hooks: {', '.join(component['hooks'])}\n"
    
    # Guardar en cache
    await cache.set(cache_key, response, ttl=300)
    return response

@mcp.tool
async def find_similar_components(
    component_code: Annotated[str, "Component code to find similar ones"],
    threshold: Annotated[float, "Similarity threshold (0-1)"] = 0.7
) -> str:
    """
    Find components similar to the provided code.
    Helps avoid duplicating existing components.
    """
    project_path = os.getcwd()
    
    # Analizar el componente proporcionado
    component_signature = await navigator.extract_component_signature(component_code)
    
    # Buscar componentes similares
    similar = await navigator.find_similar(
        component_signature, 
        project_path, 
        threshold
    )
    
    if not similar:
        return "✅ No similar components found. This appears to be unique."
    
    response = f"⚠️ Found {len(similar)} similar component(s):\n\n"
    for match in similar:
        response += f"""
**{match['name']}** (Similarity: {match['similarity']:.0%})
- 📂 Path: `{match['path']}`
- 🔄 Similar aspects: {', '.join(match['similarities'])}
- 💡 Consider using this instead or extending it
"""
    
    return response

@mcp.tool
async def get_project_structure(
    max_depth: Annotated[int, "Maximum folder depth to explore"] = 3
) -> str:
    """
    Get the project's folder structure and organization.
    Shows where different types of files are located.
    """
    project_path = os.getcwd()
    structure = await guide.get_folder_structure(project_path, max_depth)
    
    response = "📁 **Project Structure:**\n\n```\n"
    response += structure
    response += "\n```\n\n"
    
    # Agregar resumen de organización
    stats = await guide.get_project_stats(project_path)
    response += f"""
📊 **Project Statistics:**
- React Components: {stats['components']}
- Custom Hooks: {stats['hooks']}
- Pages/Routes: {stats['pages']}
- Style Files: {stats['styles']}
- Test Files: {stats['tests']}
- Total Files: {stats['total_files']}
"""
    
    return response

# ============================================
# ✅ VALIDATOR TOOLS
# ============================================

@mcp.tool
async def validate_component(
    code: Annotated[str, "React component code to validate"],
    rules: Annotated[Optional[List[str]], "Specific rules to check"] = None
) -> str:
    """
    Validate React component against team standards.
    Checks for best practices, patterns, and potential issues.
    """
    # Cargar reglas del equipo
    if not rules:
        rules = await validator.load_team_rules()
    
    # Ejecutar validación
    validation_result = await validator.validate(code, rules)
    
    # Formatear respuesta
    response = "## 🔍 Validation Report\n\n"
    
    if validation_result['is_valid']:
        response += "✅ **Component passes all validations!**\n\n"
    else:
        response += "⚠️ **Issues found:**\n\n"
    
    # Mostrar errores
    if validation_result['errors']:
        response += "### 🔴 Errors (Must fix):\n"
        for error in validation_result['errors']:
            response += f"- {error['message']} (Line {error.get('line', 'N/A')})\n"
            if error.get('suggestion'):
                response += f"  💡 *Suggestion:* {error['suggestion']}\n"
    
    # Mostrar warnings
    if validation_result['warnings']:
        response += "\n### 🟡 Warnings (Should fix):\n"
        for warning in validation_result['warnings']:
            response += f"- {warning['message']}\n"
            if warning.get('suggestion'):
                response += f"  💡 *Suggestion:* {warning['suggestion']}\n"
    
    # Mostrar sugerencias
    if validation_result['suggestions']:
        response += "\n### 💡 Suggestions:\n"
        for suggestion in validation_result['suggestions']:
            response += f"- {suggestion}\n"
    
    # Verificar duplicados
    if validation_result.get('similar_components'):
        response += "\n### 🔄 Similar Components Found:\n"
        response += "Consider using these existing components:\n"
        for comp in validation_result['similar_components']:
            response += f"- `{comp['name']}` at `{comp['path']}`\n"
    
    return response

@mcp.tool
async def check_imports(
    file_path: Annotated[str, "Path to the file to check"]
) -> str:
    """
    Check if imports are correct and following conventions.
    Suggests optimizations and finds unused imports.
    """
    content = Path(file_path).read_text()
    
    # Analizar imports
    import_analysis = await validator.analyze_imports(content)
    
    response = "## 📦 Import Analysis\n\n"
    
    if import_analysis['unused']:
        response += "### 🧹 Unused imports:\n"
        for imp in import_analysis['unused']:
            response += f"- `{imp}`\n"
    
    if import_analysis['missing']:
        response += "\n### ⚠️ Missing imports:\n"
        for imp in import_analysis['missing']:
            response += f"- `{imp}`\n"
    
    if import_analysis['suggestions']:
        response += "\n### 💡 Optimization suggestions:\n"
        for sug in import_analysis['suggestions']:
            response += f"- {sug}\n"
    
    if not any([import_analysis['unused'], import_analysis['missing'], import_analysis['suggestions']]):
        response += "✅ All imports look good!"
    
    return response

# ============================================
# 📚 PROJECT GUIDE TOOLS
# ============================================

@mcp.tool
async def how_to_run() -> str:
    """
    Get instructions on how to run the current project.
    Includes setup steps, environment variables, and scripts.
    """
    project_path = os.getcwd()
    
    # Leer package.json
    package_json = Path(project_path) / "package.json"
    if not package_json.exists():
        return "❌ No package.json found in current directory"
    
    with open(package_json) as f:
        package = json.load(f)
    
    scripts = package.get('scripts', {})
    
    response = "## 🚀 How to Run This Project\n\n"
    
    # Instrucciones de instalación
    response += "### 1️⃣ Install Dependencies:\n```bash\n"
    if Path(project_path, "yarn.lock").exists():
        response += "yarn install\n"
    elif Path(project_path, "pnpm-lock.yaml").exists():
        response += "pnpm install\n"
    else:
        response += "npm install\n"
    response += "```\n\n"
    
    # Variables de entorno
    env_example = Path(project_path) / ".env.example"
    if env_example.exists():
        response += "### 2️⃣ Setup Environment Variables:\n```bash\n"
        response += "cp .env.example .env\n"
        response += "# Edit .env with your values\n```\n\n"
    
    # Scripts disponibles
    response += "### 3️⃣ Available Scripts:\n"
    for script_name, script_cmd in scripts.items():
        if script_name in ['dev', 'start', 'build', 'test', 'lint']:
            response += f"- **`npm run {script_name}`**: {script_cmd}\n"
    
    # Comando principal
    if 'dev' in scripts:
        response += f"\n### ▶️ Start Development:\n```bash\nnpm run dev\n```"
    elif 'start' in scripts:
        response += f"\n### ▶️ Start Application:\n```bash\nnpm start\n```"
    
    return response

@mcp.tool
async def get_conventions() -> str:
    """
    Get coding conventions and patterns used in this project.
    Includes naming conventions, file structure, and best practices.
    """
    project_path = os.getcwd()
    
    # Analizar convenciones del proyecto
    conventions = await guide.analyze_conventions(project_path)
    
    response = "## 📝 Project Conventions\n\n"
    
    response += f"""
### 🏷️ Naming Conventions:
- **Components**: {conventions['component_naming']} (e.g., `UserProfile.tsx`)
- **Hooks**: {conventions['hook_naming']} (e.g., `useAuth.ts`)
- **Utils**: {conventions['util_naming']} (e.g., `formatDate.ts`)
- **Types**: {conventions['type_naming']} (e.g., `User.types.ts`)

### 📁 File Organization:
- **Components**: `{conventions['component_location']}`
- **Pages**: `{conventions['page_location']}`
- **Styles**: {conventions['style_approach']}
- **Tests**: {conventions['test_location']}

### 🎨 Styling Approach:
- **Library**: {conventions['styling_library']}
- **Methodology**: {conventions['css_methodology']}

### 🧩 Component Patterns:
- **State Management**: {conventions['state_management']}
- **Props Pattern**: {conventions['props_pattern']}
- **Export Style**: {conventions['export_style']}
"""
    
    # Agregar ejemplos si existen
    if conventions.get('examples'):
        response += "\n### 💡 Examples from this project:\n"
        for example in conventions['examples'][:3]:
            response += f"- `{example['file']}`: {example['pattern']}\n"
    
    return response

# ============================================
# 📂 RESOURCES
# ============================================

@mcp.resource("project://overview")
async def get_project_overview() -> str:
    """Complete overview of the project structure and configuration."""
    project_path = os.getcwd()
    
    # Generar overview completo
    overview = {
        "name": Path(project_path).name,
        "type": "Frontend React/Next.js Application",
        "structure": await guide.get_folder_structure(project_path, 2),
        "dependencies": await guide.get_dependencies(),
        "scripts": await guide.get_scripts(),
        "conventions": await guide.analyze_conventions(project_path),
        "stats": await guide.get_project_stats(project_path)
    }
    
    return json.dumps(overview, indent=2)

@mcp.resource("components://catalog")
async def get_components_catalog() -> str:
    """Catalog of all React components in the project."""
    project_path = os.getcwd()
    
    # Obtener catálogo de componentes
    components = await navigator.get_all_components(project_path)
    
    catalog = {
        "total": len(components),
        "components": components,
        "categories": await navigator.categorize_components(components),
        "updated_at": datetime.now().isoformat()
    }
    
    return json.dumps(catalog, indent=2)

# ============================================
# 🎯 PROMPTS
# ============================================

@mcp.prompt(
    name="analyze_component",
    description="Analyze a React component comprehensively",
    arguments=[
        {"name": "component_name", "description": "Name of the component", "required": True}
    ]
)
async def analyze_component_prompt(component_name: str) -> str:
    return f"""Please analyze the React component '{component_name}':

1. First, find the component using find_component tool
2. Check if there are similar components using find_similar_components
3. Validate the component code using validate_component
4. Check the imports using check_imports
5. Provide a summary with recommendations

Focus on:
- Code quality and best practices
- Potential optimizations
- Reusability opportunities
- Testing suggestions"""

@mcp.prompt(
    name="onboard_developer",
    description="Help a new developer understand the project",
    arguments=[]
)
async def onboard_developer_prompt() -> str:
    return """Help me understand this Frontend project:

1. Show the project structure using get_project_structure
2. Explain how to run it using how_to_run
3. Show the conventions using get_conventions
4. List main components using the components catalog
5. Provide a quick-start guide

Make it beginner-friendly and comprehensive."""

# ============================================
# 🚀 MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    # Configurar modo de ejecución
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--dev":
        # Modo desarrollo con hot-reload
        mcp.run(debug=True, hot_reload=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "--http":
        # Modo HTTP para deployment remoto
        mcp.run(
            transport="streamable-http",
            host="0.0.0.0",
            port=int(os.getenv("PORT", 8080))
        )
    else:
        # Modo stdio para Cursor
        mcp.run()
```

---

## 🛠️ Módulos Auxiliares

### Navigator Module
```python
# src/tools/navigator.py
from typing import List, Dict, Optional
import os
import re
from pathlib import Path
import ast

class ComponentNavigator:
    def __init__(self):
        self.component_patterns = [
            r'export\s+(?:default\s+)?(?:function|const)\s+(\w+)',
            r'const\s+(\w+)\s*=\s*\([^)]*\)\s*=>',
            r'function\s+(\w+)\s*\([^)]*\)',
        ]
        
    async def find_components(self, query: str, project_path: str) -> List[Dict]:
        """Find components matching the query."""
        components = []
        
        for root, dirs, files in os.walk(project_path):
            # Skip node_modules and hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
            
            for file in files:
                if file.endswith(('.tsx', '.jsx')):
                    file_path = Path(root) / file
                    content = file_path.read_text()
                    
                    # Search for component patterns
                    for pattern in self.component_patterns:
                        matches = re.findall(pattern, content)
                        for match in matches:
                            if query.lower() in match.lower():
                                components.append({
                                    'name': match,
                                    'path': str(file_path.relative_to(project_path)),
                                    'type': self._get_component_type(file_path),
                                    'exports': self._get_exports(content),
                                    'imports': self._get_imports(content),
                                    'hooks': self._get_hooks(content),
                                    'props': self._get_props(content, match)
                                })
        
        return components
    
    def _get_component_type(self, file_path: Path) -> str:
        """Determine component type based on location."""
        path_str = str(file_path).lower()
        if 'pages' in path_str or 'app' in path_str:
            return 'Page'
        elif 'layout' in path_str:
            return 'Layout'
        elif 'hook' in path_str:
            return 'Hook'
        else:
            return 'Component'
    
    def _get_imports(self, content: str) -> List[str]:
        """Extract import statements."""
        import_pattern = r'import\s+.*?\s+from\s+[\'"]([^\'"]+)[\'"]'
        return re.findall(import_pattern, content)[:5]  # Limit to 5 for brevity
    
    def _get_exports(self, content: str) -> List[str]:
        """Extract export statements."""
        export_pattern = r'export\s+(?:default\s+)?(?:function|const|class)\s+(\w+)'
        return list(set(re.findall(export_pattern, content)))
    
    def _get_hooks(self, content: str) -> List[str]:
        """Extract React hooks used."""
        hook_pattern = r'use[A-Z]\w+'
        return list(set(re.findall(hook_pattern, content)))
    
    def _get_props(self, content: str, component_name: str) -> List[str]:
        """Extract component props."""
        # Simplified prop extraction
        props_pattern = rf'{component_name}\s*[=:]\s*\(?\s*{{\s*([^}}]+)\s*}}'
        matches = re.search(props_pattern, content)
        if matches:
            props_str = matches.group(1)
            props = re.findall(r'(\w+)[:,]', props_str)
            return props
        return []
    
    async def extract_component_signature(self, code: str) -> Dict:
        """Extract signature from component code for similarity comparison."""
        return {
            'imports': self._get_imports(code),
            'hooks': self._get_hooks(code),
            'props': self._get_props(code, 'Component'),
            'exports': self._get_exports(code)
        }
    
    async def find_similar(self, signature: Dict, project_path: str, threshold: float) -> List[Dict]:
        """Find components similar to the provided signature."""
        similar = []
        
        # Implementación simplificada de búsqueda de similitud
        all_components = await self.find_components('', project_path)
        
        for component in all_components:
            similarity = self._calculate_similarity(signature, component)
            if similarity >= threshold:
                similar.append({
                    'name': component['name'],
                    'path': component['path'],
                    'similarity': similarity,
                    'similarities': self._get_similarities(signature, component)
                })
        
        return sorted(similar, key=lambda x: x['similarity'], reverse=True)
    
    def _calculate_similarity(self, sig1: Dict, sig2: Dict) -> float:
        """Calculate similarity between two component signatures."""
        # Simplified similarity calculation
        score = 0.0
        total = 0
        
        # Compare hooks
        if sig1.get('hooks') and sig2.get('hooks'):
            common_hooks = set(sig1['hooks']) & set(sig2['hooks'])
            all_hooks = set(sig1['hooks']) | set(sig2['hooks'])
            if all_hooks:
                score += len(common_hooks) / len(all_hooks)
                total += 1
        
        # Compare props
        if sig1.get('props') and sig2.get('props'):
            common_props = set(sig1['props']) & set(sig2['props'])
            all_props = set(sig1['props']) | set(sig2['props'])
            if all_props:
                score += len(common_props) / len(all_props)
                total += 1
        
        return score / total if total > 0 else 0.0
    
    def _get_similarities(self, sig1: Dict, sig2: Dict) -> List[str]:
        """Get list of similarities between components."""
        similarities = []
        
        if set(sig1.get('hooks', [])) & set(sig2.get('hooks', [])):
            similarities.append('Similar hooks usage')
        if set(sig1.get('props', [])) & set(sig2.get('props', [])):
            similarities.append('Similar props structure')
        if set(sig1.get('imports', [])) & set(sig2.get('imports', [])):
            similarities.append('Common dependencies')
        
        return similarities
```

---

## 🚀 Configuración para Hosting Remoto

### Opción 1: **Cloudflare Workers**

```python
# src/cloudflare_worker.py
from fastmcp import FastMCP
import json

mcp = FastMCP("Frontend GPS")

# Configurar todas las tools aquí...

async def handle_request(request):
    """Handle HTTP requests for Cloudflare Workers."""
    if request.method == "POST" and "/mcp" in request.url:
        body = await request.json()
        response = await mcp.handle_request(body)
        return Response(json.dumps(response), headers={
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        })
    
    return Response("MCP Server Running", status=200)

# Export for Cloudflare Workers
addEventListener('fetch', event => {
    event.respondWith(handle_request(event.request))
})
```

**wrangler.toml:**
```toml
name = "frontend-mcp"
main = "src/cloudflare_worker.py"
compatibility_date = "2024-01-01"

[build]
command = "pip install -r requirements.txt -t ."

[[routes]]
pattern = "mcp.tudominio.com/*"
custom_domain = true
```

### Opción 2: **Google Cloud Run con Docker**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar UV para mejor gestión de paquetes
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copiar archivos del proyecto
COPY pyproject.toml .
COPY src/ ./src/

# Instalar dependencias
RUN uv pip install --system -r pyproject.toml

# Variables de entorno
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Ejecutar servidor
CMD ["python", "src/server.py", "--http"]
```

**Deploy a Cloud Run:**
```bash
# Build y push de la imagen
gcloud builds submit --tag gcr.io/PROJECT_ID/frontend-mcp

# Deploy del servicio
gcloud run deploy frontend-mcp \
  --image gcr.io/PROJECT_ID/frontend-mcp \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 512Mi
```

### Opción 3: **Railway/Render (Más Simple)**

```yaml
# railway.json o render.yaml
services:
  - type: web
    name: frontend-mcp
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: python src/server.py --http
    envVars:
      - key: PORT
        value: 8080
```

**Deploy con un click:**
- Railway: `railway up`
- Render: Push a GitHub y conectar repositorio

### Opción 4: **AWS Lambda con Serverless Framework**

```yaml
# serverless.yml
service: frontend-mcp

provider:
  name: aws
  runtime: python3.11
  region: us-east-1

functions:
  mcp:
    handler: src.lambda_handler.handler
    events:
      - http:
          path: /mcp
          method: post
          cors: true
    environment:
      MCP_MODE: production
```

```python
# src/lambda_handler.py
from fastmcp import FastMCP
import json

mcp = FastMCP("Frontend GPS")

# Configurar tools...

def handler(event, context):
    """AWS Lambda handler."""
    body = json.loads(event['body'])
    response = mcp.handle_request_sync(body)  # Versión sync para Lambda
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(response)
    }
```

---

## 🔧 Configuración de Cliente (Cursor)

### Para servidor local:
```json
{
  "mcpServers": {
    "frontend-gps": {
      "command": "python",
      "args": ["/path/to/frontend-mcp/src/server.py"],
      "env": {
        "PROJECT_ROOT": "${workspaceFolder}"
      }
    }
  }
}
```

### Para servidor remoto:
```json
{
  "mcpServers": {
    "frontend-gps": {
      "type": "http",
      "url": "https://mcp.tudominio.com/mcp",
      "headers": {
        "Authorization": "Bearer ${env:MCP_TOKEN}"
      }
    }
  }
}
```

---

## 📋 Archivos de Configuración

### pyproject.toml
```toml
[project]
name = "frontend-mcp"
version = "0.1.0"
description = "MCP Frontend GPS and Code Reviewer"
readme = "README.md"
requires-python = ">=3.10"
dependencies = [
    "fastmcp>=0.3.0",
    "pydantic>=2.0.0",
    "aiofiles>=23.0.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.ruff]
line-length = 100
select = ["E", "F", "I"]

[tool.black]
line-length = 100
```

### requirements.txt (alternativa)
```
fastmcp>=0.3.0
pydantic>=2.0.0
aiofiles>=23.0.0
python-dotenv>=1.0.0
```

### .env
```bash
# Configuración del servidor
MCP_MODE=production
PORT=8080

# Cache
CACHE_TTL=300
CACHE_DIR=.mcp-cache

# Autenticación (para servidor remoto)
MCP_API_KEY=your-secret-key

# Configuración del proyecto
DEFAULT_PROJECT_PATH=/workspace
MAX_SEARCH_DEPTH=5
```

---

## 🛠️ CLI y Herramientas de Desarrollo

### Testing local:
```bash
# Modo desarrollo con hot-reload
fastmcp dev src/server.py

# Inspector visual
fastmcp inspect src/server.py

# Testing específico
python -m pytest tests/
```

### Scripts útiles:
```bash
# scripts/dev.sh
#!/bin/bash
source venv/bin/activate
fastmcp dev src/server.py --reload

# scripts/test.sh
#!/bin/bash
python -m pytest tests/ -v

# scripts/deploy.sh
#!/bin/bash
docker build -t frontend-mcp .
docker push gcr.io/PROJECT/frontend-mcp
gcloud run deploy frontend-mcp --image gcr.io/PROJECT/frontend-mcp
```

---

## 📊 Comparación de Opciones de Hosting

| Plataforma | Costo/mes | Pros | Contras | Mejor para |
|------------|-----------|------|---------|------------|
| **Cloudflare Workers** | $0-5 | Edge computing, 100k req/día gratis | Límites de CPU | MVP, baja latencia |
| **Google Cloud Run** | $0-20 | Escala a 0, Docker nativo | Config inicial | Producción escalable |
| **Railway/Render** | $5-20 | Deploy simple, GitHub integration | Menos control | Desarrollo rápido |
| **AWS Lambda** | $0-15 | Ecosistema AWS, serverless | Cold starts | Integración AWS |
| **VPS (DigitalOcean)** | $5-40 | Control total | Más mantenimiento | Control completo |

---

## 🔐 Seguridad para Servidor Remoto

### Implementación de autenticación:
```python
# src/auth.py
from fastmcp import FastMCP
from fastmcp.auth import OAuth2Provider
import os

mcp = FastMCP("Frontend GPS")

# Configurar OAuth2 (para Cloudflare o similar)
mcp.configure_auth(
    provider=OAuth2Provider(
        client_id=os.getenv("OAUTH_CLIENT_ID"),
        client_secret=os.getenv("OAUTH_CLIENT_SECRET"),
        authorize_url="https://auth.tudominio.com/authorize",
        token_url="https://auth.tudominio.com/token"
    )
)

# O usar API Keys simples
@mcp.middleware
async def check_api_key(request):
    api_key = request.headers.get("X-API-Key")
    if api_key != os.getenv("MCP_API_KEY"):
        raise UnauthorizedError("Invalid API key")
    return request
```

---

## 🚀 Quickstart Completo

```bash
# 1. Setup inicial
git clone https://github.com/tu-repo/frontend-mcp
cd frontend-mcp

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -e .  # Instala en modo desarrollo

# 4. Configurar variables de entorno
cp .env.example .env
# Editar .env con tus valores

# 5. Testing local
fastmcp dev src/server.py

# 6. Build para producción
docker build -t frontend-mcp .

# 7. Deploy (ejemplo con Cloud Run)
gcloud run deploy frontend-mcp --source .
```

---

## 🎯 Ventajas de FastMCP Python

1. **Simplicidad extrema**: Decoradores simples, código limpio
2. **Mantenimiento activo**: Actualizaciones constantes
3. **Ecosistema maduro**: Python tiene excelentes librerías para parsing
4. **Deploy flexible**: Funciona en cualquier plataforma
5. **Performance**: Async/await nativo, muy eficiente
6. **Debugging fácil**: Herramientas Python maduras
7. **Costo bajo**: Funciona bien en servicios serverless gratuitos

---

## 📈 Plan de Implementación

### Semana 1: MVP Local
- Setup del proyecto
- Implementar Navigator básico
- Testing con equipo

### Semana 2: Funcionalidades Core
- Validator completo
- Project Guide
- Cache system

### Semana 3: Deployment
- Elegir plataforma de hosting
- Configurar CI/CD
- Deploy y testing remoto

### Semana 4: Pulido
- Optimización de performance
- Documentación completa
- Onboarding del equipo

---

## 🏁 Conclusión

Con **FastMCP Python** tienes:
- ✅ Desarrollo rápido y mantenible
- ✅ Deploy flexible en cualquier plataforma
- ✅ Costo mínimo o gratuito para empezar
- ✅ Herramientas de desarrollo excelentes
- ✅ Comunidad activa y soporte continuo
- ✅ Código limpio y fácil de entender

El MVP completo se puede tener funcionando en **2 semanas** con todas las funcionalidades core listas para que tu equipo empiece a usarlo inmediatamente.