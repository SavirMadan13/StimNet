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
            <h1>StimNet Research Platform</h1>
            <p>Collaborative neuroscience data analysis across institutions</p>
            <p><strong>Node:</strong> {{node_id}} | <strong>Status:</strong> <span class="status status-completed">HEALTHY</span></p>
            <h1>🧠 </h1>
        </div>

        <div class="section">
            <h2>Available Data Catalogs</h2>
            <div id="catalogsInfo">
                <p>Loading available datasets...</p>
            </div>
        </div>

        <div class="section">
            <h2>Submit Analysis Request</h2>
            <p>Submit a request for data analysis. Your request will be reviewed by the data host before execution.</p>
            
            <form id="requestForm">
                <div class="form-row">
                    <div class="form-group">
                        <label for="requester_name">Full Name *</label>
                        <input type="text" id="requester_name" name="requester_name" required>
                    </div>
                    <div class="form-group">
                        <label for="requester_institution">Institution *</label>
                        <input type="text" id="requester_institution" name="requester_institution" required>
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="requester_email">Email Address *</label>
                        <input type="email" id="requester_email" name="requester_email" required>
                    </div>
                    <div class="form-group">
                        <label for="requester_affiliation">Department/Affiliation</label>
                        <input type="text" id="requester_affiliation" name="requester_affiliation">
                    </div>
                </div>

                <div class="form-group">
                    <label for="analysis_title">Analysis Title *</label>
                    <input type="text" id="analysis_title" name="analysis_title" required placeholder="Brief title describing your analysis">
                </div>

                <div class="form-group">
                    <label for="analysis_description">Analysis Description *</label>
                    <textarea id="analysis_description" name="analysis_description" required placeholder="Describe your analysis methodology and approach"></textarea>
                </div>

                <div class="form-group">
                    <label for="data_catalog">Data Catalog *</label>
                    <select id="data_catalog" name="data_catalog" required onchange="loadScoreTimelineOptions()">
                        <option value="">Select a dataset...</option>
                    </select>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="selected_score">Score/Outcome Measure</label>
                        <select id="selected_score" name="selected_score">
                            <option value="">Select score option...</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="selected_timeline">Timeline/Analysis Period</label>
                        <select id="selected_timeline" name="selected_timeline">
                            <option value="">Select timeline option...</option>
                        </select>
                    </div>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="priority">Priority</label>
                        <select id="priority" name="priority">
                            <option value="low">Low</option>
                            <option value="normal" selected>Normal</option>
                            <option value="high">High</option>
                            <option value="urgent">Urgent</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="estimated_duration">Estimated Duration</label>
                        <select id="estimated_duration" name="estimated_duration">
                            <option value="">Select duration...</option>
                            <option value="1 hour">1 hour</option>
                            <option value="2-4 hours">2-4 hours</option>
                            <option value="1 day">1 day</option>
                            <option value="2-3 days">2-3 days</option>
                            <option value="1 week">1 week</option>
                            <option value="2+ weeks">2+ weeks</option>
                        </select>
                    </div>
                </div>

                <div class="form-group">
                    <label for="script_type">Script Type *</label>
                    <select id="script_type" name="script_type" required onchange="handleScriptTypeChange()">
                        <option value="">Select a script type...</option>
                        <option value="demographics">Demographics Analysis</option>
                        <option value="correlation">Correlation Analysis</option>
                        <option value="damage_score">DBS Damage Score Analysis</option>
                        <option value="custom">Custom Script</option>
                    </select>
                </div>

                <div class="form-group" id="script_content_group" style="display: none;">
                    <label for="script_content">Analysis Script *</label>
                    <textarea id="script_content" name="script_content" placeholder="Enter your Python script here..."></textarea>
                </div>

                <div class="form-group">
                    <label>Upload Script File (optional):</label>
                    <input type="file" id="script_file" accept=".py" onchange="handleScriptUpload(event)">
                    <p style="font-size: 0.9em; color: #666;">Upload a .py file to automatically populate the script field</p>
                </div>

                <div class="form-group">
                    <label>Upload Data File (optional):</label>
                    <input type="file" id="data_file" accept=".nii,.nii.gz,.csv,.tsv,.npy,.npz,.mat,.json" onchange="handleDataUpload(event)">
                    <p style="font-size: 0.9em; color: #666;">Upload data files (.nii, .csv, etc.) to use in your analysis</p>
                    <div id="uploaded_files"></div>
                </div>

                <button type="button" onclick="submitRequest()">Submit Analysis Request</button>
            </form>
        </div>


        <div id="results" style="display:none;">
            <div class="section">
                <h2>📊 Request Status</h2>
                <div id="resultsContent"></div>
            </div>
        </div>

        <div class="section">
            <h2>View Analysis Results</h2>
            <p>Enter your request ID to view the results of your analysis:</p>
            
            <div class="form-group">
                <label for="request_id_input">Request ID</label>
                <input type="text" id="request_id_input" placeholder="Enter your request ID (e.g., a49ff15b-6837-4057-b08a-480002ccccd9)">
                <button type="button" onclick="viewResults()">View Results</button>
            </div>
            
            <div id="resultsView" style="display:none;">
                <h3>Analysis Results</h3>
                <div id="resultsViewContent"></div>
            </div>
        </div>

        <div class="section">
            <h2>API Access</h2>
            <p><strong>For Developers:</strong></p>
            <ul>
                <li><a href="/docs" target="_blank">API Documentation (Swagger)</a></li>
                <li><a href="/api/v1/data-catalogs" target="_blank">Data Catalogs API</a></li>
                <li><a href="/api/v1/analysis-requests" target="_blank">Analysis Requests API</a></li>
                <li><a href="/health" target="_blank">Health Check</a></li>
            </ul>
            
            <p><strong>Python Client SDK:</strong></p>
            <div class="code">from client_sdk import DistributedClient

async with DistributedClient("{{base_url}}") as client:
    await client.authenticate("demo", "demo")
    request_id = await client.submit_analysis_request({
        "requester_name": "Dr. Smith",
        "requester_institution": "University of Research",
        "analysis_title": "Parkinson's Disease Analysis",
        "data_catalog_name": "clinical_trial_data",
        "script_content": "print('Hello World')"
    })
    result = await client.wait_for_request(request_id)</div>
        </div>

        <div class="section">
            <h2>Example Scripts</h2>
            
            <div class="example-script">
                <h4>Demographics Analysis</h4>
                <div class="code"># Import data loading helper
from data_loader import load_data, save_results

# Load data from selected catalog
data = load_data()
subjects = data['subjects']

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
save_results(result)</div>
            </div>

            <div class="example-script">
                <h4>📈 Correlation Analysis</h4>
                <div class="code"># Import data loading helper
from data_loader import load_data, save_results
from scipy import stats

# Load data from selected catalog
data_dict = load_data()
subjects = data_dict['subjects']
outcomes = data_dict['outcomes']

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

# Save results
save_results(result)</div>
            </div>

            <div class="example-script">
                <h4>DBS Damage Score Analysis</h4>
                <div class="code"># Import data loading helper
from data_loader import load_data, save_results
from scipy import stats
import numpy as np
import nibabel as nib

print("DBS VTA Damage Score Analysis Starting...")

# Load data from selected catalog
data = load_data()
vta_metadata = data['vta_metadata']
connectivity_map = data['connectivity_map']

print(f"Loaded {len(vta_metadata)} VTA subjects")
print(f"Loaded connectivity map: {connectivity_map.shape}")

# Calculate damage scores (overlap between VTA and connectivity map)
damage_scores = []
clinical_improvements = []

for idx, row in vta_metadata.iterrows():
    # In real analysis, load each VTA file and calculate overlap
    # For demo, we'll use synthetic damage scores
    # Simulate realistic correlation between damage and outcome
    base_damage = np.random.normal(0.5, 0.15)
    base_damage = max(0.1, min(0.9, base_damage))

    # Add some realistic noise
    noise = np.random.normal(0, 0.1)
    damage_score = base_damage + noise

    damage_scores.append(damage_score)
    clinical_improvements.append(row['clinical_improvement'])

# Convert to numpy arrays
damage_scores = np.array(damage_scores)
clinical_improvements = np.array(clinical_improvements)

# Calculate correlation
corr, p_val = stats.pearsonr(damage_scores, clinical_improvements)

# Additional statistics
mean_damage = float(np.mean(damage_scores))
mean_improvement = float(np.mean(clinical_improvements))

result = {
    "analysis_type": "dbs_damage_score",
    "sample_size": len(vta_metadata),
    "correlation": {
        "correlation_coefficient": float(corr),
        "p_value": float(p_val),
        "significant": p_val < 0.05
    },
    "summary_statistics": {
        "mean_damage_score": mean_damage,
        "mean_clinical_improvement": mean_improvement,
        "damage_score_range": [float(np.min(damage_scores)), float(np.max(damage_scores))],
        "improvement_range": [float(np.min(clinical_improvements)), float(np.max(clinical_improvements))]
    },
    "interpretation": "Higher damage scores indicate greater VTA overlap with connectivity map"
}

print(f"Damage score analysis complete!")
print(f"Damage-Outcome correlation: r={corr:.3f}, p={p_val:.3f}")
print(f"Mean damage score: {mean_damage:.3f}")
print(f"Mean clinical improvement: {mean_improvement:.1f}%")

# Save results
save_results(result)</div>
            </div>
        </div>
    </div>

    <script src="/static/app.js?v=2"></script>
</body>
</html>
"""

def get_web_interface_html(node_id: str, base_url: str) -> str:
    """Get the web interface HTML with dynamic values"""
    return SIMPLE_WEB_INTERFACE.replace("{{node_id}}", node_id).replace("{{base_url}}", base_url)