# Database Migrations

This directory contains database schema migrations for Frontend GPS.

## Structure

```
database/
├── migrations/
│   └── 001_initial_schema.sql    # Initial schema (projects & components tables)
└── README.md
```

## Migrations

### 001_initial_schema.sql

Creates the initial database schema:
- `projects` table: Stores project configurations
- `components` table: Stores indexed React components
- Indexes for fast searching

## Running Migrations

### Local Development (Docker)

Migrations run automatically when you execute:
```bash
./scripts/setup_local_db.sh
```

### Manual Execution

```bash
# Using docker
docker exec -i frontend-mcp-db psql -U postgres -d frontend_mcp < database/migrations/001_initial_schema.sql

# Using psql directly
psql -U postgres -d frontend_mcp < database/migrations/001_initial_schema.sql
```

### Production (Supabase, Railway, Render, etc.)

1. Connect to your production database
2. Copy the contents of the migration file
3. Execute the SQL in your database console

## Adding New Migrations

When adding new migrations:
1. Create a new file: `002_description.sql`
2. Use descriptive names
3. Include rollback instructions in comments
4. Test locally before deploying

## Database Providers Supported

This schema works with any PostgreSQL-compatible database:
- ✅ PostgreSQL (local or remote)
- ✅ Supabase
- ✅ Railway PostgreSQL
- ✅ Render PostgreSQL
- ✅ AWS RDS PostgreSQL
- ✅ Google Cloud SQL PostgreSQL
- ✅ Azure Database for PostgreSQL

