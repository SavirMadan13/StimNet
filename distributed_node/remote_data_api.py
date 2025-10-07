"""
Enhanced API endpoints for remote data submission and processing
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Union
import json
import uuid
import hashlib
import os
import tempfile
import asyncio
import logging
from datetime import datetime
from pathlib import Path

from .database import get_db
from .models import Job, DataCatalog, JobStatus, ScriptType
from .security import get_current_user, SecurityValidator
from .config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/remote", tags=["Remote Data Processing"])


class RemoteJobManager:
    """Manages remote job execution and data processing"""
    
    def __init__(self):
        self.active_jobs = {}
        self.job_results = {}
    
    async def process_data_submission(self, job_id: str, data_files: List[UploadFile], 
                                    script_content: str, parameters: Dict[str, Any]):
        """Process a remote data submission"""
        try:
            # Create temporary workspace
            workspace = tempfile.mkdtemp(prefix=f"remote_job_{job_id}_")
            
            # Save uploaded files
            uploaded_files = []
            for file in data_files:
                file_path = os.path.join(workspace, file.filename)
                with open(file_path, "wb") as f:
                    content = await file.read()
                    f.write(content)
                uploaded_files.append(file_path)
            
            # Execute the analysis script
            result = await self._execute_analysis(workspace, script_content, parameters, uploaded_files)
            
            # Store results
            self.job_results[job_id] = result
            
            # Cleanup workspace
            import shutil
            shutil.rmtree(workspace, ignore_errors=True)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing remote job {job_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def _execute_analysis(self, workspace: str, script_content: str, 
                               parameters: Dict[str, Any], data_files: List[str]):
        """Execute analysis script with uploaded data"""
        try:
            # Create analysis environment
            analysis_globals = {
                'workspace': workspace,
                'data_files': data_files,
                'parameters': parameters,
                'results': {}
            }
            
            # Import common libraries
            exec("""
import pandas as pd
import numpy as np
from scipy import stats
import json
import os
from pathlib import Path

# Helper function to load data files
def load_data_file(filename):
    for file_path in data_files:
        if os.path.basename(file_path) == filename:
            if filename.endswith('.csv'):
                return pd.read_csv(file_path)
            elif filename.endswith('.json'):
                with open(file_path, 'r') as f:
                    return json.load(f)
            elif filename.endswith(('.xlsx', '.xls')):
                return pd.read_excel(file_path)
    raise FileNotFoundError(f"Data file {filename} not found")

# Helper function to save results
def save_result(key, value):
    results[key] = value
""", analysis_globals)
            
            # Execute user script
            exec(script_content, analysis_globals)
            
            # Extract results
            results = analysis_globals.get('results', {})
            
            return {
                "success": True,
                "results": results,
                "files_processed": len(data_files),
                "execution_time": 1.0  # TODO: Track actual execution time
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}


# Global job manager instance
job_manager = RemoteJobManager()


@router.post("/submit-data")
async def submit_data_for_analysis(
    background_tasks: BackgroundTasks,
    script_content: str = Form(...),
    parameters: str = Form(default="{}"),
    analysis_type: str = Form(default="python"),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Submit data files and analysis script for remote processing
    
    This endpoint allows users to upload data files along with analysis code
    and get results back without exposing the raw data.
    """
    
    # Validate inputs
    if not files:
        raise HTTPException(status_code=400, detail="At least one data file is required")
    
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 files allowed per submission")
    
    # Parse parameters
    try:
        params = json.loads(parameters)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in parameters")
    
    # Validate script security
    from .security import validate_script_security
    security_check = validate_script_security(script_content, analysis_type)
    if not security_check["is_safe"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Script failed security validation: {security_check['warnings']}"
        )
    
    # Validate uploaded files
    for file in files:
        if file.size > 100 * 1024 * 1024:  # 100MB limit
            raise HTTPException(
                status_code=400, 
                detail=f"File {file.filename} exceeds 100MB limit"
            )
    
    # Create job record
    job_id = str(uuid.uuid4())
    script_hash = hashlib.sha256(script_content.encode()).hexdigest()
    
    # Find or create a default data catalog for remote submissions
    data_catalog = db.query(DataCatalog).filter(
        DataCatalog.name == "remote_submissions"
    ).first()
    
    if not data_catalog:
        data_catalog = DataCatalog(
            name="remote_submissions",
            description="Remote data submissions for analysis",
            data_type="mixed",
            access_level="private",
            total_records=0
        )
        db.add(data_catalog)
        db.commit()
        db.refresh(data_catalog)
    
    job = Job(
        job_id=job_id,
        requester_node_id=1,  # Default node
        executor_node_id=1,
        data_catalog_id=data_catalog.id,
        script_type=analysis_type,
        script_content=script_content,
        script_hash=script_hash,
        parameters=params,
        filters={"remote_submission": True},
        status=JobStatus.QUEUED
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Start background processing
    background_tasks.add_task(
        process_remote_job, job.id, files, script_content, params
    )
    
    return {
        "job_id": job_id,
        "status": "submitted",
        "message": "Data submitted for analysis. Use the job_id to check results.",
        "files_received": [f.filename for f in files],
        "estimated_processing_time": "1-5 minutes"
    }


async def process_remote_job(job_id: int, files: List[UploadFile], 
                           script_content: str, parameters: Dict[str, Any]):
    """Background task to process remote job"""
    from .database import SessionLocal
    db = SessionLocal()
    try:
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return
        
        # Update job status
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        db.commit()
        
        # Process the job
        result = await job_manager.process_data_submission(
            job.job_id, files, script_content, parameters
        )
        
        # Update job with results
        if result["success"]:
            job.status = JobStatus.COMPLETED
            job.result_data = result["results"]
            job.execution_time = result.get("execution_time", 0)
            job.records_processed = result.get("files_processed", 0)
        else:
            job.status = JobStatus.FAILED
            job.error_message = result["error"]
        
        job.completed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        logger.error(f"Error in background job processing: {e}")
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


@router.get("/job/{job_id}/status")
async def get_remote_job_status(job_id: str, db: Session = Depends(get_db)):
    """Get the status of a remote job"""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    response = {
        "job_id": job_id,
        "status": job.status,
        "submitted_at": job.submitted_at.isoformat(),
        "progress": job.progress
    }
    
    if job.started_at:
        response["started_at"] = job.started_at.isoformat()
    
    if job.completed_at:
        response["completed_at"] = job.completed_at.isoformat()
        response["execution_time"] = job.execution_time
    
    if job.status == JobStatus.COMPLETED:
        response["results_available"] = True
    elif job.status == JobStatus.FAILED:
        response["error"] = job.error_message
    
    return response


@router.get("/job/{job_id}/results")
async def get_remote_job_results(job_id: str, db: Session = Depends(get_db)):
    """Get the results of a completed remote job"""
    job = db.query(Job).filter(Job.job_id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400, 
            detail=f"Job is not completed. Current status: {job.status}"
        )
    
    # Privacy check
    if (job.records_processed and 
        job.records_processed < settings.min_cohort_size):
        return {
            "job_id": job_id,
            "status": "blocked",
            "message": f"Results blocked: cohort size < {settings.min_cohort_size}",
            "min_cohort_size": settings.min_cohort_size
        }
    
    return {
        "job_id": job_id,
        "status": "completed",
        "results": job.result_data,
        "execution_time": job.execution_time,
        "records_processed": job.records_processed,
        "completed_at": job.completed_at.isoformat()
    }


@router.post("/quick-analysis")
async def quick_analysis(
    background_tasks: BackgroundTasks,
    data: dict,
    analysis_script: str,
    parameters: Optional[Dict[str, Any]] = None
):
    """
    Quick analysis endpoint for JSON data (no file upload required)
    
    Useful for simple analyses where data can be sent as JSON
    """
    
    # Validate data size
    data_str = json.dumps(data)
    if len(data_str) > 10 * 1024 * 1024:  # 10MB limit for JSON
        raise HTTPException(status_code=400, detail="Data too large (max 10MB for JSON)")
    
    # Create job ID
    job_id = str(uuid.uuid4())
    
    # Execute analysis directly
    try:
        # Create analysis environment
        analysis_globals = {
            'data': data,
            'parameters': parameters or {},
            'results': {}
        }
        
        # Import common libraries
        exec("""
import pandas as pd
import numpy as np
from scipy import stats
import json

# Convert data to DataFrame if it's a list of records
if isinstance(data, list) and len(data) > 0 and isinstance(data[0], dict):
    df = pd.DataFrame(data)
else:
    df = None

# Helper function to save results
def save_result(key, value):
    results[key] = value
""", analysis_globals)
        
        # Execute user script
        exec(analysis_script, analysis_globals)
        
        # Extract results
        results = analysis_globals.get('results', {})
        
        return {
            "job_id": job_id,
            "status": "completed",
            "results": results,
            "execution_time": 0.1,
            "records_processed": len(data) if isinstance(data, list) else 1
        }
        
    except Exception as e:
        return {
            "job_id": job_id,
            "status": "failed",
            "error": str(e)
        }


@router.get("/analysis-templates")
async def get_analysis_templates():
    """Get pre-built analysis templates for common tasks"""
    
    templates = {
        "descriptive_stats": {
            "name": "Descriptive Statistics",
            "description": "Calculate basic descriptive statistics for numerical columns",
            "script": """
# Descriptive statistics analysis
if df is not None:
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    stats_result = {}
    
    for col in numeric_cols:
        stats_result[col] = {
            'mean': float(df[col].mean()),
            'median': float(df[col].median()),
            'std': float(df[col].std()),
            'min': float(df[col].min()),
            'max': float(df[col].max()),
            'count': int(df[col].count())
        }
    
    save_result('descriptive_stats', stats_result)
    save_result('total_records', len(df))
else:
    save_result('error', 'No tabular data provided')
""",
            "parameters": {},
            "data_format": "List of dictionaries (records)"
        },
        
        "correlation_analysis": {
            "name": "Correlation Analysis",
            "description": "Calculate correlation matrix for numerical variables",
            "script": """
# Correlation analysis
if df is not None:
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    if len(numeric_cols) >= 2:
        corr_matrix = df[numeric_cols].corr()
        
        # Convert to serializable format
        corr_dict = {}
        for i, col1 in enumerate(numeric_cols):
            corr_dict[col1] = {}
            for j, col2 in enumerate(numeric_cols):
                corr_dict[col1][col2] = float(corr_matrix.iloc[i, j])
        
        save_result('correlation_matrix', corr_dict)
        save_result('variables_analyzed', list(numeric_cols))
    else:
        save_result('error', 'Need at least 2 numerical variables for correlation')
else:
    save_result('error', 'No tabular data provided')
""",
            "parameters": {},
            "data_format": "List of dictionaries (records)"
        },
        
        "group_comparison": {
            "name": "Group Comparison",
            "description": "Compare groups using t-test or ANOVA",
            "script": """
# Group comparison analysis
group_col = parameters.get('group_column', 'group')
value_col = parameters.get('value_column', 'value')

if df is not None and group_col in df.columns and value_col in df.columns:
    groups = df[group_col].unique()
    
    if len(groups) == 2:
        # Two-sample t-test
        group1_data = df[df[group_col] == groups[0]][value_col]
        group2_data = df[df[group_col] == groups[1]][value_col]
        
        t_stat, p_value = stats.ttest_ind(group1_data, group2_data)
        
        save_result('test_type', 'two_sample_t_test')
        save_result('t_statistic', float(t_stat))
        save_result('p_value', float(p_value))
        save_result('group1_mean', float(group1_data.mean()))
        save_result('group2_mean', float(group2_data.mean()))
        save_result('significant', p_value < 0.05)
        
    elif len(groups) > 2:
        # One-way ANOVA
        group_data = [df[df[group_col] == group][value_col] for group in groups]
        f_stat, p_value = stats.f_oneway(*group_data)
        
        save_result('test_type', 'one_way_anova')
        save_result('f_statistic', float(f_stat))
        save_result('p_value', float(p_value))
        save_result('groups', list(groups))
        save_result('significant', p_value < 0.05)
    
    else:
        save_result('error', 'Need at least 2 groups for comparison')
else:
    save_result('error', f'Required columns not found: {group_col}, {value_col}')
""",
            "parameters": {
                "group_column": "Name of the grouping variable column",
                "value_column": "Name of the value/measurement column"
            },
            "data_format": "List of dictionaries with group and value columns"
        }
    }
    
    return {"templates": templates}


@router.websocket("/job/{job_id}/stream")
async def stream_job_progress(websocket, job_id: str):
    """WebSocket endpoint for real-time job progress updates"""
    await websocket.accept()
    
    try:
        while True:
            # Check job status
            from .database import SessionLocal
            db_session = SessionLocal()
            job = db_session.query(Job).filter(Job.job_id == job_id).first()
            db_session.close()
            
            if not job:
                await websocket.send_json({"error": "Job not found"})
                break
            
            # Send status update
            status_update = {
                "job_id": job_id,
                "status": job.status,
                "progress": job.progress,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            if job.status == JobStatus.COMPLETED:
                status_update["results_available"] = True
            elif job.status == JobStatus.FAILED:
                status_update["error"] = job.error_message
            
            await websocket.send_json(status_update)
            
            # Break if job is finished
            if job.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
                break
            
            # Wait before next update
            await asyncio.sleep(2)
            
    except Exception as e:
        logger.error(f"WebSocket error for job {job_id}: {e}")
    finally:
        await websocket.close()