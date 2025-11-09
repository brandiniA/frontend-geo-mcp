#!/usr/bin/env python
"""
Script para ejecutar herramientas MCP directamente.
"""

import asyncio
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.registry.database_client import DatabaseClient
from dotenv import load_dotenv

load_dotenv()


async def run_get_unused_feature_flags(project_id: str):
    """Ejecuta la herramienta get_unused_feature_flags."""
    db = DatabaseClient()
    
    try:
        unused_flags = await db.get_unused_feature_flags(project_id)
        
        if not unused_flags:
            print(f"✅ All feature flags in project '{project_id}' are being used!")
            return
        
        print(f"⚠️ **Unused Feature Flags in '{project_id}':**\n")
        for flag in unused_flags:
            print(f"- **{flag['name']}**", end="")
            if flag.get('description'):
                print(f" - {flag['description']}")
            else:
                print()
        
        print(f"\n📊 Total: {len(unused_flags)} unused feature flags")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/run_mcp_tool.py <project_id>")
        print("Example: python scripts/run_mcp_tool.py platform-funnel")
        sys.exit(1)
    
    project_id = sys.argv[1]
    asyncio.run(run_get_unused_feature_flags(project_id))

