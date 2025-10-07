# Remote Data Submission and Processing System

## Overview

Your distributed framework now supports **remote data submission and processing** from any machine! Users can send data to your server via the Cloudflare tunnel, trigger analysis scripts, and get results back without exposing raw data.

## 🌐 Your Public Endpoint

**Cloudflare URL**: `https://julian-robin-aaron-rss.trycloudflare.com`

This URL mirrors your localhost and is accessible from anywhere on the internet.

## 🚀 New Features Added

### 1. Enhanced API Endpoints

- **`POST /api/v1/remote/submit-data`** - Upload files and analysis scripts
- **`POST /api/v1/remote/quick-analysis`** - Submit JSON data for immediate analysis
- **`GET /api/v1/remote/job/{job_id}/status`** - Check job progress
- **`GET /api/v1/remote/job/{job_id}/results`** - Get analysis results
- **`GET /api/v1/remote/analysis-templates`** - Get pre-built analysis templates
- **`WebSocket /api/v1/remote/job/{job_id}/stream`** - Real-time progress updates

### 2. Remote Client (`remote_client.py`)

A powerful Python client that makes it easy to submit data from any machine:

```python
from remote_client import RemoteDataClient

# Connect to your server
client = RemoteDataClient("https://julian-robin-aaron-rss.trycloudflare.com")

# Submit files for analysis
job_id = client.submit_files_for_analysis(
    files=["data.csv", "metadata.json"],
    analysis_script="""
    # Your analysis code here
    df = load_data_file("data.csv")
    result = df.describe()
    save_result("statistics", result.to_dict())
    """,
    parameters={"analysis_type": "descriptive"}
)

# Wait for results
results = client.wait_for_results(job_id)
print(results)
```

### 3. Pre-built Analysis Templates

Ready-to-use templates for common analyses:
- **Descriptive Statistics** - Basic stats for numerical columns
- **Correlation Analysis** - Correlation matrices and relationships
- **Group Comparison** - T-tests and ANOVA for group differences

## 📋 Usage Examples

### Command Line Interface

```bash
# Check server health
python remote_client.py --url https://julian-robin-aaron-rss.trycloudflare.com health

# Submit files for analysis
python remote_client.py --url https://julian-robin-aaron-rss.trycloudflare.com submit \
    data.csv metadata.json \
    --script analysis.py \
    --params '{"analysis_type": "full"}' \
    --wait

# Quick JSON analysis
python remote_client.py --url https://julian-robin-aaron-rss.trycloudflare.com quick \
    --data '{"records": [{"x": 1, "y": 2}, {"x": 3, "y": 4}]}' \
    --script quick_stats.py

# Use analysis templates
python remote_client.py --url https://julian-robin-aaron-rss.trycloudflare.com template \
    --name descriptive_stats \
    --data data.csv

# List available templates
python remote_client.py --url https://julian-robin-aaron-rss.trycloudflare.com templates
```

### Python API

```python
# Quick JSON analysis
data = [
    {"name": "Alice", "age": 25, "score": 85.5},
    {"name": "Bob", "age": 30, "score": 92.1},
    {"name": "Charlie", "age": 28, "score": 78.9}
]

script = """
ages = [person['age'] for person in data]
scores = [person['score'] for person in data]
save_result('avg_age', sum(ages) / len(ages))
save_result('avg_score', sum(scores) / len(scores))
"""

result = client.submit_json_data(data, script)
```

### File Upload Analysis

```python
# Upload CSV/JSON files with custom analysis
analysis_script = """
# Load uploaded data
df1 = load_data_file("experiment_data.csv")
df2 = load_data_file("metadata.json")

# Perform analysis
correlation = df1.corr()
summary_stats = df1.describe()

# Save results
save_result("correlation_matrix", correlation.to_dict())
save_result("summary_statistics", summary_stats.to_dict())
save_result("sample_size", len(df1))
"""

job_id = client.submit_files_for_analysis(
    files=["experiment_data.csv", "metadata.json"],
    analysis_script=analysis_script,
    parameters={"experiment_id": "EXP001"}
)

results = client.wait_for_results(job_id)
```

## 🔒 Security Features

- **Script Validation**: All scripts are checked for dangerous operations
- **Sandboxed Execution**: Scripts run in isolated environments
- **Privacy Controls**: Minimum cohort size enforcement
- **Authentication**: Token-based authentication
- **File Size Limits**: 100MB per file, 10MB for JSON data
- **Network Isolation**: No external network access during execution

## 🧪 Demo and Testing

Run the demo to see the system in action:

```bash
python examples/quick_analysis_demo.py
```

This will:
1. Check server health
2. Run quick JSON analysis
3. Test analysis templates
4. Upload files for processing
5. Show real-time results

## 📊 Analysis Script Format

Your analysis scripts have access to these helper functions:

```python
# For file uploads
load_data_file("filename.csv")  # Load uploaded CSV/JSON/Excel files
save_result("key", value)       # Store results

# Available variables
workspace      # Temporary directory path
data_files     # List of uploaded file paths
parameters     # User-provided parameters

# For JSON data
data          # The submitted JSON data
df            # Auto-converted DataFrame (if applicable)
save_result("key", value)  # Store results
```

## 🌍 Remote Access Workflow

1. **From Any Machine**: Users can access your Cloudflare URL
2. **Submit Data**: Upload files or send JSON data with analysis scripts
3. **Secure Processing**: Scripts run in sandboxed Docker containers
4. **Get Results**: Receive processed results without exposing raw data
5. **Privacy Protected**: Only aggregate/summary results are returned

## 🔧 Server Management

### Starting the Server

```bash
python run_server.py
```

The server will be available at:
- **Local**: http://localhost:8000
- **Public**: https://julian-robin-aaron-rss.trycloudflare.com
- **API Docs**: https://julian-robin-aaron-rss.trycloudflare.com/docs

### Monitoring

- **Health Check**: `GET /health`
- **Active Jobs**: Check the health endpoint for job counts
- **Logs**: Server logs show all processing activity

## 📈 Use Cases

### Research Collaboration
- Researchers can submit data from different institutions
- Run standardized analyses across multiple datasets
- Get results without sharing raw data

### Data Analysis Services
- Provide analysis capabilities to external users
- Process uploaded datasets with custom scripts
- Return insights while maintaining data privacy

### Distributed Computing
- Submit computational jobs from remote machines
- Scale analysis across multiple nodes
- Coordinate multi-site studies

## 🚨 Important Notes

1. **Data Privacy**: Raw data never leaves your server - only analysis results are returned
2. **Resource Limits**: Each job has memory and CPU limits to prevent abuse
3. **Authentication**: All API calls require authentication (demo credentials: demo/demo)
4. **Cohort Size**: Results are blocked if sample size is below minimum threshold
5. **Script Security**: Dangerous operations (file system access, network calls) are blocked

## 🎯 Next Steps

1. **Customize Templates**: Add your own analysis templates for common use cases
2. **Enhanced Security**: Implement proper user management and API keys
3. **Scale Up**: Add job queuing and multiple worker nodes
4. **Monitoring**: Add detailed logging and performance metrics
5. **Documentation**: Create user guides for your specific use cases

Your system is now ready for remote data submission and processing! Users can securely send data from anywhere and get analysis results back through your Cloudflare tunnel.