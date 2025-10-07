"""
Data catalog management for discovering and managing data sources
"""
import os
import json
import pandas as pd
import sqlite3
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging
from sqlalchemy.orm import Session

from distributed_node.models import DataCatalog
from distributed_node.database import SessionLocal

logger = logging.getLogger(__name__)


class DataCatalogManager:
    """Manages data catalogs and metadata"""
    
    def __init__(self, data_root: str = "./data"):
        self.data_root = Path(data_root)
        self.data_root.mkdir(exist_ok=True)
        
        # Create subdirectories
        (self.data_root / "catalogs").mkdir(exist_ok=True)
        (self.data_root / "metadata").mkdir(exist_ok=True)
        (self.data_root / "schemas").mkdir(exist_ok=True)
    
    def create_catalog(
        self,
        name: str,
        description: str,
        data_type: str,
        data_source: Union[str, Path, Dict[str, Any]],
        access_level: str = "private",
        schema_definition: Optional[Dict[str, Any]] = None
    ) -> int:
        """Create a new data catalog"""
        
        # Auto-detect schema if not provided
        if schema_definition is None:
            schema_definition = self._infer_schema(data_source, data_type)
        
        # Count records
        total_records = self._count_records(data_source, data_type)
        
        # Create database entry
        db = SessionLocal()
        try:
            catalog = DataCatalog(
                name=name,
                description=description,
                data_type=data_type,
                schema_definition=schema_definition,
                access_level=access_level,
                total_records=total_records
            )
            
            db.add(catalog)
            db.commit()
            db.refresh(catalog)
            
            # Save catalog metadata to file
            self._save_catalog_metadata(catalog.id, {
                "name": name,
                "description": description,
                "data_type": data_type,
                "data_source": str(data_source),
                "access_level": access_level,
                "schema_definition": schema_definition,
                "total_records": total_records
            })
            
            logger.info(f"Created data catalog '{name}' with ID {catalog.id}")
            return catalog.id
            
        finally:
            db.close()
    
    def get_catalog(self, catalog_id: int) -> Optional[DataCatalog]:
        """Get catalog by ID"""
        db = SessionLocal()
        try:
            return db.query(DataCatalog).filter(DataCatalog.id == catalog_id).first()
        finally:
            db.close()
    
    def list_catalogs(self, access_level: Optional[str] = None) -> List[DataCatalog]:
        """List all catalogs, optionally filtered by access level"""
        db = SessionLocal()
        try:
            query = db.query(DataCatalog)
            if access_level:
                query = query.filter(DataCatalog.access_level == access_level)
            return query.all()
        finally:
            db.close()
    
    def update_catalog(self, catalog_id: int, **updates) -> bool:
        """Update catalog metadata"""
        db = SessionLocal()
        try:
            catalog = db.query(DataCatalog).filter(DataCatalog.id == catalog_id).first()
            if not catalog:
                return False
            
            for key, value in updates.items():
                if hasattr(catalog, key):
                    setattr(catalog, key, value)
            
            db.commit()
            return True
        finally:
            db.close()
    
    def delete_catalog(self, catalog_id: int) -> bool:
        """Delete a catalog"""
        db = SessionLocal()
        try:
            catalog = db.query(DataCatalog).filter(DataCatalog.id == catalog_id).first()
            if not catalog:
                return False
            
            db.delete(catalog)
            db.commit()
            
            # Remove metadata file
            metadata_file = self.data_root / "metadata" / f"catalog_{catalog_id}.json"
            if metadata_file.exists():
                metadata_file.unlink()
            
            return True
        finally:
            db.close()
    
    def _infer_schema(self, data_source: Union[str, Path, Dict], data_type: str) -> Dict[str, Any]:
        """Infer schema from data source"""
        try:
            if data_type == "csv":
                if isinstance(data_source, (str, Path)):
                    df = pd.read_csv(data_source, nrows=100)  # Sample for schema
                    return self._pandas_to_schema(df)
            
            elif data_type == "json":
                if isinstance(data_source, (str, Path)):
                    with open(data_source, 'r') as f:
                        sample_data = json.load(f)
                    return self._json_to_schema(sample_data)
            
            elif data_type == "sqlite":
                if isinstance(data_source, (str, Path)):
                    return self._sqlite_to_schema(data_source)
            
            elif data_type == "parquet":
                if isinstance(data_source, (str, Path)):
                    df = pd.read_parquet(data_source)
                    return self._pandas_to_schema(df)
            
            # Default schema
            return {"type": "unknown", "columns": []}
            
        except Exception as e:
            logger.warning(f"Could not infer schema: {e}")
            return {"type": "unknown", "columns": [], "error": str(e)}
    
    def _pandas_to_schema(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Convert pandas DataFrame to schema definition"""
        columns = []
        for col in df.columns:
            dtype = str(df[col].dtype)
            
            # Map pandas dtypes to standard types
            if dtype.startswith('int'):
                col_type = "integer"
            elif dtype.startswith('float'):
                col_type = "float"
            elif dtype.startswith('bool'):
                col_type = "boolean"
            elif dtype.startswith('datetime'):
                col_type = "datetime"
            else:
                col_type = "string"
            
            columns.append({
                "name": col,
                "type": col_type,
                "nullable": df[col].isnull().any(),
                "unique_values": df[col].nunique() if col_type in ["string", "integer"] else None
            })
        
        return {
            "type": "tabular",
            "columns": columns,
            "row_count": len(df),
            "memory_usage": df.memory_usage(deep=True).sum()
        }
    
    def _json_to_schema(self, data: Any) -> Dict[str, Any]:
        """Convert JSON data to schema definition"""
        if isinstance(data, dict):
            fields = []
            for key, value in data.items():
                fields.append({
                    "name": key,
                    "type": type(value).__name__,
                    "nested": isinstance(value, (dict, list))
                })
            return {"type": "object", "fields": fields}
        
        elif isinstance(data, list) and data:
            sample = data[0]
            return {
                "type": "array",
                "item_type": type(sample).__name__,
                "length": len(data),
                "sample_item": self._json_to_schema(sample) if isinstance(sample, (dict, list)) else None
            }
        
        return {"type": "unknown"}
    
    def _sqlite_to_schema(self, db_path: Union[str, Path]) -> Dict[str, Any]:
        """Get schema from SQLite database"""
        conn = sqlite3.connect(db_path)
        try:
            cursor = conn.cursor()
            
            # Get table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            schema = {"type": "database", "tables": []}
            
            for table in tables:
                # Get column info
                cursor.execute(f"PRAGMA table_info({table});")
                columns = []
                for col_info in cursor.fetchall():
                    columns.append({
                        "name": col_info[1],
                        "type": col_info[2],
                        "nullable": not col_info[3],
                        "primary_key": bool(col_info[5])
                    })
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table};")
                row_count = cursor.fetchone()[0]
                
                schema["tables"].append({
                    "name": table,
                    "columns": columns,
                    "row_count": row_count
                })
            
            return schema
            
        finally:
            conn.close()
    
    def _count_records(self, data_source: Union[str, Path, Dict], data_type: str) -> int:
        """Count records in data source"""
        try:
            if data_type == "csv":
                if isinstance(data_source, (str, Path)):
                    # Fast line count for CSV
                    with open(data_source, 'r') as f:
                        return sum(1 for _ in f) - 1  # Subtract header
            
            elif data_type == "json":
                if isinstance(data_source, (str, Path)):
                    with open(data_source, 'r') as f:
                        data = json.load(f)
                    return len(data) if isinstance(data, list) else 1
            
            elif data_type == "sqlite":
                if isinstance(data_source, (str, Path)):
                    conn = sqlite3.connect(data_source)
                    try:
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                        tables = [row[0] for row in cursor.fetchall()]
                        
                        total = 0
                        for table in tables:
                            cursor.execute(f"SELECT COUNT(*) FROM {table};")
                            total += cursor.fetchone()[0]
                        return total
                    finally:
                        conn.close()
            
            elif data_type == "parquet":
                if isinstance(data_source, (str, Path)):
                    df = pd.read_parquet(data_source)
                    return len(df)
            
            return 0
            
        except Exception as e:
            logger.warning(f"Could not count records: {e}")
            return 0
    
    def _save_catalog_metadata(self, catalog_id: int, metadata: Dict[str, Any]):
        """Save catalog metadata to file"""
        metadata_file = self.data_root / "metadata" / f"catalog_{catalog_id}.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2, default=str)
    
    def load_catalog_metadata(self, catalog_id: int) -> Optional[Dict[str, Any]]:
        """Load catalog metadata from file"""
        metadata_file = self.data_root / "metadata" / f"catalog_{catalog_id}.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        return None
    
    def register_existing_data(self, data_path: str, name: str, description: str = "") -> int:
        """Register existing data files as a catalog"""
        data_path = Path(data_path)
        
        if not data_path.exists():
            raise FileNotFoundError(f"Data path does not exist: {data_path}")
        
        # Determine data type from file extension
        if data_path.is_file():
            suffix = data_path.suffix.lower()
            if suffix == '.csv':
                data_type = 'csv'
            elif suffix == '.json':
                data_type = 'json'
            elif suffix == '.db' or suffix == '.sqlite':
                data_type = 'sqlite'
            elif suffix == '.parquet':
                data_type = 'parquet'
            else:
                data_type = 'file'
        else:
            data_type = 'directory'
        
        return self.create_catalog(
            name=name,
            description=description,
            data_type=data_type,
            data_source=str(data_path),
            access_level="private"
        )