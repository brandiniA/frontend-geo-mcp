#!/usr/bin/env python3
"""
Script para probar la validación de nombres de componentes del parser.
Verifica que el parser rechaza constantes, variables y funciones correctamente.
"""

import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.parser import ReactParser


def test_component_validation():
    """Prueba exhaustiva de la validación de nombres de componentes."""
    parser = ReactParser()
    
    test_cases = {
        # ✅ DEBE ACEPTAR - Componentes válidos en PascalCase
        "✅ COMPONENTES VÁLIDOS (PascalCase)": {
            "Button": True,
            "UserProfile": True,
            "LoginForm": True,
            "NavBar": True,
            "Card": True,
            "Modal": True,
            "Dropdown": True,
            "DataTable": True,
            "MyAwesomeComponent": True,
        },
        
        # ❌ DEBE RECHAZAR - Constantes en SCREAMING_SNAKE_CASE
        "❌ CONSTANTES SCREAMING_SNAKE_CASE": {
            "API_URL": False,
            "CONFIG_NAME": False,
            "DB_HOST": False,
            "REACT_APP_KEY": False,
            "NODE_ENV": False,
            "VITE_SECRET": False,
            "MAX_RETRIES": False,
            "DEFAULT_TIMEOUT": False,
            "THEME_COLORS": False,
        },
        
        # ❌ DEBE RECHAZAR - camelCase (minúscula inicial)
        "❌ camelCase (minúscula inicial)": {
            "button": False,
            "userProfile": False,
            "myComponent": False,
            "count": False,
            "userData": False,
            "apiKey": False,
        },
        
        # ❌ DEBE RECHAZAR - Funciones comunes (prefijos is*, has*, can*, etc.)
        "❌ PATRONES DE FUNCIONES/VARIABLES": {
            "isActive": False,
            "hasError": False,
            "canDelete": False,
            "shouldRender": False,
            "getValue": False,
            "setValue": False,
            "makeRequest": False,
            "createUser": False,
            "fetchData": False,
            "parseJSON": False,
            "validateEmail": False,
        },
        
        # ❌ DEBE RECHAZAR - Constantes con sufijos comunes
        "❌ CONSTANTES CON SUFIJOS": {
            "Config_DEFAULT": False,
            "Theme_DARK": False,
            "Theme_LIGHT": False,
            "SIZE_MAX": False,
            "PORT_TIMEOUT": False,
            "API_KEYS": False,
            "Settings_OPTIONS": False,
        },
        
        # ❌ DEBE RECHAZAR - Palabras reservadas
        "❌ PALABRAS RESERVADAS": {
            "Component": False,
            "React": False,
            "Fragment": False,
            "Suspense": False,
            "Error": False,
            "Promise": False,
            "Object": False,
        },
        
        # ❌ DEBE RECHAZAR - Nombres inválidos
        "❌ NOMBRES INVÁLIDOS": {
            "2Button": False,
            "_private": False,
            "": False,
        },
    }
    
    print("=" * 80)
    print("PRUEBA DE VALIDACIÓN DE COMPONENTES REACT")
    print("=" * 80)
    
    total_tests = 0
    passed_tests = 0
    failed_tests = []
    
    for category, cases in test_cases.items():
        print(f"\n{category}")
        print("-" * 80)
        
        for name, expected in cases.items():
            result = parser._is_valid_component_name(name)
            status = "✅ PASS" if result == expected else "❌ FAIL"
            total_tests += 1
            
            if result == expected:
                passed_tests += 1
                print(f"  {status} | {name:25s} | Esperado: {expected:5} | Obtenido: {result:5}")
            else:
                failed_tests.append((name, expected, result))
                print(f"  {status} | {name:25s} | ❌ ERROR - Esperado: {expected:5} | Obtenido: {result:5}")
    
    print("\n" + "=" * 80)
    print(f"RESUMEN: {passed_tests}/{total_tests} pruebas pasadas")
    print("=" * 80)
    
    if failed_tests:
        print("\n⚠️  PRUEBAS FALLIDAS:")
        for name, expected, result in failed_tests:
            print(f"   - {name}: esperado {expected}, obtuvo {result}")
        return False
    else:
        print("\n✅ ¡Todas las pruebas pasaron correctamente!")
        return True


if __name__ == "__main__":
    success = test_component_validation()
    sys.exit(0 if success else 1)
