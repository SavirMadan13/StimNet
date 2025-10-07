# How to Run the Distributed Data Access Framework

This guide provides step-by-step instructions to get the distributed framework up and running.

## Quick Start (5 minutes)

### Step 1: Install Dependencies

```bash
# Make sure you're in the project directory
cd /Users/savirmadan/Development/StimNet

# Install Python dependencies
pip install -r requirements.txt
```

### Step 2: Build Docker Images

```bash
# Build Python execution environment
docker build -t distributed-python:latest -f docker/Dockerfile.python .

# Build R execution environment (optional)
docker build -t distributed-r:latest -f docker/Dockerfile.r .
```

### Step 3: Set Up Demo Data

```bash
# Create demo datasets and database
python examples/setup_demo_data.py
```

### Step 4: Start the Server

```bash
# Start the distributed node server
python -m distributed_node.main
```

The server will start on `http://localhost:8000`. You should see output like:
```
INFO:distributed_node.main:Starting Distributed Node Server v1.0.0
INFO:distributed_node.main:Node ID: node-1
INFO:distributed_node.main:Institution: My Institution
INFO:distributed_node.database:Database tables created successfully
INFO:distributed_node.main:Application startup complete
INFO:uvicorn.error:Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### Step 5: Test the Client

Open a new terminal and run:

```bash
# Test the client SDK
python examples/simple_client.py
```

You should see output showing:
- Node health check
- Available data catalogs
- Job submission and execution
- Results

## Detailed Setup

### Environment Configuration

Create a `.env` file for custom configuration:

```bash
cat > .env << EOF
# Node Configuration
NODE_ID=my-research-node
NODE_NAME=My Research Institution Node
INSTITUTION_NAME=My University

# Security (CHANGE THESE IN PRODUCTION!)
SECRET_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Database
DATABASE_URL=sqlite:///./distributed_node.db

# Data settings
DATA_ROOT=./data
WORK_DIR=./work
MIN_COHORT_SIZE=5

# Resource limits
MAX_EXECUTION_TIME=1800
MAX_MEMORY_MB=4096
MAX_CPU_CORES=4

# Logging
LOG_LEVEL=INFO
ENABLE_AUDIT_LOG=true
AUDIT_LOG_FILE=./audit.log
EOF
```

### Production Database Setup (Optional)

For production use, set up PostgreSQL:

```bash
# Install PostgreSQL (macOS)
brew install postgresql
brew services start postgresql

# Create database
createdb distributed_framework

# Update .env file
echo "DATABASE_URL=postgresql://username:password@localhost/distributed_framework" >> .env
```

## Usage Examples

### 1. Basic Client Usage

```python
import asyncio
from client_sdk import DistributedClient, JobSubmission

async def run_analysis():
    async with DistributedClient("http://localhost:8000") as client:
        # Authenticate
        await client.authenticate("demo", "demo")
        
        # Submit Python analysis
        job_id = await client.submit_job(JobSubmission(
            target_node_id="node-1",
            data_catalog_name="clinical_trial_data",
            script_type="python",
            script_content="""
import pandas as pd
import numpy as np

# Your analysis code here
result = {"mean_age": 45.2, "n": 150}
""",
            parameters={"analysis_type": "descriptive"}
        ))
        
        # Wait for results
        result = await client.wait_for_job(job_id)
        print(f"Results: {result.result_data}")

asyncio.run(run_analysis())
```

### 2. Submit Script Files

```python
import asyncio
from client_sdk import DistributedClient

async def submit_script():
    async with DistributedClient("http://localhost:8000") as client:
        await client.authenticate("demo", "demo")
        
        # Submit a script file
        job_id = await client.submit_script_file(
            "analysis_scripts/correlation_analysis.py",
            target_node_id="node-1",
            data_catalog_name="clinical_trial_data",
            parameters={
                "outcome_variable": "UPDRS_change",
                "predictor_variables": ["age", "quality_of_life"]
            },
            filters={"diagnosis": "PD"}
        )
        
        result = await client.wait_for_job(job_id)
        print(f"Analysis complete: {result.status}")

asyncio.run(submit_script())
```

### 3. Multi-Node Setup

To connect multiple institutions:

**Node 1 (Institution A):**
```bash
# .env for Node 1
NODE_ID=institution-a
NODE_NAME=Hospital A Research Node
INSTITUTION_NAME=Hospital A
PORT=8000
```

**Node 2 (Institution B):**
```bash
# .env for Node 2  
NODE_ID=institution-b
NODE_NAME=Hospital B Research Node
INSTITUTION_NAME=Hospital B
PORT=8001
```

Start both nodes:
```bash
# Terminal 1
python -m distributed_node.main

# Terminal 2
PORT=8001 python -m distributed_node.main
```

Connect from client:
```python
# Connect to multiple nodes
nodes = [
    "http://localhost:8000",  # Institution A
    "http://localhost:8001"   # Institution B
]

for node_url in nodes:
    async with DistributedClient(node_url) as client:
        # Submit same analysis to each node
        job_id = await client.submit_job(...)
        result = await client.wait_for_job(job_id)
        print(f"Results from {node_url}: {result.result_data}")
```

## API Documentation

Once the server is running, visit:
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Node Discovery:** http://localhost:8000/api/v1/discovery

### Key Endpoints

- `GET /health` - Check node status
- `GET /api/v1/discovery` - Discover node capabilities
- `GET /api/v1/data-catalogs` - List available datasets
- `POST /api/v1/jobs` - Submit analysis job
- `GET /api/v1/jobs/{job_id}` - Get job status/results

## Security Features

### Script Validation
The framework automatically validates scripts for security:
- Blocks dangerous functions (`exec`, `eval`, `os.system`, etc.)
- Enforces resource limits (CPU, memory, time)
- Runs in isolated Docker containers
- No network access during execution

### Privacy Controls
- Minimum cohort size enforcement
- Results aggregation only
- Audit logging of all operations
- Data access controls

### Authentication
```python
# Token-based authentication
await client.authenticate("username", "password")

# API key authentication (for services)
client = DistributedClient("http://localhost:8000", api_key="your-api-key")
```

## Monitoring and Debugging

### Check Server Logs
```bash
# If running directly
python -m distributed_node.main

# Check audit logs
tail -f audit.log
```

### Monitor Jobs
```python
import asyncio
from client_sdk import DistributedClient

async def monitor():
    async with DistributedClient("http://localhost:8000") as client:
        jobs = await client.list_jobs(status="running")
        for job in jobs:
            print(f"Job {job.job_id}: {job.progress*100:.1f}% complete")

asyncio.run(monitor())
```

### Health Monitoring
```bash
# Check node health
curl http://localhost:8000/health

# Check specific job
curl http://localhost:8000/api/v1/jobs/YOUR_JOB_ID
```

## Troubleshooting

### Common Issues

1. **Docker not found:**
```bash
# Install Docker Desktop or Docker Engine
# Make sure Docker daemon is running
docker --version
```

2. **Port already in use:**
```bash
# Check what's using port 8000
lsof -i :8000

# Use different port
PORT=8001 python -m distributed_node.main
```

3. **Permission errors:**
```bash
# Fix Docker permissions (Linux)
sudo usermod -aG docker $USER
# Log out and back in
```

4. **Database errors:**
```bash
# Reset database
rm distributed_node.db
python examples/setup_demo_data.py
```

5. **Import errors:**
```bash
# Make sure you're in the right directory
cd /Users/savirmadan/Development/StimNet

# Check Python path
python -c "import sys; print(sys.path)"
```

### Debug Mode

Enable debug logging:
```bash
echo "LOG_LEVEL=DEBUG" >> .env
python -m distributed_node.main
```

## Next Steps

1. **Add Your Data:** Replace demo data with real datasets
2. **Custom Analysis:** Write domain-specific analysis scripts
3. **Scale Up:** Deploy to multiple servers/institutions
4. **Security:** Implement proper authentication and TLS
5. **Integration:** Connect with existing research infrastructure

## Support

For issues or questions:
1. Check the logs for error messages
2. Review the [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
3. Look at example scripts in the `examples/` directory
4. Check the API documentation at `/docs` endpoint

The framework is designed to be flexible and extensible. You can customize it for your specific research needs while maintaining security and privacy controls.
