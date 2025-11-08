# MCP Component Search Strategy Guide

**Documento de Diseño: Estrategias Óptimas para Búsqueda de Componentes**

**Versión:** 1.0  
**Fecha:** Octubre 2025  
**Autor:** AI Code Assistant  
**Aplicable a:** Platform Funnel (645+ componentes React)

---

## 📋 Tabla de Contenidos

1. [Problema Identificado](#problema-identificado)
2. [Análisis de Soluciones](#análisis-de-soluciones)
3. [Estrategias Recomendadas](#estrategias-recomendadas)
4. [Implementación](#implementación)
5. [Casos de Uso](#casos-de-uso)
6. [Métricas de Éxito](#métricas-de-éxito)

---

## 🔴 Problema Identificado

### Limitación Actual
- **Total de componentes:** 645+ archivos React
- **Límite actual en MCP:** 20 componentes indexados
- **Cobertura:** Solo ~3% del codebase
- **Impacto:** Búsquedas incompletas, resultados inexactos

### Consecuencias
1. ❌ No se pueden encontrar componentes importantes
2. ❌ Búsquedas semánticas devuelven resultados parciales
3. ❌ Duplicidad de esfuerzo (búsqueda manual + MCP)
4. ❌ Experiencia de usuario pobre

---

## 📊 Análisis de Soluciones

### Opción 1: Pagination (❌ NO RECOMENDADO)

**Implementación:**
```javascript
list_components(page: number, limit: number = 20, project_id: string)
// list_components(1) → componentes 1-20
// list_components(2) → componentes 21-40
// ... 32 llamadas para ver todos
```

| Aspecto | Evaluación |
|--------|------------|
| **Facilidad** | ⭐⭐⭐ Fácil de implementar |
| **Performance** | ⭐ Muy lento (32+ llamadas necesarias) |
| **UX** | ⭐ Frustrante para el usuario |
| **Descubrimiento** | ⭐ Buscar un componente es tedioso |
| **Utilidad** | ⭐⭐ Solo útil para exploración casual |

**Conclusión:** Anti-pattern para búsqueda. Evitar.

---

### Opción 2: Búsqueda Filtrada por Ubicación (✅ RECOMENDADO)

**Implementación:**
```javascript
list_components_in_path(path: string, project_id: string)
// Retorna todos los componentes en una ruta específica
// Ejemplo: list_components_in_path("src/components/purchase", "platform-funnel")
// Retorna: ~45 componentes (manejable)

list_components_by_type(type: string, project_id: string)
// Tipos: "atom", "molecule", "page", "container", "hook"
// Ejemplo: list_components_by_type("atom", "platform-funnel")
// Retorna: ~120 componentes
```

**Estructura del proyecto:**
```
src/
├── components/        (300+ componentes)
│   ├── purchase/      (45 componentes) ✅
│   ├── seats/         (30 componentes) ✅
│   ├── payment/       (25 componentes) ✅
│   └── ...
├── ui/
│   ├── atoms/         (120 componentes) ✅
│   ├── molecules/     (180 componentes) ✅
│   └── organisms/     (50 componentes) ✅
├── hooks/             (55 custom hooks) ✅
└── utils/             (120 funciones utilitarias)
```

| Aspecto | Evaluación |
|--------|------------|
| **Facilidad** | ⭐⭐⭐⭐ Muy fácil de implementar |
| **Performance** | ⭐⭐⭐⭐ Una sola llamada |
| **UX** | ⭐⭐⭐⭐⭐ Excelente |
| **Descubrimiento** | ⭐⭐⭐⭐ Rápido y preciso |
| **Utilidad** | ⭐⭐⭐⭐⭐ Muy útil para investigación |

**Ventajas:**
- ✅ Una sola llamada al MCP
- ✅ Resultados manejables (< 200 componentes)
- ✅ Intuitivo para los desarrolladores
- ✅ Fácil de filtrar localmente si es necesario

---

### Opción 3: Búsqueda Semántica Avanzada (✅ MÁS POTENTE)

**Implementación:**
```javascript
search_components_semantic(query: string, filters: object, project_id: string)

// Ejemplos de uso:
search_components_semantic("price breakdown", {
  type: "atom",
  path: "src/ui",
  contains_hook: "useState"
})

// Busca en:
// - Nombres de componentes
// - JSDoc (descriptions, params, return types)
// - Props esperadas
// - Hooks utilizados
// - Comentarios en código
```

| Aspecto | Evaluación |
|--------|------------|
| **Facilidad** | ⭐⭐⭐ Requiere procesamiento adicional |
| **Performance** | ⭐⭐⭐⭐ Optimizado con índices |
| **UX** | ⭐⭐⭐⭐⭐ Excelente - encuentra lo que necesitas |
| **Descubrimiento** | ⭐⭐⭐⭐⭐ Muy inteligente |
| **Utilidad** | ⭐⭐⭐⭐⭐ Altamente útil |

**Ventajas:**
- ✅ Entiende intención, no solo keywords
- ✅ Filtra automáticamente resultados relevantes
- ✅ Multiidioma potencial (English + Spanish)
- ✅ Busca en documentación JSDoc

---

### Opción 4: Estadísticas + Categorización (✅ COMPLEMENTARIA)

**Implementación:**
```javascript
get_component_stats(project_id: string)
// Retorna estructura completa del índice

interface ComponentStats {
  total: number
  byType: {
    atoms: number
    molecules: number
    pages: number
    hooks: number
    containers: number
  }
  byPath: {
    [path: string]: number
  }
  lastUpdated: ISO8601DateTime
  indexCoverage: percentage
}

// Ejemplo de respuesta:
{
  total: 645,
  byType: {
    atoms: 120,
    molecules: 180,
    pages: 45,
    hooks: 55,
    containers: 80,
    utils: 165
  },
  byPath: {
    "src/components/purchase": 45,
    "src/ui/atoms": 120,
    "src/ui/molecules": 180,
    ...
  },
  indexCoverage: 100%
}
```

| Aspecto | Evaluación |
|--------|------------|
| **Facilidad** | ⭐⭐⭐⭐ Trivial de implementar |
| **Performance** | ⭐⭐⭐⭐⭐ Cache en memoria |
| **UX** | ⭐⭐⭐⭐ Proporciona contexto |
| **Descubrimiento** | ⭐⭐⭐ Te orienta dónde buscar |
| **Utilidad** | ⭐⭐⭐⭐ Muy útil de referencia |

**Ventajas:**
- ✅ Una llamada inicial
- ✅ Orienta al usuario
- ✅ Verifica cobertura de indexación
- ✅ Ayuda a tomar decisiones de búsqueda

---

## 🎯 Estrategias Recomendadas

### ✅ Estrategia Ganadora: La Combinación (3 Pilares)

Implementar estas 3 nuevas funciones en tu MCP:

#### **Pilar 1: Búsqueda por Ubicación**
```javascript
list_components_in_path(path: string, project_id: string): ComponentInfo[]
```

**Cuándo usarlo:**
- Explorar una feature específica
- Entender la arquitectura de un módulo
- Encontrar componentes relacionados

**Ejemplo práctico:**
```
Usuario: "Encuentra componentes en checkout"
MCP: list_components_in_path("src/components/purchase/Checkout", "platform-funnel")
Resultado: 8 componentes (Checkout, CheckoutContainer, PaymentForm, etc.)
```

---

#### **Pilar 2: Búsqueda Semántica**
```javascript
search_components_semantic(
  query: string,
  filters?: {
    type?: "atom" | "molecule" | "page" | "hook" | "container"
    path?: string
    contains_hook?: string
    contains_dependency?: string
  },
  project_id: string
): ComponentInfo[]
```

**Cuándo usarlo:**
- No sabes dónde está algo
- Tienes una idea pero necesitas encontrar implementación similar
- Búsquedas complejas multicriterio

**Ejemplo práctico:**
```
Usuario: "Encuentra componentes que manejen precios"
MCP: search_components_semantic("price breakdown total", {
  path: "src/components/purchase",
  type: "atom"
})
Resultado: [PricingRow, LocalizedCurrency, PriceDisplay]
```

---

#### **Pilar 3: Estadísticas Contextuales**
```javascript
get_component_index_stats(project_id: string): IndexStats
```

**Cuándo usarlo:**
- Entender estructura del proyecto
- Verificar cobertura de indexación
- Tomar decisiones sobre dónde buscar

**Ejemplo práctico:**
```
Usuario: "Cuántos componentes hay?"
MCP: get_component_index_stats("platform-funnel")
Resultado: { total: 645, atoms: 120, molecules: 180, ... }
```

---

## 🔧 Implementación

### Paso 1: Extender el MCP Server

**Archivo:** `mcp-server/handlers/components.js` (o similar)

```javascript
// Función 1: Búsqueda por ruta
async function listComponentsInPath(path, projectId) {
  const components = indexDB.query({
    path: { $regex: path },
    project: projectId
  });
  return components.sort((a, b) => a.name.localeCompare(b.name));
}

// Función 2: Búsqueda semántica
async function searchComponentsSemantic(query, filters, projectId) {
  const searchFields = [
    'name',
    'description',
    'jsdoc.description',
    'jsdoc.params[].description',
    'props[].name'
  ];

  let results = indexDB.search(query, searchFields, {
    project: projectId,
    ...filters
  });

  // Rank por relevancia (name match > description match)
  return results.sort((a, b) => b.relevance - a.relevance);
}

// Función 3: Estadísticas
async function getComponentIndexStats(projectId) {
  const all = indexDB.query({ project: projectId });
  
  const stats = {
    total: all.length,
    byType: groupBy(all, 'type'),
    byPath: groupBy(all, 'path'),
    lastUpdated: new Date(),
    indexCoverage: calculateCoverage(projectId)
  };

  return stats;
}
```

---

### Paso 2: Registrar en el MCP

**Archivo:** `mcp.json` (o similar)

```json
{
  "tools": {
    "mcp_Frontend_GPS__list_components_in_path": {
      "description": "List all components in a specific directory path",
      "inputSchema": {
        "properties": {
          "path": { "type": "string" },
          "project_id": { "type": "string" }
        },
        "required": ["path", "project_id"]
      }
    },
    "mcp_Frontend_GPS__search_components_semantic": {
      "description": "Search components by meaning with optional filters",
      "inputSchema": {
        "properties": {
          "query": { "type": "string" },
          "filters": { "type": "object" },
          "project_id": { "type": "string" }
        },
        "required": ["query", "project_id"]
      }
    },
    "mcp_Frontend_GPS__get_component_index_stats": {
      "description": "Get statistics about indexed components",
      "inputSchema": {
        "properties": {
          "project_id": { "type": "string" }
        },
        "required": ["project_id"]
      }
    }
  }
}
```

---

## 📚 Casos de Uso

### Caso 1: Explorar Feature de Checkout

**Escenario:** "Necesito entender toda la estructura de checkout"

**Flujo:**
```
1. get_component_index_stats() 
   → Entender que hay 645 componentes
   
2. list_components_in_path("src/components/purchase/Checkout")
   → Obtener 8 componentes de checkout
   
3. get_component_details("Checkout")
   → Analizar dependencias
   
4. get_component_details("PurchasePricing")
   → Profundizar en subcomponentes
```

**Resultado:** Visión clara de la arquitectura en 4 llamadas

---

### Caso 2: Buscar Componente de Precios

**Escenario:** "Dónde está el desglose de precios en checkout?"

**Flujo:**
```
1. search_components_semantic("price breakdown checkout", {
     type: "atom",
     path: "src/components"
   })
   → Retorna: [PricingRow, LocalizedCurrency, ...]
   
2. get_component_details("PricingRow")
   → Analizar props y uso
```

**Resultado:** Encuentra componente en 2 llamadas (vs 32 con pagination)

---

### Caso 3: Reutilizar Patrón Existente

**Escenario:** "Quiero un componente que maneje currency, como se hace aquí?"

**Flujo:**
```
1. search_components_semantic("currency formatter", {
     contains_dependency: "currency-formatter"
   })
   → Retorna: [LocalizedCurrency, PriceFormatter, ...]
   
2. get_component_details("LocalizedCurrency")
   → Copiar patrón implementado
```

**Resultado:** Reutilización de patterns existentes

---

## 📈 Métricas de Éxito

### Antes (Estado Actual)
| Métrica | Valor |
|---------|-------|
| Componentes indexados | 20 (3%) |
| Tiempo promedio búsqueda manual | 10-15 min |
| Tasa de descubrimiento | 20% |
| Llamadas MCP necesarias | 1 (limitado) |
| Satisfacción del usuario | ⭐⭐ Baja |

### Después (Con 3 Pilares)
| Métrica | Valor |
|---------|-------|
| Componentes indexados | 645 (100%) |
| Tiempo promedio búsqueda | 30 seg - 2 min |
| Tasa de descubrimiento | 95%+ |
| Llamadas MCP necesarias | 1-3 (óptimas) |
| Satisfacción del usuario | ⭐⭐⭐⭐⭐ Excelente |

---

## 🚀 Plan de Implementación

### Fase 1: Foundation (Semana 1)
- [ ] Extender MCP con `list_components_in_path`
- [ ] Extender MCP con `get_component_index_stats`
- [ ] Pruebas básicas

### Fase 2: Búsqueda Semántica (Semana 2)
- [ ] Implementar `search_components_semantic`
- [ ] Optimizar índice de búsqueda
- [ ] Pruebas completas

### Fase 3: Integración (Semana 3)
- [ ] Documentar todas las funciones
- [ ] Entrenar al AI assistant
- [ ] Recolectar feedback

---

## 📝 Conclusiones

### ❌ Evitar
- ❌ Pagination (ineficiente, 32+ llamadas)
- ❌ Listar todo sin filtros (sobrecarga)
- ❌ Búsquedas genéricas sin contexto

### ✅ Adoptar
- ✅ Búsqueda por ubicación + contexto
- ✅ Búsqueda semántica inteligente
- ✅ Estadísticas de referencia
- ✅ Combinación de 3 pilares

### 💡 Resultado Final
Una experiencia de búsqueda de componentes **rápida, intuitiva y eficiente**, similar a IDEs profesionales como VS Code o WebStorm.

---

## 📞 Contacto & Feedback

Si tienes preguntas o sugerencias sobre esta estrategia, documenta en el formato:

```
[FEEDBACK]
Tipo: Bug | Feature | Improvement | Question
Descripción: ...
Caso de Uso: ...
```

---

**Documento finalizado:** Octubre 2025  
**Próxima revisión:** Después de la Fase 3
