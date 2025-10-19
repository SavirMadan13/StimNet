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
            <h2>📝 Submit Analysis Request</h2>
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
                    <label for="research_question">Research Question *</label>
                    <textarea id="research_question" name="research_question" required placeholder="What specific research question are you trying to answer?"></textarea>
                </div>

                <div class="form-group">
                    <label for="analysis_description">Analysis Description *</label>
                    <textarea id="analysis_description" name="analysis_description" required placeholder="Describe your analysis methodology and approach"></textarea>
                </div>

                <div class="form-group">
                    <label for="methodology">Methodology</label>
                    <textarea id="methodology" name="methodology" placeholder="Detailed methodology (optional)"></textarea>
                </div>

                <div class="form-group">
                    <label for="expected_outcomes">Expected Outcomes</label>
                    <textarea id="expected_outcomes" name="expected_outcomes" placeholder="What outcomes do you expect from this analysis?"></textarea>
                </div>

                <div class="form-row">
                    <div class="form-group">
                        <label for="data_catalog">Data Catalog *</label>
                        <select id="data_catalog" name="data_catalog" required onchange="loadScoreTimelineOptions()">
                            <option value="">Select a dataset...</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label for="script_type">Script Type *</label>
                        <select id="script_type" name="script_type" required>
                            <option value="python">Python</option>
                            <option value="r">R</option>
                        </select>
                    </div>
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
                    <label for="script_content">Analysis Script *</label>
                    <textarea id="script_content" name="script_content" required placeholder="Enter your Python or R script here..."># Import data loading helper (automatically available)
from data_loader import load_data, save_results

print("🔍 Starting analysis...")

# Load data from selected catalog (no paths needed!)
data = load_data()

# Access your data by name
subjects = data['subjects']
print(f"📊 Loaded {len(subjects)} subjects")

# Your analysis here
result = {
    "sample_size": len(subjects),
    "age_mean": float(subjects['age'].mean()),
    "sex_distribution": subjects['sex'].value_counts().to_dict(),
    "analysis_complete": True
}

# Save results
save_results(result)
print(f"✅ Analysis complete!")
</textarea>
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

                <button type="button" onclick="submitRequest()">📝 Submit Analysis Request</button>
                <button type="button" onclick="loadExample('demographics')">📊 Load Demographics Example</button>
                <button type="button" onclick="loadExample('correlation')">📈 Load Correlation Example</button>
                <button type="button" onclick="loadExample('damage_score')">🧠 Load Damage Score Example</button>
            </form>
        </div>

        <div class="section">
            <h2>📋 Example Scripts</h2>
            
            <div class="example-script">
                <h4>📊 Demographics Analysis</h4>
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
        </div>

        <div id="results" style="display:none;">
            <div class="section">
                <h2>📊 Request Status</h2>
                <div id="resultsContent"></div>
            </div>
        </div>

        <div class="section">
            <h2>🔍 View Analysis Results</h2>
            <p>Enter your request ID to view the results of your analysis:</p>
            
            <div class="form-group">
                <label for="request_id_input">Request ID</label>
                <input type="text" id="request_id_input" placeholder="Enter your request ID (e.g., a49ff15b-6837-4057-b08a-480002ccccd9)">
                <button type="button" onclick="viewResults()">🔍 View Results</button>
            </div>
            
            <div id="resultsView" style="display:none;">
                <h3>📊 Analysis Results</h3>
                <div id="resultsViewContent"></div>
            </div>
        </div>

        <div class="section">
            <h2>🔗 API Access</h2>
            <p><strong>For Developers:</strong></p>
            <ul>
                <li><a href="/docs" target="_blank">📚 API Documentation (Swagger)</a></li>
                <li><a href="/api/v1/data-catalogs" target="_blank">📊 Data Catalogs API</a></li>
                <li><a href="/api/v1/analysis-requests" target="_blank">📝 Analysis Requests API</a></li>
                <li><a href="/health" target="_blank">❤️ Health Check</a></li>
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
    </div>

    <script src="/static/app.js?v=2"></script>
</body>
</html>
"""

def get_web_interface_html(node_id: str, base_url: str) -> str:
    """Get the web interface HTML with dynamic values"""
    return SIMPLE_WEB_INTERFACE.replace("{{node_id}}", node_id).replace("{{base_url}}", base_url)