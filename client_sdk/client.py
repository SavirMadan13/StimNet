"""
Client SDK for interacting with distributed nodes
"""
import httpx
import json
import asyncio
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging

from .models import NodeInfo, DataCatalog, JobSubmission, JobResult

logger = logging.getLogger(__name__)


class DistributedClient:
    """Client for interacting with distributed data nodes"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, verify_ssl: bool = True):
        """
        Initialize the client
        
        Args:
            base_url: Base URL of the node server (e.g., "https://node1.example.com")
            api_key: Optional API key for authentication
            verify_ssl: Whether to verify SSL certificates
        """
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.verify_ssl = verify_ssl
        self.session = None
        self.auth_token = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = httpx.AsyncClient(verify=self.verify_ssl)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.aclose()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {"Content-Type": "application/json"}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        elif self.api_key:
            headers["X-API-Key"] = self.api_key
        return headers
    
    async def authenticate(self, username: str, password: str) -> bool:
        """
        Authenticate with the node server
        
        Args:
            username: Username
            password: Password
            
        Returns:
            True if authentication successful
        """
        if not self.session:
            self.session = httpx.AsyncClient(verify=self.verify_ssl)
        
        try:
            response = await self.session.post(
                f"{self.base_url}/api/v1/auth/token",
                data={"username": username, "password": password}
            )
            response.raise_for_status()
            
            data = response.json()
            self.auth_token = data["access_token"]
            return True
            
        except httpx.HTTPError as e:
            logger.error(f"Authentication failed: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """Check node health status"""
        if not self.session:
            self.session = httpx.AsyncClient(verify=self.verify_ssl)
        
        response = await self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    async def discover_node(self) -> NodeInfo:
        """Discover node capabilities and data catalogs"""
        if not self.session:
            self.session = httpx.AsyncClient(verify=self.verify_ssl)
        
        response = await self.session.get(
            f"{self.base_url}/api/v1/discovery",
            headers=self._get_headers()
        )
        response.raise_for_status()
        
        data = response.json()
        return NodeInfo(
            nodes=data["nodes"],
            data_catalogs=[DataCatalog(**catalog) for catalog in data["data_catalogs"]]
        )
    
    async def list_data_catalogs(self, access_level: Optional[str] = None) -> List[DataCatalog]:
        """List available data catalogs"""
        if not self.session:
            self.session = httpx.AsyncClient(verify=self.verify_ssl)
        
        params = {}
        if access_level:
            params["access_level"] = access_level
        
        response = await self.session.get(
            f"{self.base_url}/api/v1/data-catalogs",
            params=params,
            headers=self._get_headers()
        )
        response.raise_for_status()
        
        data = response.json()
        return [DataCatalog(**catalog) for catalog in data]
    
    async def get_data_catalog(self, catalog_id: int) -> DataCatalog:
        """Get specific data catalog details"""
        if not self.session:
            self.session = httpx.AsyncClient(verify=self.verify_ssl)
        
        response = await self.session.get(
            f"{self.base_url}/api/v1/data-catalogs/{catalog_id}",
            headers=self._get_headers()
        )
        response.raise_for_status()
        
        data = response.json()
        return DataCatalog(**data)
    
    async def submit_job(self, job: JobSubmission) -> str:
        """
        Submit a job for execution
        
        Args:
            job: Job submission details
            
        Returns:
            Job ID
        """
        if not self.session:
            self.session = httpx.AsyncClient(verify=self.verify_ssl)
        
        payload = {
            "target_node_id": job.target_node_id,
            "data_catalog_name": job.data_catalog_name,
            "script_type": job.script_type,
            "script_content": job.script_content,
            "parameters": job.parameters or {},
            "filters": job.filters or {}
        }
        
        response = await self.session.post(
            f"{self.base_url}/api/v1/jobs",
            json=payload,
            headers=self._get_headers()
        )
        response.raise_for_status()
        
        data = response.json()
        return data["job_id"]
    
    async def submit_script_file(self, script_path: str, **kwargs) -> str:
        """
        Submit a script file for execution
        
        Args:
            script_path: Path to script file
            **kwargs: Additional job parameters
            
        Returns:
            Job ID
        """
        script_path = Path(script_path)
        
        # Determine script type from extension
        script_type_map = {
            '.py': 'python',
            '.r': 'r',
            '.sql': 'sql',
            '.ipynb': 'jupyter'
        }
        
        script_type = script_type_map.get(script_path.suffix.lower())
        if not script_type:
            raise ValueError(f"Unsupported script type: {script_path.suffix}")
        
        # Read script content
        with open(script_path, 'r') as f:
            script_content = f.read()
        
        job = JobSubmission(
            script_type=script_type,
            script_content=script_content,
            **kwargs
        )
        
        return await self.submit_job(job)
    
    async def get_job_status(self, job_id: str) -> JobResult:
        """Get job status and results"""
        if not self.session:
            self.session = httpx.AsyncClient(verify=self.verify_ssl)
        
        response = await self.session.get(
            f"{self.base_url}/api/v1/jobs/{job_id}",
            headers=self._get_headers()
        )
        response.raise_for_status()
        
        data = response.json()
        return JobResult(**data)
    
    async def wait_for_job(self, job_id: str, timeout: int = 3600, poll_interval: int = 5) -> JobResult:
        """
        Wait for job completion
        
        Args:
            job_id: Job ID to wait for
            timeout: Maximum time to wait in seconds
            poll_interval: How often to check status in seconds
            
        Returns:
            Final job result
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            result = await self.get_job_status(job_id)
            
            if result.status in ["completed", "failed", "cancelled", "blocked"]:
                return result
            
            # Check timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")
            
            await asyncio.sleep(poll_interval)
    
    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job"""
        if not self.session:
            self.session = httpx.AsyncClient(verify=self.verify_ssl)
        
        try:
            response = await self.session.delete(
                f"{self.base_url}/api/v1/jobs/{job_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return True
        except httpx.HTTPError:
            return False
    
    async def list_jobs(self, status: Optional[str] = None, limit: int = 100) -> List[JobResult]:
        """List jobs with optional status filter"""
        if not self.session:
            self.session = httpx.AsyncClient(verify=self.verify_ssl)
        
        params = {"limit": limit}
        if status:
            params["status"] = status
        
        response = await self.session.get(
            f"{self.base_url}/api/v1/jobs",
            params=params,
            headers=self._get_headers()
        )
        response.raise_for_status()
        
        data = response.json()
        return [JobResult(**job) for job in data]


# Synchronous wrapper for easier use
class SyncDistributedClient:
    """Synchronous wrapper for DistributedClient"""
    
    def __init__(self, *args, **kwargs):
        self.client = DistributedClient(*args, **kwargs)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        asyncio.run(self.client.__aexit__(exc_type, exc_val, exc_tb))
    
    def authenticate(self, username: str, password: str) -> bool:
        return asyncio.run(self._run_async(self.client.authenticate(username, password)))
    
    def health_check(self) -> Dict[str, Any]:
        return asyncio.run(self._run_async(self.client.health_check()))
    
    def discover_node(self) -> NodeInfo:
        return asyncio.run(self._run_async(self.client.discover_node()))
    
    def list_data_catalogs(self, access_level: Optional[str] = None) -> List[DataCatalog]:
        return asyncio.run(self._run_async(self.client.list_data_catalogs(access_level)))
    
    def submit_job(self, job: JobSubmission) -> str:
        return asyncio.run(self._run_async(self.client.submit_job(job)))
    
    def submit_script_file(self, script_path: str, **kwargs) -> str:
        return asyncio.run(self._run_async(self.client.submit_script_file(script_path, **kwargs)))
    
    def get_job_status(self, job_id: str) -> JobResult:
        return asyncio.run(self._run_async(self.client.get_job_status(job_id)))
    
    def wait_for_job(self, job_id: str, timeout: int = 3600, poll_interval: int = 5) -> JobResult:
        return asyncio.run(self._run_async(self.client.wait_for_job(job_id, timeout, poll_interval)))
    
    def cancel_job(self, job_id: str) -> bool:
        return asyncio.run(self._run_async(self.client.cancel_job(job_id)))
    
    def list_jobs(self, status: Optional[str] = None, limit: int = 100) -> List[JobResult]:
        return asyncio.run(self._run_async(self.client.list_jobs(status, limit)))
    
    async def _run_async(self, coro):
        """Run async method with proper session management"""
        async with self.client as client:
            return await coro
