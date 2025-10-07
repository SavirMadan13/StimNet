"""
Basic tests for the distributed framework
"""
import pytest
import asyncio
from unittest.mock import Mock, patch
from client_sdk import DistributedClient, ScriptType
from distributed_node.config import Settings
from distributed_node.models import DataCatalog, Job, JobStatus


def test_settings_creation():
    """Test that settings can be created with defaults"""
    settings = Settings()
    assert settings.app_name == "Distributed Node Server"
    assert settings.port == 8000
    assert settings.min_cohort_size == 10


def test_client_creation():
    """Test that client can be created"""
    client = DistributedClient()
    assert client.default_timeout == 30.0
    assert client.known_nodes == {}
    assert client.auth_tokens == {}


def test_client_add_node():
    """Test adding a node to the client"""
    client = DistributedClient()
    client.add_node("test_node", "http://localhost:8000")
    
    assert "test_node" in client.known_nodes
    assert client.known_nodes["test_node"] == "http://localhost:8000"


def test_client_add_node_with_auth():
    """Test adding a node with authentication token"""
    client = DistributedClient()
    client.add_node("test_node", "http://localhost:8000", "test_token")
    
    assert "test_node" in client.known_nodes
    assert "test_node" in client.auth_tokens
    assert client.auth_tokens["test_node"] == "test_token"


@pytest.mark.asyncio
async def test_client_discover_node_unknown():
    """Test discovering an unknown node raises error"""
    client = DistributedClient()
    
    with pytest.raises(ValueError, match="Unknown node"):
        await client.discover_node("unknown_node")


def test_job_status_enum():
    """Test job status enumeration"""
    assert JobStatus.QUEUED == "queued"
    assert JobStatus.RUNNING == "running" 
    assert JobStatus.COMPLETED == "completed"
    assert JobStatus.FAILED == "failed"
    assert JobStatus.CANCELLED == "cancelled"


def test_script_type_enum():
    """Test script type enumeration"""
    assert ScriptType.PYTHON == "python"
    assert ScriptType.R == "r"
    assert ScriptType.SQL == "sql"
    assert ScriptType.JUPYTER == "jupyter"


class TestDataCatalogManager:
    """Test data catalog management"""
    
    def test_import(self):
        """Test that data catalog manager can be imported"""
        from data_layer import DataCatalogManager
        manager = DataCatalogManager()
        assert manager is not None


class TestPrivacyManager:
    """Test privacy management"""
    
    def test_import(self):
        """Test that privacy manager can be imported"""
        from data_layer import PrivacyManager
        manager = PrivacyManager()
        assert manager.min_cohort_size == 10
        assert manager.enable_differential_privacy == False
    
    def test_cohort_size_check(self):
        """Test cohort size validation"""
        from data_layer import PrivacyManager
        manager = PrivacyManager(min_cohort_size=5)
        
        # Test with sufficient size
        result = manager.check_cohort_size(10)
        assert result["is_valid"] == True
        assert result["cohort_size"] == 10
        
        # Test with insufficient size
        result = manager.check_cohort_size(3)
        assert result["is_valid"] == False
        assert result["cohort_size"] == 3


class TestSecurity:
    """Test security functions"""
    
    def test_import(self):
        """Test that security module can be imported"""
        from distributed_node import security
        assert security is not None
    
    def test_password_hashing(self):
        """Test password hashing functions"""
        from distributed_node.security import get_password_hash, verify_password
        
        password = "test_password"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert verify_password(password, hashed) == True
        assert verify_password("wrong_password", hashed) == False
    
    def test_script_validation(self):
        """Test script security validation"""
        from distributed_node.security import validate_script_security
        
        # Safe script
        safe_script = "print('hello world')"
        result = validate_script_security(safe_script, "python")
        assert result["is_safe"] == True
        assert len(result["blocked_patterns"]) == 0
        
        # Dangerous script
        dangerous_script = "import os; os.system('rm -rf /')"
        result = validate_script_security(dangerous_script, "python")
        assert result["is_safe"] == False
        assert len(result["blocked_patterns"]) > 0


if __name__ == "__main__":
    pytest.main([__file__])