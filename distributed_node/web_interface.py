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
    <style>
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px; 
            margin: 0 auto; 
            padding: 20px;
            background: #f5f5f5;
        }
        .container { 
            background: white; 
            padding: 30px; 
            border-radius: 10px; 
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #eee;
        }
        .section {
            margin: 30px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #007bff;
        }
        .form-group {
            margin: 15px 0;
        }
        label {
            display: block;
            font-weight: bold;
            margin-bottom: 5px;
            color: #333;
        }
        input, textarea, select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            font-size: 14px;
        }
        textarea {
            height: 200px;
            font-family: 'Monaco', 'Menlo', monospace;
        }
        button {
            background: #007bff;
            color: white;
            padding: 12px 24px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px 5px;
        }
        button:hover { background: #0056b3; }
        .btn-secondary { background: #6c757d; }
        .btn-secondary:hover { background: #545b62; }
        .results {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .code {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            padding: 15px;
            border-radius: 5px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 12px;
            white-space: pre-wrap;
        }
        .status { 
            padding: 5px 10px; 
            border-radius: 3px; 
            font-size: 12px;
            font-weight: bold;
        }
        .status-completed { background: #d4edda; color: #155724; }
        .status-running { background: #fff3cd; color: #856404; }
        .status-failed { background: #f8d7da; color: #721c24; }
        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .example-script {
            background: #e7f3ff;
            border: 1px solid #b8daff;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
    </style>
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
            <div class="grid">
                <div>
                    <h4>🏥 Clinical Trial Data</h4>
                    <p><strong>150 subjects</strong> - Parkinson's disease research</p>
                    <p>Columns: subject_id, age, sex, diagnosis, visit, UPDRS scores, quality of life</p>
                </div>
                <div>
                    <h4>🧠 Imaging Data</h4>
                    <p><strong>100 scans</strong> - T1, DTI, fMRI neuroimaging</p>
                    <p>Columns: subject_id, scan_type, quality, motion_score, file_path</p>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>🧪 Try It Out - Submit Analysis Script</h2>
            
            <form id="analysisForm">
                <div class="form-group">
                    <label>Data Catalog:</label>
                    <select id="catalog" name="catalog">
                        <option value="clinical_trial_data">Clinical Trial Data (150 subjects)</option>
                        <option value="imaging_data">Imaging Data (100 scans)</option>
                        <option value="demo_dataset">Demo Dataset (50 records)</option>
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
                    <label>Analysis Script:</label>
                    <textarea id="script_content" name="script_content" placeholder="Enter your Python or R script here...">import pandas as pd
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

    <script>
        let currentJobId = null;
        
        function loadExample(type) {
            const textarea = document.getElementById('script_content');
            
            if (type === 'demographics') {
                textarea.value = `import pandas as pd
import os
import json
from datetime import datetime

print("📊 Demographics Analysis Starting...")

# Load clinical data
data_root = os.environ.get('DATA_ROOT', './data')
subjects_path = os.path.join(data_root, 'catalogs', 'clinical_trial_data', 'subjects.csv')

if os.path.exists(subjects_path):
    df = pd.read_csv(subjects_path)
    print(f"📂 Loaded {len(df)} subjects")
    
    # Calculate demographics
    result = {
        "analysis_type": "demographics",
        "total_subjects": len(df),
        "age_statistics": {
            "mean": float(df['age'].mean()),
            "std": float(df['age'].std()),
            "min": int(df['age'].min()),
            "max": int(df['age'].max())
        },
        "sex_distribution": df['sex'].value_counts().to_dict(),
        "diagnosis_breakdown": df['diagnosis'].value_counts().to_dict(),
        "visit_distribution": df['visit'].value_counts().to_dict(),
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"✅ Demographics analysis complete!")
    print(f"👥 {result['total_subjects']} subjects analyzed")
    
    # Save results
    with open(os.environ.get('OUTPUT_FILE', 'output.json'), 'w') as f:
        json.dump(result, f, indent=2)
else:
    print("❌ Data file not found")
    result = {"error": "Data not found"}
    with open(os.environ.get('OUTPUT_FILE', 'output.json'), 'w') as f:
        json.dump(result, f)`;
            } else if (type === 'correlation') {
                textarea.value = `import pandas as pd
import numpy as np
from scipy import stats
import os
import json
from datetime import datetime

print("📈 Correlation Analysis Starting...")

# Load data
data_root = os.environ.get('DATA_ROOT', './data')
subjects = pd.read_csv(f'{data_root}/catalogs/clinical_trial_data/subjects.csv')
outcomes = pd.read_csv(f'{data_root}/catalogs/clinical_trial_data/outcomes.csv')

print(f"📂 Loaded {len(subjects)} subjects, {len(outcomes)} outcomes")

# Merge datasets
data = subjects.merge(outcomes, on=['subject_id', 'visit'], how='inner')
print(f"🔗 Merged dataset: {len(data)} records")

# Correlation analysis
if len(data) >= 10:
    corr_age_updrs, p_age_updrs = stats.pearsonr(data['age'], data['UPDRS_total'])
    corr_qol_updrs, p_qol_updrs = stats.pearsonr(data['quality_of_life'], data['UPDRS_change'])
    
    result = {
        "analysis_type": "correlation_analysis",
        "sample_size": len(data),
        "correlations": {
            "age_vs_UPDRS_total": {
                "correlation": float(corr_age_updrs),
                "p_value": float(p_age_updrs),
                "significant": p_age_updrs < 0.05
            },
            "quality_of_life_vs_UPDRS_change": {
                "correlation": float(corr_qol_updrs), 
                "p_value": float(p_qol_updrs),
                "significant": p_qol_updrs < 0.05
            }
        },
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"✅ Correlation analysis complete!")
    print(f"📊 Age vs UPDRS: r={corr_age_updrs:.3f}, p={p_age_updrs:.3f}")
    print(f"📊 QoL vs UPDRS change: r={corr_qol_updrs:.3f}, p={p_qol_updrs:.3f}")
else:
    result = {"error": "Insufficient data for correlation analysis"}

# Save results
with open(os.environ.get('OUTPUT_FILE', 'output.json'), 'w') as f:
    json.dump(result, f, indent=2)`;
            }
        }
        
        async function submitJob() {
            const catalog = document.getElementById('catalog').value;
            const scriptType = document.getElementById('script_type').value;
            const scriptContent = document.getElementById('script_content').value;
            
            if (!scriptContent.trim()) {
                alert('Please enter a script!');
                return;
            }
            
            try {
                // Step 1: Authenticate
                const authResponse = await fetch('/api/v1/auth/token', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: 'username=demo&password=demo'
                });
                
                const authData = await authResponse.json();
                const token = authData.access_token;
                
                // Step 2: Submit job
                const jobResponse = await fetch('/api/v1/jobs', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        target_node_id: 'node-1',
                        data_catalog_name: catalog,
                        script_type: scriptType,
                        script_content: scriptContent,
                        parameters: { submitted_via: 'web_interface' }
                    })
                });
                
                const jobData = await jobResponse.json();
                currentJobId = jobData.job_id;
                
                document.getElementById('results').style.display = 'block';
                document.getElementById('resultsContent').innerHTML = `
                    <p><strong>Job Submitted:</strong> ${currentJobId}</p>
                    <p><span class="status status-running">RUNNING</span> Executing your script...</p>
                    <button onclick="checkResults()">🔄 Check Results</button>
                `;
                
                // Auto-check results after a delay
                setTimeout(checkResults, 3000);
                
            } catch (error) {
                document.getElementById('results').style.display = 'block';
                document.getElementById('resultsContent').innerHTML = `
                    <div class="error">
                        <strong>Error:</strong> ${error.message}
                    </div>
                `;
            }
        }
        
        async function checkResults() {
            if (!currentJobId) return;
            
            try {
                const response = await fetch(`/api/v1/jobs/${currentJobId}`);
                const result = await response.json();
                
                let statusClass = 'status-running';
                if (result.status === 'completed') statusClass = 'status-completed';
                if (result.status === 'failed') statusClass = 'status-failed';
                
                let content = `
                    <p><strong>Job ID:</strong> ${result.job_id}</p>
                    <p><strong>Status:</strong> <span class="status ${statusClass}">${result.status.toUpperCase()}</span></p>
                    <p><strong>Execution Time:</strong> ${result.execution_time?.toFixed(2) || 'N/A'}s</p>
                    <p><strong>Records Processed:</strong> ${result.records_processed || 'N/A'}</p>
                `;
                
                if (result.status === 'completed' && result.result_data) {
                    content += `
                        <div class="results">
                            <h4>📊 Analysis Results:</h4>
                            <div class="code">${JSON.stringify(result.result_data, null, 2)}</div>
                        </div>
                    `;
                } else if (result.status === 'failed') {
                    content += `
                        <div class="error">
                            <strong>Error:</strong> ${result.error_message || 'Unknown error'}
                        </div>
                    `;
                } else if (result.status === 'blocked') {
                    content += `
                        <div class="error">
                            <strong>Privacy Block:</strong> ${result.result_data?.message || 'Results blocked due to privacy constraints'}
                        </div>
                    `;
                }
                
                if (result.status === 'running' || result.status === 'queued') {
                    content += `<button onclick="checkResults()">🔄 Check Again</button>`;
                }
                
                document.getElementById('resultsContent').innerHTML = content;
                
            } catch (error) {
                document.getElementById('resultsContent').innerHTML = `
                    <div class="error">Error checking results: ${error.message}</div>
                `;
            }
        }
    </script>
</body>
</html>
"""

def get_web_interface_html(node_id: str, base_url: str) -> str:
    """Get the web interface HTML with dynamic values"""
    return SIMPLE_WEB_INTERFACE.replace("{{node_id}}", node_id).replace("{{base_url}}", base_url)
