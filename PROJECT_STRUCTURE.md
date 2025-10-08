# 📁 StimNet Research Platform - Project Structure

## 🎯 **Overview**
This document provides a complete overview of all folders and files in the StimNet distributed data access framework, explaining what each component does and how they work together.

---

## 📂 **Root Directory Files**

### **🚀 Main Execution Scripts**
| File | Purpose | Usage |
|------|---------|-------|
| `run_server.py` | **Main server launcher** | `python run_server.py` |
| `restart_all.py` | **Complete restart script** | `python restart_all.py` |
| `restart.sh` | **Bash restart script** | `./restart.sh` |
| `tunnel_manager.py` | **Cloudflare tunnel manager** | `python tunnel_manager.py --type cloudflare` |
| `get_public_url.py` | **Get current tunnel URL** | `python get_public_url.py` |

### **📋 Configuration & Setup**
| File | Purpose | Contents |
|------|---------|----------|
| `requirements.txt` | **Original dependencies** | Full package list (has compatibility issues) |
| `requirements_core.txt` | **Working dependencies** | Core packages that work with Python 3.13 |
| `requirements_minimal.txt` | **Minimal dependencies** | Bare minimum packages |
| `.env` | **Environment variables** | Node ID, secrets, database URL, etc. |
| `docker-compose.yml` | **Docker orchestration** | Multi-container setup (legacy) |

### **📚 Documentation**
| File | Purpose | Audience |
|------|---------|----------|
| `README.md` | **Original project readme** | Developers |
| `QUICK_START.md` | **3-step getting started** | New users |
| `RUN_INSTRUCTIONS.md` | **Comprehensive running guide** | All users |
| `SETUP.md` | **Detailed setup instructions** | System administrators |
| `USER_GUIDE.md` | **End-user instructions** | Non-technical users |
| `RESTART_INSTRUCTIONS.md` | **Restart procedures** | Operations |
| `CROSS_NETWORK_TESTING.md` | **Multi-network testing** | Testers |
| `ARCHITECTURE.md` | **Technical architecture** | Architects |
| `SYSTEM_ARCHITECTURE_DIAGRAM.md` | **Visual architecture** | All stakeholders |
| `PROJECT_STRUCTURE.md` | **This file** | Developers |

---

## 📂 **Core Framework (`distributed_node/`)**

### **🏗️ Main Application Files**
| File | Purpose | Status |
|------|---------|--------|
| `__init__.py` | **Package initialization** | ✅ Active |
| `config.py` | **Settings & configuration** | ✅ Active - Pydantic settings |
| `database.py` | **Database connection & setup** | ✅ Active - SQLAlchemy |
| `models.py` | **Data models & schemas** | ✅ Active - SQLAlchemy models |
| `security.py` | **Authentication & validation** | ✅ Active - JWT, bcrypt |

### **🚀 Server Implementations**
| File | Purpose | Status |
|------|---------|--------|
| `simple_main.py` | **Demo server (fake execution)** | 🚧 Legacy |
| `real_main.py` | **Production server (real execution)** | ✅ **CURRENT** |
| `main.py` | **Full server (with Docker)** | 🚧 Future |

### **⚡ Execution Engine**
| File | Purpose | Status |
|------|---------|--------|
| `real_executor.py` | **Real script execution engine** | ✅ **ACTIVE** |
| `job_executor.py` | **Docker-based executor** | 🚧 Future |
| `web_interface.py` | **HTML web interface** | ✅ **ACTIVE** |

---

## 📂 **Client SDK (`client_sdk/`)**

| File | Purpose | Usage |
|------|---------|-------|
| `__init__.py` | **SDK package init** | Import: `from client_sdk import DistributedClient` |
| `client.py` | **Main client class** | `DistributedClient`, `SyncDistributedClient` |
| `models.py` | **Client data models** | `JobSubmission`, `JobResult`, `DataCatalog` |

**Example Usage:**
```python
from client_sdk import DistributedClient, JobSubmission
async with DistributedClient("http://localhost:8000") as client:
    job_id = await client.submit_job(JobSubmission(...))
```

---

## 📂 **Examples & Testing (`examples/`)**

### **🧪 Test Scripts**
| File | Purpose | What It Tests |
|------|---------|---------------|
| `simple_client.py` | **Basic client demo** | Authentication, job submission, results |
| `remote_client_test.py` | **Multi-node testing** | Cross-network connectivity |
| `setup_demo_data.py` | **Demo data generator** | Creates 3 data catalogs with 300+ records |
| `quick_analysis_demo.py` | **User demo script** | Your custom demo |
| `demo_analysis_script.py` | **Analysis demo** | Your custom analysis |

### **🔬 Advanced Testing**
| File | Purpose | What It Tests |
|------|---------|---------------|
| `test_script_execution.py` | **Script execution testing** | Custom analysis scripts |
| `test_real_execution.py` | **Real data processing** | Actual CSV data analysis |
| `test_real_simple.py` | **Simple real execution** | Basic real script execution |

---

## 📂 **Data Layer (`data/`)**

### **📊 Data Catalogs (`data/catalogs/`)**
```
data/catalogs/
├── clinical_trial_data/          # 150 subjects - Parkinson's research
│   ├── subjects.csv             # Demographics: age, sex, diagnosis, visit
│   └── outcomes.csv             # UPDRS scores, quality of life, treatment response
├── imaging_data/                # 100 scans - Neuroimaging
│   └── scan_metadata.csv        # Scan type, quality, motion scores, file paths
└── demo_dataset/                # 50 records - Testing/demos
    └── (generated dynamically)
```

### **🔒 Legacy Data (`data/read_only/`)**
| File | Purpose | Status |
|------|---------|--------|
| `subjects.csv` | **Original demo subjects** | 🚧 Legacy (2 records) |
| `outcomes.csv` | **Original demo outcomes** | 🚧 Legacy (2 records) |
| `paths.csv` | **Original file paths** | 🚧 Legacy (2 records) |

---

## 📂 **Analysis Scripts (`analysis_scripts/`)**

| File | Purpose | Language |
|------|---------|----------|
| `correlation_analysis.py` | **Statistical correlation analysis** | Python |
| *(Add your custom scripts here)* | **Domain-specific analyses** | Python/R |

**Template Structure:**
```python
# Load data from DATA_ROOT environment variable
# Process with pandas/numpy/scipy
# Save results to OUTPUT_FILE environment variable
```

---

## 📂 **Docker & Containers (`docker/`)**

| File | Purpose | Status |
|------|---------|--------|
| `Dockerfile.python` | **Python execution environment** | ✅ Built |
| `Dockerfile.r` | **R execution environment** | ✅ Built |

**Built Images:**
- `distributed-python:latest` - Python 3.11 + scientific libraries
- `distributed-r:latest` - R 4.3.2 + statistical packages

---

## 📂 **Legacy Components**

### **🏥 Original Site App (`site_app/`)**
| File | Purpose | Status |
|------|---------|--------|
| `main.py` | **Original neuroimaging server** | 🚧 Legacy - specialized for NIfTI |

### **⚙️ Original Worker (`worker/`)**
| File | Purpose | Status |
|------|---------|--------|
| `run_job.py` | **Original job runner** | 🚧 Legacy - neuroimaging specific |
| `Dockerfile` | **Original worker container** | 🚧 Legacy |

### **🌐 Nginx Configuration (`nginx/`)**
| File | Purpose | Status |
|------|---------|--------|
| `site.conf` | **Nginx reverse proxy config** | 🚧 Legacy - for production deployment |

---

## 📂 **Working Directory (`work/`)**

**Runtime directory for job execution:**
```
work/
├── {job-id-1}/                  # Individual job workspace
│   ├── script.py               # User's submitted script
│   ├── job_config.json         # Job parameters and filters
│   └── output.json             # Analysis results
├── {job-id-2}/                  # Another job workspace
└── ...                         # One directory per job
```

---

## 📂 **Virtual Environment (`venv/`)**

**Python virtual environment with all dependencies:**
- FastAPI, uvicorn (web server)
- SQLAlchemy, pydantic (database & models)
- pandas, numpy, scipy (data analysis)
- httpx, requests (HTTP clients)
- JWT, bcrypt (security)

---

## 🗃️ **Database Files**

| File | Purpose | Contents |
|------|---------|----------|
| `distributed_node.db` | **Main SQLite database** | Nodes, jobs, data catalogs, audit logs |
| `tunnel.log` | **Tunnel connection logs** | Cloudflare tunnel status and URLs |
| `audit.log` | **Security audit trail** | All API requests and job executions |

---

## 🎯 **Key File Relationships**

### **🔄 Startup Flow:**
```
run_server.py
    ↓
distributed_node/real_main.py
    ↓
config.py (settings) + database.py (connection) + models.py (schema)
    ↓
real_executor.py (script execution) + web_interface.py (UI)
```

### **🌐 Client Flow:**
```
client_sdk/client.py
    ↓
HTTP requests to distributed_node/real_main.py
    ↓
real_executor.py executes scripts
    ↓
Results stored in work/{job-id}/output.json
    ↓
Returned to client via API
```

### **📊 Data Flow:**
```
User submits script via web interface or client SDK
    ↓
Script saved to work/{job-id}/script.py
    ↓
real_executor.py runs script with access to data/catalogs/
    ↓
Results saved to work/{job-id}/output.json
    ↓
Results returned via API (with privacy controls)
```

---

## 🛠️ **Development vs Production Files**

### **✅ Currently Active (Development)**
- `distributed_node/real_main.py` - Main server
- `distributed_node/real_executor.py` - Script execution
- `client_sdk/` - Full client SDK
- `examples/simple_client.py` - Working examples
- `data/catalogs/` - Demo datasets

### **🚧 Future/Production**
- `distributed_node/main.py` - Full server with Docker
- `distributed_node/job_executor.py` - Docker-based execution
- `docker/` - Container definitions
- `nginx/` - Production proxy

### **🗂️ Legacy (Original Project)**
- `site_app/` - Original neuroimaging server
- `worker/` - Original job runner
- `data/read_only/` - Original demo data

---

## 🎮 **How to Use This Structure**

### **🚀 Quick Start:**
1. **Run**: `python run_server.py`
2. **Visit**: http://localhost:8000
3. **Test**: Click "Load Demographics Example" → "Run Analysis"

### **🔧 Development:**
1. **Modify**: `distributed_node/real_main.py` for server changes
2. **Add Scripts**: Put analysis scripts in `analysis_scripts/`
3. **Add Data**: Put datasets in `data/catalogs/your_dataset/`
4. **Test**: Use scripts in `examples/` directory

### **📊 Data Management:**
1. **Add Catalogs**: Create folders in `data/catalogs/`
2. **CSV Files**: Place data files in catalog folders
3. **Metadata**: Update database via `examples/setup_demo_data.py`

### **🌐 Deployment:**
1. **Local**: Use `run_server.py`
2. **Tunnels**: Use `tunnel_manager.py`
3. **Cloud**: Use configs in root directory
4. **Production**: Use Docker files and nginx config

---

## 📈 **File Importance Ranking**

### **🔥 Critical (Don't Delete)**
1. `distributed_node/real_main.py` - Main server
2. `distributed_node/real_executor.py` - Script execution
3. `client_sdk/client.py` - Client SDK
4. `run_server.py` - Server launcher
5. `data/catalogs/` - Your actual data

### **⚡ Important (Active Use)**
6. `distributed_node/config.py` - Settings
7. `distributed_node/models.py` - Database schema
8. `examples/simple_client.py` - Working examples
9. `tunnel_manager.py` - Network access
10. `restart_all.py` - Operations

### **📚 Documentation (Reference)**
11. All `.md` files - Documentation and guides
12. `examples/` - Test and demo scripts

### **🗂️ Legacy (Can Archive)**
13. `site_app/` - Original neuroimaging server
14. `worker/` - Original job runner
15. `data/read_only/` - Original demo data

---

## 🔍 **Quick File Finder**

### **Need to modify server behavior?**
→ `distributed_node/real_main.py`

### **Need to change script execution?**
→ `distributed_node/real_executor.py`

### **Need to update web interface?**
→ HTML: `distributed_node/web_interface.py`  
→ JavaScript: `distributed_node/static/app.js`  
→ CSS: `distributed_node/static/styles.css`

### **Need to add new data?**
→ `data/catalogs/your_new_dataset/`

### **Need to test functionality?**
→ `examples/simple_client.py`

### **Need to restart everything?**
→ `python restart_all.py`

### **Need to check what's running?**
→ `python get_public_url.py`

### **Need to write analysis scripts?**
→ `analysis_scripts/your_analysis.py`

---

## 🎯 **Current System State**

### **✅ Active Components:**
```
🖥️  Server: distributed_node/real_main.py (Port 8000)
🌐 Tunnel: maui-everyday-tomato-member.trycloudflare.com
🗄️  Database: distributed_node.db (SQLite)
📊 Data: 3 catalogs, 300+ demo records
🔒 Security: JWT auth, script validation, privacy controls
🧪 Execution: Real Python script processing
🌍 Access: Local + global web interface
```

### **📊 Data Catalogs:**
```
clinical_trial_data/    150 subjects (Parkinson's research)
├── subjects.csv       Demographics, diagnosis, visits
└── outcomes.csv       UPDRS scores, quality of life, treatment response

imaging_data/          100 scans (Neuroimaging)
└── scan_metadata.csv  T1, DTI, fMRI scan information

demo_dataset/          50 records (Testing)
└── (dynamically generated test data)
```

### **🔄 Management Commands:**
```bash
# Full restart with tunnel
python restart_all.py

# Stop everything
python restart_all.py --stop

# Check status
python restart_all.py --status

# Manual server start
python run_server.py

# Manual tunnel start
python tunnel_manager.py --type cloudflare --port 8000
```

---

## 🎉 **Summary**

Your **StimNet Research Platform** is a comprehensive distributed data access framework with:

- **🏗️ Modular Architecture**: Clear separation of concerns
- **🚀 Multiple Interfaces**: Web UI, API, Python SDK
- **🔒 Security First**: Authentication, validation, privacy controls
- **📊 Real Data Processing**: Actual analysis on your datasets
- **🌍 Global Access**: Cloudflare tunnels for cross-network access
- **🔧 Easy Management**: One-command restart and status checking
- **📚 Complete Documentation**: Guides for all user types

**The project structure is designed for both ease of use and professional deployment!** 🌟

---
**Last Updated**: October 7, 2025 - All components operational and documented
