# Distributed Data Access and Remote Execution Framework

A comprehensive framework for secure, distributed data access and remote script execution across multiple machines and institutions. This system enables researchers and organizations to collaborate on data analysis while maintaining strict privacy and security controls.

## 🚀 Key Features

- **Distributed Architecture**: Peer-to-peer network of data nodes
- **Secure Execution**: Sandboxed script execution in Docker containers
- **Privacy Controls**: K-anonymity, differential privacy, and data aggregation
- **Multi-Language Support**: Python, R, SQL, and Jupyter notebooks
- **RESTful API**: Complete REST API for all operations
- **Client SDK**: Easy-to-use Python SDK for remote interactions
- **Comprehensive Security**: JWT authentication, TLS encryption, audit logging
- **Data Catalog Management**: Automatic schema inference and metadata management

## 📁 Project Structure

```
distributed-framework/
├── README.md                      # This file
├── ARCHITECTURE.md                # Detailed architecture documentation
├── requirements.txt               # Python dependencies
├── docker-compose.yml             # Container orchestration
├── distributed_node/              # Core server components
│   ├── main.py                   # FastAPI application
│   ├── config.py                 # Configuration management
│   ├── models.py                 # Database models
│   ├── database.py               # Database configuration
│   ├── security.py               # Authentication and security
│   └── job_executor.py           # Job execution engine
├── client_sdk/                   # Python client SDK
│   ├── client.py                 # Main client class
│   └── models.py                 # Client data models
├── data_layer/                   # Data access and privacy
│   ├── catalog_manager.py        # Data catalog management
│   ├── data_provider.py          # Secure data access
│   └── privacy_manager.py        # Privacy controls
├── examples/                     # Usage examples and demos
│   ├── basic_usage.py            # Basic client examples
│   ├── setup_demo_data.py        # Demo data creation
│   └── scripts/                  # Sample analysis scripts
├── tests/                        # Test suite
├── docs/                         # Documentation
└── data/                         # Data storage
    ├── demo/                     # Demo datasets
    ├── catalogs/                 # Data catalog definitions
    └── metadata/                 # Catalog metadata
```

## 🛠️ Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd distributed-framework

# Install dependencies
pip install -r requirements.txt

# Set up demo data
python examples/setup_demo_data.py
```

### 2. Start the Node Server

```bash
# Start the distributed node server
python -m distributed_node.main

# Or with custom configuration
export NODE_ID="my-institution"
export NODE_NAME="My Research Institution"
export SECRET_KEY="your-secure-secret-key"
python -m distributed_node.main
```

### 3. Basic Usage

```python
import asyncio
from client_sdk import DistributedClient, ScriptType

async def example():
    # Create client and connect to node
    client = DistributedClient()
    client.add_node("node1", "http://localhost:8000")
    
    # Authenticate
    client.authenticate("node1", "demo_user", "demo_password")
    
    # Discover available data
    discovery = await client.discover_node("node1")
    print(f"Found {len(discovery.data_catalogs)} data catalogs")
    
    # Submit a Python analysis job
    script = """
import pandas as pd
import numpy as np

# Your analysis code here
result = {
    "message": "Analysis completed",
    "mean_value": np.random.normal(10, 2),
    "sample_size": 100
}
"""
    
    job_id = await client.submit_job(
        node_id="node1",
        data_catalog_name="patient_demographics",
        script_type=ScriptType.PYTHON,
        script_content=script
    )
    
    # Wait for results
    result = await client.wait_for_job_completion("node1", job_id)
    print(f"Job completed: {result.status}")
    print(f"Results: {result.result_data}")

# Run the example
asyncio.run(example())
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with your configuration:

```bash
# Node identification
NODE_ID=my-institution-node
NODE_NAME=My Research Institution
INSTITUTION_NAME=My Institution

# Security
SECRET_KEY=your-very-secure-secret-key-change-this
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=postgresql://user:password@localhost/distributed_db
# Or for SQLite: DATABASE_URL=sqlite:///./distributed_node.db

# Redis (for job queue)
REDIS_URL=redis://localhost:6379/0

# Privacy settings
MIN_COHORT_SIZE=10
ENABLE_DIFFERENTIAL_PRIVACY=false
PRIVACY_EPSILON=1.0

# Resource limits
MAX_EXECUTION_TIME=3600
MAX_MEMORY_MB=4096
MAX_CPU_CORES=4

# Data paths
DATA_ROOT=./data
WORK_DIR=./work

# Security
REQUIRE_TLS=true
TRUSTED_NODES=node1.example.com,node2.example.com
```

### Docker Deployment

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 📊 API Endpoints

### Health and Discovery
- `GET /health` - Node health status
- `GET /api/v1/discovery` - Node capabilities and data catalogs
- `GET /api/v1/nodes` - List known nodes
- `GET /api/v1/data-catalogs` - List available data catalogs

### Authentication
- `POST /api/v1/auth/token` - Get access token

### Job Management
- `POST /api/v1/jobs` - Submit new job
- `GET /api/v1/jobs/{job_id}` - Get job status and results
- `GET /api/v1/jobs` - List jobs
- `DELETE /api/v1/jobs/{job_id}` - Cancel job

### Data Catalogs
- `GET /api/v1/data-catalogs/{catalog_id}` - Get catalog details

## 🔒 Security Features

### Authentication & Authorization
- JWT-based authentication
- Role-based access control (RBAC)
- API key support for service accounts
- Optional mutual TLS (mTLS)

### Privacy Controls
- **K-Anonymity**: Minimum cohort size enforcement
- **Differential Privacy**: Optional noise injection
- **Data Aggregation**: Only summary statistics returned
- **Access Logging**: Complete audit trail
- **Script Validation**: Security scanning of submitted scripts

### Execution Security
- **Sandboxed Execution**: Scripts run in isolated Docker containers
- **No Network Access**: Containers run with `--network=none`
- **Resource Limits**: CPU, memory, and time constraints
- **Read-Only Data**: Data mounted as read-only volumes

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=distributed_node --cov=client_sdk --cov=data_layer

# Run specific test file
pytest tests/test_client.py
```

## 📚 Examples

### Multi-Node Federated Analysis

```python
async def federated_analysis():
    client = DistributedClient()
    
    # Add multiple nodes
    nodes = {
        "hospital_a": "https://hospital-a.example.com",
        "hospital_b": "https://hospital-b.example.com",
        "research_center": "https://research.example.com"
    }
    
    for node_id, endpoint in nodes.items():
        client.add_node(node_id, endpoint)
    
    # Run same analysis on all nodes
    script = """
    # Federated analysis script
    result = {
        "site_summary": {
            "total_subjects": len(data),
            "mean_age": data['age'].mean(),
            "primary_outcome": data['outcome'].mean()
        }
    }
    """
    
    # Submit to all nodes
    results = {}
    for node_id in nodes:
        job_id = await client.submit_job(
            node_id, "patient_data", ScriptType.PYTHON, script
        )
        result = await client.wait_for_job_completion(node_id, job_id)
        results[node_id] = result
    
    # Aggregate results
    total_subjects = sum(r.result_data["site_summary"]["total_subjects"] 
                        for r in results.values())
    print(f"Total subjects across all sites: {total_subjects}")
```

### Custom Data Catalog

```python
from data_layer import DataCatalogManager

# Create catalog manager
catalog_manager = DataCatalogManager("./data")

# Register existing data
catalog_id = catalog_manager.register_existing_data(
    data_path="./my_data/patient_records.csv",
    name="patient_records",
    description="Patient clinical records"
)

# Or create from scratch
catalog_id = catalog_manager.create_catalog(
    name="genomic_data",
    description="Genomic variant data",
    data_type="csv",
    data_source="./data/genomics.csv",
    access_level="restricted"
)
```

## 🚀 Production Deployment

### Recommended Setup

1. **Use PostgreSQL** for the database instead of SQLite
2. **Set up Redis** for job queuing and caching
3. **Configure TLS** with proper certificates (Let's Encrypt)
4. **Enable mTLS** for enhanced security between nodes
5. **Set up monitoring** with Prometheus and Grafana
6. **Configure log aggregation** (ELK stack or similar)
7. **Implement backup strategies** for data and metadata

### Security Checklist

- [ ] Change default secret keys
- [ ] Enable TLS/mTLS
- [ ] Configure firewall rules
- [ ] Set up audit logging
- [ ] Implement rate limiting
- [ ] Regular security updates
- [ ] Monitor for suspicious activity
- [ ] Backup encryption keys

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: See `docs/` directory for detailed guides
- **Examples**: Check `examples/` for usage patterns
- **Issues**: Report bugs and request features via GitHub Issues
- **Architecture**: See `ARCHITECTURE.md` for system design details

## 🔄 Changelog

### Version 1.0.0
- Initial release
- Core distributed framework
- Python, R, SQL, Jupyter support
- Privacy controls and security features
- Client SDK and REST API
- Comprehensive documentation and examples