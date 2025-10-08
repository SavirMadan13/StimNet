"""
Simple web interface for the distributed framework
Makes it easy for users to try out the system
"""
from fastapi import Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os

# HTML template for the web interface
SIMPLE_WEB_INTERFACE = """
<!DOCTYPE html>
<html>
<head>
    <title>StimNet Research Platform</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" href="/static/styles.css">
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧠 StimNet Research Platform</h1>
            <p>Collaborative neuroscience data analysis across institutions</p>
            <p><strong>Node:</strong> {{node_id}} | <strong>Status:</strong> <span class="status status-completed">HEALTHY</span></p>
        </div>

        <div class="section">
            <h2>📊 Available Data Catalogs</h2>
            <div id="catalogsInfo">
                <p>Loading available datasets...</p>
            </div>
        </div>

        <div class="section">
            <h2>🧪 Try It Out - Submit Analysis Script</h2>
            
            <form id="analysisForm">
                <div class="form-group">
                    <label>Data Catalog:</label>
                    <select id="catalog" name="catalog">
                        <option value="">Loading datasets...</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>Script Type:</label>
                    <select id="script_type" name="script_type">
                        <option value="python">Python</option>
                        <option value="r">R</option>
                    </select>
                </div>

                <div class="form-group">
                    <label>📁 Upload Script File (optional):</label>
                    <input type="file" id="script_file" accept=".py,.r,.R" onchange="handleScriptUpload(event)">
                    <p style="font-size: 0.9em; color: #666;">Upload a .py or .R file to automatically populate the script field</p>
                </div>

                <div class="form-group">
                    <label>📊 Upload Data File (optional):</label>
                    <input type="file" id="data_file" accept=".nii,.nii.gz,.csv,.tsv,.npy,.npz,.mat,.json" onchange="handleDataUpload(event)">
                    <p style="font-size: 0.9em; color: #666;">Upload data files (.nii, .csv, etc.) to use in your analysis</p>
                    <div id="uploaded_files"></div>
                </div>

                <div class="form-group">
                    <label>Analysis Script:</label>
                    <textarea id="script_content" name="script_content" placeholder="Enter your Python or R script here, or upload a file above...">import pandas as pd
import os
import json
from datetime import datetime

print("🔍 Starting analysis...")

# Load data
data_root = os.environ.get('DATA_ROOT', './data')
subjects_path = os.path.join(data_root, 'catalogs', 'clinical_trial_data', 'subjects.csv')

if os.path.exists(subjects_path):
    df = pd.read_csv(subjects_path)
    print(f"📊 Loaded {len(df)} subjects")
    
    # Your analysis here
    result = {
        "sample_size": len(df),
        "age_mean": float(df['age'].mean()),
        "sex_distribution": df['sex'].value_counts().to_dict(),
        "analysis_complete": True,
        "timestamp": datetime.now().isoformat()
    }
    
    # Save results
    with open(os.environ.get('OUTPUT_FILE', 'output.json'), 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"✅ Analysis complete: {result}")
else:
    print("❌ Data not found")
</textarea>
                </div>

                <button type="button" onclick="submitJob()">🚀 Run Analysis</button>
                <button type="button" onclick="loadExample('demographics')">📊 Load Demographics Example</button>
                <button type="button" onclick="loadExample('correlation')">📈 Load Correlation Example</button>
            </form>
        </div>

        <div class="section">
            <h2>📋 Example Scripts</h2>
            
            <div class="example-script">
                <h4>📊 Demographics Analysis</h4>
                <div class="code">import pandas as pd
import os
import json

# Load clinical data
data_root = os.environ.get('DATA_ROOT', './data')
subjects = pd.read_csv(f'{data_root}/catalogs/clinical_trial_data/subjects.csv')

# Calculate demographics
result = {
    "total_subjects": len(subjects),
    "age_stats": {
        "mean": float(subjects['age'].mean()),
        "std": float(subjects['age'].std())
    },
    "sex_distribution": subjects['sex'].value_counts().to_dict(),
    "diagnosis_breakdown": subjects['diagnosis'].value_counts().to_dict()
}

# Save results
with open(os.environ.get('OUTPUT_FILE', 'output.json'), 'w') as f:
    json.dump(result, f)</div>
            </div>

            <div class="example-script">
                <h4>📈 Correlation Analysis</h4>
                <div class="code">import pandas as pd
import numpy as np
from scipy import stats
import os
import json

# Load data
data_root = os.environ.get('DATA_ROOT', './data')
subjects = pd.read_csv(f'{data_root}/catalogs/clinical_trial_data/subjects.csv')
outcomes = pd.read_csv(f'{data_root}/catalogs/clinical_trial_data/outcomes.csv')

# Merge datasets
data = subjects.merge(outcomes, on=['subject_id', 'visit'])

# Correlation analysis
corr, p_val = stats.pearsonr(data['age'], data['UPDRS_total'])

result = {
    "correlation": float(corr),
    "p_value": float(p_val),
    "sample_size": len(data),
    "significant": p_val < 0.05
}

with open(os.environ.get('OUTPUT_FILE', 'output.json'), 'w') as f:
    json.dump(result, f)</div>
            </div>
        </div>

        <div id="results" style="display:none;">
            <div class="section">
                <h2>📊 Analysis Results</h2>
                <div id="resultsContent"></div>
            </div>
        </div>

        <div class="section">
            <h2>🔗 API Access</h2>
            <p><strong>For Developers:</strong></p>
            <ul>
                <li><a href="/docs" target="_blank">📚 API Documentation (Swagger)</a></li>
                <li><a href="/api/v1/data-catalogs" target="_blank">📊 Data Catalogs API</a></li>
                <li><a href="/health" target="_blank">❤️ Health Check</a></li>
            </ul>
            
            <p><strong>Python Client SDK:</strong></p>
            <div class="code">from client_sdk import DistributedClient

async with DistributedClient("{{base_url}}") as client:
    await client.authenticate("demo", "demo")
    job_id = await client.submit_script_file("my_analysis.py", 
                                           target_node_id="node-1",
                                           data_catalog_name="clinical_trial_data")
    result = await client.wait_for_job(job_id)</div>
        </div>
    </div>

    <script src="/static/app.js"></script>
</body>
</html>
"""

def get_web_interface_html(node_id: str, base_url: str) -> str:
    """Get the web interface HTML with dynamic values"""
    return SIMPLE_WEB_INTERFACE.replace("{{node_id}}", node_id).replace("{{base_url}}", base_url)
