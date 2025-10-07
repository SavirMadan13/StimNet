"""
Main FastAPI application for distributed node server
"""
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
import time
import hashlib
import uuid
from datetime import datetime, timedelta

from .config import settings
from .database import get_db, init_db
from .models import (
    Node, DataCatalog, Job, AuditLog,
    NodeResponse, DataCatalogResponse, JobResponse,
    JobCreate, JobSubmissionRequest, JobSubmissionResponse,
    NodeDiscoveryResponse, HealthCheckResponse,
    JobStatus, ScriptType
)
from .security import verify_token, create_access_token, get_current_user
from .job_executor import JobExecutor
from .remote_data_api import router as remote_api_router

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        *([logging.FileHandler(settings.log_file)] if settings.log_file else [])
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Distributed Data Access and Remote Execution Framework",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.debug else settings.trusted_nodes,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Job executor instance
job_executor = JobExecutor()

# Include remote API router
app.include_router(remote_api_router)

# Startup time for uptime calculation
startup_time = time.time()


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Node ID: {settings.node_id}")
    logger.info(f"Institution: {settings.institution_name}")
    
    # Initialize database
    init_db()
    
    # Start job executor
    await job_executor.start()
    
    logger.info("Application startup complete")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("Shutting down application")
    await job_executor.stop()


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


# Job submission and management
@app.post("/api/v1/jobs", response_model=JobSubmissionResponse)
async def submit_job(
    job_request: JobSubmissionRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Submit a job for execution"""
    
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
        requester_node_id=target_node.id,  # For now, same as executor
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
    
    # Add to execution queue
    await job_executor.submit_job(job.id)
    
    # Log the submission
    audit_log = AuditLog(
        job_id=job.id,
        node_id=target_node.id,
        action="job_submitted",
        details={
            "script_type": job_request.script_type,
            "data_catalog": job_request.data_catalog_name,
            "script_hash": script_hash
        },
        user_info=current_user,
        ip_address="127.0.0.1"  # TODO: Get real IP
    )
    db.add(audit_log)
    db.commit()
    
    return JobSubmissionResponse(
        job_id=job_id,
        status="submitted",
        message="Job submitted successfully"
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
            result_data={"message": f"Results blocked: cohort size < {settings.min_cohort_size}"},
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


@app.delete("/api/v1/jobs/{job_id}")
async def cancel_job(job_id: str, db: Session = Depends(get_db)):
    """Cancel a running job"""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status not in [JobStatus.QUEUED, JobStatus.RUNNING]:
        raise HTTPException(status_code=400, detail="Job cannot be cancelled")
    
    # Cancel the job
    await job_executor.cancel_job(job.id)
    
    job.status = JobStatus.CANCELLED
    db.commit()
    
    return {"message": "Job cancelled successfully"}


# Authentication endpoints
@app.post("/api/v1/auth/token")
async def login(username: str = Form(...), password: str = Form(...)):
    """Authenticate and get access token"""
    # TODO: Implement proper user authentication
    # For now, accept any credentials for demo purposes
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
        "distributed_node.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )