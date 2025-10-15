"""
Main FastAPI application for distributed node server
"""
from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File, Form
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
import shutil
from pathlib import Path

from .config import settings
from .database import get_db, init_db
from .models import (
    Node, DataCatalog, Job, AuditLog, AnalysisRequest, ScoreTimelineOption,
    NodeResponse, DataCatalogResponse, JobResponse,
    JobCreate, JobSubmissionRequest, JobSubmissionResponse,
    NodeDiscoveryResponse, HealthCheckResponse,
    AnalysisRequestCreate, AnalysisRequestResponse, AnalysisRequestUpdate,
    ScoreTimelineOptionResponse, DataCatalogWithOptionsResponse,
    JobStatus, ScriptType, RequestStatus
)
from .security import verify_token, create_access_token, get_current_user
from .job_executor import JobExecutor
from .remote_data_api import router as remote_api_router
from .web_interface import get_web_interface_html

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

# Upload configuration
UPLOAD_DIR = Path("uploads")
SCRIPTS_DIR = UPLOAD_DIR / "scripts"
DATA_DIR = UPLOAD_DIR / "data"

# Ensure upload directories exist
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_SCRIPT_EXTENSIONS = {".py", ".r", ".R"}
ALLOWED_DATA_EXTENSIONS = {".nii", ".nii.gz", ".csv", ".tsv", ".npy", ".npz", ".mat", ".json"}


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


# Web interface endpoint
@app.get("/", response_class=HTMLResponse)
async def web_interface():
    """Main web interface"""
    base_url = f"http://{settings.host}:{settings.port}"
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


# Analysis Request endpoints
@app.post("/api/v1/analysis-requests", response_model=AnalysisRequestResponse)
async def create_analysis_request(
    request: AnalysisRequestCreate,
    db: Session = Depends(get_db)
):
    """Create a new analysis request"""
    
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    
    # Create analysis request
    analysis_request = AnalysisRequest(
        request_id=request_id,
        requester_name=request.requester_name,
        requester_institution=request.requester_institution,
        requester_email=request.requester_email,
        requester_affiliation=request.requester_affiliation,
        analysis_title=request.analysis_title,
        analysis_description=request.analysis_description,
        research_question=request.research_question,
        methodology=request.methodology,
        expected_outcomes=request.expected_outcomes,
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
    
    db.add(analysis_request)
    db.commit()
    db.refresh(analysis_request)
    
    return AnalysisRequestResponse.from_orm(analysis_request)


@app.get("/api/v1/analysis-requests", response_model=List[AnalysisRequestResponse])
async def list_analysis_requests(
    status: Optional[RequestStatus] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List analysis requests with optional status filter"""
    query = db.query(AnalysisRequest).order_by(AnalysisRequest.submitted_at.desc())
    
    if status:
        query = query.filter(AnalysisRequest.status == status)
    
    requests = query.limit(limit).all()
    return [AnalysisRequestResponse.from_orm(req) for req in requests]


@app.get("/api/v1/analysis-requests/{request_id}", response_model=AnalysisRequestResponse)
async def get_analysis_request(request_id: str, db: Session = Depends(get_db)):
    """Get specific analysis request details"""
    request = db.query(AnalysisRequest).filter(AnalysisRequest.request_id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Analysis request not found")
    
    return AnalysisRequestResponse.from_orm(request)


@app.put("/api/v1/analysis-requests/{request_id}", response_model=AnalysisRequestResponse)
async def update_analysis_request(
    request_id: str,
    update: AnalysisRequestUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update analysis request status (approve/deny)"""
    request = db.query(AnalysisRequest).filter(AnalysisRequest.request_id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Analysis request not found")
    
    # Update fields
    if update.status is not None:
        request.status = update.status
    if update.approved_by is not None:
        request.approved_by = update.approved_by
    if update.approval_notes is not None:
        request.approval_notes = update.approval_notes
    if update.approved_at is not None:
        request.approved_at = update.approved_at
    if update.expires_at is not None:
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
        
        # Add to execution queue
        await job_executor.submit_job(job.id)
    
    db.commit()
    db.refresh(request)
    
    return AnalysisRequestResponse.from_orm(request)


# Score/Timeline options endpoints
@app.get("/api/v1/score-timeline-options/{catalog_id}", response_model=List[ScoreTimelineOptionResponse])
async def get_score_timeline_options(catalog_id: str, db: Session = Depends(get_db)):
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
    # Get catalogs from manifest (simplified for now)
    import json
    with open('/workspace/data/data_manifest.json', 'r') as f:
        manifest = json.load(f)
    
    catalogs_with_options = []
    
    for catalog_data in manifest['catalogs']:
        # Get score/timeline options from database
        score_options = db.query(ScoreTimelineOption).filter(
            ScoreTimelineOption.data_catalog_id == catalog_data['id'],
            ScoreTimelineOption.option_type == 'score',
            ScoreTimelineOption.is_active == True
        ).all()
        
        timeline_options = db.query(ScoreTimelineOption).filter(
            ScoreTimelineOption.data_catalog_id == catalog_data['id'],
            ScoreTimelineOption.option_type == 'timeline',
            ScoreTimelineOption.is_active == True
        ).all()
        
        catalog_response = DataCatalogWithOptionsResponse(
            id=catalog_data['id'],
            name=catalog_data['name'],
            description=catalog_data.get('description'),
            data_type=catalog_data.get('data_type', 'tabular'),
            schema_definition={"files": catalog_data.get('files', [])},
            access_level=catalog_data.get('privacy_level', 'private'),
            total_records=sum(file.get('record_count', 0) for file in catalog_data.get('files', [])),
            last_updated=datetime.now(),
            score_options=[ScoreTimelineOptionResponse.from_orm(opt) for opt in score_options],
            timeline_options=[ScoreTimelineOptionResponse.from_orm(opt) for opt in timeline_options]
        )
        
        catalogs_with_options.append(catalog_response)
    
    return catalogs_with_options


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
                    const requests = await response.json();
                    
                    const requestsList = document.getElementById('requestsList');
                    if (requests.length === 0) {
                        requestsList.innerHTML = '<p>No pending requests.</p>';
                        return;
                    }
                    
                    let html = '';
                    requests.forEach(request => {
                        html += `
                            <div class="request-item">
                                <div class="request-header">
                                    <h3 class="request-title">${request.analysis_title}</h3>
                                    <span class="status-pending">PENDING</span>
                                </div>
                                <div class="request-meta">
                                    <strong>Requester:</strong> ${request.requester_name} (${request.requester_institution})<br>
                                    <strong>Email:</strong> ${request.requester_email}<br>
                                    <strong>Dataset:</strong> ${request.data_catalog_name}<br>
                                    <strong>Priority:</strong> ${request.priority}<br>
                                    <strong>Submitted:</strong> ${new Date(request.submitted_at).toLocaleString()}
                                </div>
                                <div class="request-description">
                                    <strong>Research Question:</strong> ${request.research_question}<br>
                                    <strong>Description:</strong> ${request.analysis_description}
                                </div>
                                <div class="request-actions">
                                    <button class="approve" onclick="approveRequest('${request.request_id}')">✅ Approve</button>
                                    <button class="deny" onclick="denyRequest('${request.request_id}')">❌ Deny</button>
                                    <button onclick="viewRequest('${request.request_id}')">👁️ View Details</button>
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
                if (!confirm('Are you sure you want to approve this request?')) return;
                
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
                        alert('Request approved successfully!');
                        loadRequests();
                    } else {
                        alert('Error approving request');
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
                        alert('Error denying request');
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


# File upload endpoints
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
    """Upload a data file (.nii, .csv, etc.)"""
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
        
        return {
            "file_id": file_id,
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