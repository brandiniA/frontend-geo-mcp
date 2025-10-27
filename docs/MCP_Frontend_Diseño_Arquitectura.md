# Diseño de MCP Frontend: GPS + Code Reviewer

## 🎯 Objetivo Principal

Diseñar un **Model Context Protocol (MCP)** práctico, ejecutable y simple que actúe como **"GPS + Code Reviewer" exclusivamente para Frontend**, facilitando:
1. La navegación rápida de proyectos Frontend
2. La validación de código React/Next.js contra estándares del equipo
3. Evitar duplicidad de componentes existentes

---

## 📋 Contexto del Equipo & Proyecto

### Stack Tecnológico Frontend
- **JavaScript, React, Next.js (con `/app` directory)**
- **Styling:** TailwindCSS, SASS
- **Herramientas:** Cursor AI (principal), CodeRabbit (reviews), Vite, Rollup
- **Meta-frameworks:** Preact (soporte)
- **Inteligencia:** Cursor con custom rules (archivos `.mdc`)

### Estructura del Equipo
- **5 desarrolladores:** 1 Frontend Senior (tú), 1 Backend, 2 FullStack, 1 Mobile
- **Enfoque actual:** Construir solución Frontend primero (MVP)
- **Objetivo futuro:** Expandir a Backend + Cross-Stack

### Tipo de Proyecto
- **WhiteLabel app** con soporte multi-tenant
- **Feature flags:** Usados para modificaciones por tenant
- **Configuración especial:** dnsmasq para simular URLs específicas por marca
- **Múltiples repositorios Frontend:** Con variaciones en estructura entre proyectos

---

## 🏗️ Arquitectura Propuesta

### Estructura de Alto Nivel

```
frontend-mcp/
├── core/
│   ├── indexer/           # Motor de indexación y análisis
│   ├── validator/          # Motor de validación de código
│   └── query/             # Motor de consultas y respuestas
├── adapters/
│   ├── cursor/            # Integración con Cursor
│   └── filesystem/        # Lectura de archivos
├── modules/
│   ├── navigator/         # Búsqueda y orientación
│   ├── validator/         # Revisión de código
│   └── project-guide/     # Guía del proyecto
└── config/
    └── rules/             # Rules y convenciones
```

### Arquitectura Conceptual

```
┌─────────────────────────────────────┐
│         Cursor AI IDE               │
├─────────────────────────────────────┤
│      MCP Protocol Interface         │
└────────────┬────────────────────────┘
             │
┌────────────▼────────────────────────┐
│       MCP Frontend Server           │
│  ┌──────────────────────────────┐   │
│  │    Request Handler           │   │
│  └────┬─────────┬──────┬────────┘   │
│       │         │      │            │
│  ┌────▼───┐ ┌──▼──┐ ┌─▼────────┐   │
│  │Navigator│ │Valid│ │Proj Guide│   │
│  └────┬───┘ └──┬──┘ └─┬────────┘   │
│       │         │      │            │
│  ┌────▼─────────▼──────▼────────┐   │
│  │     Core Services             │   │
│  │  • Indexer                    │   │
│  │  • AST Parser (lightweight)   │   │
│  │  • Rule Engine                │   │
│  │  • Cache Manager              │   │
│  └───────────────────────────────┘   │
└─────────────────────────────────────┘
```

### Decisión Clave: Arquitectura Event-Driven con Cache

**Por qué:** 
- Respuestas instantáneas para navegación
- Indexación incremental sin bloquear
- Cache persistente entre sesiones

**Cómo funciona:**
1. Al iniciar, indexa proyecto en background
2. Guarda índice en cache local (`.mcp-cache/`)
3. Actualiza incrementalmente con file watchers
4. Responde desde cache para velocidad

---

## 🔧 Diseño de Componentes Principales

### 1. Navigator Module

**Estrategia de Indexación:**
```typescript
interface ComponentIndex {
  components: Map<string, ComponentInfo>
  hooks: Map<string, HookInfo>
  styles: Map<string, StyleInfo>
  utils: Map<string, UtilInfo>
  searchIndex: TrieStructure  // Para búsqueda rápida
}

interface ComponentInfo {
  name: string
  path: string
  type: 'page' | 'component' | 'layout'
  imports: string[]
  exports: string[]
  props?: PropTypes
  examples?: UsageExample[]
  lastModified: Date
}
```

**Algoritmo de Búsqueda:**
- **Fuzzy matching** para nombres de componentes
- **Semantic search** usando embeddings locales (opcional para MVP)
- **Categorización automática** por análisis de imports/exports

### 2. Validator Module

**Pipeline de Validación:**
```
Código Input → Parser Ligero → Rule Matcher → Similarity Checker → Report
```

**Estrategia de Rules:**
```typescript
interface ValidationRule {
  id: string
  severity: 'error' | 'warning' | 'info'
  pattern: RegExp | ASTPattern
  message: string
  fix?: AutoFix
  examples: { good: string[], bad: string[] }
}
```

**Detección de Duplicados:**
- Hash de estructura de componentes (sin detalles)
- Comparación de propTypes/interfaces
- Análisis de imports similares

### 3. Project Guide Module

**Extracción de Información:**
```typescript
interface ProjectMetadata {
  structure: FolderStructure
  conventions: ConventionSet
  scripts: PackageScripts
  dependencies: DependencyMap
  featureFlags: FeatureFlagConfig
  documentation: DocLinks
}
```

---

## 🚀 Integración con Cursor

### Configuración del MCP

**En Cursor (`.cursorrules`):**
```json
{
  "mcpServers": {
    "frontend-gps": {
      "command": "node",
      "args": ["~/.cursor/extensions/frontend-mcp/server.js"],
      "env": {
        "PROJECT_ROOT": "${workspaceFolder}",
        "CACHE_DIR": "${workspaceFolder}/.mcp-cache"
      }
    }
  }
}
```

### Protocolo de Comunicación

**Formato de Requests:**
```typescript
interface MCPRequest {
  tool: 'navigate' | 'validate' | 'guide'
  query: string
  context?: {
    currentFile?: string
    selectedCode?: string
    projectPath: string
  }
}
```

**Formato de Responses:**
```typescript
interface MCPResponse {
  type: 'answer' | 'suggestion' | 'validation'
  content: string
  actions?: Action[]  // Links directos a archivos
  confidence: number
  sources: string[]   // Archivos analizados
}
```

---

## 📊 Análisis de Código Sin Complejidad

### Parser Ligero con Regex + AST Básico

**Estrategia híbrida:**
1. **Regex para extracción rápida** (95% casos)
2. **AST simple** solo para casos complejos
3. **No compilación**, solo análisis estático

**Ejemplo de análisis:**
```javascript
// Extracción rápida con regex
const extractComponent = (code) => {
  const componentRegex = /(?:export\s+)?(?:default\s+)?(?:function|const)\s+(\w+)/g
  const propsRegex = /\((?:\s*{\s*([^}]+)\s*}|([^)]+))\)/
  const hooksRegex = /use[A-Z]\w+/g
  
  return {
    name: componentRegex.exec(code)?.[1],
    props: parseProps(propsRegex.exec(code)),
    hooks: [...code.matchAll(hooksRegex)].map(m => m[0])
  }
}
```

### Detección de Patrones

**Sin parsing complejo:**
- Identificar imports/exports con regex
- Detectar hooks por convención `use*`
- Encontrar componentes por patrones JSX
- Analizar estructura por indentación

---

## 🎯 Plan de MVP

### Fase 1: Navigator Básico (1 semana)

**Funcionalidades:**
- Indexación de componentes React
- Búsqueda por nombre
- Respuesta con ubicación exacta

**Implementación mínima:**
```javascript
// MVP: Simple file scanner
class SimpleNavigator {
  async indexProject(rootPath) {
    // 1. Scan *.jsx, *.tsx files
    // 2. Extract component names
    // 3. Build search index
    // 4. Cache results
  }
  
  async findComponent(query) {
    // 1. Fuzzy match in index
    // 2. Return path + preview
  }
}
```

### Fase 2: Validator Simple (1 semana)

**Funcionalidades:**
- Cargar rules desde `.mdc` files
- Validar código seleccionado
- Sugerir componentes existentes

### Fase 3: Project Guide (3 días)

**Funcionalidades:**
- Leer README y package.json
- Extraer scripts y estructura
- Presentar resumen ejecutivo

---

## 🛠️ Funcionalidades Clave del MCP

### 1. **Navigator (Búsqueda & Orientación)**
**Propósito:** Responder "¿Dónde está X?" en el proyecto Frontend

**Ejemplos de preguntas:**
- "¿Dónde encuentro componentes de formularios?"
- "¿Cuál es la estructura de carpetas de este proyecto?"
- "¿Dónde están los hooks personalizados?"
- "¿Cómo está organizado el proyecto?"
- "¿Dónde viven los estilos globales?"
- "¿Hay un componente de botón ya existente?"

**Cómo funciona:**
- Lee la estructura real del proyecto
- Analiza componentes existentes
- Retorna ubicación exacta + contexto + ejemplos de uso

### 2. **Validator (Revisor de Código)**
**Propósito:** Validar código propuesto contra estándares del equipo

**Ejemplos de preguntas:**
- "¿Cumple este componente React con nuestros estándares?"
- "¿Está usando la librería correcta (TailwindCSS vs SASS)?"
- "¿Hay un componente existente similar?"
- "¿Hay duplicidad de código aquí?"
- "¿Esto sigue nuestro patrón de estructura?"

**Cómo funciona:**
- Carga custom rules (`.mdc` files)
- Analiza código propuesto
- Verifica contra patrones existentes
- Sugiere componentes existentes + ubicación
- Retorna recomendaciones accionables

### 3. **Project Guide (Orientación del Proyecto)**
**Propósito:** Entender rápidamente cómo funciona un proyecto Frontend

**Ejemplos de preguntas:**
- "¿Cómo corro este proyecto?"
- "¿Cuáles son las convenciones de nombres?"
- "¿Cómo funcionan los feature flags en este proyecto?"
- "¿Cuál es la arquitectura de carpetas?"
- "¿Hay documentación específica que deba saber?"

**Cómo funciona:**
- Lee README y comentarios del proyecto
- Analiza estructura y patrones
- Retorna resumen ejecutivo + detalles

---

## 🔄 Flujo de Trabajo del MCP

### Inicialización
```
1. Cursor inicia → Spawn MCP server
2. MCP detecta proyecto → Verifica cache
3. Si no hay cache → Indexación inicial (background)
4. Ready para queries
```

### Query Flow
```
1. Usuario pregunta "¿Dónde está el componente Button?"
2. MCP busca en índice
3. Encuentra matches + contexto
4. Retorna con links directos
```

### Validación Flow
```
1. Usuario selecciona código
2. Pide validación
3. MCP carga rules + analiza
4. Compara con componentes existentes
5. Retorna sugerencias
```

---

## 🎨 UX en Cursor

### Comandos Naturales
```
@frontend-gps where is the login form?
@frontend-gps validate this component
@frontend-gps show me similar components
@frontend-gps how to run this project?
```

### Respuestas Estructuradas
```markdown
📍 **Found: LoginForm Component**
- Location: `/src/features/auth/components/LoginForm.tsx`
- Type: Form Component
- Uses: React Hook Form, Zod validation
- Similar: `SignupForm`, `ResetPasswordForm`

[Open File] [Show Examples] [View Tests]
```

---

## 📈 Estimaciones y Roadmap

### MVP (2-3 semanas)
- **Semana 1**: Navigator básico + integración Cursor
- **Semana 2**: Validator simple + rules loader
- **Semana 3**: Testing + polish + documentation

### Post-MVP (1-2 meses)
- Cache inteligente con invalidación
- Detección de duplicados avanzada
- Análisis semántico de componentes
- UI preview de componentes
- Integración con CodeRabbit

---

## ⚠️ Riesgos y Mitigaciones

### Riesgo 1: Performance en Proyectos Grandes
**Mitigación**: 
- Cache agresivo
- Indexación incremental
- Límites de profundidad configurable

### Riesgo 2: Múltiples Estructuras de Proyecto
**Mitigación**:
- Detección automática de patrones
- Configuración por proyecto (`.mcp-config`)
- Fallbacks inteligentes

### Riesgo 3: Mantenimiento de Rules
**Mitigación**:
- Rules en archivos `.mdc` versionados
- Herencia de rules globales/locales
- Validación automática de rules

---

## 🚦 Próximos Pasos Concretos

### Inmediato (Esta semana)
1. **Crear prototipo del Navigator**
   - Simple scanner de archivos
   - Índice en memoria
   - API básica de búsqueda

2. **Probar integración Cursor**
   - Setup MCP protocol
   - Comandos básicos
   - Verificar latencia

### Corto Plazo (2-3 semanas)
3. **Implementar Validator MVP**
4. **Agregar cache persistente**
5. **Documentar setup y uso**

### Mediano Plazo (1-2 meses)
6. **Mejorar detección de duplicados**
7. **Agregar análisis semántico**
8. **Integrar con herramientas existentes**

---

## 💡 Decisiones de Diseño Clave

### 1. **No usar AST complejo inicialmente**
- Regex cubre 90% de casos
- Más rápido y simple
- AST solo cuando sea necesario

### 2. **Cache como ciudadano de primera clase**
- Todo se cachea
- Invalidación inteligente
- Respuestas instantáneas

### 3. **Modular desde el día 1**
- Cada módulo independiente
- Fácil agregar/quitar features
- Testing aislado

### 4. **Configuración por convención**
- Detectar automáticamente estructura
- Mínima config manual
- Adaptable a proyectos existentes

### 5. **Respuestas accionables**
- Siempre incluir links directos
- Ejemplos cuando sea posible
- Acciones sugeridas

---

## ✅ Criterios de Éxito del MCP (Frontend)

El MCP debe ser:

1. **Útil para programadores Frontend día a día**
   - Responde "¿Dónde está X?" en segundos
   - Valida código antes de que sea committeado
   - Reduce preguntas repetitivas al equipo

2. **Simple y Fácil de Usar**
   - Interfaz clara en Cursor
   - Respuestas directas y accionables
   - Sin setup complejo

3. **Útil para el equipo completo (incluyendo FullStack)**
   - Cualquiera que trabaje en Frontend puede usarlo
   - Responde preguntas tanto de Frontend como de FullStack

4. **Integrable en Cursor**
   - Funciona como MCP nativo en Cursor
   - Acceso a custom rules (`.mdc` files)
   - Análisis en tiempo real del proyecto

5. **Ejecutable y Pragmático**
   - Implementable sin dependencias complejas
   - Basado en análisis real de archivos del proyecto
   - No requiere cambios al workflow actual

---

Este diseño prioriza simplicidad y utilidad inmediata, con una arquitectura que permite evolución sin reescribir. El MVP se puede tener funcionando en 2-3 semanas con dedicación parcial de 1-2 desarrolladores.