"""
Data models for the client SDK
"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime


class DataCatalog(BaseModel):
    """Data catalog information"""
    id: int
    name: str
    description: Optional[str]
    data_type: str
    schema_definition: Optional[Dict[str, Any]]
    access_level: str
    total_records: int
    last_updated: datetime


class NodeInfo(BaseModel):
    """Node discovery information"""
    nodes: List[Dict[str, Any]]
    data_catalogs: List[DataCatalog]


class JobSubmission(BaseModel):
    """Job submission request"""
    target_node_id: str
    data_catalog_name: str
    script_type: str  # python, r, sql, jupyter
    script_content: str
    parameters: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None


class JobResult(BaseModel):
    """Job execution result"""
    id: int
    job_id: str
    script_type: str
    status: str  # queued, running, completed, failed, cancelled, blocked
    progress: float
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_time: Optional[float]
    memory_used_mb: Optional[float]
    records_processed: Optional[int]
    submitted_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
