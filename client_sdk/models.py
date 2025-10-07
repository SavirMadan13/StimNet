"""
Client SDK data models
"""
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class ScriptType(str, Enum):
    PYTHON = "python"
    R = "r"
    SQL = "sql"
    JUPYTER = "jupyter"


class NodeInfo(BaseModel):
    """Information about a distributed node"""
    id: int
    node_id: str
    name: str
    institution: str
    endpoint_url: str
    is_active: bool
    last_seen: datetime


class DataCatalog(BaseModel):
    """Information about a data catalog"""
    id: int
    name: str
    description: Optional[str]
    data_type: str
    schema_definition: Optional[Dict[str, Any]]
    access_level: str
    total_records: int
    last_updated: datetime


class JobResult(BaseModel):
    """Job execution result"""
    id: int
    job_id: str
    script_type: str
    status: JobStatus
    progress: float
    result_data: Optional[Dict[str, Any]]
    error_message: Optional[str]
    execution_time: Optional[float]
    memory_used_mb: Optional[float]
    records_processed: Optional[int]
    submitted_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class JobSubmissionRequest(BaseModel):
    """Request to submit a job"""
    target_node_id: str
    data_catalog_name: str
    script_type: ScriptType
    script_content: str
    parameters: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None


class NodeDiscovery(BaseModel):
    """Node discovery response"""
    nodes: List[NodeInfo]
    data_catalogs: List[DataCatalog]


class HealthStatus(BaseModel):
    """Node health status"""
    status: str
    node_id: str
    version: str
    uptime: float
    active_jobs: int
    total_jobs: int