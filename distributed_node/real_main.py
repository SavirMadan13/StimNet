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
    Node, DataCatalog, Job, AuditLog, AnalysisRequest, ScoreTimelineOption,
    NodeResponse, DataCatalogResponse, JobResponse,
    JobSubmissionRequest, JobSubmissionResponse,
    NodeDiscoveryResponse, HealthCheckResponse,
    AnalysisRequestResponse, ScoreTimelineOptionResponse, DataCatalogWithOptionsResponse,
    AnalysisRequestCreate, AnalysisRequestUpdate,
    JobStatus, ScriptType, RequestStatus
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
        manifest_path = Path("data/data_manifest_simple.json")
        
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
                    if file_path.exists():
                        # Count actual records and auto-detect columns
                        import pandas as pd
                        try:
                            if file_info['type'] == 'csv':
                                df = pd.read_csv(file_path)
                                actual_count = len(df)
                                # Only count records from the first file (subjects) to get unique patient count
                                if total_records == 0:
                                    total_records = actual_count
                                
                                # Auto-detect columns if not already present
                                if 'columns' not in file_info or not file_info['columns']:
                                    columns = []
                                    for col in df.columns:
                                        dtype = str(df[col].dtype)
                                        if dtype.startswith('int'):
                                            col_type = 'int'
                                        elif dtype.startswith('float'):
                                            col_type = 'float'
                                        elif dtype.startswith('bool'):
                                            col_type = 'bool'
                                        elif dtype.startswith('datetime'):
                                            col_type = 'datetime'
                                        else:
                                            col_type = 'string'
                                        
                                        columns.append({
                                            "name": col,
                                            "type": col_type
                                        })
                                    
                                    file_info['columns'] = columns
                                
                                files_info.append({
                                    **file_info,
                                    'actual_record_count': actual_count,
                                    'exists': True
                                })
                            else:
                                # For non-CSV files, just mark as existing
                                files_info.append({
                                    **file_info,
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


# Analysis Request endpoints
@app.post("/api/v1/analysis-requests", response_model=AnalysisRequestResponse)
async def create_analysis_request(
    request: AnalysisRequestCreate,
    db: Session = Depends(get_db)
):
    """Create a new analysis request"""
    try:
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        
        # Create new analysis request
        db_request = AnalysisRequest(
            request_id=request_id,
            requester_name=request.requester_name,
            requester_institution=request.requester_institution,
            requester_email=request.requester_email,
            requester_affiliation=request.requester_affiliation,
            analysis_title=request.analysis_title,
            analysis_description=request.analysis_description,
            target_node_id=request.target_node_id,
            data_catalog_name=request.data_catalog_name,
            selected_score=request.selected_score,
            selected_timeline=request.selected_timeline,
            script_type=request.script_type,
            script_content=request.script_content,
            parameters=request.parameters or {},
            filters=request.filters or {},
            priority=request.priority,
            estimated_duration=request.estimated_duration,
            status=RequestStatus.PENDING
        )
        
        db.add(db_request)
        db.commit()
        db.refresh(db_request)
        
        return AnalysisRequestResponse.from_orm(db_request)
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create analysis request: {str(e)}")


@app.get("/api/v1/analysis-requests", response_model=List[AnalysisRequestResponse])
async def list_analysis_requests(
    status: Optional[str] = None,
    user_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List analysis requests with optional filtering"""
    query = db.query(AnalysisRequest)
    
    if status:
        query = query.filter(AnalysisRequest.status == status)
    if user_id:
        query = query.filter(AnalysisRequest.user_id == user_id)
    
    requests = query.order_by(AnalysisRequest.submitted_at.desc()).all()
    return [AnalysisRequestResponse.from_orm(req) for req in requests]


@app.get("/api/v1/analysis-requests/{request_id}", response_model=AnalysisRequestResponse)
async def get_analysis_request(
    request_id: str,
    db: Session = Depends(get_db)
):
    """Get a specific analysis request"""
    request = db.query(AnalysisRequest).filter(AnalysisRequest.request_id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Analysis request not found")
    
    return AnalysisRequestResponse.from_orm(request)


@app.get("/api/v1/analysis-requests/{request_id}/results")
async def get_analysis_results(request_id: str, db: Session = Depends(get_db)):
    """Get analysis results for a specific request"""
    try:
        # Get the analysis request
        request = db.query(AnalysisRequest).filter(AnalysisRequest.request_id == request_id).first()
        if not request:
            raise HTTPException(status_code=404, detail="Analysis request not found")
        
        # Get the associated job
        job = db.query(Job).filter(Job.analysis_request_id == request.id).first()
        if not job:
            raise HTTPException(status_code=404, detail="No job found for this request")
        
        # Get the results from the job
        return {
            "request_id": request_id,
            "status": request.status,
            "job_id": job.id,
            "job_status": job.status,
            "results": [
                {
                    "id": job.id,
                    "result_type": "analysis_result",
                    "result_data": job.result_data,
                    "created_at": job.completed_at.isoformat() if job.completed_at else job.submitted_at.isoformat(),
                    "metadata": {
                        "execution_time": job.execution_time,
                        "memory_used_mb": job.memory_used_mb,
                        "records_processed": job.records_processed,
                        "error_message": job.error_message
                    }
                }
            ] if job.result_data else [],
            "total_results": 1 if job.result_data else 0
        }
    except Exception as e:
        logger.error(f"Error getting analysis results: {e}")
        raise HTTPException(status_code=500, detail="Error getting analysis results")


@app.put("/api/v1/analysis-requests/{request_id}", response_model=AnalysisRequestResponse)
async def update_analysis_request(
    request_id: str,
    update: AnalysisRequestUpdate,
    db: Session = Depends(get_db)
):
    """Update an analysis request (approve/deny)"""
    request = db.query(AnalysisRequest).filter(AnalysisRequest.request_id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Analysis request not found")
    
    # Update fields
    if update.status:
        request.status = update.status
    if update.approved_by:
        request.approved_by = update.approved_by
    if update.approval_notes:
        request.approval_notes = update.approval_notes
    if update.approved_at:
        request.approved_at = update.approved_at
    if update.expires_at:
        request.expires_at = update.expires_at
    
    # If approved, create a job
    if update.status == RequestStatus.APPROVED:
        # Find target node
        target_node = db.query(Node).filter(Node.node_id == request.target_node_id).first()
        if not target_node:
            raise HTTPException(status_code=404, detail="Target node not found")
        
        # Create job
        job_id = str(uuid.uuid4())
        script_hash = hashlib.sha256(request.script_content.encode()).hexdigest()
        
        job = Job(
            job_id=job_id,
            requester_node_id=target_node.id,
            executor_node_id=target_node.id,
            data_catalog_id=request.data_catalog_name,
            analysis_request_id=request.id,
            script_type=request.script_type,
            script_content=request.script_content,
            script_hash=script_hash,
            parameters=request.parameters or {},
            filters=request.filters or {},
            status=JobStatus.QUEUED
        )
        
        db.add(job)
        db.commit()
        db.refresh(job)
        
        # Execute job in background thread (REAL EXECUTION)
        logger.info(f"🚀 Queuing approved job {job_id} for REAL execution")
        thread = threading.Thread(target=_execute_job_sync, args=(job.id,), daemon=True)
        thread.start()
    
    db.commit()
    db.refresh(request)
    
    return AnalysisRequestResponse.from_orm(request)


# Score/Timeline options endpoints
@app.get("/api/v1/score-timeline-options/{catalog_id}", response_model=List[ScoreTimelineOptionResponse])
async def get_score_timeline_options(
    catalog_id: str, 
    db: Session = Depends(get_db)
):
    """Get available score and timeline options for a data catalog"""
    options = db.query(ScoreTimelineOption).filter(
        ScoreTimelineOption.data_catalog_id == catalog_id,
        ScoreTimelineOption.is_active == True
    ).all()
    
    return [ScoreTimelineOptionResponse.from_orm(option) for option in options]


@app.get("/api/v1/data-catalogs-with-options", response_model=List[DataCatalogWithOptionsResponse])
async def list_data_catalogs_with_options(
    access_level: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List data catalogs with their score/timeline options"""
    try:
        # Get catalogs from manifest
        manifest_path = Path(__file__).parent.parent / "data" / "data_manifest_simple.json"
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        catalogs_with_options = []
        
        for catalog_data in manifest.get("catalogs", []):
            # Auto-detect columns for each file
            enhanced_files = []
            total_records = 0
            
            for file_info in catalog_data.get("files", []):
                file_path = Path(file_info['path'])
                if file_path.exists():
                    # Count actual records and auto-detect columns
                    import pandas as pd
                    try:
                        if file_info['type'] == 'csv':
                            df = pd.read_csv(file_path)
                            actual_count = len(df)
                            # Only count records from the first file (subjects) to get unique patient count
                            if total_records == 0:
                                total_records = actual_count
                            
                            # Auto-detect columns if not already present
                            if 'columns' not in file_info or not file_info['columns']:
                                columns = []
                                for col in df.columns:
                                    dtype = str(df[col].dtype)
                                    if dtype.startswith('int'):
                                        col_type = 'int'
                                    elif dtype.startswith('float'):
                                        col_type = 'float'
                                    elif dtype.startswith('bool'):
                                        col_type = 'bool'
                                    elif dtype.startswith('datetime'):
                                        col_type = 'datetime'
                                    else:
                                        col_type = 'string'
                                    
                                    columns.append({
                                        "name": col,
                                        "type": col_type
                                    })
                                
                                file_info['columns'] = columns
                            
                            enhanced_files.append({
                                **file_info,
                                'actual_record_count': actual_count,
                                'exists': True
                            })
                        else:
                            # For non-CSV files, just mark as existing
                            enhanced_files.append({
                                **file_info,
                                'exists': True
                            })
                    except Exception as e:
                        enhanced_files.append({
                            **file_info,
                            'exists': False,
                            'error': str(e)
                        })
                else:
                    enhanced_files.append({
                        **file_info,
                        'exists': False
                    })
            
            # Get score/timeline options from database
            options = db.query(ScoreTimelineOption).filter(
                ScoreTimelineOption.data_catalog_id == catalog_data["id"],
                ScoreTimelineOption.is_active == True
            ).all()
            
            score_options = []
            timeline_options = []
            
            for option in options:
                option_response = ScoreTimelineOptionResponse.from_orm(option)
                if option.option_type == "score":
                    score_options.append(option_response)
                elif option.option_type == "timeline":
                    timeline_options.append(option_response)
            
            # Create response
            catalog_response = DataCatalogWithOptionsResponse(
                id=catalog_data["id"],
                name=catalog_data["name"],
                description=catalog_data.get("description", ""),
                data_type=catalog_data.get("data_type", "tabular"),
                schema_definition={"files": enhanced_files},
                access_level=catalog_data.get("privacy_level", "public"),
                total_records=total_records,
                last_updated=datetime.now(),
                files=enhanced_files,
                score_options=score_options,
                timeline_options=timeline_options
            )
            
            # Apply access level filter if specified
            if access_level and catalog_response.access_level != access_level:
                continue
                
            catalogs_with_options.append(catalog_response)
        
        return catalogs_with_options
        
    except Exception as e:
        logger.error(f"Error loading data catalogs with options: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load data catalogs: {str(e)}")


# Admin interface endpoint
@app.get("/admin", response_class=HTMLResponse)
async def admin_interface():
    """Admin interface for managing analysis requests"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>StimNet Admin Interface</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
            .container { background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .header { text-align: center; margin-bottom: 30px; padding-bottom: 20px; border-bottom: 2px solid #eee; }
            .section { margin: 30px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #007bff; }
            .request-item { background: white; border: 1px solid #e0e0e0; border-radius: 8px; padding: 20px; margin: 15px 0; }
            .request-header { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 10px; }
            .request-title { font-size: 18px; font-weight: 600; color: #333; margin: 0; }
            .request-meta { font-size: 14px; color: #666; margin: 5px 0; }
            .request-description { color: #555; margin: 10px 0; line-height: 1.5; }
            .request-actions { margin-top: 15px; }
            button { background: #007bff; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; margin: 5px; }
            button:hover { background: #0056b3; }
            button.approve { background: #28a745; }
            button.deny { background: #dc3545; }
            .status-pending { color: #856404; background: #fff3cd; padding: 4px 8px; border-radius: 4px; }
            .status-approved { color: #155724; background: #d4edda; padding: 4px 8px; border-radius: 4px; }
            .status-denied { color: #721c24; background: #f8d7da; padding: 4px 8px; border-radius: 4px; }
            .script-preview { background: #f8f9fa; border: 1px solid #e9ecef; border-radius: 4px; padding: 10px; margin: 10px 0; font-family: monospace; font-size: 12px; max-height: 200px; overflow-y: auto; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔧 StimNet Admin Interface</h1>
                <p>Manage analysis requests and system administration</p>
            </div>
            
            <div class="section">
                <h2>📝 Pending Analysis Requests</h2>
                <div id="requestsList">
                    <p>Loading requests...</p>
                </div>
            </div>
        </div>
        
        <script>
            async function loadRequests() {
                try {
                    const response = await fetch('/api/v1/analysis-requests?status=pending');
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    const requests = await response.json();
                    
                    const requestsList = document.getElementById('requestsList');
                    if (!requests || requests.length === 0) {
                        requestsList.innerHTML = '<p>No pending requests.</p>';
                        return;
                    }
                    
                    let html = '';
                    requests.forEach(request => {
                        // Ensure request has required fields
                        if (!request.request_id) {
                            console.warn('Request missing request_id:', request);
                            return;
                        }
                        
                        // Safely handle all fields with fallbacks
                        const safeRequest = {
                            request_id: request.request_id || 'unknown',
                            analysis_title: request.analysis_title || 'Untitled Analysis',
                            requester_name: request.requester_name || 'Unknown',
                            requester_institution: request.requester_institution || 'Unknown Institution',
                            requester_email: request.requester_email || 'No email provided',
                            data_catalog_name: request.data_catalog_name || 'Unknown Dataset',
                            priority: request.priority || 'normal',
                            submitted_at: request.submitted_at || new Date().toISOString(),
                            analysis_description: request.analysis_description || 'No description provided',
                            script_content: request.script_content || ''
                        };
                        
                        html += `
                            <div class="request-item">
                                <div class="request-header">
                                    <h3 class="request-title">${safeRequest.analysis_title}</h3>
                                    <span class="status-pending">PENDING</span>
                                </div>
                                <div class="request-meta">
                                    <strong>Requester:</strong> ${safeRequest.requester_name} (${safeRequest.requester_institution})<br>
                                    <strong>Email:</strong> ${safeRequest.requester_email}<br>
                                    <strong>Dataset:</strong> ${safeRequest.data_catalog_name}<br>
                                    <strong>Priority:</strong> ${safeRequest.priority}<br>
                                    <strong>Submitted:</strong> ${new Date(safeRequest.submitted_at).toLocaleString()}
                                </div>
                                <div class="request-description">
                                    <strong>Description:</strong> ${safeRequest.analysis_description}
                                </div>
                                <div class="script-preview">
                                    <strong>Script Preview:</strong><br>
                                    <pre>${safeRequest.script_content && safeRequest.script_content.length > 0 ? 
                                        (safeRequest.script_content.length > 500 ? safeRequest.script_content.substring(0, 500) + '...' : safeRequest.script_content) : 
                                        'No script content available'}</pre>
                                </div>
                                <div class="request-actions">
                                    <button class="approve" onclick="approveRequest('${safeRequest.request_id}')">✅ Approve</button>
                                    <button class="deny" onclick="denyRequest('${safeRequest.request_id}')">❌ Deny</button>
                                    <button onclick="viewRequest('${safeRequest.request_id}')">👁️ View Details</button>
                                </div>
                            </div>
                        `;
                    });
                    requestsList.innerHTML = html;
                } catch (error) {
                    document.getElementById('requestsList').innerHTML = '<p style="color: red;">Error loading requests: ' + error.message + '</p>';
                }
            }
            
            async function approveRequest(requestId) {
                if (!confirm('Are you sure you want to approve this request? This will start the analysis job.')) return;
                
                try {
                    const response = await fetch(`/api/v1/analysis-requests/${requestId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            status: 'approved',
                            approved_by: 'Admin',
                            approved_at: new Date().toISOString()
                        })
                    });
                    
                    if (response.ok) {
                        alert('Request approved successfully! The analysis job has been started.');
                        loadRequests();
                    } else {
                        const error = await response.json();
                        alert('Error approving request: ' + error.detail);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }
            
            async function denyRequest(requestId) {
                const reason = prompt('Please provide a reason for denial:');
                if (!reason) return;
                
                try {
                    const response = await fetch(`/api/v1/analysis-requests/${requestId}`, {
                        method: 'PUT',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            status: 'denied',
                            approved_by: 'Admin',
                            approval_notes: reason,
                            approved_at: new Date().toISOString()
                        })
                    });
                    
                    if (response.ok) {
                        alert('Request denied successfully!');
                        loadRequests();
                    } else {
                        const error = await response.json();
                        alert('Error denying request: ' + error.detail);
                    }
                } catch (error) {
                    alert('Error: ' + error.message);
                }
            }
            
            function viewRequest(requestId) {
                window.open(`/api/v1/analysis-requests/${requestId}`, '_blank');
            }
            
            // Load requests on page load
            document.addEventListener('DOMContentLoaded', loadRequests);
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "distributed_node.real_main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
