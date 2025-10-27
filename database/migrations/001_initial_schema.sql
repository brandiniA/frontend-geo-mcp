-- Frontend MCP Database Schema
-- Initial schema for projects and components

-- Tabla de proyectos
CREATE TABLE IF NOT EXISTS projects (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  repository_url TEXT NOT NULL,
  branch TEXT DEFAULT 'main',
  type TEXT CHECK (type IN ('application', 'library')),
  is_active BOOLEAN DEFAULT true,
  last_sync TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Tabla de componentes
CREATE TABLE IF NOT EXISTS components (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  project_id TEXT REFERENCES projects(id) ON DELETE CASCADE,
  file_path TEXT NOT NULL,
  props JSONB DEFAULT '[]',
  hooks JSONB DEFAULT '[]',
  imports JSONB DEFAULT '[]',
  exports JSONB DEFAULT '[]',
  component_type TEXT,
  description TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(name, project_id, file_path)
);

-- Índices para búsqueda rápida
CREATE INDEX IF NOT EXISTS idx_components_name ON components(name);
CREATE INDEX IF NOT EXISTS idx_components_project ON components(project_id);
CREATE INDEX IF NOT EXISTS idx_components_type ON components(component_type);

-- Índice de búsqueda full-text
CREATE INDEX IF NOT EXISTS idx_components_search ON components 
USING gin(to_tsvector('english', name || ' ' || COALESCE(description, '')));

-- Insertar proyecto de prueba (opcional)
INSERT INTO projects (id, name, repository_url, branch, type)
VALUES ('test-project', 'Test Project', 'https://github.com/facebook/react', 'main', 'library')
ON CONFLICT (id) DO NOTHING;

-- Comentarios para documentación
COMMENT ON TABLE projects IS 'Proyectos React/Next.js a indexar';
COMMENT ON TABLE components IS 'Componentes React indexados';
COMMENT ON COLUMN components.props IS 'Props del componente en formato JSON';
COMMENT ON COLUMN components.hooks IS 'Hooks utilizados en formato JSON';
COMMENT ON COLUMN components.imports IS 'Imports del archivo en formato JSON';
COMMENT ON COLUMN components.exports IS 'Exports del archivo en formato JSON';

