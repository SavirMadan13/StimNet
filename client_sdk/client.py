"""
Main client for interacting with distributed nodes
"""
import httpx
import asyncio
import time
import logging
from typing import List, Optional, Dict, Any, Union
from urllib.parse import urljoin

from .models import (
    NodeInfo, DataCatalog, JobResult, JobSubmissionRequest, 
    NodeDiscovery, HealthStatus, JobStatus, ScriptType
)

logger = logging.getLogger(__name__)


class DistributedClient:
    """Client for interacting with distributed data nodes"""
    
    def __init__(
        self,
        default_timeout: float = 30.0,
        verify_ssl: bool = True,
        max_retries: int = 3
    ):
        self.default_timeout = default_timeout
        self.verify_ssl = verify_ssl
        self.max_retries = max_retries
        self.known_nodes: Dict[str, str] = {}  # node_id -> endpoint_url
        self.auth_tokens: Dict[str, str] = {}  # node_id -> token
        
        # HTTP client configuration
        self.client_config = {
            "timeout": httpx.Timeout(default_timeout),
            "verify": verify_ssl,
            "follow_redirects": True
        }
    
    def add_node(self, node_id: str, endpoint_url: str, auth_token: Optional[str] = None):
        """Add a known node to the client"""
        self.known_nodes[node_id] = endpoint_url.rstrip('/')
        if auth_token:
            self.auth_tokens[node_id] = auth_token
        logger.info(f"Added node {node_id} at {endpoint_url}")
    
    def authenticate(self, node_id: str, username: str, password: str) -> bool:
        """Authenticate with a node and store the token"""
        if node_id not in self.known_nodes:
            raise ValueError(f"Unknown node: {node_id}")
        
        endpoint = self.known_nodes[node_id]
        
        try:
            with httpx.Client(**self.client_config) as client:
                response = client.post(
                    urljoin(endpoint, "/api/v1/auth/token"),
                    data={"username": username, "password": password}
                )
                response.raise_for_status()
                
                token_data = response.json()
                self.auth_tokens[node_id] = token_data["access_token"]
                logger.info(f"Successfully authenticated with node {node_id}")
                return True
                
        except httpx.HTTPError as e:
            logger.error(f"Authentication failed for node {node_id}: {e}")
            return False
    
    def _get_headers(self, node_id: str) -> Dict[str, str]:
        """Get headers including authentication for a node"""
        headers = {"Content-Type": "application/json"}
        if node_id in self.auth_tokens:
            headers["Authorization"] = f"Bearer {self.auth_tokens[node_id]}"
        return headers
    
    async def discover_node(self, node_id: str) -> NodeDiscovery:
        """Discover a node's capabilities and data catalogs"""
        if node_id not in self.known_nodes:
            raise ValueError(f"Unknown node: {node_id}")
        
        endpoint = self.known_nodes[node_id]
        headers = self._get_headers(node_id)
        
        async with httpx.AsyncClient(**self.client_config) as client:
            response = await client.get(
                urljoin(endpoint, "/api/v1/discovery"),
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            return NodeDiscovery(**data)
    
    async def get_health_status(self, node_id: str) -> HealthStatus:
        """Get health status of a node"""
        if node_id not in self.known_nodes:
            raise ValueError(f"Unknown node: {node_id}")
        
        endpoint = self.known_nodes[node_id]
        
        async with httpx.AsyncClient(**self.client_config) as client:
            response = await client.get(urljoin(endpoint, "/health"))
            response.raise_for_status()
            
            data = response.json()
            return HealthStatus(**data)
    
    async def list_data_catalogs(self, node_id: str, access_level: Optional[str] = None) -> List[DataCatalog]:
        """List available data catalogs on a node"""
        if node_id not in self.known_nodes:
            raise ValueError(f"Unknown node: {node_id}")
        
        endpoint = self.known_nodes[node_id]
        headers = self._get_headers(node_id)
        
        params = {}
        if access_level:
            params["access_level"] = access_level
        
        async with httpx.AsyncClient(**self.client_config) as client:
            response = await client.get(
                urljoin(endpoint, "/api/v1/data-catalogs"),
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            return [DataCatalog(**item) for item in data]
    
    async def get_data_catalog(self, node_id: str, catalog_id: int) -> DataCatalog:
        """Get details of a specific data catalog"""
        if node_id not in self.known_nodes:
            raise ValueError(f"Unknown node: {node_id}")
        
        endpoint = self.known_nodes[node_id]
        headers = self._get_headers(node_id)
        
        async with httpx.AsyncClient(**self.client_config) as client:
            response = await client.get(
                urljoin(endpoint, f"/api/v1/data-catalogs/{catalog_id}"),
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            return DataCatalog(**data)
    
    async def submit_job(
        self,
        node_id: str,
        data_catalog_name: str,
        script_type: Union[ScriptType, str],
        script_content: str,
        parameters: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> str:
        """Submit a job for execution on a remote node"""
        if node_id not in self.known_nodes:
            raise ValueError(f"Unknown node: {node_id}")
        
        endpoint = self.known_nodes[node_id]
        headers = self._get_headers(node_id)
        
        # Ensure script_type is a string
        if isinstance(script_type, ScriptType):
            script_type = script_type.value
        
        job_request = JobSubmissionRequest(
            target_node_id=node_id,
            data_catalog_name=data_catalog_name,
            script_type=script_type,
            script_content=script_content,
            parameters=parameters or {},
            filters=filters or {}
        )
        
        async with httpx.AsyncClient(**self.client_config) as client:
            response = await client.post(
                urljoin(endpoint, "/api/v1/jobs"),
                headers=headers,
                json=job_request.dict()
            )
            response.raise_for_status()
            
            data = response.json()
            return data["job_id"]
    
    async def get_job_status(self, node_id: str, job_id: str) -> JobResult:
        """Get status and results of a job"""
        if node_id not in self.known_nodes:
            raise ValueError(f"Unknown node: {node_id}")
        
        endpoint = self.known_nodes[node_id]
        headers = self._get_headers(node_id)
        
        async with httpx.AsyncClient(**self.client_config) as client:
            response = await client.get(
                urljoin(endpoint, f"/api/v1/jobs/{job_id}"),
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            return JobResult(**data)
    
    async def wait_for_job_completion(
        self,
        node_id: str,
        job_id: str,
        poll_interval: float = 5.0,
        timeout: Optional[float] = None
    ) -> JobResult:
        """Wait for a job to complete, polling for status"""
        start_time = time.time()
        
        while True:
            result = await self.get_job_status(node_id, job_id)
            
            if result.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.BLOCKED]:
                return result
            
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Job {job_id} did not complete within {timeout} seconds")
            
            await asyncio.sleep(poll_interval)
    
    async def cancel_job(self, node_id: str, job_id: str) -> bool:
        """Cancel a running job"""
        if node_id not in self.known_nodes:
            raise ValueError(f"Unknown node: {node_id}")
        
        endpoint = self.known_nodes[node_id]
        headers = self._get_headers(node_id)
        
        try:
            async with httpx.AsyncClient(**self.client_config) as client:
                response = await client.delete(
                    urljoin(endpoint, f"/api/v1/jobs/{job_id}"),
                    headers=headers
                )
                response.raise_for_status()
                return True
        except httpx.HTTPError as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return False
    
    async def list_jobs(
        self,
        node_id: str,
        status: Optional[JobStatus] = None,
        limit: int = 100
    ) -> List[JobResult]:
        """List jobs on a node"""
        if node_id not in self.known_nodes:
            raise ValueError(f"Unknown node: {node_id}")
        
        endpoint = self.known_nodes[node_id]
        headers = self._get_headers(node_id)
        
        params = {"limit": limit}
        if status:
            params["status"] = status.value
        
        async with httpx.AsyncClient(**self.client_config) as client:
            response = await client.get(
                urljoin(endpoint, "/api/v1/jobs"),
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            return [JobResult(**item) for item in data]
    
    # Convenience methods
    async def run_python_script(
        self,
        node_id: str,
        data_catalog_name: str,
        script_content: str,
        parameters: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        wait_for_completion: bool = True,
        timeout: Optional[float] = None
    ) -> JobResult:
        """Run a Python script and optionally wait for completion"""
        job_id = await self.submit_job(
            node_id, data_catalog_name, ScriptType.PYTHON,
            script_content, parameters, filters
        )
        
        if wait_for_completion:
            return await self.wait_for_job_completion(node_id, job_id, timeout=timeout)
        else:
            return await self.get_job_status(node_id, job_id)
    
    async def run_r_script(
        self,
        node_id: str,
        data_catalog_name: str,
        script_content: str,
        parameters: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        wait_for_completion: bool = True,
        timeout: Optional[float] = None
    ) -> JobResult:
        """Run an R script and optionally wait for completion"""
        job_id = await self.submit_job(
            node_id, data_catalog_name, ScriptType.R,
            script_content, parameters, filters
        )
        
        if wait_for_completion:
            return await self.wait_for_job_completion(node_id, job_id, timeout=timeout)
        else:
            return await self.get_job_status(node_id, job_id)
    
    async def run_sql_query(
        self,
        node_id: str,
        data_catalog_name: str,
        query: str,
        parameters: Optional[Dict[str, Any]] = None,
        filters: Optional[Dict[str, Any]] = None,
        wait_for_completion: bool = True,
        timeout: Optional[float] = None
    ) -> JobResult:
        """Run a SQL query and optionally wait for completion"""
        job_id = await self.submit_job(
            node_id, data_catalog_name, ScriptType.SQL,
            query, parameters, filters
        )
        
        if wait_for_completion:
            return await self.wait_for_job_completion(node_id, job_id, timeout=timeout)
        else:
            return await self.get_job_status(node_id, job_id)
    
    # Batch operations
    async def discover_all_nodes(self) -> Dict[str, NodeDiscovery]:
        """Discover all known nodes"""
        results = {}
        tasks = []
        
        for node_id in self.known_nodes:
            tasks.append(self.discover_node(node_id))
        
        discoveries = await asyncio.gather(*tasks, return_exceptions=True)
        
        for node_id, discovery in zip(self.known_nodes.keys(), discoveries):
            if isinstance(discovery, Exception):
                logger.error(f"Failed to discover node {node_id}: {discovery}")
            else:
                results[node_id] = discovery
        
        return results
    
    async def get_all_health_statuses(self) -> Dict[str, HealthStatus]:
        """Get health status of all known nodes"""
        results = {}
        tasks = []
        
        for node_id in self.known_nodes:
            tasks.append(self.get_health_status(node_id))
        
        statuses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for node_id, status in zip(self.known_nodes.keys(), statuses):
            if isinstance(status, Exception):
                logger.error(f"Failed to get health status for node {node_id}: {status}")
            else:
                results[node_id] = status
        
        return results