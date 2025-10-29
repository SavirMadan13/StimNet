# StimNet Research Platform

A distributed data access and remote execution framework for secure, privacy-preserving collaborative research across multiple institutions.

## Overview

StimNet enables researchers to:
- **Securely share data** across institutions without moving raw data
- **Execute remote analysis scripts** in sandboxed environments
- **Enforce privacy controls** (minimum cohort sizes, aggregation only)
- **Provide audit trails** for all operations
- **Scale horizontally** across multiple nodes/institutions

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Start the Server
```bash
python run_server.py
```

### 3. Access the Web Interface
- **Local**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Project Structure

```
StimNet/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── run_server.py               # Main server entry point
├── launch.sh                   # Advanced startup script
├── distributed_node/           # Core application
│   ├── real_main.py           # Main FastAPI application
│   ├── config.py              # Configuration settings
│   ├── database.py            # Database models and setup
│   ├── models.py              # Pydantic models
│   ├── security.py            # Authentication and security
│   ├── real_executor.py       # Script execution engine
│   ├── web_interface.py       # Web UI components
│   └── static/                # Web assets
├── client_sdk/                # Python client library
│   ├── client.py              # Main client class
│   └── models.py              # Client models
├── examples/                  # Example scripts and demos
├── data/                      # Data catalogs and manifests
├── docker/                    # Docker execution environments
└── nginx/                     # Nginx configuration
```

## Key Features

### 🔒 **Security & Privacy**
- Script validation and sandboxed execution
- Minimum cohort size enforcement
- Data aggregation only (no raw data leaves the institution)
- Complete audit trails
- JWT-based authentication

### 🚀 **Easy to Use**
- Web-based interface for non-technical users
- Python SDK for developers
- RESTful API for integration
- Pre-built analysis examples

### 📊 **Data Management**
- Multiple data catalog support
- Automatic data loading
- File upload capabilities
- Metadata management

### 🔧 **Flexible Execution**
- Python and R script support
- Docker-based sandboxing
- Resource limits and timeouts
- Background job processing

## Usage

### Web Interface
1. Visit http://localhost:8000
2. Select a dataset from the dropdown
3. Write or load an example analysis script
4. Click "Run Analysis" to execute
5. View results in real-time

### Python SDK
```python
import asyncio
from client_sdk import DistributedClient, JobSubmission

async def run_analysis():
    async with DistributedClient("http://localhost:8000") as client:
        # Authenticate
        await client.authenticate("demo", "demo")
        
        # Submit analysis
        job_id = await client.submit_job(JobSubmission(
            target_node_id="node-1",
            data_catalog_name="clinical_trial_data",
            script_type="python",
            script_content="""
import pandas as pd
from data_loader import load_data, save_results

# Load data
data = load_data()
subjects = data['subjects']

# Analysis
result = {
    "total_subjects": len(subjects),
    "mean_age": float(subjects['age'].mean())
}

# Save results
save_results(result)
""",
            parameters={"analysis_type": "demographics"}
        ))
        
        # Wait for results
        result = await client.wait_for_job(job_id)
        print(f"Results: {result.result_data}")

asyncio.run(run_analysis())
```

## API Endpoints

- `GET /health` - Health check
- `GET /api/v1/discovery` - Node discovery
- `GET /api/v1/data-catalogs` - List available datasets
- `POST /api/v1/jobs` - Submit analysis job
- `GET /api/v1/jobs/{job_id}` - Get job status/results
- `POST /api/v1/analysis-requests` - Submit analysis request
- `GET /admin` - Admin interface

## Configuration

The application can be configured via environment variables:

```bash
# Node Configuration
NODE_ID=node-1
NODE_NAME=My Research Node
INSTITUTION_NAME=My Institution

# Security
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=sqlite:///./distributed_node.db

# Data settings
DATA_ROOT=./data
WORK_DIR=./work
MIN_COHORT_SIZE=5

# Logging
LOG_LEVEL=INFO
```

## Development

### Running in Development Mode
```bash
# Start with auto-reload
python run_server.py

# Or use the advanced launcher
./launch.sh --dev
```

### Adding New Data Catalogs
1. Add your data files to `data/catalogs/your_dataset/`
2. Update `data/data_manifest_simple.json`
3. Restart the server

### Custom Analysis Scripts
Place your analysis scripts in `analysis_scripts/` and reference them in the web interface or API calls.

## Production Deployment

For production deployment:
1. Set up PostgreSQL database
2. Configure TLS/SSL certificates
3. Set up proper authentication
4. Configure monitoring and logging
5. Use the provided Docker containers for script execution

## Support

- **Documentation**: See individual guide files in the repository
- **API Docs**: Visit `/docs` endpoint when server is running
- **Health Check**: Visit `/health` endpoint
- **Examples**: Check the `examples/` directory

## License

This project is designed for research and educational purposes. Please ensure compliance with your institution's data sharing policies and applicable regulations.