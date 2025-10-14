"""
Job execution engine for running scripts in sandboxed environments
"""
import asyncio
import docker
import json
import os
import tempfile
import time
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from contextlib import asynccontextmanager

from .config import settings
from .database import engine
from .models import Job, JobStatus
from .security import validate_script_security, SecurityValidator

logger = logging.getLogger(__name__)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class JobExecutor:
    """Handles job execution in sandboxed Docker containers"""
    
    def __init__(self):
        self.docker_client = None
        self.job_queue = asyncio.Queue()
        self.running_jobs = {}
        self.worker_task = None
        self.is_running = False
    
    async def start(self):
        """Start the job executor"""
        try:
            self.docker_client = docker.from_env()
            self.is_running = True
            self.worker_task = asyncio.create_task(self._worker())
            logger.info("Job executor started with Docker support")
        except Exception as e:
            logger.warning(f"Docker not available, running in local mode: {e}")
            self.docker_client = None
            self.is_running = True
            self.worker_task = asyncio.create_task(self._worker())
            logger.info("Job executor started in local mode (no Docker)")
    
    async def stop(self):
        """Stop the job executor"""
        self.is_running = False
        if self.worker_task:
            self.worker_task.cancel()
            try:
                await self.worker_task
            except asyncio.CancelledError:
                pass
        
        # Cancel running jobs
        for job_id in list(self.running_jobs.keys()):
            await self.cancel_job(job_id)
        
        if self.docker_client:
            self.docker_client.close()
        
        logger.info("Job executor stopped")
    
    async def submit_job(self, job_id: int):
        """Submit a job for execution"""
        await self.job_queue.put(job_id)
        logger.info(f"Job {job_id} submitted to queue")
    
    async def cancel_job(self, job_id: int):
        """Cancel a running job"""
        if job_id in self.running_jobs:
            container = self.running_jobs[job_id]
            try:
                container.stop(timeout=10)
                container.remove()
                del self.running_jobs[job_id]
                logger.info(f"Job {job_id} cancelled")
            except Exception as e:
                logger.error(f"Error cancelling job {job_id}: {e}")
    
    async def _worker(self):
        """Main worker loop for processing jobs"""
        while self.is_running:
            try:
                # Get next job from queue (with timeout to allow graceful shutdown)
                job_id = await asyncio.wait_for(self.job_queue.get(), timeout=1.0)
                await self._execute_job(job_id)
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                await asyncio.sleep(1)
    
    async def _execute_job(self, job_id: int):
        """Execute a single job"""
        db = SessionLocal()
        try:
            job = db.query(Job).filter(Job.id == job_id).first()
            if not job:
                logger.error(f"Job {job_id} not found")
                return
            
            logger.info(f"Starting execution of job {job.job_id}")
            
            # Update job status
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            db.commit()
            
            # Validate script security
            security_check = validate_script_security(job.script_content, job.script_type)
            if not security_check["is_safe"]:
                job.status = JobStatus.FAILED
                job.error_message = f"Script failed security validation: {security_check['warnings']}"
                job.completed_at = datetime.utcnow()
                db.commit()
                return
            
            # Execute the job
            result = await self._run_in_container(job, db)
            
            # Update job with results
            if result["success"]:
                job.status = JobStatus.COMPLETED
                job.result_data = result["data"]
                job.execution_time = result["execution_time"]
                job.memory_used_mb = result.get("memory_used_mb")
                job.records_processed = result.get("records_processed")
            else:
                job.status = JobStatus.FAILED
                job.error_message = result["error"]
            
            job.completed_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Job {job.job_id} completed with status {job.status}")
            
        except Exception as e:
            logger.error(f"Error executing job {job_id}: {e}")
            if job:
                job.status = JobStatus.FAILED
                job.error_message = str(e)
                job.completed_at = datetime.utcnow()
                db.commit()
        finally:
            db.close()
    
    async def _run_in_container(self, job: Job, db) -> Dict[str, Any]:
        """Run job script in a Docker container or locally if Docker unavailable"""
        start_time = time.time()
        
        # If Docker is not available, run locally
        if self.docker_client is None:
            return await self._run_locally(job, db)
        
        try:
            # Create temporary directory for job files
            with tempfile.TemporaryDirectory() as temp_dir:
                # Prepare script and data files
                script_path = os.path.join(temp_dir, f"script.{self._get_file_extension(job.script_type)}")
                with open(script_path, 'w') as f:
                    f.write(job.script_content)
                
                # Prepare job configuration
                config_path = os.path.join(temp_dir, "job_config.json")
                job_config = {
                    "job_id": job.job_id,
                    "script_type": job.script_type,
                    "parameters": job.parameters,
                    "filters": job.filters,
                    "data_catalog_id": job.data_catalog_id
                }
                with open(config_path, 'w') as f:
                    json.dump(job_config, f)
                
                # Prepare output directory
                output_path = os.path.join(temp_dir, "output.json")
                
                # Select appropriate Docker image
                image = self._get_docker_image(job.script_type)
                
                # Prepare container command
                command = self._get_container_command(job.script_type, script_path, config_path, output_path)
                
                # Run container
                container = self.docker_client.containers.run(
                    image,
                    command,
                    volumes={
                        temp_dir: {'bind': '/workspace', 'mode': 'rw'},
                        settings.data_root: {'bind': '/data', 'mode': 'ro'}
                    },
                    working_dir='/workspace',
                    network_mode='none',  # No network access
                    mem_limit=f"{settings.max_memory_mb}m",
                    cpu_count=settings.max_cpu_cores,
                    remove=False,
                    detach=True,
                    environment={
                        'PYTHONPATH': '/workspace',
                        'DATA_ROOT': '/data',
                        'JOB_CONFIG': '/workspace/job_config.json',
                        'OUTPUT_FILE': '/workspace/output.json'
                    }
                )
                
                # Store container reference for potential cancellation
                self.running_jobs[job.id] = container
                
                try:
                    # Wait for container to complete
                    result = container.wait(timeout=settings.max_execution_time)
                    
                    # Get container logs
                    logs = container.logs().decode('utf-8')
                    
                    # Get container stats
                    stats = container.stats(stream=False)
                    memory_used_mb = stats['memory_stats'].get('usage', 0) / (1024 * 1024)
                    
                    # Clean up container
                    container.remove()
                    if job.id in self.running_jobs:
                        del self.running_jobs[job.id]
                    
                    execution_time = time.time() - start_time
                    
                    # Check exit code
                    if result['StatusCode'] != 0:
                        return {
                            "success": False,
                            "error": f"Script execution failed with exit code {result['StatusCode']}\nLogs: {logs}",
                            "execution_time": execution_time
                        }
                    
                    # Read output file
                    if os.path.exists(output_path):
                        with open(output_path, 'r') as f:
                            output_data = json.load(f)
                    else:
                        output_data = {"message": "No output file generated"}
                    
                    return {
                        "success": True,
                        "data": output_data,
                        "execution_time": execution_time,
                        "memory_used_mb": memory_used_mb,
                        "records_processed": output_data.get("records_processed"),
                        "logs": logs
                    }
                
                except docker.errors.ContainerError as e:
                    return {
                        "success": False,
                        "error": f"Container execution error: {e}",
                        "execution_time": time.time() - start_time
                    }
                
                except Exception as e:
                    # Clean up container on error
                    try:
                        container.stop(timeout=10)
                        container.remove()
                    except:
                        pass
                    
                    if job.id in self.running_jobs:
                        del self.running_jobs[job.id]
                    
                    raise e
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Job execution error: {e}",
                "execution_time": time.time() - start_time
            }
    
    def _get_file_extension(self, script_type: str) -> str:
        """Get file extension for script type"""
        extensions = {
            "python": "py",
            "r": "r",
            "sql": "sql",
            "jupyter": "ipynb"
        }
        return extensions.get(script_type.lower(), "txt")
    
    def _get_docker_image(self, script_type: str) -> str:
        """Get Docker image for script type"""
        images = {
            "python": settings.execution_image_python,
            "r": settings.execution_image_r,
            "sql": "postgres:13",  # For SQL execution
            "jupyter": "jupyter/scipy-notebook:latest"
        }
        return images.get(script_type.lower(), settings.execution_image_python)
    
    def _get_container_command(self, script_type: str, script_path: str, config_path: str, output_path: str) -> list:
        """Get container command for script type"""
        commands = {
            "python": ["python", "/workspace/script.py"],
            "r": ["Rscript", "/workspace/script.r"],
            "sql": ["psql", "-f", "/workspace/script.sql"],
            "jupyter": ["jupyter", "nbconvert", "--execute", "/workspace/script.ipynb"]
        }
        return commands.get(script_type.lower(), ["python", "/workspace/script.py"])
    
    async def _run_locally(self, job: Job, db) -> Dict[str, Any]:
        """Run job script locally (fallback when Docker is not available)"""
        start_time = time.time()
        
        try:
            # Create temporary directory for job files
            with tempfile.TemporaryDirectory() as temp_dir:
                # Prepare script file
                script_path = os.path.join(temp_dir, f"script.{self._get_file_extension(job.script_type)}")
                with open(script_path, 'w') as f:
                    f.write(job.script_content)
                
                # Prepare job configuration
                config_path = os.path.join(temp_dir, "job_config.json")
                job_config = {
                    "job_id": job.job_id,
                    "script_type": job.script_type,
                    "parameters": job.parameters or {},
                    "filters": job.filters or {},
                    "data_catalog_id": job.data_catalog_id
                }
                with open(config_path, 'w') as f:
                    json.dump(job_config, f)
                
                # Prepare output file
                output_path = os.path.join(temp_dir, "output.json")
                
                # Set up environment
                env = os.environ.copy()
                env.update({
                    'PYTHONPATH': temp_dir,
                    'DATA_ROOT': settings.data_root,
                    'JOB_CONFIG': config_path,
                    'OUTPUT_FILE': output_path
                })
                
                # For now, only support Python scripts locally
                if job.script_type.lower() == 'python':
                    # Create a simple wrapper script
                    wrapper_script = os.path.join(temp_dir, "wrapper.py")
                    with open(wrapper_script, 'w') as f:
                        f.write(PYTHON_WRAPPER_SCRIPT)
                    
                    # Run the wrapper script
                    import subprocess
                    result = subprocess.run(
                        ['python', wrapper_script],
                        cwd=temp_dir,
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=settings.max_execution_time
                    )
                    
                    execution_time = time.time() - start_time
                    
                    # Check exit code
                    if result.returncode != 0:
                        return {
                            "success": False,
                            "error": f"Script execution failed with exit code {result.returncode}\nStderr: {result.stderr}",
                            "execution_time": execution_time
                        }
                    
                    # Read output file
                    if os.path.exists(output_path):
                        with open(output_path, 'r') as f:
                            output_data = json.load(f)
                    else:
                        output_data = {"message": "No output file generated"}
                    
                    return {
                        "success": True,
                        "data": output_data,
                        "execution_time": execution_time,
                        "memory_used_mb": 0,  # Not available in local mode
                        "records_processed": output_data.get("records_processed"),
                        "logs": result.stdout
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Script type {job.script_type} not supported in local mode",
                        "execution_time": time.time() - start_time
                    }
        
        except Exception as e:
            logger.error(f"Error running job locally: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time
            }


# Execution wrapper script for Python jobs
PYTHON_WRAPPER_SCRIPT = '''
import json
import sys
import os
import traceback
from datetime import datetime

# Load job configuration
with open(os.environ["JOB_CONFIG"], "r") as f:
    config = json.load(f)

# Set up environment
job_id = config["job_id"]
parameters = config["parameters"]
filters = config["filters"]
data_catalog_id = config["data_catalog_id"]

# Initialize result
result = {
    "job_id": job_id,
    "status": "running",
    "started_at": datetime.utcnow().isoformat(),
    "records_processed": 0,
    "data": None,
    "error": None
}

try:
    # Import required libraries
    import pandas as pd
    import numpy as np
    from scipy import stats
    import matplotlib
    matplotlib.use('Agg')  # Use non-interactive backend
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    # Make parameters available to user script
    globals().update(parameters)
    
    # Execute user script
    exec(open("/workspace/script.py").read())
    
    # If the script defines a 'result' variable, use it
    if 'result' in locals():
        result["data"] = locals()["result"]
    else:
        result["data"] = {"message": "Script executed successfully"}
    
    result["status"] = "completed"
    result["completed_at"] = datetime.utcnow().isoformat()

except Exception as e:
    result["status"] = "failed"
    result["error"] = str(e)
    result["traceback"] = traceback.format_exc()
    result["completed_at"] = datetime.utcnow().isoformat()

# Write result
with open(os.environ["OUTPUT_FILE"], "w") as f:
    json.dump(result, f, indent=2)
'''
