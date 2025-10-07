"""
Real execution FastAPI application for distributed node server
"""
from fastapi import FastAPI, HTTPException, Depends, status, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
import time
import hashlib
import uuid
from datetime import datetime, timedelta
import asyncio
import threading

from .config import settings
from .database import get_db, init_db
from .models import (
    Node, DataCatalog, Job, AuditLog,
    NodeResponse, DataCatalogResponse, JobResponse,
    JobSubmissionRequest, JobSubmissionResponse,
    NodeDiscoveryResponse, HealthCheckResponse,
    JobStatus, ScriptType
)
from .security import create_access_token
from .real_executor import RealScriptExecutor
from .web_interface import get_web_interface_html

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Distributed Data Access and Remote Execution Framework - Real Execution Mode",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Real script executor
script_executor = RealScriptExecutor()

# Startup time for uptime calculation
startup_time = time.time()


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version} - REAL EXECUTION MODE")
    logger.info(f"Node ID: {settings.node_id}")
    logger.info(f"Institution: {settings.institution_name}")
    logger.info("🚀 Real script execution enabled!")
    
    # Initialize database
    init_db()
    
    logger.info("Application startup complete")


# Web interface endpoint
@app.get("/", response_class=HTMLResponse)
async def web_interface():
    """Simple web interface for easy testing"""
    base_url = "http://localhost:8000"  # Could be made dynamic
    return get_web_interface_html(settings.node_id, base_url)


# Health check endpoint
@app.get("/health", response_model=HealthCheckResponse)
async def health_check(db: Session = Depends(get_db)):
    """Health check endpoint"""
    active_jobs = db.query(Job).filter(Job.status.in_([JobStatus.QUEUED, JobStatus.RUNNING])).count()
    total_jobs = db.query(Job).count()
    
    return HealthCheckResponse(
        status="healthy",
        node_id=settings.node_id,
        version=settings.app_version,
        uptime=time.time() - startup_time,
        active_jobs=active_jobs,
        total_jobs=total_jobs
    )


# Node discovery endpoints
@app.get("/api/v1/discovery", response_model=NodeDiscoveryResponse)
async def discover_node(db: Session = Depends(get_db)):
    """Discover this node's capabilities and data catalogs"""
    # Get current node info
    current_node = db.query(Node).filter(Node.node_id == settings.node_id).first()
    if not current_node:
        raise HTTPException(status_code=404, detail="Node not found")
    
    # Get available data catalogs
    data_catalogs = db.query(DataCatalog).filter(
        DataCatalog.access_level.in_(["public", "restricted"])
    ).all()
    
    return NodeDiscoveryResponse(
        nodes=[NodeResponse.from_orm(current_node)],
        data_catalogs=[DataCatalogResponse.from_orm(catalog) for catalog in data_catalogs]
    )


@app.get("/api/v1/nodes", response_model=List[NodeResponse])
async def list_nodes(db: Session = Depends(get_db)):
    """List all known nodes"""
    nodes = db.query(Node).filter(Node.is_active == True).all()
    return [NodeResponse.from_orm(node) for node in nodes]


@app.get("/api/v1/data-catalogs", response_model=List[DataCatalogResponse])
async def list_data_catalogs(
    access_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List available data catalogs"""
    query = db.query(DataCatalog)
    
    if access_level:
        query = query.filter(DataCatalog.access_level == access_level)
    else:
        # Only show public and restricted catalogs by default
        query = query.filter(DataCatalog.access_level.in_(["public", "restricted"]))
    
    catalogs = query.all()
    return [DataCatalogResponse.from_orm(catalog) for catalog in catalogs]


@app.get("/api/v1/data-catalogs/{catalog_id}", response_model=DataCatalogResponse)
async def get_data_catalog(catalog_id: int, db: Session = Depends(get_db)):
    """Get specific data catalog details"""
    catalog = db.query(DataCatalog).filter(DataCatalog.id == catalog_id).first()
    if not catalog:
        raise HTTPException(status_code=404, detail="Data catalog not found")
    
    return DataCatalogResponse.from_orm(catalog)


def _execute_job_sync(job_id: int):
    """Execute job synchronously in background thread"""
    from .database import SessionLocal
    
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        logger.info(f"🚀 Starting REAL execution of job {job.job_id}")
        
        # Update job status
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.commit()
        
        # Validate script security
        security_check = script_executor.validate_script_security(job.script_content, job.script_type)
        
        if not security_check["is_safe"]:
            logger.warning(f"Script security validation failed for job {job.job_id}: {security_check['warnings']}")
            job.status = JobStatus.FAILED
            job.error_message = f"Script failed security validation: {security_check['warnings']}"
            job.completed_at = datetime.utcnow()
            db.commit()
            return
        
        if security_check["warnings"]:
            logger.warning(f"Script security warnings for job {job.job_id}: {security_check['warnings']}")
        
        # Execute the script with REAL execution
        logger.info(f"⚡ Executing script with real data processing...")
        
        execution_result = script_executor.execute_script(
            script_content=job.script_content,
            script_type=job.script_type,
            job_id=job.job_id,
            parameters=job.parameters,
            filters=job.filters,
            data_catalog_id=job.data_catalog_id
        )
        
        # Update job with results
        if execution_result["success"]:
            job.status = JobStatus.COMPLETED
            job.result_data = execution_result["data"]
            job.execution_time = execution_result["execution_time"]
            job.records_processed = execution_result.get("records_processed", 0)
            logger.info(f"✅ Job {job.job_id} completed successfully in {execution_result['execution_time']:.2f}s")
        else:
            job.status = JobStatus.FAILED
            job.error_message = execution_result["error"]
            job.result_data = execution_result.get("data", {})
            logger.error(f"❌ Job {job.job_id} failed: {execution_result['error']}")
        
        job.completed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        logger.error(f"Error executing job {job_id}: {e}")
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


# Job submission and management (REAL EXECUTION)
@app.post("/api/v1/jobs", response_model=JobSubmissionResponse)
async def submit_job(
    job_request: JobSubmissionRequest,
    db: Session = Depends(get_db)
):
    """Submit a job for REAL execution"""
    
    # Find target node (for now, assume it's this node)
    target_node = db.query(Node).filter(Node.node_id == job_request.target_node_id).first()
    if not target_node:
        raise HTTPException(status_code=404, detail="Target node not found")
    
    # Find data catalog
    data_catalog = db.query(DataCatalog).filter(
        DataCatalog.name == job_request.data_catalog_name
    ).first()
    if not data_catalog:
        raise HTTPException(status_code=404, detail="Data catalog not found")
    
    # Validate script type
    if job_request.script_type not in settings.allowed_script_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Script type {job_request.script_type} not allowed"
        )
    
    # Create job
    job_id = str(uuid.uuid4())
    script_hash = hashlib.sha256(job_request.script_content.encode()).hexdigest()
    
    job = Job(
        job_id=job_id,
        requester_node_id=target_node.id,
        executor_node_id=target_node.id,
        data_catalog_id=data_catalog.id,
        script_type=job_request.script_type,
        script_content=job_request.script_content,
        script_hash=script_hash,
        parameters=job_request.parameters or {},
        filters=job_request.filters or {},
        status=JobStatus.QUEUED
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Execute job in background thread (REAL EXECUTION)
    logger.info(f"🚀 Queuing job {job_id} for REAL execution")
    thread = threading.Thread(target=_execute_job_sync, args=(job.id,), daemon=True)
    thread.start()
    
    return JobSubmissionResponse(
        job_id=job_id,
        status="submitted",
        message="Job submitted for REAL execution"
    )


@app.get("/api/v1/jobs/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get job status and results"""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Privacy check - only return results if minimum cohort size is met
    if (job.status == JobStatus.COMPLETED and 
        job.records_processed and 
        job.records_processed < settings.min_cohort_size):
        
        # Return blocked status instead of results
        return JobResponse(
            id=job.id,
            job_id=job.job_id,
            script_type=job.script_type,
            status="blocked",
            progress=job.progress,
            result_data={"message": f"Results blocked: cohort size ({job.records_processed}) < minimum ({settings.min_cohort_size})"},
            error_message=None,
            execution_time=job.execution_time,
            memory_used_mb=job.memory_used_mb,
            records_processed=job.records_processed,
            submitted_at=job.submitted_at,
            started_at=job.started_at,
            completed_at=job.completed_at
        )
    
    return JobResponse.from_orm(job)


@app.get("/api/v1/jobs", response_model=List[JobResponse])
async def list_jobs(
    status: Optional[JobStatus] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List jobs with optional status filter"""
    query = db.query(Job).order_by(Job.submitted_at.desc())
    
    if status:
        query = query.filter(Job.status == status)
    
    jobs = query.limit(limit).all()
    return [JobResponse.from_orm(job) for job in jobs]


# Authentication endpoints
@app.post("/api/v1/auth/token")
async def login(username: str = Form(...), password: str = Form(...)):
    """Authenticate and get access token"""
    # Simple demo authentication - accept any non-empty credentials
    if username and password:
        access_token = create_access_token(data={"sub": username})
        return {"access_token": access_token, "token_type": "bearer"}
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "distributed_node.real_main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
