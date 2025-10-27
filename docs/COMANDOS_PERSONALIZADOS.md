# Guía de Instalación: Comandos Personalizados para Python

Esta guía te ayudará a configurar los comandos personalizados de Python en tu sistema para facilitar el desarrollo con ambientes virtuales.

## 📋 Contenido

1. [¿Qué son estos comandos?](#qué-son-estos-comandos)
2. [Requisitos](#requisitos)
3. [Instalación Rápida](#instalación-rápida)
4. [Instalación Manual](#instalación-manual)
5. [Verificación](#verificación)
6. [Comandos Disponibles](#comandos-disponibles)
7. [Personalización](#personalización)

---

## 🤔 ¿Qué son estos comandos?

Son alias y funciones personalizadas de bash que facilitan:

- ✅ Activar/desactivar ambientes virtuales Python
- ✅ Ejecutar scripts Python con retroalimentación visual
- ✅ Ver el estado del proyecto rápidamente
- ✅ Todo con colores, emojis y divisores visuales

**Ejemplo:**

Sin estos comandos:
```bash
source /path/to/project/.venv/bin/activate
python script.py
deactivate
```

Con estos comandos:
```bash
py-up
py-run script
py-down
```

---

## ✅ Requisitos

- **Bash** (no sh, dash u otro shell)
- Linux o macOS
- Acceso a tu directorio home (`~`)

---

## 🚀 Instalación Rápida

Si quieres instalar todo de una vez, copia y pega esto en tu terminal:

```bash
# Descargar la configuración
cat > ~/.bash_functions << 'EOF'
# ==================== COLORES ====================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# ==================== ACTIVATE/DEACTIVATE ====================

# Activate Python virtual environment with nice feedback
pyup() {
    if [ -f ".venv/bin/activate" ]; then
        source .venv/bin/activate
        echo -e "${GREEN}✓${NC} ${CYAN}Virtual environment activated!${NC}"
        echo -e "${BLUE}→${NC} Python: $(python --version)"
        echo -e "${BLUE}→${NC} Location: $(which python)"
    else
        echo -e "${RED}✗${NC} ${YELLOW}No .venv found in current directory${NC}"
        return 1
    fi
}

# Deactivate with confirmation feedback
pydown() {
    if [ -n "$VIRTUAL_ENV" ]; then
        deactivate
        echo -e "${GREEN}✓${NC} ${CYAN}Virtual environment deactivated${NC}"
    else
        echo -e "${YELLOW}⚠${NC}  No active virtual environment"
    fi
}

# Activate venv from any subdirectory in the project
pyfind() {
    local depth=0
    local max_depth=5
    
    while [ $depth -le $max_depth ]; do
        if [ -f ".venv/bin/activate" ]; then
            source .venv/bin/activate
            echo -e "${GREEN}✓${NC} ${CYAN}Virtual environment activated from:${NC} $(pwd)"
            echo -e "${BLUE}→${NC} Python: $(python --version)"
            return 0
        fi
        
        if [ "$(pwd)" = "/" ]; then
            break
        fi
        
        cd ..
        ((depth++))
    done
    
    echo -e "${RED}✗${NC} ${YELLOW}No virtual environment found${NC}"
    return 1
}

# ==================== RUN PYTHON FILES ====================

# Function to find and run a Python file with nice output
pyrun() {
    local filename="$1"
    
    if [ -z "$filename" ]; then
        echo -e "${RED}✗${NC} ${YELLOW}Usage:${NC} py-run <filename> [args...]"
        echo -e "${BLUE}→${NC} Example: py-run server.py"
        return 1
    fi
    
    # Add .py extension if not provided
    if [[ ! "$filename" == *.py ]]; then
        filename="${filename}.py"
    fi
    
    # Search in common directories
    local search_dirs=("." "src" "scripts" "bin" "tools" "app" "main" "lib")
    
    for dir in "${search_dirs[@]}"; do
        if [ -f "$dir/$filename" ]; then
            echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            echo -e "${GREEN}▶${NC}  Running: ${BLUE}$dir/$filename${NC}"
            echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            python "$dir/$filename" "${@:2}"
            local exit_code=$?
            echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            if [ $exit_code -eq 0 ]; then
                echo -e "${GREEN}✓${NC}  Process completed successfully"
            else
                echo -e "${RED}✗${NC}  Process exited with code: ${exit_code}"
            fi
            echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
            return $exit_code
        fi
    done
    
    echo -e "${RED}✗${NC} ${YELLOW}File not found:${NC} ${BLUE}$filename${NC}"
    echo -e "${BLUE}→${NC} Searched in: ${search_dirs[*]}"
    return 1
}

# ==================== UTILITIES ====================

# Show project status
pystatus() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📊  Project Status${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    
    if [ -n "$VIRTUAL_ENV" ]; then
        echo -e "${GREEN}✓${NC}  Virtual Environment: ${BLUE}ACTIVE${NC}"
        echo -e "${BLUE}→${NC}  Python: $(python --version)"
        echo -e "${BLUE}→${NC}  Location: ${BLUE}$VIRTUAL_ENV${NC}"
    else
        echo -e "${YELLOW}⚠${NC}  Virtual Environment: ${YELLOW}INACTIVE${NC}"
    fi
    
    echo ""
    echo -e "${BLUE}→${NC}  UV: $(uv --version 2>/dev/null || echo 'Not installed')"
    
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Show all available commands
pyhelp() {
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📚  Available Commands${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo -e "${GREEN}Environment:${NC}"
    echo -e "  ${BLUE}py-up${NC}        → Activate virtual environment"
    echo -e "  ${BLUE}py-down${NC}      → Deactivate virtual environment"
    echo -e "  ${BLUE}py-find${NC}      → Find and activate venv from subdirectory"
    echo -e "  ${BLUE}py-status${NC}    → Show project status"
    echo ""
    echo -e "${GREEN}Running:${NC}"
    echo -e "  ${BLUE}py-run${NC}       → Find and run a Python file"
    echo ""
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}
EOF

# Crear aliases
cat > ~/.bash_aliases << 'EOF'
# Python development aliases
alias py-up='pyup'
alias py-down='pydown'
alias py-find='pyfind'
alias py-run='pyrun'
alias py-status='pystatus'
alias py-help='pyhelp'
EOF

# Agregar a bashrc si no está
if ! grep -q "bash_functions" ~/.bashrc; then
    echo "" >> ~/.bashrc
    echo "# Load custom bash functions" >> ~/.bashrc
    echo "[ -f ~/.bash_functions ] && source ~/.bash_functions" >> ~/.bashrc
fi

echo "✓ ¡Configuración completada!"
echo "Abre una nueva terminal y ejecuta: py-help"
```

Copia el bloque anterior completo y pégalo en tu terminal. ✅

---

## 🔧 Instalación Manual

Si prefieres hacerlo paso a paso:

### Paso 1: Crear `~/.bash_functions`

```bash
nano ~/.bash_functions
```

Copia el contenido de las funciones que está más abajo en esta guía (sección "Código Fuente").

### Paso 2: Crear `~/.bash_aliases`

```bash
nano ~/.bash_aliases
```

Agrega:
```bash
# Python development aliases
alias py-up='pyup'
alias py-down='pydown'
alias py-find='pyfind'
alias py-run='pyrun'
alias py-status='pystatus'
alias py-help='pyhelp'
```

### Paso 3: Actualizar `~/.bashrc`

Abre tu `.bashrc`:
```bash
nano ~/.bashrc
```

Agrega al final:
```bash
# Load custom bash functions
[ -f ~/.bash_functions ] && source ~/.bash_functions
```

### Paso 4: Recargar la configuración

```bash
source ~/.bashrc
```

---

## ✅ Verificación

Para verificar que todo está correctamente instalado:

```bash
# Abre una NUEVA terminal

# Test 1: Ver la ayuda
py-help

# Test 2: Ver el estado
py-status

# Test 3: Verificar que los archivos existen
ls -la ~/.bash_functions ~/.bash_aliases
```

Si ves los comandos funcionando con colores y emojis, ¡está todo correcto! ✓

---

## 📚 Comandos Disponibles

### `py-up` - Activar Ambiente Virtual

```bash
py-up
```

**Qué hace:**
- Busca `.venv/bin/activate` en el directorio actual
- Lo activa
- Muestra la versión de Python y ubicación

**Cuándo usarlo:**
- Al abrir una nueva terminal en tu proyecto

---

### `py-down` - Desactivar Ambiente Virtual

```bash
py-down
```

**Qué hace:**
- Desactiva el ambiente virtual actual
- Confirma la desactivación

---

### `py-find` - Buscar Activar desde Subdirectorio

```bash
py-find
```

**Qué hace:**
- Busca `.venv` en el directorio actual y directorios padres (hasta 5 niveles)
- Lo activa automáticamente

**Cuándo usarlo:**
- Cuando estás en un subdirectorio del proyecto
- Cuando no sabes exactamente dónde está el `.venv`

---

### `py-run` - Ejecutar Archivo Python

```bash
py-run <archivo> [argumentos]
```

**Ejemplos:**
```bash
py-run server.py
py-run script --verbose
py-run tests.py
```

**Qué hace:**
- Busca el archivo en directorios comunes
- Lo ejecuta con Python
- Muestra divisores visuales y estado de salida

---

### `py-status` - Ver Estado del Proyecto

```bash
py-status
```

**Muestra:**
- Si el ambiente virtual está activo
- Versión de Python
- Ubicación del ambiente
- Versión de herramientas (uv, etc.)

---

### `py-help` - Mostrar Ayuda

```bash
py-help
```

**Muestra:**
- Lista de todos los comandos
- Descripción breve de cada uno

---

## ⚙️ Personalización

### Cambiar Colores

Edita `~/.bash_functions` y busca la sección "COLORES":

```bash
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'
```

Puedes encontrar códigos de color ANSI en: https://en.wikipedia.org/wiki/ANSI_escape_code#Colors

### Agregar Nuevos Comandos

Abre `~/.bash_functions` y agrega al final:

```bash
# Mi nuevo comando
micomando() {
    echo "¡Hola desde mi comando!"
}
```

Luego agrega el alias en `~/.bash_aliases`:

```bash
alias mi-cmd='micomando'
```

Recarga con:
```bash
source ~/.bash_functions
```

### Modificar Directorios de Búsqueda

En `py-run`, edita la línea:

```bash
local search_dirs=("." "src" "scripts" "bin" "tools" "app" "main" "lib")
```

Agrega o quita directorios según necesites.

---

## 🔍 Troubleshooting

### Problema: "command not found"

**Solución:**
1. Abre una NUEVA terminal (importante)
2. Verifica que los archivos existen: `ls -la ~/.bash_functions ~/.bash_aliases`
3. Recarga manualmente: `source ~/.bash_functions`

### Problema: Los colores no funcionan

**Solución:**
1. Verifica que usas bash: `echo $SHELL` (debe terminar en `/bash`)
2. Si ves `/bin/sh`, abre bash explícitamente: `bash`
3. Si sigue sin funcionar, verifica que el terminal soporta colores ANSI

### Problema: El alias no funciona pero la función sí

**Solución:**
- Verifica que `.bash_aliases` se está cargando en `.bashrc`
- Algunos sistemas usan `~/.bash_profile` en lugar de `~/.bashrc`
- Agrega la línea de carga también en `~/.bash_profile`:
  ```bash
  [ -f ~/.bash_aliases ] && source ~/.bash_aliases
  ```

---

## 📝 Código Fuente Completo

Si necesitas copiar manualmente, aquí está el código completo:

### ~/.bash_functions

[Contenido completo de bash_functions con todas las funciones]

### ~/.bash_aliases

```bash
# Python development aliases
alias py-up='pyup'
alias py-down='pydown'
alias py-find='pyfind'
alias py-run='pyrun'
alias py-status='pystatus'
alias py-help='pyhelp'
```

---

## 🤝 Compartir con tu Equipo

Para compartir esta configuración con tus colegas:

1. **Opción 1: Instalar Manualmente**
   - Dales esta guía
   - Que sigan los pasos de instalación

2. **Opción 2: Script Automático**
   - Crea un script `setup.sh` en tu proyecto
   - Que lo ejecuten: `bash setup.sh`

3. **Opción 3: Documentación en el Proyecto**
   - Mantén esta guía en `docs/COMANDOS_PERSONALIZADOS.md`
   - Referencia en el README

---

## ✨ ¿Por qué usar esto?

- ⏱️ **Ahorra tiempo** - Menos comandos para escribir
- 🎨 **Visual** - Colores y emojis para mejor UX
- 🔄 **Consistente** - Mismo comportamiento en todos tus proyectos
- 📦 **Portátil** - Funciona en cualquier proyecto Python
- 🛠️ **Personalizable** - Fácil de adaptar

---

**Última actualización:** Octubre 2025
