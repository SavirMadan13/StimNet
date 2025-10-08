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


@router.post("/execute-script")
async def execute_script(
    background_tasks: BackgroundTasks,
    script_content: str = Form(...),
    script_type: str = Form(default="python"),
    parameters: str = Form(default="{}"),
    data: Optional[str] = Form(default=None),
    timeout: int = Form(default=300),
    files: Optional[List[UploadFile]] = File(default=None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Execute arbitrary scripts with optional data input
    
    This endpoint allows users to submit scripts for execution with:
    - Script code in various languages (Python, R, shell, etc.)
    - Optional data files or JSON data
    - Parameters for the script
    - Configurable timeout and resource limits
    """
    
    # Validate script type
    supported_types = ["python", "r", "shell", "bash", "nodejs", "custom"]
    if script_type not in supported_types:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported script type. Supported: {supported_types}"
        )
    
    # Parse parameters
    try:
        params = json.loads(parameters) if parameters else {}
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in parameters")
    
    # Parse data if provided
    input_data = None
    if data:
        try:
            input_data = json.loads(data)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in data field")
    
    # Validate script security
    from .security import validate_script_security
    security_check = validate_script_security(script_content, script_type)
    if not security_check["is_safe"]:
        raise HTTPException(
            status_code=400, 
            detail=f"Script failed security validation: {security_check['warnings']}"
        )
    
    # Validate uploaded files if any
    uploaded_files_info = []
    if files:
        if len(files) > 20:
            raise HTTPException(status_code=400, detail="Maximum 20 files allowed")
        
        for file in files:
            if file.size > 500 * 1024 * 1024:  # 500MB limit per file
                raise HTTPException(
                    status_code=400, 
                    detail=f"File {file.filename} exceeds 500MB limit"
                )
            uploaded_files_info.append({
                "filename": file.filename,
                "size": file.size,
                "content_type": file.content_type
            })
    
    # Create execution job
    job_id = str(uuid.uuid4())
    script_hash = hashlib.sha256(script_content.encode()).hexdigest()
    
    # Find or create script execution catalog
    data_catalog = db.query(DataCatalog).filter(
        DataCatalog.name == "script_execution"
    ).first()
    
    if not data_catalog:
        data_catalog = DataCatalog(
            name="script_execution",
            description="Arbitrary script execution environment",
            data_type="executable",
            access_level="private",
            total_records=0
        )
        db.add(data_catalog)
        db.commit()
        db.refresh(data_catalog)
    
    # Prepare job parameters
    job_params = {
        **params,
        "execution_type": "script",
        "timeout": timeout,
        "input_data": input_data,
        "uploaded_files": uploaded_files_info
    }
    
    job = Job(
        job_id=job_id,
        requester_node_id=1,  # Default node
        executor_node_id=1,
        data_catalog_id=data_catalog.id,
        script_type=script_type,
        script_content=script_content,
        script_hash=script_hash,
        parameters=job_params,
        filters={"script_execution": True, "timeout": timeout},
        status=JobStatus.QUEUED
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Start background execution
    background_tasks.add_task(
        execute_script_job, job.id, files or [], input_data, params, timeout
    )
    
    return {
        "job_id": job_id,
        "status": "submitted",
        "message": "Script submitted for execution",
        "script_type": script_type,
        "estimated_completion": f"{timeout} seconds maximum",
        "files_uploaded": len(files) if files else 0
    }


async def execute_script_job(job_id: int, files: List[UploadFile], 
                           input_data: Optional[Dict[str, Any]], 
                           parameters: Dict[str, Any], timeout: int):
    """Background task to execute arbitrary scripts"""
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
        
        # Execute the script
        executor = ScriptExecutor()
        result = await executor.execute_script(
            job.job_id, job.script_content, job.script_type, 
            files, input_data, parameters, timeout
        )
        
        # Update job with results
        if result["success"]:
            job.status = JobStatus.COMPLETED
            job.result_data = result["output"]
            job.execution_time = result.get("execution_time", 0)
            job.records_processed = result.get("records_processed", 0)
        else:
            job.status = JobStatus.FAILED
            job.error_message = result["error"]
        
        job.completed_at = datetime.utcnow()
        db.commit()
        
    except Exception as e:
        logger.error(f"Error in script execution job: {e}")
        if job:
            job.status = JobStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
    finally:
        db.close()


class ScriptExecutor:
    """Enhanced script executor for arbitrary code execution"""
    
    def __init__(self):
        self.supported_types = {
            "python": self._execute_python,
            "r": self._execute_r,
            "shell": self._execute_shell,
            "bash": self._execute_shell,
            "nodejs": self._execute_nodejs,
            "custom": self._execute_custom
        }
    
    async def execute_script(self, job_id: str, script_content: str, script_type: str,
                           files: List[UploadFile], input_data: Optional[Dict[str, Any]],
                           parameters: Dict[str, Any], timeout: int):
        """Execute script with proper sandboxing and resource limits"""
        
        start_time = time.time()
        
        try:
            # Create secure workspace
            workspace = tempfile.mkdtemp(prefix=f"script_exec_{job_id}_")
            
            # Save uploaded files
            uploaded_file_paths = []
            if files:
                for file in files:
                    file_path = os.path.join(workspace, file.filename)
                    with open(file_path, "wb") as f:
                        content = await file.read()
                        f.write(content)
                    uploaded_file_paths.append(file_path)
            
            # Prepare execution environment
            env_data = {
                "job_id": job_id,
                "workspace": workspace,
                "parameters": parameters,
                "input_data": input_data,
                "uploaded_files": uploaded_file_paths,
                "timeout": timeout
            }
            
            # Execute based on script type
            if script_type in self.supported_types:
                result = await self.supported_types[script_type](
                    script_content, workspace, env_data, timeout
                )
            else:
                result = {
                    "success": False,
                    "error": f"Unsupported script type: {script_type}"
                }
            
            # Add execution time
            result["execution_time"] = time.time() - start_time
            
            # Cleanup workspace
            import shutil
            shutil.rmtree(workspace, ignore_errors=True)
            
            return result
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Script execution failed: {str(e)}",
                "execution_time": time.time() - start_time
            }
    
    async def _execute_python(self, script_content: str, workspace: str, 
                            env_data: Dict[str, Any], timeout: int):
        """Execute Python script in sandboxed environment"""
        
        try:
            # Create Python execution script
            python_wrapper = f'''
import sys
import os
import json
import time
from datetime import datetime
import traceback

# Set up environment
workspace = "{workspace}"
os.chdir(workspace)

# Load environment data
job_id = "{env_data["job_id"]}"
parameters = {json.dumps(env_data["parameters"])}
input_data = {json.dumps(env_data["input_data"])}
uploaded_files = {json.dumps(env_data["uploaded_files"])}

# Initialize results
results = {{}}
output_lines = []

# Capture print output
class OutputCapture:
    def write(self, text):
        output_lines.append(text)
        sys.__stdout__.write(text)
    
    def flush(self):
        sys.__stdout__.flush()

sys.stdout = OutputCapture()

# Helper functions for scripts
def save_result(key, value):
    """Save a result value"""
    results[key] = value

def load_file(filename):
    """Load an uploaded file"""
    for file_path in uploaded_files:
        if os.path.basename(file_path) == filename:
            if filename.endswith('.json'):
                with open(file_path, 'r') as f:
                    return json.load(f)
            elif filename.endswith('.csv'):
                import pandas as pd
                return pd.read_csv(file_path)
            else:
                with open(file_path, 'r') as f:
                    return f.read()
    raise FileNotFoundError(f"File {{filename}} not found")

def save_file(filename, content):
    """Save content to a file in workspace"""
    file_path = os.path.join(workspace, filename)
    if isinstance(content, str):
        with open(file_path, 'w') as f:
            f.write(content)
    else:
        with open(file_path, 'wb') as f:
            f.write(content)
    return file_path

# Execute user script
try:
    start_time = time.time()
    
    # Import common libraries
    import pandas as pd
    import numpy as np
    from scipy import stats
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    
    # Execute the user script
    exec("""{script_content}""")
    
    execution_time = time.time() - start_time
    
    # Prepare final output
    final_output = {{
        "success": True,
        "results": results,
        "output": "".join(output_lines),
        "execution_time": execution_time,
        "files_in_workspace": os.listdir(workspace)
    }}
    
except Exception as e:
    final_output = {{
        "success": False,
        "error": str(e),
        "traceback": traceback.format_exc(),
        "output": "".join(output_lines)
    }}

# Write output
with open(os.path.join(workspace, "execution_result.json"), "w") as f:
    json.dump(final_output, f, indent=2, default=str)
'''
            
            # Write wrapper script
            wrapper_path = os.path.join(workspace, "wrapper.py")
            with open(wrapper_path, "w") as f:
                f.write(python_wrapper)
            
            # Execute with Docker for security
            import docker
            client = docker.from_env()
            
            try:
                container = client.containers.run(
                    settings.execution_image_python,
                    ["python", "/workspace/wrapper.py"],
                    volumes={
                        workspace: {'bind': '/workspace', 'mode': 'rw'},
                        os.path.abspath(settings.data_root): {'bind': '/data', 'mode': 'ro'}
                    },
                    working_dir='/workspace',
                    network_mode='none',  # No network access
                    mem_limit='512m',
                    cpu_count=2,
                    remove=False,
                    detach=True,
                    environment={'PYTHONPATH': '/workspace', 'DATA_DIR': '/data'}
                )
                
                # Wait for completion with timeout
                result = container.wait(timeout=timeout)
                logs = container.logs().decode('utf-8')
                container.remove()
                
                # Read execution result
                result_path = os.path.join(workspace, "execution_result.json")
                if os.path.exists(result_path):
                    with open(result_path, "r") as f:
                        execution_result = json.load(f)
                else:
                    execution_result = {
                        "success": False,
                        "error": "No execution result file generated",
                        "logs": logs
                    }
                
                return execution_result
                
            except docker.errors.ContainerError as e:
                return {
                    "success": False,
                    "error": f"Container execution failed: {e}"
                }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Python execution setup failed: {e}"
            }
    
    async def _execute_r(self, script_content: str, workspace: str, 
                        env_data: Dict[str, Any], timeout: int):
        """Execute R script in sandboxed environment"""
        
        try:
            # Create R execution script
            r_wrapper = f'''
# Set up environment
setwd("{workspace}")

# Load environment data
job_id <- "{env_data["job_id"]}"
parameters <- {json.dumps(env_data["parameters"])}
input_data <- {json.dumps(env_data["input_data"])}
uploaded_files <- {json.dumps(env_data["uploaded_files"])}

# Initialize results
results <- list()

# Helper functions
save_result <- function(key, value) {{
    results[[key]] <<- value
}}

load_csv_file <- function(filename) {{
    for(file_path in uploaded_files) {{
        if(basename(file_path) == filename) {{
            return(read.csv(file_path))
        }}
    }}
    stop(paste("File", filename, "not found"))
}}

# Execute user script
tryCatch({{
    {script_content}
    
    # Save results
    jsonlite::write_json(list(
        success = TRUE,
        results = results,
        message = "R script executed successfully"
    ), "execution_result.json", auto_unbox = TRUE)
    
}}, error = function(e) {{
    jsonlite::write_json(list(
        success = FALSE,
        error = as.character(e),
        message = "R script execution failed"
    ), "execution_result.json", auto_unbox = TRUE)
}})
'''
            
            # Write R script
            r_script_path = os.path.join(workspace, "script.R")
            with open(r_script_path, "w") as f:
                f.write(r_wrapper)
            
            # Execute with Docker
            import docker
            client = docker.from_env()
            
            container = client.containers.run(
                "r-base:4.3.0",
                ["Rscript", "/workspace/script.R"],
                volumes={workspace: {'bind': '/workspace', 'mode': 'rw'}},
                working_dir='/workspace',
                network_mode='none',
                mem_limit='512m',
                cpu_count=2,
                remove=False,
                detach=True
            )
            
            result = container.wait(timeout=timeout)
            logs = container.logs().decode('utf-8')
            container.remove()
            
            # Read result
            result_path = os.path.join(workspace, "execution_result.json")
            if os.path.exists(result_path):
                with open(result_path, "r") as f:
                    return json.load(f)
            else:
                return {
                    "success": False,
                    "error": "R script execution failed",
                    "logs": logs
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"R execution failed: {e}"
            }
    
    async def _execute_shell(self, script_content: str, workspace: str, 
                           env_data: Dict[str, Any], timeout: int):
        """Execute shell script in sandboxed environment"""
        
        try:
            # Create shell script
            shell_script = f'''#!/bin/bash
set -e

# Set up environment
cd "{workspace}"
export JOB_ID="{env_data["job_id"]}"
export WORKSPACE="{workspace}"

# Create environment files
cat > env_data.json << 'EOF'
{json.dumps(env_data)}
EOF

# Execute user script
{script_content}

# Create result file
cat > execution_result.json << 'EOF'
{{
    "success": true,
    "message": "Shell script executed successfully",
    "workspace_files": $(ls -la)
}}
EOF
'''
            
            script_path = os.path.join(workspace, "script.sh")
            with open(script_path, "w") as f:
                f.write(shell_script)
            
            os.chmod(script_path, 0o755)
            
            # Execute with Docker
            import docker
            client = docker.from_env()
            
            container = client.containers.run(
                "ubuntu:22.04",
                ["/bin/bash", "/workspace/script.sh"],
                volumes={workspace: {'bind': '/workspace', 'mode': 'rw'}},
                working_dir='/workspace',
                network_mode='none',
                mem_limit='256m',
                cpu_count=1,
                remove=False,
                detach=True
            )
            
            result = container.wait(timeout=timeout)
            logs = container.logs().decode('utf-8')
            container.remove()
            
            # Read result
            result_path = os.path.join(workspace, "execution_result.json")
            if os.path.exists(result_path):
                with open(result_path, "r") as f:
                    execution_result = json.load(f)
                execution_result["logs"] = logs
                return execution_result
            else:
                return {
                    "success": result['StatusCode'] == 0,
                    "error": "Shell script execution completed" if result['StatusCode'] == 0 else "Shell script failed",
                    "logs": logs,
                    "exit_code": result['StatusCode']
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Shell execution failed: {e}"
            }
    
    async def _execute_nodejs(self, script_content: str, workspace: str, 
                            env_data: Dict[str, Any], timeout: int):
        """Execute Node.js script in sandboxed environment"""
        
        try:
            # Create Node.js wrapper
            js_wrapper = f'''
const fs = require('fs');
const path = require('path');

// Set up environment
process.chdir("{workspace}");

const envData = {json.dumps(env_data)};
const jobId = envData.job_id;
const parameters = envData.parameters;
const inputData = envData.input_data;
const uploadedFiles = envData.uploaded_files;

// Initialize results
const results = {{}};

// Helper functions
function saveResult(key, value) {{
    results[key] = value;
}}

function loadFile(filename) {{
    for (const filePath of uploadedFiles) {{
        if (path.basename(filePath) === filename) {{
            if (filename.endsWith('.json')) {{
                return JSON.parse(fs.readFileSync(filePath, 'utf8'));
            }} else {{
                return fs.readFileSync(filePath, 'utf8');
            }}
        }}
    }}
    throw new Error(`File ${{filename}} not found`);
}}

// Execute user script
try {{
    {script_content}
    
    // Save results
    fs.writeFileSync('execution_result.json', JSON.stringify({{
        success: true,
        results: results,
        message: "Node.js script executed successfully"
    }}, null, 2));
    
}} catch (error) {{
    fs.writeFileSync('execution_result.json', JSON.stringify({{
        success: false,
        error: error.message,
        stack: error.stack
    }}, null, 2));
}}
'''
            
            # Write Node.js script
            js_script_path = os.path.join(workspace, "script.js")
            with open(js_script_path, "w") as f:
                f.write(js_wrapper)
            
            # Execute with Docker
            import docker
            client = docker.from_env()
            
            container = client.containers.run(
                "node:18-alpine",
                ["node", "/workspace/script.js"],
                volumes={workspace: {'bind': '/workspace', 'mode': 'rw'}},
                working_dir='/workspace',
                network_mode='none',
                mem_limit='512m',
                cpu_count=2,
                remove=False,
                detach=True
            )
            
            result = container.wait(timeout=timeout)
            logs = container.logs().decode('utf-8')
            container.remove()
            
            # Read result
            result_path = os.path.join(workspace, "execution_result.json")
            if os.path.exists(result_path):
                with open(result_path, "r") as f:
                    return json.load(f)
            else:
                return {
                    "success": False,
                    "error": "Node.js script execution failed",
                    "logs": logs
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Node.js execution failed: {e}"
            }
    
    async def _execute_custom(self, script_content: str, workspace: str, 
                            env_data: Dict[str, Any], timeout: int):
        """Execute custom script (user defines execution method)"""
        
        return {
            "success": False,
            "error": "Custom script execution not yet implemented"
        }


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