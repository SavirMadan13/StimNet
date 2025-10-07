# Quick Start Guide

Get the Distributed Data Access and Remote Execution Framework up and running in minutes.

## 🚀 Prerequisites

- Python 3.9+
- Docker (for script execution)
- Git

## 📦 Installation

### Option 1: Local Development Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd distributed-framework

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up demo data
python examples/setup_demo_data.py

# 5. Start the server
python -m distributed_node.main
```

### Option 2: Docker Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd distributed-framework

# 2. Create environment file
cp .env.example .env

# 3. Start with Docker Compose
docker-compose up -d

# 4. Set up demo data (in the container)
docker-compose exec app python examples/setup_demo_data.py
```

## 🔧 Configuration

Create a `.env` file with your settings:

```bash
NODE_ID=my-node
NODE_NAME=My Research Node
SECRET_KEY=your-secure-secret-key
DATABASE_URL=sqlite:///./distributed_node.db
```

## 🧪 Test the Installation

### 1. Check Server Status

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "node_id": "my-node",
  "version": "1.0.0",
  "uptime": 123.45,
  "active_jobs": 0,
  "total_jobs": 0
}
```

### 2. View API Documentation

Open your browser and go to: http://localhost:8000/docs

### 3. Run Example Client

```python
import asyncio
from client_sdk import DistributedClient, ScriptType

async def quick_test():
    # Create client
    client = DistributedClient()
    client.add_node("local", "http://localhost:8000")
    
    # Authenticate (demo credentials)
    client.authenticate("local", "demo", "demo")
    
    # Discover available data
    discovery = await client.discover_node("local")
    print(f"Available catalogs: {len(discovery.data_catalogs)}")
    
    # Submit a simple job
    script = """
result = {
    "message": "Hello from distributed framework!",
    "status": "success"
}
"""
    
    if discovery.data_catalogs:
        catalog_name = discovery.data_catalogs[0].name
        job_result = await client.run_python_script(
            "local", catalog_name, script, wait_for_completion=True
        )
        print(f"Job result: {job_result.result_data}")

# Run the test
asyncio.run(quick_test())
```

## 📊 Next Steps

### 1. Add Your Data

```python
from data_layer import DataCatalogManager

# Create catalog manager
catalog_manager = DataCatalogManager("./data")

# Register your CSV data
catalog_id = catalog_manager.register_existing_data(
    data_path="path/to/your/data.csv",
    name="my_dataset",
    description="My research dataset"
)
```

### 2. Run Real Analysis

```python
analysis_script = """
import pandas as pd
import numpy as np

# Your analysis code here
# Data will be available through the data provider

result = {
    "analysis": "statistical_summary",
    "sample_size": 100,
    "mean_age": 45.2,
    "findings": "Significant correlation found"
}
"""

# Submit and run
job_result = await client.run_python_script(
    "local", "my_dataset", analysis_script
)
```

### 3. Set Up Multiple Nodes

```python
# Add multiple nodes
client.add_node("hospital_a", "https://hospital-a.example.com")
client.add_node("hospital_b", "https://hospital-b.example.com")

# Run federated analysis
for node_id in ["hospital_a", "hospital_b"]:
    result = await client.run_python_script(
        node_id, "patient_data", analysis_script
    )
    print(f"Results from {node_id}: {result.result_data}")
```

## 🔒 Security Setup

### 1. Generate Secure Keys

```bash
# Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Enable HTTPS

```bash
# Generate self-signed certificate for testing
openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes

# Move to certs directory
mkdir -p certs
mv key.pem cert.pem certs/
```

### 3. Configure Environment

```bash
# Update .env file
SECRET_KEY=your-generated-secure-key
REQUIRE_TLS=true
MIN_COHORT_SIZE=10
```

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Change port in .env
   PORT=8001
   ```

2. **Docker permission denied**
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

3. **Database connection error**
   ```bash
   # For SQLite, ensure directory exists
   mkdir -p data
   
   # For PostgreSQL, check connection
   psql -h localhost -U postgres
   ```

4. **Module not found**
   ```bash
   # Ensure virtual environment is activated
   source venv/bin/activate
   pip install -r requirements.txt
   ```

## 📚 Learn More

- **Full Documentation**: See [README.md](README.md)
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Deployment**: See [DEPLOYMENT.md](DEPLOYMENT.md)
- **Examples**: Check the `examples/` directory
- **API Reference**: Visit `/docs` endpoint when server is running

## 🆘 Getting Help

- Check the [troubleshooting section](#troubleshooting)
- Review the logs: `docker-compose logs app`
- Open an issue on GitHub
- Check existing examples in `examples/`

---

**Congratulations!** 🎉 You now have a working distributed data access and remote execution framework. Start by exploring the examples and then customize it for your specific use case.