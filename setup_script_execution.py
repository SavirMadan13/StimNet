#!/usr/bin/env python3
"""
Setup script for the Script Execution Framework
This script ensures all necessary dependencies and Docker images are available
"""
import subprocess
import sys
import os
import docker
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} completed successfully")
            return True
        else:
            print(f"❌ {description} failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} failed: {e}")
        return False


def check_docker():
    """Check if Docker is available and running"""
    print("🐳 Checking Docker availability...")
    try:
        client = docker.from_env()
        client.ping()
        print("✅ Docker is running and accessible")
        return True
    except Exception as e:
        print(f"❌ Docker is not available: {e}")
        print("Please install Docker and ensure it's running")
        return False


def pull_docker_images():
    """Pull necessary Docker images"""
    images = [
        ("python:3.11-slim", "Base Python execution environment"),
        ("r-base:4.3.0", "R execution environment"),
        ("ubuntu:22.04", "Shell script environment"),
        ("node:18-alpine", "Node.js execution environment")
    ]
    
    client = docker.from_env()
    
    for image, description in images:
        print(f"📦 Pulling {description} ({image})...")
        try:
            client.images.pull(image)
            print(f"✅ {description} pulled successfully")
        except Exception as e:
            print(f"❌ Failed to pull {image}: {e}")
            return False
    
    return True


def build_python_execution_image():
    """Build the local Python execution image with scientific/NIfTI stack"""
    try:
        print("🏗️  Building local Python execution image (local/research-python:latest)...")
        dockerfile = os.path.join("docker", "Dockerfile.python")
        if not os.path.exists(dockerfile):
            print("⚠️  Dockerfile not found at docker/Dockerfile.python; skipping build")
            return False
        client = docker.from_env()
        image, logs = client.images.build(
            path=os.path.dirname(dockerfile),
            dockerfile=os.path.basename(dockerfile),
            tag="local/research-python:latest",
            pull=True
        )
        # Stream build logs summary
        print("✅ Built image:", image.tags)
        return True
    except Exception as e:
        print(f"❌ Failed to build Python execution image: {e}")
        return False


def install_python_dependencies():
    """Install required Python packages"""
    requirements = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "httpx",
        "docker",
        "pandas",
        "numpy",
        "scipy",
        "matplotlib",
        "seaborn",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-multipart",
        "nibabel",
        "nilearn"
    ]
    
    print("📦 Installing Python dependencies...")
    for package in requirements:
        if not run_command(f"pip install {package}", f"Installing {package}"):
            return False
    
    return True


def setup_directories():
    """Create necessary directories"""
    directories = [
        "data/script_execution",
        "logs",
        "temp"
    ]
    
    print("📁 Setting up directories...")
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")
    
    return True


def create_env_file():
    """Create environment configuration file"""
    env_content = """# Script Execution Framework Configuration

# Database
DATABASE_URL=sqlite:///./distributed_node.db

# Security
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Node Configuration
NODE_ID=node-1
INSTITUTION_NAME=Local Institution
HOST=0.0.0.0
PORT=8000

# Execution Limits
MAX_EXECUTION_TIME=300
MAX_MEMORY_MB=512
MAX_CPU_CORES=2
MIN_COHORT_SIZE=5

# Docker Images
EXECUTION_IMAGE_PYTHON=local/research-python:latest
EXECUTION_IMAGE_R=r-base:4.3.0

# Allowed Script Types
ALLOWED_SCRIPT_TYPES=python,r,shell,bash,nodejs

# Data Root
DATA_ROOT=./data

# Logging
LOG_LEVEL=INFO
DEBUG=true
"""
    
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env configuration file...")
        with open(env_file, "w") as f:
            f.write(env_content)
        print("✅ .env file created")
    else:
        print("ℹ️  .env file already exists")
    
    return True


def test_setup():
    """Test the setup by running a simple script execution"""
    print("🧪 Testing script execution setup...")
    
    try:
        # Import the client SDK
        sys.path.insert(0, ".")
        from client_sdk import DistributedClient
        
        print("✅ Client SDK import successful")
        
        # Test Docker connectivity
        client = docker.from_env()
        
        # Run a simple Python container test
        container = client.containers.run(
            "python:3.11-slim",
            ["python", "-c", "print('Hello from Docker!')"],
            remove=True,
            capture_output=True,
            text=True
        )
        
        print("✅ Docker container execution test successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Setup test failed: {e}")
        return False


def main():
    """Main setup function"""
    print("🚀 Script Execution Framework Setup")
    print("=" * 50)
    
    success = True
    
    # Check prerequisites
    if not check_docker():
        success = False
    
    # Install Python dependencies
    if success and not install_python_dependencies():
        success = False
    
    # Pull Docker images
    if success and not pull_docker_images():
        success = False
    
    # Setup directories
    if success and not setup_directories():
        success = False
    
    # Create configuration
    if success and not create_env_file():
        success = False
    
    # Test setup
    if success and not test_setup():
        success = False
    
    print("\n" + "=" * 50)
    
    if success:
        print("🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Review and customize the .env file")
        print("2. Start the server: python run_server.py")
        print("3. Run examples: python examples/simple_script_execution.py")
        print("4. View API docs at: http://localhost:8000/docs")
    else:
        print("❌ Setup failed. Please resolve the issues above and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()