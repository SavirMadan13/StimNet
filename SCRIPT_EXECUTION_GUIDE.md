# Script Execution Framework

This document describes the enhanced script execution capabilities that allow you to pass both data and code for remote execution in secure, sandboxed environments.

## Overview

The Script Execution Framework extends your distributed data processing system to support:

- **Arbitrary Code Execution**: Run scripts in multiple languages (Python, R, Shell, Node.js)
- **Data Processing**: Upload files or pass JSON data for processing
- **Secure Sandboxing**: All scripts run in isolated Docker containers with no network access
- **Resource Limits**: Configurable memory, CPU, and timeout limits
- **Real-time Monitoring**: Track execution progress and get detailed results

## Supported Script Types

### 1. Python Scripts
- **Language**: Python 3.11
- **Libraries**: pandas, numpy, scipy, matplotlib, seaborn
- **Use Cases**: Data analysis, statistical computing, machine learning

### 2. R Scripts
- **Language**: R 4.3.0
- **Libraries**: Base R, jsonlite (for JSON handling)
- **Use Cases**: Statistical analysis, data visualization, research computing

### 3. Shell Scripts
- **Language**: Bash on Ubuntu 22.04
- **Use Cases**: File processing, system operations, data pipeline tasks

### 4. Node.js Scripts
- **Language**: Node.js 18
- **Libraries**: Core Node.js modules (limited for security)
- **Use Cases**: JavaScript-based data processing, JSON manipulation

## API Endpoints

### Execute Script
```
POST /api/v1/remote/execute-script
```

Execute arbitrary scripts with optional data and files.

**Parameters:**
- `script_content` (required): The script code to execute
- `script_type` (optional): Type of script (python, r, shell, bash, nodejs)
- `parameters` (optional): JSON parameters to pass to the script
- `data` (optional): JSON data to pass to the script
- `files` (optional): Files to upload for processing
- `timeout` (optional): Maximum execution time in seconds (default: 300)

**Response:**
```json
{
  "job_id": "uuid-string",
  "status": "submitted",
  "message": "Script submitted for execution",
  "script_type": "python",
  "estimated_completion": "300 seconds maximum",
  "files_uploaded": 2
}
```

### Submit Data with Script
```
POST /api/v1/remote/submit-data
```

Submit data files with analysis script for processing.

**Parameters:**
- `script_content` (required): Analysis script code
- `files` (required): Data files to upload
- `parameters` (optional): JSON parameters for the analysis
- `analysis_type` (optional): Type of analysis script (default: python)

### Quick Analysis
```
POST /api/v1/remote/quick-analysis
```

Perform quick analysis on JSON data without file upload.

**Parameters:**
- `data` (required): JSON data to analyze
- `analysis_script` (required): Python script for analysis
- `parameters` (optional): Parameters for the script

**Response:** Returns results immediately (no job tracking needed)

### Get Job Status
```
GET /api/v1/remote/job/{job_id}/status
```

Get the status of a script execution job.

### Get Job Results
```
GET /api/v1/remote/job/{job_id}/results
```

Get the results of a completed script execution job.

## Client SDK Usage

### Python Client Example

```python
from client_sdk import DistributedClient

async def execute_python_script():
    async with DistributedClient("http://localhost:8000") as client:
        # Authenticate
        await client.authenticate("username", "password")
        
        # Python script
        script = """
import pandas as pd
import numpy as np

# Use parameters
sample_size = parameters.get('sample_size', 100)

# Generate data
data = np.random.normal(0, 1, sample_size)

# Analyze
mean_val = np.mean(data)
std_val = np.std(data)

# Save results
save_result('mean', float(mean_val))
save_result('std', float(std_val))
save_result('sample_size', sample_size)

print(f"Analysis complete: mean={mean_val:.3f}")
"""
        
        # Execute script
        job_id = await client.execute_script(
            script,
            script_type="python",
            parameters={"sample_size": 200},
            timeout=120
        )
        
        # Wait for results
        result = await client.wait_for_job(job_id)
        print(f"Results: {result.result_data}")
```

### Data File Processing Example

```python
async def process_data_files():
    async with DistributedClient("http://localhost:8000") as client:
        await client.authenticate("username", "password")
        
        # Analysis script
        script = """
# Load uploaded files
df1 = load_file("data1.csv")  # Automatically detects CSV
df2 = load_file("data2.json") # Automatically detects JSON

# Process data
combined = pd.concat([df1, df2], ignore_index=True)
summary = combined.describe()

# Save results
save_result('total_records', len(combined))
save_result('summary_stats', summary.to_dict())

print(f"Processed {len(combined)} records")
"""
        
        # Submit with files
        job_id = await client.submit_data_with_script(
            script,
            files=["data1.csv", "data2.json"],
            parameters={"analysis_type": "summary"}
        )
        
        result = await client.wait_for_job(job_id)
        print(f"Processing complete: {result.result_data}")
```

### Quick Analysis Example

```python
async def quick_analysis():
    async with DistributedClient("http://localhost:8000") as client:
        await client.authenticate("username", "password")
        
        # Sample data
        data = [
            {"name": "Alice", "score": 85},
            {"name": "Bob", "score": 92},
            {"name": "Charlie", "score": 78}
        ]
        
        # Analysis script
        script = """
df = pd.DataFrame(data)
avg_score = df['score'].mean()
max_score = df['score'].max()

save_result('average', float(avg_score))
save_result('maximum', int(max_score))
save_result('count', len(df))
"""
        
        # Get immediate results
        result = await client.quick_analysis(data, script)
        print(f"Quick results: {result['results']}")
```

## Script Environment

### Available Variables

All scripts have access to these variables:

- `parameters`: Dictionary of user-provided parameters
- `input_data`: JSON data passed to the script (if any)
- `uploaded_files`: List of uploaded file paths
- `workspace`: Path to the script's working directory
- `job_id`: Unique identifier for the execution job

### Helper Functions

#### Python Scripts
- `save_result(key, value)`: Save a result value
- `load_file(filename)`: Load an uploaded file (auto-detects format)
- `save_file(filename, content)`: Save content to a file in workspace

#### R Scripts
- `save_result(key, value)`: Save a result value
- `load_csv_file(filename)`: Load a CSV file from uploaded files

#### Node.js Scripts
- `saveResult(key, value)`: Save a result value
- `loadFile(filename)`: Load an uploaded file

### Example Script Templates

#### Statistical Analysis (Python)
```python
# Statistical analysis template
import pandas as pd
import numpy as np
from scipy import stats

# Load data
df = pd.DataFrame(input_data) if input_data else load_file("data.csv")

# Basic statistics
numeric_cols = df.select_dtypes(include=[np.number]).columns

results = {}
for col in numeric_cols:
    results[col] = {
        'mean': float(df[col].mean()),
        'median': float(df[col].median()),
        'std': float(df[col].std()),
        'min': float(df[col].min()),
        'max': float(df[col].max())
    }

save_result('statistics', results)
save_result('total_records', len(df))
```

#### Correlation Analysis (R)
```r
# Correlation analysis template
library(jsonlite)

# Load data
if (length(uploaded_files) > 0) {
    data <- read.csv(uploaded_files[1])
} else {
    data <- data.frame(input_data)
}

# Calculate correlations
numeric_cols <- sapply(data, is.numeric)
numeric_data <- data[numeric_cols]

if (ncol(numeric_data) >= 2) {
    cor_matrix <- cor(numeric_data, use = "complete.obs")
    
    save_result("correlation_matrix", cor_matrix)
    save_result("variables", colnames(numeric_data))
}

save_result("total_records", nrow(data))
```

#### File Processing (Shell)
```bash
#!/bin/bash
# File processing template

echo "Processing uploaded files..."

# Count files and lines
file_count=$(ls *.csv *.json 2>/dev/null | wc -l)
total_lines=0

for file in *.csv *.json; do
    if [ -f "$file" ]; then
        lines=$(wc -l < "$file")
        total_lines=$((total_lines + lines))
        echo "Processed $file: $lines lines"
    fi
done

# Create summary
cat > processing_summary.json << EOF
{
    "files_processed": $file_count,
    "total_lines": $total_lines,
    "processing_date": "$(date -Iseconds)",
    "status": "completed"
}
EOF

echo "Processing complete: $file_count files, $total_lines lines"
```

## Security Features

### Sandboxing
- All scripts run in isolated Docker containers
- No network access (network_mode='none')
- Limited filesystem access (only workspace directory)
- Resource limits (memory, CPU, timeout)

### Script Validation
Scripts are automatically validated for dangerous patterns:

- **Python**: Blocks `exec()`, `eval()`, file operations, network access
- **R**: Blocks system calls, package installation, file operations
- **Shell**: Blocks destructive commands, network tools, system modifications
- **Node.js**: Blocks filesystem access, child processes, network modules

### Resource Limits
- **Memory**: 512MB default (configurable)
- **CPU**: 2 cores maximum
- **Timeout**: 300 seconds default (configurable)
- **File Size**: 500MB per file, 20 files maximum

## Error Handling

### Common Error Types

1. **Security Validation Failed**
   ```json
   {
     "error": "Script failed security validation: ['eval(' detected]"
   }
   ```

2. **Timeout Exceeded**
   ```json
   {
     "error": "Script execution timeout exceeded (300 seconds)"
   }
   ```

3. **Resource Limit Exceeded**
   ```json
   {
     "error": "Container execution failed: memory limit exceeded"
   }
   ```

4. **Script Runtime Error**
   ```json
   {
     "error": "NameError: name 'undefined_variable' is not defined",
     "traceback": "..."
   }
   ```

## Best Practices

### Script Development
1. **Keep scripts focused**: One script should do one thing well
2. **Handle errors gracefully**: Use try-catch blocks for robust execution
3. **Use parameters**: Make scripts configurable with parameters
4. **Save intermediate results**: Use `save_result()` for important findings
5. **Add logging**: Use print statements to track execution progress

### Performance Optimization
1. **Minimize data loading**: Only load necessary data
2. **Use efficient algorithms**: Consider computational complexity
3. **Set appropriate timeouts**: Balance between completion and resource usage
4. **Process data in chunks**: For large datasets, process incrementally

### Security Considerations
1. **Avoid dangerous operations**: Don't use file system, network, or system calls
2. **Validate inputs**: Check parameters and data before processing
3. **Limit resource usage**: Be mindful of memory and CPU consumption
4. **Use safe libraries**: Stick to approved data processing libraries

## Examples

See the `examples/` directory for comprehensive examples:

- `script_execution_demo.py`: Full-featured demo of all script types
- `simple_script_execution.py`: Simple examples for quick testing

## Troubleshooting

### Script Won't Execute
1. Check script syntax and security validation
2. Verify authentication and permissions
3. Ensure resource limits are appropriate
4. Check server logs for detailed error messages

### Results Not Available
1. Wait for job completion (check status endpoint)
2. Verify job completed successfully
3. Check for privacy constraints (minimum cohort size)
4. Ensure results were saved using `save_result()`

### Performance Issues
1. Reduce script complexity or data size
2. Increase timeout limits
3. Optimize algorithms and data structures
4. Consider breaking large jobs into smaller pieces

## API Reference

For complete API documentation, visit `/docs` on your running server instance.