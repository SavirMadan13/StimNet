"""
Security and authentication module
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
import hashlib
import logging

from .config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token security
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """Verify and decode a JWT token"""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user from token"""
    return verify_token(credentials.credentials)


def validate_script_security(script_content: str, script_type: str) -> Dict[str, Any]:
    """
    Validate script for security issues
    Returns dict with validation results
    """
    validation_result = {
        "is_safe": True,
        "warnings": [],
        "blocked_patterns": [],
        "risk_level": "low"
    }
    
    # Define dangerous patterns by script type
    dangerous_patterns = {
        "python": [
            "__import__",
            "exec(",
            "eval(",
            "compile(",
            "open(",
            "file(",
            "input(",
            "raw_input(",
            "subprocess",
            "os.system",
            "os.popen",
            "os.spawn",
            "shutil.rmtree",
            "socket",
            "urllib",
            "requests",
            "http",
            "ftp",
            "telnet",
            "pickle",
            "marshal",
            "ctypes",
            "sys.exit",
            "quit(",
            "exit(",
        ],
        "r": [
            "system(",
            "shell(",
            "file(",
            "url(",
            "download",
            "install.packages",
            "source(",
            "load(",
            "library(",  # Could be dangerous depending on library
            "require(",
            "quit(",
            "q(",
        ],
        "sql": [
            "DROP",
            "DELETE",
            "UPDATE",
            "INSERT",
            "CREATE",
            "ALTER",
            "TRUNCATE",
            "EXEC",
            "EXECUTE",
            "xp_",
            "sp_",
            "--",
            "/*",
            "UNION",
            "INFORMATION_SCHEMA",
            "sys.",
        ],
        "shell": [
            "rm -rf",
            "rm -f",
            "rmdir",
            "dd if=",
            "mkfs",
            "fdisk",
            "mount",
            "umount",
            "sudo",
            "su ",
            "passwd",
            "useradd",
            "userdel",
            "usermod",
            "chmod 777",
            "chown",
            "curl",
            "wget",
            "nc ",
            "netcat",
            "telnet",
            "ssh",
            "scp",
            "rsync",
            "crontab",
            "systemctl",
            "service",
            "iptables",
            "ufw",
            "kill -9",
            "killall",
            "pkill",
            "nohup",
            "screen",
            "tmux",
            "/etc/",
            "/proc/",
            "/sys/",
            "/dev/",
            "> /dev/",
            "2>/dev/null",
            "&& rm",
            "; rm",
            "| rm",
        ],
        "bash": [
            "rm -rf",
            "rm -f",
            "rmdir",
            "dd if=",
            "mkfs",
            "fdisk",
            "mount",
            "umount",
            "sudo",
            "su ",
            "passwd",
            "useradd",
            "userdel",
            "usermod",
            "chmod 777",
            "chown",
            "curl",
            "wget",
            "nc ",
            "netcat",
            "telnet",
            "ssh",
            "scp",
            "rsync",
            "crontab",
            "systemctl",
            "service",
            "iptables",
            "ufw",
            "kill -9",
            "killall",
            "pkill",
            "nohup",
            "screen",
            "tmux",
            "/etc/",
            "/proc/",
            "/sys/",
            "/dev/",
            "> /dev/",
            "2>/dev/null",
            "&& rm",
            "; rm",
            "| rm",
        ],
        "nodejs": [
            "require('child_process')",
            "require('fs')",
            "require('net')",
            "require('http')",
            "require('https')",
            "require('url')",
            "require('os')",
            "require('cluster')",
            "require('crypto')",
            "require('dgram')",
            "require('dns')",
            "require('tls')",
            "require('vm')",
            "require('worker_threads')",
            "process.exit",
            "process.kill",
            "process.abort",
            "eval(",
            "Function(",
            "setTimeout(",
            "setInterval(",
            "setImmediate(",
            "global.",
            "__dirname",
            "__filename",
            "Buffer.",
            ".exec(",
            ".spawn(",
            ".fork(",
            ".unlink(",
            ".rmdir(",
            ".writeFile(",
            ".createWriteStream(",
        ],
        "custom": [
            # Generic dangerous patterns for unknown script types
            "system",
            "exec",
            "eval",
            "shell",
            "command",
            "process",
            "file",
            "network",
            "socket",
            "http",
            "url",
            "download",
            "upload",
            "delete",
            "remove",
            "kill",
            "exit",
            "quit",
        ]
    }
    
    script_lower = script_content.lower()
    patterns_to_check = dangerous_patterns.get(script_type.lower(), [])
    
    for pattern in patterns_to_check:
        if pattern.lower() in script_lower:
            validation_result["blocked_patterns"].append(pattern)
            validation_result["warnings"].append(f"Potentially dangerous pattern detected: {pattern}")
    
    # Determine risk level
    if len(validation_result["blocked_patterns"]) > 0:
        if any(p in ["DROP", "DELETE", "system(", "exec(", "eval("] for p in validation_result["blocked_patterns"]):
            validation_result["risk_level"] = "high"
            validation_result["is_safe"] = False
        elif len(validation_result["blocked_patterns"]) > 3:
            validation_result["risk_level"] = "medium"
        else:
            validation_result["risk_level"] = "low"
    
    # Additional checks
    if len(script_content) > 50000:  # 50KB limit
        validation_result["warnings"].append("Script is very large")
        validation_result["risk_level"] = "medium"
    
    # Check for excessive complexity (simple heuristic)
    if script_content.count('\n') > 1000:
        validation_result["warnings"].append("Script has many lines")
        validation_result["risk_level"] = "medium"
    
    return validation_result


def generate_script_hash(script_content: str) -> str:
    """Generate a hash for script content"""
    return hashlib.sha256(script_content.encode('utf-8')).hexdigest()


def check_node_permission(node_id: str, action: str, resource: str = None) -> bool:
    """
    Check if a node has permission to perform an action
    This is a basic implementation - extend as needed
    """
    # For now, allow all actions from trusted nodes
    if node_id in settings.trusted_nodes:
        return True
    
    # Basic permission logic
    allowed_actions = {
        "read_catalog": True,
        "submit_job": True,
        "read_job": True,
        "cancel_job": False,  # Only job owner can cancel
    }
    
    return allowed_actions.get(action, False)


def audit_log_action(
    action: str,
    node_id: str,
    details: Dict[str, Any] = None,
    user_info: Dict[str, Any] = None,
    ip_address: str = None
):
    """
    Log an action for audit purposes
    """
    if not settings.enable_audit_log:
        return
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat(),
        "action": action,
        "node_id": node_id,
        "details": details or {},
        "user_info": user_info or {},
        "ip_address": ip_address or "unknown"
    }
    
    try:
        with open(settings.audit_log_file, "a") as f:
            f.write(f"{log_entry}\n")
    except Exception as e:
        logger.error(f"Failed to write audit log: {e}")


class SecurityValidator:
    """Security validation utilities"""
    
    @staticmethod
    def validate_file_upload(file_content: bytes, filename: str) -> Dict[str, Any]:
        """Validate uploaded file for security"""
        result = {
            "is_safe": True,
            "warnings": [],
            "file_type": "unknown"
        }
        
        # Check file size
        if len(file_content) > 100 * 1024 * 1024:  # 100MB limit
            result["warnings"].append("File is very large")
            result["is_safe"] = False
        
        # Basic file type detection
        if filename.endswith(('.py', '.pyx', '.pyw')):
            result["file_type"] = "python"
        elif filename.endswith(('.r', '.R')):
            result["file_type"] = "r"
        elif filename.endswith(('.sql',)):
            result["file_type"] = "sql"
        elif filename.endswith(('.ipynb',)):
            result["file_type"] = "jupyter"
        
        # Check for binary content
        try:
            file_content.decode('utf-8')
        except UnicodeDecodeError:
            result["warnings"].append("File contains binary data")
            result["is_safe"] = False
        
        return result
    
    @staticmethod
    def sanitize_parameters(params: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize job parameters"""
        sanitized = {}
        
        for key, value in params.items():
            # Remove potentially dangerous keys
            if key.startswith('_') or key in ['__class__', '__module__', '__dict__']:
                continue
            
            # Limit string length
            if isinstance(value, str) and len(value) > 1000:
                value = value[:1000]
            
            # Limit list/dict size
            if isinstance(value, (list, dict)) and len(value) > 100:
                continue
            
            sanitized[key] = value
        
        return sanitized