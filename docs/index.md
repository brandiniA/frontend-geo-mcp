# Frontend GPS - Documentation Index

Complete documentation for Frontend GPS MCP Server.

## 📚 Main Documentation

- **[SETUP.md](./SETUP.md)** - Complete setup and installation guide
- **[DATABASE.md](./database/DATABASE.md)** - Database schema and exploration
- **[TOOLS.md](./tools/TOOLS.md)** - MCP Tools reference and usage
- **[ARCHITECTURE.md](./architecture/ARCHITECTURE.md)** - System architecture and design decisions

## 🚀 Quick Links

### Getting Started
1. [Installation](./SETUP.md#🚀-quick-start)
2. [Configuration](./SETUP.md#3-configure-environment)
3. [First Run](./SETUP.md#6-run-mcp-server)

### Database
1. [Schema Overview](./database/DATABASE.md#📋-schema-overview)
2. [Exploration Tools](./database/DATABASE.md#🔍-exploring-the-database)
3. [SQL Queries](./database/DATABASE.md#📝-useful-sql-queries)

### Tools
1. [Navigator Tools](./tools/TOOLS.md#🔍-navigator-tools)
2. [Sync Tools](./tools/TOOLS.md#🔄-sync-tools)
3. [Statistics Tools](./tools/TOOLS.md#📊-statistics-tools)

### Architecture
1. [System Design](./architecture/ARCHITECTURE.md#🏗️-system-architecture)
2. [Components](./architecture/ARCHITECTURE.md#🧩-core-components)
3. [Data Flow](./architecture/ARCHITECTURE.md#🔄-data-flow)

## 📖 Additional Resources

- [README.md](../README.md) - Project overview
- [Custom Commands](./COMANDOS_PERSONALIZADOS.md) - Helper commands
- [MCP Frontend Design](./MCP_Frontend_Diseño_Arquitectura.md) - Original architecture document
- [FastMCP Reference](./MCP_Frontend_Python_FastMCP_Completo.md) - Complete FastMCP guide

## 🤔 Common Questions

**Q: How do I search for a component?**
A: Use the `find_component` tool in Cursor or see [Navigator Tools](./tools/TOOLS.md#find_component)

**Q: How do I add a new project to index?**
A: Edit `.mcp-config.json` and use `sync_project` tool. See [Sync Tools](./tools/TOOLS.md#sync_project)

**Q: How do I explore the database?**
A: Use Adminer at `http://localhost:8080`. See [Database Exploration](./database/DATABASE.md#🔍-exploring-the-database)

**Q: What is the database schema?**
A: See [Schema Overview](./database/DATABASE.md#📋-schema-overview)

## 🆘 Troubleshooting

- [Database Connection Issues](./database/DATABASE.md#❌-troubleshooting)
- [Tool Errors](./tools/TOOLS.md#❌-troubleshooting)
- [Setup Problems](./SETUP.md#❌-troubleshooting)

---

**Last Updated:** October 2025
**Version:** Frontend GPS MVP v0.1.0
