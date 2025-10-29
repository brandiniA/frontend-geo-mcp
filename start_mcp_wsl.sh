#!/bin/bash
cd /home/basr/personal/frontend-geo-mcp
export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/frontend_mcp"
export PYTHONPATH="/home/basr/personal/frontend-geo-mcp"
uv run fastmcp run src/server.py
