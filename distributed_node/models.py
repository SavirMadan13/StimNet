"""
Database models for the distributed node
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from enum import Enum

Base = declarative_base()


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RequestStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    EXPIRED = "expired"


class ScriptType(str, Enum):
    PYTHON = "python"
    R = "r"
    SQL = "sql"
    JUPYTER = "jupyter"
    CUSTOM = "custom"


# Database Models
class Node(Base):
    __tablename__ = "nodes"
    
    id = Column(Integer, primary_key=True, index=True)
    node_id = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    institution = Column(String(200), nullable=False)
    endpoint_url = Column(String(500), nullable=False)
    public_key = Column(Text)
    is_active = Column(Boolean, default=True)
    last_seen = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    jobs_submitted = relationship("Job", foreign_keys="Job.requester_node_id", back_populates="requester_node")
    jobs_executed = relationship("Job", foreign_keys="Job.executor_node_id", back_populates="executor_node")


class DataCatalog(Base):
    __tablename__ = "data_catalogs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    data_type = Column(String(100), nullable=False)
    schema_definition = Column(JSON)
    access_level = Column(String(50), default="private")  # public, restricted, private
    total_records = Column(Integer, default=0)
    last_updated = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    
    # Note: jobs relationship removed - now using manifest catalog IDs (strings) instead of database IDs


class Job(Base):
    __tablename__ = "jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String(100), unique=True, index=True, nullable=False)
    requester_node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    executor_node_id = Column(Integer, ForeignKey("nodes.id"), nullable=False)
    data_catalog_id = Column(String, nullable=False)  # Now stores manifest catalog ID (string)
    analysis_request_id = Column(Integer, ForeignKey("analysis_requests.id"), nullable=True)
    
    script_type = Column(String(50), nullable=False)
    script_content = Column(Text, nullable=False)
    script_hash = Column(String(100), nullable=False)
    
    parameters = Column(JSON)
    filters = Column(JSON)
    uploaded_file_ids = Column(JSON)  # List of uploaded file IDs to use
    
    status = Column(String(50), default=JobStatus.QUEUED)
    progress = Column(Float, default=0.0)
    
    # Results and metadata
    result_data = Column(JSON)
    error_message = Column(Text)
    execution_time = Column(Float)
    memory_used_mb = Column(Float)
    records_processed = Column(Integer)
    
    # Timestamps
    submitted_at = Column(DateTime, default=func.now())
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Relationships
    requester_node = relationship("Node", foreign_keys=[requester_node_id], back_populates="jobs_submitted")
    executor_node = relationship("Node", foreign_keys=[executor_node_id], back_populates="jobs_executed")
    analysis_request = relationship("AnalysisRequest", back_populates="jobs")
    # Note: data_catalog relationship removed - now using manifest catalog IDs (strings) instead of database IDs
    audit_logs = relationship("AuditLog", back_populates="job")


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("jobs.id"))
    node_id = Column(Integer, ForeignKey("nodes.id"))
    action = Column(String(100), nullable=False)
    details = Column(JSON)
    user_info = Column(JSON)
    ip_address = Column(String(45))
    timestamp = Column(DateTime, default=func.now())
    
    # Relationships
    job = relationship("Job", back_populates="audit_logs")
    node = relationship("Node")


class AnalysisRequest(Base):
    __tablename__ = "analysis_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(100), unique=True, index=True, nullable=False)
    
    # Requester information
    requester_name = Column(String(200), nullable=False)
    requester_institution = Column(String(200), nullable=False)
    requester_email = Column(String(200), nullable=False)
    requester_affiliation = Column(String(200))
    
    # Analysis details
    analysis_title = Column(String(300), nullable=False)
    analysis_description = Column(Text, nullable=False)
    
    # Data and analysis parameters
    target_node_id = Column(String(100), nullable=False)
    data_catalog_name = Column(String(200), nullable=False)
    selected_score = Column(String(100))  # Selected score/timeline option
    selected_timeline = Column(String(100))
    
    # Script information
    script_type = Column(String(50), nullable=False)
    script_content = Column(Text, nullable=False)
    parameters = Column(JSON)
    filters = Column(JSON)
    
    # Request management
    status = Column(String(50), default=RequestStatus.PENDING)
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    estimated_duration = Column(String(50))  # e.g., "2 hours", "1 day"
    
    # Approval information
    approved_by = Column(String(200))
    approval_notes = Column(Text)
    approved_at = Column(DateTime)
    expires_at = Column(DateTime)
    
    # Timestamps
    submitted_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    jobs = relationship("Job", back_populates="analysis_request")


class ScoreTimelineOption(Base):
    __tablename__ = "score_timeline_options"
    
    id = Column(Integer, primary_key=True, index=True)
    data_catalog_id = Column(String(100), nullable=False)  # References catalog ID from manifest
    option_type = Column(String(50), nullable=False)  # "score" or "timeline"
    option_name = Column(String(200), nullable=False)
    option_description = Column(Text)
    option_value = Column(String(200), nullable=False)  # The actual value to use
    is_default = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    # No direct relationships for now, but could link to catalogs


# Pydantic Models for API
class NodeCreate(BaseModel):
    node_id: str
    name: str
    institution: str
    endpoint_url: str
    public_key: Optional[str] = None


class NodeResponse(BaseModel):
    id: int
    node_id: str
    name: str
    institution: str
    endpoint_url: str
    is_active: bool
    last_seen: datetime
    
    class Config:
        from_attributes = True


class DataCatalogCreate(BaseModel):
    name: str
    description: Optional[str] = None
    data_type: str
    schema_definition: Optional[Dict[str, Any]] = None
    access_level: str = "private"
    total_records: int = 0


class DataCatalogResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    data_type: str
    schema_definition: Optional[Dict[str, Any]]
    access_level: str
    total_records: int
    last_updated: datetime
    
    class Config:
        from_attributes = True


class JobCreate(BaseModel):
    script_type: ScriptType
    script_content: str
    data_catalog_id: int
    parameters: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None


class JobResponse(BaseModel):
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
    
    class Config:
        from_attributes = True


class JobSubmissionRequest(BaseModel):
    target_node_id: str
    data_catalog_name: str
    script_type: ScriptType
    script_content: str
    parameters: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    uploaded_file_ids: Optional[List[str]] = None  # IDs of uploaded files to use


class JobSubmissionResponse(BaseModel):
    job_id: str
    status: str
    message: str


class NodeDiscoveryResponse(BaseModel):
    nodes: list[NodeResponse]
    data_catalogs: list[DataCatalogResponse]


class HealthCheckResponse(BaseModel):
    status: str
    node_id: str
    version: str
    uptime: float
    active_jobs: int
    total_jobs: int


# New Pydantic models for analysis requests
class AnalysisRequestCreate(BaseModel):
    requester_name: str
    requester_institution: str
    requester_email: str
    requester_affiliation: Optional[str] = None
    analysis_title: str
    analysis_description: str
    target_node_id: str
    data_catalog_name: str
    selected_score: Optional[str] = None
    selected_timeline: Optional[str] = None
    script_type: ScriptType
    script_content: str
    parameters: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    priority: str = "normal"
    estimated_duration: Optional[str] = None


class AnalysisRequestResponse(BaseModel):
    id: int
    request_id: str
    requester_name: str
    requester_institution: str
    requester_email: str
    requester_affiliation: Optional[str]
    analysis_title: str
    analysis_description: str
    target_node_id: str
    data_catalog_name: str
    selected_score: Optional[str]
    selected_timeline: Optional[str]
    script_type: str
    script_content: str
    parameters: Optional[Dict[str, Any]]
    filters: Optional[Dict[str, Any]]
    status: str
    priority: str
    estimated_duration: Optional[str]
    approved_by: Optional[str]
    approval_notes: Optional[str]
    approved_at: Optional[datetime]
    expires_at: Optional[datetime]
    submitted_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AnalysisRequestUpdate(BaseModel):
    status: Optional[RequestStatus] = None
    approved_by: Optional[str] = None
    approval_notes: Optional[str] = None
    approved_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None


class ScoreTimelineOptionResponse(BaseModel):
    id: int
    data_catalog_id: str
    option_type: str
    option_name: str
    option_description: Optional[str]
    option_value: str
    is_default: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class DataCatalogWithOptionsResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    data_type: str
    schema_definition: Optional[Dict[str, Any]] = None
    access_level: str
    total_records: int
    last_updated: Optional[datetime] = None
    files: Optional[List[Dict[str, Any]]] = []
    score_options: List[ScoreTimelineOptionResponse] = []
    timeline_options: List[ScoreTimelineOptionResponse] = []
    
    class Config:
        from_attributes = True