#!/bin/bash
cd /Users/brandonalonsosalinasrangel/Documents/GitHub/frontend-geo-mcp
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/frontend_mcp"
export PYTHONPATH="/Users/brandonalonsosalinasrangel/Documents/GitHub/frontend-geo-mcp"
uv run --with fastmcp --with sqlalchemy --with alembic --with supabase --with postgrest --with gitpython --with aiofiles --with httpx --with python-dotenv --with pydantic --with typing-extensions --with psycopg2-binary fastmcp run src/server.py


