#!/usr/bin/env python
"""
Script para probar las herramientas MCP directamente.
Simula cómo se llamarían desde Cursor.
"""

import asyncio
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.registry.database_client import DatabaseClient
from dotenv import load_dotenv

load_dotenv()


async def test_mcp_tools():
    """Prueba las herramientas MCP de feature flags simulando las funciones del server."""
    
    db = DatabaseClient()
    project_id = "platform-funnel"
    
    print("🧪 Probando herramientas MCP de Feature Flags\n")
    print("=" * 70)
    
    try:
        # Test 1: list_feature_flags
        print("\n1️⃣  list_feature_flags:")
        print("-" * 70)
        flags = await db.get_feature_flags_by_project(project_id)
        if flags:
            response = f"🚩 **Feature Flags in '{project_id}' ({len(flags)} total):**\n\n"
            for flag in flags[:10]:  # Mostrar solo los primeros 10
                response += f"- **{flag['name']}**\n"
                if flag.get('description'):
                    response += f"  - Description: {flag['description']}\n"
                if flag.get('default_value') is not None:
                    response += f"  - Default: {flag['default_value']}\n"
                if flag.get('value_type'):
                    response += f"  - Type: {flag['value_type']}\n"
                response += "\n"
            if len(flags) > 10:
                response += f"... y {len(flags) - 10} más\n"
            print(response)
        else:
            print("⚠️  No feature flags found")
        
        # Test 2: get_feature_flag_usage (replaces search_by_feature_flag)
        print("\n\n2️⃣  get_feature_flag_usage('BILLING_ADDRESS_ENABLED', 'platform-funnel', 'all'):")
        print("-" * 70)
        components = await db.get_components_using_flag("BILLING_ADDRESS_ENABLED", project_id)
        hooks = await db.get_hooks_using_flag("BILLING_ADDRESS_ENABLED", project_id)
        
        if components or hooks:
            response = f"🚩 **Feature Flag Usage: `BILLING_ADDRESS_ENABLED`**\n\n"
            if components:
                response += f"### 📦 Components ({len(components)})\n\n"
                for comp in components:
                    response += f"- **{comp['name']}** (`{comp['file_path']}`)\n"
                response += "\n"
            if hooks:
                response += f"### 🪝 Hooks ({len(hooks)})\n\n"
                for hook in hooks:
                    response += f"- **{hook['name']}** (`{hook['file_path']}`)\n"
            print(response)
        else:
            print("🔍 No components or hooks found using feature flag 'BILLING_ADDRESS_ENABLED'")
        
        # Test 3: get_feature_flag_details
        print("\n\n3️⃣  get_feature_flag_details('FUNNEL_STYLE', 'platform-funnel'):")
        print("-" * 70)
        flag = await db.get_feature_flag_by_name("FUNNEL_STYLE", project_id)
        if flag:
            response = f"🚩 **Feature Flag: FUNNEL_STYLE**\n\n"
            if flag.get('description'):
                response += f"**Description:** {flag['description']}\n\n"
            if flag.get('default_value') is not None:
                response += f"**Default Value:** {flag['default_value']}\n"
            if flag.get('value_type'):
                response += f"**Type:** {flag['value_type']}\n"
            if flag.get('possible_values'):
                response += f"**Possible Values:** {', '.join(flag['possible_values'])}\n"
            if flag.get('file_path'):
                response += f"**File:** `{flag['file_path']}`\n"
            
            comps = await db.get_components_using_flag("FUNNEL_STYLE", project_id)
            if comps:
                response += f"\n**Used in {len(comps)} component(s):**\n"
                for comp in comps:
                    response += f"- {comp['name']} (`{comp['file_path']}`)\n"
            else:
                response += "\n⚠️ **Not used in any component**\n"
            print(response)
        else:
            print("❌ Feature flag 'FUNNEL_STYLE' not found")
        
        # Test 4: get_unused_feature_flags
        print("\n\n4️⃣  get_unused_feature_flags('platform-funnel'):")
        print("-" * 70)
        unused_flags = await db.get_unused_feature_flags(project_id)
        if unused_flags:
            response = f"⚠️ **Unused Feature Flags in '{project_id}':**\n\n"
            for flag in unused_flags[:15]:  # Mostrar solo los primeros 15
                response += f"- **{flag['name']}**"
                if flag.get('description'):
                    response += f" - {flag['description']}"
                response += "\n"
            if len(unused_flags) > 15:
                response += f"\n... y {len(unused_flags) - 15} más\n"
            print(response)
        else:
            print("✅ All feature flags in project 'platform-funnel' are being used!")
        
        print("\n" + "=" * 70)
        print("✅ Todas las herramientas MCP funcionan correctamente!")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(test_mcp_tools())

