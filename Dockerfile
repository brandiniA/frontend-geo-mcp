# Frontend GPS MCP Server - Dockerfile
# Para deployment en Railway/Render

FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (git for cloning repos)
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Install UV (fast Python package manager)
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY .mcp-config.json ./

# Install Python dependencies
RUN uv pip install --system --no-cache -r pyproject.toml

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV TEMP_DIR=/tmp/mcp-repos

# Create temp directory
RUN mkdir -p /tmp/mcp-repos

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Run server in HTTP mode
CMD ["python", "src/server.py", "--http"]

