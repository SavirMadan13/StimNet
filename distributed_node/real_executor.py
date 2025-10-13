"""
Real script execution engine (non-demo mode)
"""
import os
import sys
import tempfile
import subprocess
import json
import time
import hashlib
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class RealScriptExecutor:
    """Execute scripts with real data processing"""
    
    def __init__(self, data_root: str = "./data", work_dir: str = "./work"):
        self.data_root = os.path.abspath(data_root)
        self.work_dir = os.path.abspath(work_dir)
        os.makedirs(self.work_dir, exist_ok=True)
    
    def execute_script(
        self, 
        script_content: str, 
        script_type: str,
        job_id: str,
        parameters: Dict[str, Any] = None,
        filters: Dict[str, Any] = None,
        data_catalog_id: int = None
    ) -> Dict[str, Any]:
        """Execute a script and return results"""
        
        start_time = time.time()
        
        try:
            # Create temporary directory for this job
            job_dir = os.path.join(self.work_dir, job_id)
            os.makedirs(job_dir, exist_ok=True)
            
            # Write script to file
            script_extension = self._get_script_extension(script_type)
            script_path = os.path.join(job_dir, f"script.{script_extension}")
            
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Copy data_loader.py to job directory so scripts can import it
            import shutil
            data_loader_src = os.path.join(os.path.dirname(__file__), "data_loader.py")
            data_loader_dst = os.path.join(job_dir, "data_loader.py")
            if os.path.exists(data_loader_src):
                shutil.copy2(data_loader_src, data_loader_dst)
                logger.info(f"Copied data_loader.py to job directory")
            
            # Create job configuration
            config_path = os.path.join(job_dir, "job_config.json")
            job_config = {
                "job_id": job_id,
                "script_type": script_type,
                "parameters": parameters or {},
                "filters": filters or {},
                "data_catalog_id": data_catalog_id
            }
            
            with open(config_path, 'w') as f:
                json.dump(job_config, f, indent=2)
            
            # Set up execution environment
            output_path = os.path.join(job_dir, "output.json")
            env = os.environ.copy()
            env.update({
                'DATA_ROOT': self.data_root,
                'JOB_CONFIG': config_path,
                'OUTPUT_FILE': output_path,
                'MIN_COHORT_SIZE': os.environ.get('MIN_COHORT_SIZE', '5'),
                'PYTHONPATH': os.path.dirname(os.path.dirname(__file__))
            })
            
            # Execute the script
            logger.info(f"Executing {script_type} script for job {job_id}")
            
            if script_type.lower() == "python":
                result = self._execute_python_script(script_path, job_dir, env)
            elif script_type.lower() == "r":
                result = self._execute_r_script(script_path, job_dir, env)
            else:
                raise ValueError(f"Unsupported script type: {script_type}")
            
            execution_time = time.time() - start_time
            
            # Read output file if it exists
            if os.path.exists(output_path):
                with open(output_path, 'r') as f:
                    output_data = json.load(f)
                
                return {
                    "success": True,
                    "data": output_data,
                    "execution_time": execution_time,
                    "records_processed": output_data.get("sample_size", 0),
                    "stdout": result.get("stdout", ""),
                    "stderr": result.get("stderr", "")
                }
            else:
                return {
                    "success": True,
                    "data": {
                        "message": "Script executed successfully",
                        "no_output_file": True,
                        "stdout": result.get("stdout", "")
                    },
                    "execution_time": execution_time,
                    "records_processed": 0
                }
                
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Script execution failed for job {job_id}: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "execution_time": execution_time,
                "data": {"error": str(e), "failed": True}
            }
        
        finally:
            # Cleanup (optional - keep for debugging)
            # shutil.rmtree(job_dir, ignore_errors=True)
            pass
    
    def _execute_python_script(self, script_path: str, job_dir: str, env: Dict[str, str]) -> Dict[str, Any]:
        """Execute a Python script"""
        
        try:
            result = subprocess.run([
                sys.executable, script_path
            ],
            cwd=job_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            raise Exception("Script execution timed out (5 minutes)")
        except Exception as e:
            raise Exception(f"Python execution error: {e}")
    
    def _execute_r_script(self, script_path: str, job_dir: str, env: Dict[str, str]) -> Dict[str, Any]:
        """Execute an R script"""
        
        try:
            result = subprocess.run([
                "Rscript", script_path
            ],
            cwd=job_dir,
            env=env,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
        except subprocess.TimeoutExpired:
            raise Exception("R script execution timed out (5 minutes)")
        except FileNotFoundError:
            raise Exception("R not found. Please install R to execute R scripts.")
        except Exception as e:
            raise Exception(f"R execution error: {e}")
    
    def _get_script_extension(self, script_type: str) -> str:
        """Get file extension for script type"""
        extensions = {
            "python": "py",
            "r": "r",
            "sql": "sql",
            "jupyter": "ipynb"
        }
        return extensions.get(script_type.lower(), "txt")
    
    def validate_script_security(self, script_content: str, script_type: str) -> Dict[str, Any]:
        """Basic security validation"""
        
        validation = {
            "is_safe": True,
            "warnings": [],
            "blocked_patterns": []
        }
        
        # Define dangerous patterns
        dangerous_patterns = {
            "python": [
                "import os",
                "import subprocess", 
                "import sys",
                "__import__",
                "exec(",
                "eval(",
                "open(",
                "file(",
                "input(",
                "raw_input("
            ],
            "r": [
                "system(",
                "shell(",
                "file(",
                "download"
            ]
        }
        
        script_lower = script_content.lower()
        patterns = dangerous_patterns.get(script_type.lower(), [])
        
        for pattern in patterns:
            if pattern.lower() in script_lower:
                validation["blocked_patterns"].append(pattern)
                validation["warnings"].append(f"Potentially dangerous pattern: {pattern}")
        
        # For demo purposes, allow some patterns but warn
        high_risk_patterns = ["subprocess", "os.system", "exec(", "eval("]
        for pattern in high_risk_patterns:
            if pattern.lower() in script_lower:
                validation["is_safe"] = False
                break
        
        return validation
