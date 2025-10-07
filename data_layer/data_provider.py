"""
Data provider for secure data access within job execution
"""
import os
import json
import pandas as pd
import sqlite3
import numpy as np
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DataProvider:
    """Provides secure access to data within job execution context"""
    
    def __init__(self, data_root: str = "/data", catalog_metadata: Optional[Dict[str, Any]] = None):
        self.data_root = Path(data_root)
        self.catalog_metadata = catalog_metadata or {}
        self.access_log = []
    
    def load_data(
        self,
        catalog_id: int,
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> Union[pd.DataFrame, Dict[str, Any], List[Any]]:
        """Load data from a catalog with optional filtering"""
        
        # Log data access
        self.access_log.append({
            "catalog_id": catalog_id,
            "filters": filters,
            "columns": columns,
            "limit": limit,
            "timestamp": pd.Timestamp.now().isoformat()
        })
        
        # Get catalog metadata
        catalog_info = self._get_catalog_info(catalog_id)
        if not catalog_info:
            raise ValueError(f"Catalog {catalog_id} not found")
        
        data_source = catalog_info.get("data_source")
        data_type = catalog_info.get("data_type")
        
        if not data_source:
            raise ValueError(f"No data source specified for catalog {catalog_id}")
        
        # Load data based on type
        if data_type == "csv":
            return self._load_csv(data_source, filters, columns, limit)
        elif data_type == "json":
            return self._load_json(data_source, filters, columns, limit)
        elif data_type == "sqlite":
            return self._load_sqlite(data_source, filters, columns, limit)
        elif data_type == "parquet":
            return self._load_parquet(data_source, filters, columns, limit)
        else:
            raise ValueError(f"Unsupported data type: {data_type}")
    
    def get_catalog_info(self, catalog_id: int) -> Optional[Dict[str, Any]]:
        """Get catalog information"""
        return self._get_catalog_info(catalog_id)
    
    def get_schema(self, catalog_id: int) -> Optional[Dict[str, Any]]:
        """Get schema definition for a catalog"""
        catalog_info = self._get_catalog_info(catalog_id)
        if catalog_info:
            return catalog_info.get("schema_definition")
        return None
    
    def _get_catalog_info(self, catalog_id: int) -> Optional[Dict[str, Any]]:
        """Get catalog information from metadata"""
        # Try to load from metadata file
        metadata_file = self.data_root / "metadata" / f"catalog_{catalog_id}.json"
        if metadata_file.exists():
            with open(metadata_file, 'r') as f:
                return json.load(f)
        
        # Fallback to passed metadata
        return self.catalog_metadata.get(str(catalog_id))
    
    def _load_csv(
        self,
        data_source: str,
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Load CSV data"""
        file_path = self.data_root / data_source if not os.path.isabs(data_source) else Path(data_source)
        
        # Load with optional column selection
        usecols = columns if columns else None
        nrows = limit if limit else None
        
        df = pd.read_csv(file_path, usecols=usecols, nrows=nrows)
        
        # Apply filters
        if filters:
            df = self._apply_filters(df, filters)
        
        return df
    
    def _load_json(
        self,
        data_source: str,
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> Union[Dict[str, Any], List[Any]]:
        """Load JSON data"""
        file_path = self.data_root / data_source if not os.path.isabs(data_source) else Path(data_source)
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Convert to DataFrame if it's a list of objects for easier filtering
        if isinstance(data, list) and data and isinstance(data[0], dict):
            df = pd.DataFrame(data)
            
            # Apply column selection
            if columns:
                available_cols = [col for col in columns if col in df.columns]
                df = df[available_cols]
            
            # Apply filters
            if filters:
                df = self._apply_filters(df, filters)
            
            # Apply limit
            if limit:
                df = df.head(limit)
            
            return df.to_dict('records')
        
        return data
    
    def _load_sqlite(
        self,
        data_source: str,
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Load SQLite data"""
        file_path = self.data_root / data_source if not os.path.isabs(data_source) else Path(data_source)
        
        conn = sqlite3.connect(file_path)
        try:
            # Get table names
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            if not tables:
                raise ValueError("No tables found in database")
            
            # Use first table by default (could be made configurable)
            table_name = tables[0]
            
            # Build query
            select_clause = ", ".join(columns) if columns else "*"
            query = f"SELECT {select_clause} FROM {table_name}"
            
            # Add WHERE clause for filters
            if filters:
                where_conditions = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        where_conditions.append(f"{key} = '{value}'")
                    else:
                        where_conditions.append(f"{key} = {value}")
                
                if where_conditions:
                    query += " WHERE " + " AND ".join(where_conditions)
            
            # Add LIMIT
            if limit:
                query += f" LIMIT {limit}"
            
            return pd.read_sql_query(query, conn)
            
        finally:
            conn.close()
    
    def _load_parquet(
        self,
        data_source: str,
        filters: Optional[Dict[str, Any]] = None,
        columns: Optional[List[str]] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """Load Parquet data"""
        file_path = self.data_root / data_source if not os.path.isabs(data_source) else Path(data_source)
        
        # Load with optional column selection
        df = pd.read_parquet(file_path, columns=columns)
        
        # Apply filters
        if filters:
            df = self._apply_filters(df, filters)
        
        # Apply limit
        if limit:
            df = df.head(limit)
        
        return df
    
    def _apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """Apply filters to DataFrame"""
        for column, value in filters.items():
            if column not in df.columns:
                logger.warning(f"Filter column '{column}' not found in data")
                continue
            
            if isinstance(value, dict):
                # Handle range filters, etc.
                if "min" in value:
                    df = df[df[column] >= value["min"]]
                if "max" in value:
                    df = df[df[column] <= value["max"]]
                if "in" in value:
                    df = df[df[column].isin(value["in"])]
                if "not_in" in value:
                    df = df[~df[column].isin(value["not_in"])]
            elif isinstance(value, list):
                # Filter by list of values
                df = df[df[column].isin(value)]
            else:
                # Exact match
                df = df[df[column] == value]
        
        return df
    
    def get_summary_statistics(self, catalog_id: int, columns: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get summary statistics for a catalog"""
        try:
            data = self.load_data(catalog_id, columns=columns)
            
            if isinstance(data, pd.DataFrame):
                numeric_cols = data.select_dtypes(include=[np.number]).columns
                categorical_cols = data.select_dtypes(include=['object', 'category']).columns
                
                stats = {
                    "total_records": len(data),
                    "columns": len(data.columns),
                    "numeric_columns": len(numeric_cols),
                    "categorical_columns": len(categorical_cols),
                    "memory_usage_mb": data.memory_usage(deep=True).sum() / (1024 * 1024)
                }
                
                # Numeric statistics
                if len(numeric_cols) > 0:
                    stats["numeric_stats"] = data[numeric_cols].describe().to_dict()
                
                # Categorical statistics
                if len(categorical_cols) > 0:
                    cat_stats = {}
                    for col in categorical_cols:
                        cat_stats[col] = {
                            "unique_values": data[col].nunique(),
                            "most_common": data[col].value_counts().head().to_dict()
                        }
                    stats["categorical_stats"] = cat_stats
                
                return stats
            
            else:
                return {
                    "total_records": len(data) if isinstance(data, list) else 1,
                    "data_type": type(data).__name__
                }
                
        except Exception as e:
            logger.error(f"Error getting summary statistics: {e}")
            return {"error": str(e)}
    
    def validate_access(self, catalog_id: int, requested_columns: List[str]) -> Dict[str, Any]:
        """Validate data access request"""
        catalog_info = self._get_catalog_info(catalog_id)
        if not catalog_info:
            return {"valid": False, "error": "Catalog not found"}
        
        # Check access level
        access_level = catalog_info.get("access_level", "private")
        if access_level == "private":
            return {"valid": False, "error": "Access denied: private catalog"}
        
        # Check column access
        schema = catalog_info.get("schema_definition", {})
        available_columns = []
        
        if schema.get("type") == "tabular" and "columns" in schema:
            available_columns = [col["name"] for col in schema["columns"]]
        
        invalid_columns = [col for col in requested_columns if col not in available_columns]
        if invalid_columns:
            return {
                "valid": False,
                "error": f"Invalid columns: {invalid_columns}",
                "available_columns": available_columns
            }
        
        return {"valid": True}
    
    def get_access_log(self) -> List[Dict[str, Any]]:
        """Get access log for this session"""
        return self.access_log.copy()