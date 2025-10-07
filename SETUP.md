# Distributed Data Access Framework - Setup Guide

This guide will help you set up and run the distributed data access and remote execution framework.

## Prerequisites

### System Requirements
- Python 3.9 or higher
- Docker and Docker Compose
- PostgreSQL (optional, SQLite used by default)
- Redis (optional, for production deployments)

### Installation

1. **Clone and navigate to the project:**
```bash
cd /Users/savirmadan/Development/StimNet
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install Docker** (if not already installed):
   - macOS: Download Docker Desktop from https://docker.com
   - Linux: Follow Docker installation guide for your distribution
   - Windows: Download Docker Desktop from https://docker.com

## Quick Start (Single Node)

### 1. Basic Setup

Create a `.env` file in the project root:
```bash
cat > .env << EOF
# Node Configuration
NODE_ID=node-1
NODE_NAME=My Research Node
INSTITUTION_NAME=My Institution

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production

# Database (SQLite for development)
DATABASE_URL=sqlite:///./distributed_node.db

# Data and execution settings
DATA_ROOT=./data
WORK_DIR=./work
MIN_COHORT_SIZE=5

# Logging
LOG_LEVEL=INFO
ENABLE_AUDIT_LOG=true
EOF
```

### 2. Prepare Data Directory

Create the data directory structure:
```bash
mkdir -p data/catalogs
mkdir -p work
```

### 3. Build Docker Images

Build the execution environment images:
```bash
# Python execution environment
docker build -t distributed-python:latest -f docker/Dockerfile.python .

# R execution environment  
docker build -t distributed-r:latest -f docker/Dockerfile.r .
```

### 4. Initialize Database

```bash
python -c "
from distributed_node.database import init_db
init_db()
print('Database initialized successfully')
"
```

### 5. Start the Node Server

```bash
python -m distributed_node.main
```

The server will start on `http://localhost:8000`. You can access the API documentation at `http://localhost:8000/docs`.

## Production Setup (Multi-Node)

### 1. Database Setup (PostgreSQL)

Install and configure PostgreSQL:
```bash
# Create database
createdb distributed_framework

# Update .env file
DATABASE_URL=postgresql://username:password@localhost/distributed_framework
```

### 2. Redis Setup (for job queuing)

Install and start Redis:
```bash
# macOS with Homebrew
brew install redis
brew services start redis

# Update .env file
REDIS_URL=redis://localhost:6379/0
```

### 3. TLS/SSL Configuration

Generate SSL certificates:
```bash
mkdir -p certs

# Self-signed certificate (development only)
openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem -days 365 -nodes

# For production, use Let's Encrypt or your organization's CA
```

Update `.env` for production:
```bash
cat >> .env << EOF
# Production settings
DEBUG=false
REQUIRE_TLS=true
TRUSTED_NODES=["https://node2.example.com", "https://node3.example.com"]
EOF
```

### 4. Docker Compose Deployment

Use the provided docker-compose.yml for full deployment:
```bash
docker-compose up -d
```

## Usage Examples

### 1. Using the Client SDK

Create a Python script to interact with the framework:

```python
# example_client.py
import asyncio
from client_sdk import DistributedClient, JobSubmission

async def main():
    # Connect to a node
    async with DistributedClient("http://localhost:8000") as client:
        # Authenticate (if required)
        await client.authenticate("username", "password")
        
        # Discover available data
        node_info = await client.discover_node()
        print("Available data catalogs:")
        for catalog in node_info.data_catalogs:
            print(f"- {catalog.name}: {catalog.description}")
        
        # Submit a Python script
        job = JobSubmission(
            target_node_id="node-1",
            data_catalog_name="example_dataset",
            script_type="python",
            script_content="""
import pandas as pd
import numpy as np

# Your analysis code here
result = {
    "mean_age": 45.2,
    "sample_size": 150,
    "correlation": 0.73
}
""",
            parameters={"analysis_type": "correlation"},
            filters={"age_min": 18, "age_max": 65}
        )
        
        # Submit and wait for results
        job_id = await client.submit_job(job)
        print(f"Job submitted: {job_id}")
        
        # Wait for completion
        result = await client.wait_for_job(job_id)
        print(f"Job completed with status: {result.status}")
        if result.result_data:
            print(f"Results: {result.result_data}")

if __name__ == "__main__":
    asyncio.run(main())
```

Run the example:
```bash
python example_client.py
```

### 2. Submitting Script Files

You can also submit script files directly:

```python
# submit_script.py
import asyncio
from client_sdk import DistributedClient

async def main():
    async with DistributedClient("http://localhost:8000") as client:
        # Submit a Python file
        job_id = await client.submit_script_file(
            "analysis_scripts/correlation_analysis.py",
            target_node_id="node-1",
            data_catalog_name="patient_data",
            parameters={"outcome": "treatment_response"}
        )
        
        print(f"Script submitted: {job_id}")
        
        # Monitor progress
        result = await client.wait_for_job(job_id, timeout=1800)  # 30 minutes
        print(f"Analysis complete: {result.result_data}")

asyncio.run(main())
```

### 3. Multi-Node Federation

Connect multiple institutions:

```python
# federation_example.py
import asyncio
from client_sdk import DistributedClient

async def federated_analysis():
    nodes = [
        "https://hospital-a.example.com",
        "https://hospital-b.example.com", 
        "https://hospital-c.example.com"
    ]
    
    results = []
    
    for node_url in nodes:
        async with DistributedClient(node_url) as client:
            await client.authenticate("researcher", "password")
            
            # Submit same analysis to each node
            job_id = await client.submit_job(JobSubmission(
                target_node_id=f"node-{len(results)+1}",
                data_catalog_name="clinical_trial_data",
                script_type="python",
                script_content=open("federated_analysis.py").read(),
                filters={"study_phase": "phase_3"}
            ))
            
            result = await client.wait_for_job(job_id)
            results.append(result.result_data)
    
    # Aggregate results across institutions
    print("Federated analysis results:")
    for i, result in enumerate(results):
        print(f"Institution {i+1}: {result}")

asyncio.run(federated_analysis())
```

## Data Catalog Setup

### 1. Create Data Catalogs

Add data catalogs through the API or database:

```python
# setup_catalogs.py
import asyncio
from sqlalchemy.orm import sessionmaker
from distributed_node.database import engine
from distributed_node.models import DataCatalog

async def setup_catalogs():
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    # Example: Clinical trial data catalog
    catalog = DataCatalog(
        name="clinical_trial_data",
        description="De-identified clinical trial dataset",
        data_type="tabular",
        schema_definition={
            "subjects": {
                "subject_id": "string",
                "age": "integer", 
                "sex": "string",
                "diagnosis": "string"
            },
            "outcomes": {
                "subject_id": "string",
                "visit": "string", 
                "outcome_score": "float",
                "response": "boolean"
            }
        },
        access_level="restricted",
        total_records=1500
    )
    
    db.add(catalog)
    db.commit()
    print("Data catalog created successfully")

asyncio.run(setup_catalogs())
```

### 2. Prepare Data Files

Structure your data directory:
```
data/
├── catalogs/
│   ├── clinical_trial_data/
│   │   ├── subjects.csv
│   │   ├── outcomes.csv
│   │   └── metadata.json
│   └── imaging_data/
│       ├── connectivity_matrices/
│       └── roi_masks/
└── scripts/
    ├── approved_analyses/
    └── templates/
```

## Security Configuration

### 1. Authentication Setup

Configure user authentication:
```python
# setup_auth.py
from distributed_node.security import get_password_hash
from distributed_node.models import User  # You'll need to create this model

# Create admin user
admin_password_hash = get_password_hash("secure_admin_password")
# Store in database...
```

### 2. Network Security

Configure firewall rules:
```bash
# Allow only specific ports
sudo ufw allow 8000/tcp  # API port
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 22/tcp     # Disable SSH from external networks
```

### 3. Script Security

The framework includes built-in security validation:
- Dangerous function detection
- Resource limits (CPU, memory, time)
- Network isolation
- Read-only data access

## Monitoring and Logging

### 1. Health Monitoring

Check node health:
```bash
curl http://localhost:8000/health
```

### 2. Audit Logs

Monitor the audit log:
```bash
tail -f audit.log
```

### 3. Job Monitoring

List running jobs:
```python
import asyncio
from client_sdk import DistributedClient

async def monitor_jobs():
    async with DistributedClient("http://localhost:8000") as client:
        jobs = await client.list_jobs(status="running")
        for job in jobs:
            print(f"Job {job.job_id}: {job.progress*100:.1f}% complete")

asyncio.run(monitor_jobs())
```

## Troubleshooting

### Common Issues

1. **Docker permission errors:**
```bash
sudo usermod -aG docker $USER
# Log out and back in
```

2. **Database connection errors:**
```bash
# Check database status
systemctl status postgresql
# Reset database
rm distributed_node.db
python -c "from distributed_node.database import init_db; init_db()"
```

3. **Port conflicts:**
```bash
# Check what's using port 8000
lsof -i :8000
# Kill the process or change the port in .env
```

4. **Memory/CPU limits:**
```bash
# Increase Docker resources in Docker Desktop settings
# Or adjust limits in .env:
MAX_MEMORY_MB=8192
MAX_CPU_CORES=8
```

### Logs and Debugging

Enable debug logging:
```bash
echo "LOG_LEVEL=DEBUG" >> .env
```

Check application logs:
```bash
# If running directly
python -m distributed_node.main

# If using Docker
docker logs distributed-node
```

## Next Steps

1. **Scale horizontally:** Add more nodes by deploying to additional servers
2. **Add data sources:** Connect to databases, file systems, or APIs
3. **Custom analysis:** Develop domain-specific analysis templates
4. **Integration:** Connect with existing research infrastructure
5. **Compliance:** Implement additional privacy controls as needed

For more advanced configuration and development, see the [ARCHITECTURE.md](ARCHITECTURE.md) file.
