"""
Modelos Pydantic y SQLAlchemy para Frontend GPS.
Combina validación de datos con ORM.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Index, func
from sqlalchemy.orm import declarative_base, relationship

# Base para modelos SQLAlchemy
Base = declarative_base()


# ============================================
# PYDANTIC MODELS (Validación de datos)
# ============================================

class ProjectBase(BaseModel):
    """Modelo base para proyectos."""
    name: str
    repository_url: str
    branch: str = "main"
    type: str = "application"


class ProjectCreate(ProjectBase):
    """Modelo para crear proyectos."""
    pass


class ProjectUpdate(BaseModel):
    """Modelo para actualizar proyectos."""
    name: Optional[str] = None
    branch: Optional[str] = None
    type: Optional[str] = None


class ProjectResponse(ProjectBase):
    """Modelo de respuesta para proyectos."""
    id: str
    last_sync: Optional[datetime] = None
    created_at: datetime
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class ComponentBase(BaseModel):
    """Modelo base para componentes."""
    name: str
    file_path: str
    props: List[str] = Field(default_factory=list)
    hooks: List[str] = Field(default_factory=list)
    imports: List[str] = Field(default_factory=list)
    exports: List[str] = Field(default_factory=list)
    component_type: Optional[str] = None
    description: Optional[str] = None
    jsdoc: Optional[Dict[str, Any]] = None


class ComponentCreate(ComponentBase):
    """Modelo para crear componentes."""
    project_id: str


class ComponentUpdate(BaseModel):
    """Modelo para actualizar componentes."""
    props: Optional[List[str]] = None
    hooks: Optional[List[str]] = None
    imports: Optional[List[str]] = None
    exports: Optional[List[str]] = None
    component_type: Optional[str] = None
    description: Optional[str] = None
    jsdoc: Optional[Dict[str, Any]] = None


class ComponentResponse(ComponentBase):
    """Modelo de respuesta para componentes."""
    id: int
    project_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# SQLALCHEMY MODELS (Base de datos)
# ============================================

class Project(Base):
    """Modelo SQLAlchemy para proyectos."""
    __tablename__ = "projects"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    repository_url = Column(String, nullable=False)
    branch = Column(String, default="main")
    type = Column(String, default="application")
    is_active = Column(String, default="true")
    last_sync = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relación
    components = relationship("Component", back_populates="project", cascade="all, delete-orphan")

    def to_dict(self):
        """Convierte a diccionario."""
        return {
            'id': self.id,
            'name': self.name,
            'repository_url': self.repository_url,
            'branch': self.branch,
            'type': self.type,
            'is_active': self.is_active == "true",
            'last_sync': self.last_sync,
            'created_at': self.created_at,
        }


class Component(Base):
    """Modelo SQLAlchemy para componentes."""
    __tablename__ = "components"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)
    props = Column(JSON, default=[])
    hooks = Column(JSON, default=[])
    imports = Column(JSON, default=[])
    exports = Column(JSON, default=[])
    component_type = Column(String)
    description = Column(String)
    jsdoc = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relación
    project = relationship("Project", back_populates="components")

    # Índices para búsqueda rápida
    __table_args__ = (
        Index('idx_components_name', 'name'),
        Index('idx_components_project', 'project_id'),
        Index('idx_components_unique', 'name', 'project_id', 'file_path', unique=True),
    )

    def to_dict(self):
        """Convierte a diccionario."""
        return {
            'id': self.id,
            'name': self.name,
            'project_id': self.project_id,
            'file_path': self.file_path,
            'props': self.props or [],
            'hooks': self.hooks or [],
            'imports': self.imports or [],
            'exports': self.exports or [],
            'component_type': self.component_type,
            'description': self.description,
            'jsdoc': self.jsdoc,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }
