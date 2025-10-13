"""
Real execution FastAPI application for distributed node server
"""
from fastapi import FastAPI, HTTPException, Depends, status, Form, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
import os
import shutil
from typing import List, Optional, Dict, Any
import logging
import time
import hashlib
import uuid
from datetime import datetime, timedelta
import asyncio
import threading
from pathlib import Path
import json

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

# Mount static files directory
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

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


@app.get("/api/v1/data-catalogs")
async def list_data_catalogs(
    access_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List available data catalogs from manifest file"""
    try:
        # Try to read from manifest file first
        manifest_path = Path("data/data_manifest.json")
        
        if manifest_path.exists():
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Return catalogs from manifest with enriched information
            catalogs = []
            for catalog in manifest.get('catalogs', []):
                # Verify files exist and get actual record counts
                total_records = 0
                files_info = []
                
                for file_info in catalog.get('files', []):
                    file_path = Path(file_info['path'])
                    if file_path.exists() and file_info['type'] == 'csv':
                        # Count actual records
                        import pandas as pd
                        try:
                            df = pd.read_csv(file_path)
                            actual_count = len(df)
                            total_records += actual_count
                            files_info.append({
                                **file_info,
                                'actual_record_count': actual_count,
                                'exists': True
                            })
                        except:
                            files_info.append({
                                **file_info,
                                'exists': False
                            })
                    else:
                        files_info.append({
                            **file_info,
                            'exists': file_path.exists() if file_info['type'] != 'synthetic' else True
                        })
                
                catalogs.append({
                    'id': catalog['id'],
                    'name': catalog['name'],
                    'description': catalog['description'],
                    'data_type': catalog['data_type'],
                    'privacy_level': catalog.get('privacy_level', 'high'),
                    'min_cohort_size': catalog.get('min_cohort_size', 10),
                    'files': files_info,
                    'metadata': catalog.get('metadata', {}),
                    'total_records': total_records if total_records > 0 else catalog.get('metadata', {}).get('total_subjects', 0)
                })
            
            return catalogs
        
        # Fallback to database if manifest doesn't exist
        query = db.query(DataCatalog)
        
        if access_level:
            query = query.filter(DataCatalog.access_level == access_level)
        else:
            query = query.filter(DataCatalog.access_level.in_(["public", "restricted"]))
        
        catalogs = query.all()
        return [DataCatalogResponse.from_orm(catalog) for catalog in catalogs]
        
    except Exception as e:
        logger.error(f"Error reading data catalogs: {e}")
        # Fallback to database
        query = db.query(DataCatalog)
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
    job = None
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            logger.error(f"Job {job_id} not found")
            return
        
        logger.info(f"🚀 Starting REAL execution of job {job.job_id}")
        
        # Update job status
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Error committing job status update: {e}")
            db.rollback()
            return
        
        # Validate script security
        security_check = script_executor.validate_script_security(job.script_content, job.script_type)
        
        if not security_check["is_safe"]:
            logger.warning(f"Script security validation failed for job {job.job_id}: {security_check['warnings']}")
            job.status = JobStatus.FAILED
            job.error_message = f"Script failed security validation: {security_check['warnings']}"
            job.completed_at = datetime.utcnow()
            try:
                db.commit()
            except Exception as e:
                logger.error(f"Error committing security validation failure: {e}")
                db.rollback()
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
            data_catalog_id=job.data_catalog_id,
            uploaded_file_ids=job.uploaded_file_ids or []
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
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Error committing job completion: {e}")
            db.rollback()
        
    except Exception as e:
        logger.error(f"Error executing job {job_id}: {e}")
        if job:
            try:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
            except Exception as commit_error:
                logger.error(f"Error committing job failure: {commit_error}")
                db.rollback()
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
    
    # Find data catalog from manifest
    manifest_path = Path("data/data_manifest.json")
    if not manifest_path.exists():
        raise HTTPException(status_code=500, detail="Data manifest not found")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Find catalog by ID or name in manifest (accept either)
    catalog = None
    for c in manifest.get('catalogs', []):
        if c.get('id') == job_request.data_catalog_name or c.get('name') == job_request.data_catalog_name:
            catalog = c
            break
    
    if not catalog:
        raise HTTPException(status_code=404, detail=f"Data catalog not found: {job_request.data_catalog_name}")
    
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
        data_catalog_id=catalog['id'],  # Use manifest catalog ID (string)
        script_type=job_request.script_type,
        script_content=job_request.script_content,
        script_hash=script_hash,
        parameters=job_request.parameters or {},
        filters=job_request.filters or {},
        uploaded_file_ids=job_request.uploaded_file_ids or [],
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


# File upload endpoints
UPLOAD_DIR = Path("uploads")
SCRIPTS_DIR = UPLOAD_DIR / "scripts"
DATA_DIR = UPLOAD_DIR / "data"

# Ensure upload directories exist
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_SCRIPT_EXTENSIONS = {".py", ".r", ".R"}
ALLOWED_DATA_EXTENSIONS = {".nii", ".nii.gz", ".csv", ".tsv", ".npy", ".npz", ".mat", ".json"}


def store_uploaded_file_info(file_path: str, filename: str, file_type: str) -> dict:
    """
    Store uploaded file info for later use in analysis scripts.
    Returns file info dict with file_id, path, and metadata.
    """
    try:
        uploads_info_dir = Path("uploads")
        uploads_info_dir.mkdir(exist_ok=True)
        
        info_file = uploads_info_dir / "uploaded_files.json"
        
        # Read existing uploads info
        if info_file.exists():
            with open(info_file, 'r') as f:
                uploads_info = json.load(f)
        else:
            uploads_info = {"files": []}
        
        # Create file info
        file_id = str(uuid.uuid4())
        file_info = {
            "file_id": file_id,
            "filename": filename,
            "path": file_path,
            "type": file_type.replace('.', ''),  # e.g., 'nii.gz' or 'csv'
            "uploaded_at": datetime.now().isoformat(),
            "size_bytes": Path(file_path).stat().st_size
        }
        
        uploads_info['files'].append(file_info)
        uploads_info['last_updated'] = datetime.now().isoformat()
        
        # Write back
        with open(info_file, 'w') as f:
            json.dump(uploads_info, f, indent=2)
        
        logger.info(f"Stored uploaded file info for {filename}")
        return file_info
        
    except Exception as e:
        logger.error(f"Error storing uploaded file info: {e}")
        return {}


@app.post("/api/v1/upload/script")
async def upload_script(file: UploadFile = File(...)):
    """Upload a script file (.py or .R)"""
    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_SCRIPT_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_SCRIPT_EXTENSIONS)}"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}_{file.filename}"
        file_path = SCRIPTS_DIR / safe_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Read content for preview
        with open(file_path, "r") as f:
            content = f.read()
        
        logger.info(f"Script uploaded: {safe_filename} ({len(content)} bytes)")
        
        return {
            "file_id": file_id,
            "filename": file.filename,
            "saved_as": safe_filename,
            "size_bytes": len(content),
            "content": content,
            "path": str(file_path)
        }
    
    except Exception as e:
        logger.error(f"Error uploading script: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/upload/data")
async def upload_data(file: UploadFile = File(...)):
    """Upload a data file (.nii, .csv, etc.) and auto-integrate into manifest"""
    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        # Handle .nii.gz
        if file.filename.endswith('.nii.gz'):
            file_ext = '.nii.gz'
        
        if file_ext not in ALLOWED_DATA_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_DATA_EXTENSIONS)}"
            )
        
        # Generate unique filename
        file_id = str(uuid.uuid4())
        safe_filename = f"{file_id}_{file.filename}"
        file_path = DATA_DIR / safe_filename
        
        # Save file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        file_size = file_path.stat().st_size
        
        logger.info(f"Data file uploaded: {safe_filename} ({file_size} bytes)")
        
        # Store file info for use in analysis scripts
        file_info = store_uploaded_file_info(
            file_path=str(file_path),
            filename=file.filename,
            file_type=file_ext
        )
        
        return {
            "file_id": file_info.get('file_id', file_id),
            "filename": file.filename,
            "saved_as": safe_filename,
            "size_bytes": file_size,
            "path": str(file_path),
            "type": file_ext,
            "message": f"File uploaded successfully. Use this file in your analysis script."
        }
    
    except Exception as e:
        logger.error(f"Error uploading data file: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/uploads/scripts")
async def list_uploaded_scripts():
    """List all uploaded scripts"""
    try:
        scripts = []
        for file_path in SCRIPTS_DIR.glob("*"):
            if file_path.is_file():
                scripts.append({
                    "filename": file_path.name,
                    "size_bytes": file_path.stat().st_size,
                    "uploaded_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        return scripts
    except Exception as e:
        logger.error(f"Error listing scripts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/uploads/data")
async def list_uploaded_data():
    """List all uploaded data files"""
    try:
        data_files = []
        for file_path in DATA_DIR.glob("*"):
            if file_path.is_file():
                data_files.append({
                    "filename": file_path.name,
                    "size_bytes": file_path.stat().st_size,
                    "uploaded_at": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        return data_files
    except Exception as e:
        logger.error(f"Error listing data files: {e}")
        raise HTTPException(status_code=500, detail=str(e))


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
