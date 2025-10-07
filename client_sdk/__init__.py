"""
Client SDK for Distributed Data Access and Remote Execution Framework
"""

from .client import DistributedClient
from .models import NodeInfo, DataCatalog, JobStatus, JobResult

__version__ = "1.0.0"
__all__ = ["DistributedClient", "NodeInfo", "DataCatalog", "JobStatus", "JobResult"]