#!/usr/bin/env python
"""
Script para probar la conexión a la base de datos local.
"""

import os
import sys
from pathlib import Path

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
import psycopg2

load_dotenv()


def test_connection():
    """Prueba la conexión a PostgreSQL."""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print("❌ DATABASE_URL not found in environment")
        print("   Please copy config.env.example to .env and configure it")
        return False
    
    print(f"🔗 Testing connection to: {database_url}")
    
    try:
        # Conectar
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT version()")
        version = cursor.fetchone()[0]
        print(f"✅ Connected successfully!")
        print(f"   PostgreSQL version: {version[:50]}...")
        
        # Verificar tablas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        print(f"\n📊 Tables found:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
            count = cursor.fetchone()[0]
            print(f"   - {table[0]}: {count} rows")
        
        # Test proyectos
        cursor.execute("SELECT * FROM projects")
        projects = cursor.fetchall()
        
        if projects:
            print(f"\n📂 Projects configured:")
            for project in projects:
                print(f"   - {project[1]} ({project[0]})")
        else:
            print(f"\n📂 No projects configured yet")
            print(f"   Run: python scripts/sync_projects.py --project test-project")
        
        cursor.close()
        conn.close()
        
        print(f"\n✅ Database test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"\n💡 Troubleshooting:")
        print(f"   1. Make sure Docker is running")
        print(f"   2. Run: ./scripts/setup_local_db.sh")
        print(f"   3. Check DATABASE_URL in .env file")
        return False


if __name__ == "__main__":
    test_connection()

