"""
Configuration management for distributed node
"""
import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Basic server settings
    app_name: str = "StimNet Research Platform"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Node identification
    node_id: str = Field(default_factory=lambda: os.environ.get("NODE_ID", "default-node"))
    node_name: str = Field(default_factory=lambda: os.environ.get("NODE_NAME", "Default Node"))
    institution_name: str = Field(default_factory=lambda: os.environ.get("INSTITUTION_NAME", "Default Institution"))
    
    # Security settings
    secret_key: str = Field(default_factory=lambda: os.environ.get("SECRET_KEY", "your-secret-key-change-in-production"))
    access_token_expire_minutes: int = 30
    algorithm: str = "HS256"
    
    # Database settings
    database_url: str = Field(default="sqlite:///./distributed_node.db")
    
    # Redis settings (for caching and job queue)
    redis_url: str = Field(default="redis://localhost:6379/0")
    
    # Data and execution settings
    data_root: str = Field(default="./data")
    work_dir: str = Field(default="./work")
    max_execution_time: int = 3600  # 1 hour
    max_memory_mb: int = 4096  # 4GB
    max_cpu_cores: int = 4
    
    # Privacy and security controls
    min_cohort_size: int = 10
    enable_differential_privacy: bool = False
    privacy_epsilon: float = 1.0
    
    # Allowed script types
    allowed_script_types: List[str] = ["python", "r", "sql", "jupyter"]
    
    # Docker settings
    docker_registry: str = "localhost:5000"
    execution_image_python: str = "local/research-python:latest"
    execution_image_r: str = "r-base:4.3.2"
    
    # Network settings
    trusted_nodes: List[str] = []
    require_tls: bool = True
    require_client_cert: bool = False
    
    # Logging
    log_level: str = "INFO"
    log_file: Optional[str] = None
    enable_audit_log: bool = True
    audit_log_file: str = "./audit.log"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()