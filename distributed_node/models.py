"""
Database models for the distributed node
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Float, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum

Base = declarative_base()


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


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
    
    script_type = Column(String(50), nullable=False)
    script_content = Column(Text, nullable=False)
    script_hash = Column(String(100), nullable=False)
    
    parameters = Column(JSON)
    filters = Column(JSON)
    
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