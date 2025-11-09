"""
Modelos Pydantic y SQLAlchemy para Frontend GPS.
Combina validación de datos con ORM.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey, Index, func, Boolean
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
    component_imports: Optional[List[Dict[str, Any]]] = Field(default_factory=list)


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
# HOOK MODELS (Custom Hooks)
# ============================================

class HookBase(BaseModel):
    """Modelo base para custom hooks."""
    name: str
    file_path: str
    hook_type: str = "custom"
    description: Optional[str] = None
    return_type: Optional[str] = None
    parameters: List[Dict[str, Any]] = Field(default_factory=list)
    imports: List[str] = Field(default_factory=list)
    exports: List[str] = Field(default_factory=list)
    native_hooks_used: List[str] = Field(default_factory=list)
    custom_hooks_used: List[str] = Field(default_factory=list)
    jsdoc: Optional[Dict[str, Any]] = None


class HookCreate(HookBase):
    """Modelo para crear hooks."""
    project_id: str


class HookUpdate(BaseModel):
    """Modelo para actualizar hooks."""
    description: Optional[str] = None
    return_type: Optional[str] = None
    parameters: Optional[List[Dict[str, Any]]] = None
    imports: Optional[List[str]] = None
    exports: Optional[List[str]] = None
    native_hooks_used: Optional[List[str]] = None
    custom_hooks_used: Optional[List[str]] = None
    jsdoc: Optional[Dict[str, Any]] = None


class HookResponse(HookBase):
    """Modelo de respuesta para hooks."""
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
    created_at = Column(DateTime, default=func.now())

    # Relaciones
    components = relationship("Component", back_populates="project", cascade="all, delete-orphan")
    hooks = relationship("Hook", back_populates="project", cascade="all, delete-orphan")

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
    # native_hooks_used: JSON array de nombres de hooks nativos de React
    # Ej: ["useState", "useEffect", "useContext"]
    native_hooks_used = Column(JSON, default=[])
    # custom_hooks_used: JSON array de nombres de custom hooks indexados en la tabla hooks
    # Solo contiene hooks que realmente existen en la tabla hooks de este proyecto
    # Se valida al guardar componentes (ver save_components en database_client.py)
    # Ej: ["useUserData", "useAuth", "useLocalStorage"]
    custom_hooks_used = Column(JSON, default=[])
    imports = Column(JSON, default=[])
    exports = Column(JSON, default=[])
    component_type = Column(String)
    description = Column(String)
    jsdoc = Column(JSON, nullable=True)
    # component_imports: JSON array con información estructurada de imports
    # Ej: [{"imported_names": ["Button", "Card"], "from_path": "./components", "import_type": "named"}]
    component_imports = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    project = relationship("Project", back_populates="components")
    dependencies = relationship("ComponentDependency", foreign_keys="ComponentDependency.component_id", back_populates="component")
    dependents = relationship("ComponentDependency", foreign_keys="ComponentDependency.depends_on_component_id", back_populates="depends_on_component")

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
            'native_hooks_used': self.native_hooks_used or [],
            'custom_hooks_used': self.custom_hooks_used or [],
            'imports': self.imports or [],
            'exports': self.exports or [],
            'component_type': self.component_type,
            'description': self.description,
            'jsdoc': self.jsdoc,
            'component_imports': self.component_imports or [],
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


class Hook(Base):
    """Modelo SQLAlchemy para custom hooks."""
    __tablename__ = "hooks"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    file_path = Column(String, nullable=False)
    hook_type = Column(String, default="custom")
    description = Column(String, nullable=True)
    return_type = Column(String, nullable=True)
    parameters = Column(JSON, default=[])
    imports = Column(JSON, default=[])
    exports = Column(JSON, default=[])
    native_hooks_used = Column(JSON, default=[])
    custom_hooks_used = Column(JSON, default=[])
    jsdoc = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relación
    project = relationship("Project", back_populates="hooks")

    # Índices para búsqueda rápida
    __table_args__ = (
        Index('idx_hooks_name', 'name'),
        Index('idx_hooks_project', 'project_id'),
        Index('idx_hooks_unique', 'name', 'project_id', 'file_path', unique=True),
    )

    def to_dict(self):
        """Convierte a diccionario."""
        return {
            'id': self.id,
            'name': self.name,
            'project_id': self.project_id,
            'file_path': self.file_path,
            'hook_type': self.hook_type,
            'description': self.description,
            'return_type': self.return_type,
            'parameters': self.parameters or [],
            'imports': self.imports or [],
            'exports': self.exports or [],
            'native_hooks_used': self.native_hooks_used or [],
            'jsdoc': self.jsdoc,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


class ComponentDependency(Base):
    """Modelo SQLAlchemy para dependencias entre componentes."""
    __tablename__ = "component_dependencies"

    id = Column(Integer, primary_key=True)
    component_id = Column(Integer, ForeignKey("components.id", ondelete="CASCADE"), nullable=False)
    depends_on_component_id = Column(Integer, ForeignKey("components.id", ondelete="CASCADE"), nullable=True)
    depends_on_name = Column(String, nullable=False)
    from_path = Column(String, nullable=False)
    import_type = Column(String, nullable=False)  # 'named', 'default', 'mixed', 'namespace'
    is_external = Column(Boolean, default=False)
    project_id = Column(String, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=func.now())

    # Relaciones
    component = relationship("Component", foreign_keys=[component_id], back_populates="dependencies")
    depends_on_component = relationship("Component", foreign_keys=[depends_on_component_id], back_populates="dependents")
    project = relationship("Project")

    # Índices para búsqueda rápida
    __table_args__ = (
        Index('idx_dependency_component', 'component_id'),
        Index('idx_dependency_depends_on', 'depends_on_component_id'),
        Index('idx_dependency_project', 'project_id'),
        Index('idx_dependency_unique', 'component_id', 'depends_on_component_id', 'depends_on_name', unique=True),
    )

    def to_dict(self):
        """Convierte a diccionario."""
        return {
            'id': self.id,
            'component_id': self.component_id,
            'depends_on_component_id': self.depends_on_component_id,
            'depends_on_name': self.depends_on_name,
            'from_path': self.from_path,
            'import_type': self.import_type,
            'is_external': self.is_external,
            'project_id': self.project_id,
            'created_at': self.created_at,
        }
