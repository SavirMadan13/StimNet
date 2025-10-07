"""
Client SDK for Distributed Data Access Framework
"""

from .client import DistributedClient
from .models import NodeInfo, DataCatalog, JobSubmission, JobResult

__version__ = "1.0.0"
__all__ = ["DistributedClient", "NodeInfo", "DataCatalog", "JobSubmission", "JobResult"]
