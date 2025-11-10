"""
Repositorio para operaciones de BarrelExport.
"""

import asyncio
from typing import List, Optional, Dict, Any

from src.models import BarrelExport
from .base_repository import BaseRepository
from .utils import (
    db_session,
    to_dict_list,
    model_to_dict,
    safe_upsert,
)


class BarrelExportRepository(BaseRepository):
    """Repositorio para operaciones de BarrelExport."""
    
    async def save_barrel_exports(self, exports: List[Dict[str, Any]], project_id: str) -> int:
        """
        Guarda barrel exports en la base de datos, eliminando los antiguos del proyecto.
        
        Args:
            exports: Lista de barrel exports a guardar
            project_id: ID del proyecto
            
        Returns:
            Número de barrel exports guardados
        """
        if not exports:
            return 0

        def _save():
            with db_session(self.SessionLocal) as session:
                try:
                    # Eliminar barrel exports antiguos del proyecto
                    session.query(BarrelExport).filter(
                        BarrelExport.project_id == project_id
                    ).delete(synchronize_session=False)
                    
                    saved_count = 0
                    
                    for export_data in exports:
                        export_dict = {
                            'directory_path': export_data.get('directory_path'),
                            'index_file_path': export_data.get('index_file_path'),
                            'exported_component_id': export_data.get('exported_component_id'),
                            'exported_name': export_data.get('exported_name'),
                            'source_file_path': export_data.get('source_file_path'),
                            'is_container': export_data.get('is_container', False),
                            'notes': export_data.get('notes'),
                        }
                        
                        # Usar safe_upsert para insertar o actualizar
                        safe_upsert(
                            session=session,
                            model_class=BarrelExport,
                            unique_fields={
                                'project_id': project_id,
                                'directory_path': export_data['directory_path'],
                            },
                            data=export_dict,
                            update_timestamp=True
                        )
                        
                        saved_count += 1
                    
                    session.commit()
                    print(f"✅ Saved {saved_count} barrel exports to database")
                    return saved_count
                
                except Exception as e:
                    session.rollback()
                    print(f"❌ Error saving barrel exports: {e}")
                    raise
        
        return await asyncio.to_thread(_save)
    
    async def get_by_directory(self, directory_path: str, project_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca un barrel export por directory_path.
        
        Args:
            directory_path: Ruta del directorio (normalizada)
            project_id: ID del proyecto
            
        Returns:
            Dict con datos del barrel export o None
        """
        def _get():
            with db_session(self.SessionLocal) as session:
                barrel = session.query(BarrelExport).filter(
                    BarrelExport.project_id == project_id,
                    BarrelExport.directory_path == directory_path
                ).first()
                
                if barrel:
                    return model_to_dict(barrel)
                return None
        
        return await asyncio.to_thread(_get)
    
    async def get_all_by_project(self, project_id: str) -> List[Dict[str, Any]]:
        """
        Obtiene todos los barrel exports de un proyecto.
        
        Args:
            project_id: ID del proyecto
            
        Returns:
            Lista de barrel exports
        """
        def _get_all():
            with db_session(self.SessionLocal) as session:
                barrels = session.query(BarrelExport).filter(
                    BarrelExport.project_id == project_id
                ).all()
                
                return to_dict_list(barrels)
        
        return await asyncio.to_thread(_get_all)
    
    async def get_by_component_id(self, component_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene todos los barrel exports que apuntan a un componente específico.
        
        Args:
            component_id: ID del componente
            
        Returns:
            Lista de barrel exports
        """
        def _get():
            with db_session(self.SessionLocal) as session:
                barrels = session.query(BarrelExport).filter(
                    BarrelExport.exported_component_id == component_id
                ).all()
                
                return to_dict_list(barrels)
        
        return await asyncio.to_thread(_get)
    
    async def count_by_project(self, project_id: str) -> int:
        """
        Cuenta los barrel exports de un proyecto.
        
        Args:
            project_id: ID del proyecto
            
        Returns:
            Número total de barrel exports
        """
        def _count():
            with db_session(self.SessionLocal) as session:
                return session.query(BarrelExport).filter(
                    BarrelExport.project_id == project_id
                ).count()
        
        return await asyncio.to_thread(_count)
    
    async def count_with_component(self, project_id: str) -> int:
        """
        Cuenta los barrel exports que tienen un componente asociado.
        
        Args:
            project_id: ID del proyecto
            
        Returns:
            Número de barrel exports con componente
        """
        def _count():
            with db_session(self.SessionLocal) as session:
                return session.query(BarrelExport).filter(
                    BarrelExport.project_id == project_id,
                    BarrelExport.exported_component_id.isnot(None)
                ).count()
        
        return await asyncio.to_thread(_count)
    
    async def delete_by_project(self, project_id: str) -> int:
        """
        Elimina todos los barrel exports de un proyecto.
        
        Args:
            project_id: ID del proyecto
            
        Returns:
            Número de barrel exports eliminados
        """
        def _delete():
            with db_session(self.SessionLocal) as session:
                try:
                    count = session.query(BarrelExport).filter(
                        BarrelExport.project_id == project_id
                    ).delete(synchronize_session=False)
                    
                    session.commit()
                    print(f"✅ Deleted {count} barrel exports from project {project_id}")
                    return count
                
                except Exception as e:
                    session.rollback()
                    print(f"❌ Error deleting barrel exports: {e}")
                    raise
        
        return await asyncio.to_thread(_delete)

