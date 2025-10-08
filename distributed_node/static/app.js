/**
 * StimNet Research Platform - Web Interface JavaScript
 * Handles form submission, job execution, and results display
 */

let currentJobId = null;

/**
 * Load available data catalogs from the API
 */
async function loadDataCatalogs() {
    try {
        const response = await fetch('/api/v1/data-catalogs');
        const catalogs = await response.json();
        
        // Update the dropdown
        const catalogSelect = document.getElementById('catalog');
        catalogSelect.innerHTML = ''; // Clear existing options
        
        catalogs.forEach(catalog => {
            const option = document.createElement('option');
            option.value = catalog.name;
            option.textContent = `${catalog.name} (${catalog.description || 'No description'})`;
            catalogSelect.appendChild(option);
        });
        
        // Update the catalog information display
        const catalogsInfo = document.getElementById('catalogsInfo');
        if (catalogs.length === 0) {
            catalogsInfo.innerHTML = '<p>No data catalogs available.</p>';
        } else {
            let html = '<div class="grid">';
            catalogs.forEach(catalog => {
                const icon = catalog.name.includes('clinical') ? '🏥' : 
                           catalog.name.includes('imaging') ? '🧠' : '📊';
                const recordCount = catalog.record_count || 'Unknown';
                html += `
                    <div>
                        <h4>${icon} ${catalog.name}</h4>
                        <p><strong>${catalog.description || 'No description'}</strong></p>
                        <p style="font-size: 0.9em; color: #666;">Type: ${catalog.data_type || 'N/A'}</p>
                    </div>
                `;
            });
            html += '</div>';
            catalogsInfo.innerHTML = html;
        }
        
        console.log(`Loaded ${catalogs.length} data catalogs`);
    } catch (error) {
        console.error('Error loading data catalogs:', error);
        
        // Fallback to hardcoded options if API fails
        const catalogSelect = document.getElementById('catalog');
        catalogSelect.innerHTML = `
            <option value="clinical_trial_data">Clinical Trial Data</option>
            <option value="imaging_data">Imaging Data</option>
            <option value="demo_dataset">Demo Dataset</option>
        `;
        
        const catalogsInfo = document.getElementById('catalogsInfo');
        catalogsInfo.innerHTML = '<p style="color: orange;">⚠️ Could not load catalog information from server. Using defaults.</p>';
    }
}

/**
 * Handle script file upload
 */
async function handleScriptUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
        // Show uploading message
        const textarea = document.getElementById('script_content');
        textarea.value = '// Uploading script...';
        
        // Create form data
        const formData = new FormData();
        formData.append('file', file);
        
        // Upload file
        const response = await fetch('/api/v1/upload/script', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Upload failed');
        }
        
        const result = await response.json();
        
        // Populate textarea with uploaded script content
        textarea.value = result.content;
        
        // Update script type based on file extension
        const scriptType = document.getElementById('script_type');
        if (file.name.endsWith('.py')) {
            scriptType.value = 'python';
        } else if (file.name.endsWith('.r') || file.name.endsWith('.R')) {
            scriptType.value = 'r';
        }
        
        console.log(`Script uploaded: ${result.filename} (${result.size_bytes} bytes)`);
        alert(`✅ Script uploaded successfully: ${result.filename}`);
        
    } catch (error) {
        console.error('Error uploading script:', error);
        alert(`❌ Error uploading script: ${error.message}`);
        document.getElementById('script_content').value = '';
    }
}

/**
 * Handle data file upload
 */
async function handleDataUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    
    try {
        // Show uploading message
        const uploadedFiles = document.getElementById('uploaded_files');
        uploadedFiles.innerHTML = '<p>⏳ Uploading...</p>';
        
        // Create form data
        const formData = new FormData();
        formData.append('file', file);
        
        // Upload file
        const response = await fetch('/api/v1/upload/data', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error('Upload failed');
        }
        
        const result = await response.json();
        
        // Show uploaded file info
        const sizeKB = (result.size_bytes / 1024).toFixed(2);
        uploadedFiles.innerHTML = `
            <div class="results">
                <p><strong>✅ File uploaded:</strong> ${result.filename}</p>
                <p><strong>Size:</strong> ${sizeKB} KB</p>
                <p><strong>Path:</strong> <code>${result.path}</code></p>
                <p style="font-size: 0.9em; color: #666;">
                    Use this path in your script: <code>uploads/data/${result.saved_as}</code>
                </p>
            </div>
        `;
        
        // Add example code to script textarea
        const textarea = document.getElementById('script_content');
        const exampleCode = `\n\n# Load uploaded data file:\n# file_path = "uploads/data/${result.saved_as}"\n`;
        
        if (!textarea.value.includes(result.saved_as)) {
            textarea.value += exampleCode;
        }
        
        console.log(`Data file uploaded: ${result.filename} (${result.size_bytes} bytes)`);
        
    } catch (error) {
        console.error('Error uploading data file:', error);
        document.getElementById('uploaded_files').innerHTML = `
            <div class="error">❌ Error uploading file: ${error.message}</div>
        `;
    }
}

/**
 * Initialize the page when DOM is loaded
 */
document.addEventListener('DOMContentLoaded', function() {
    loadDataCatalogs();
});

/**
 * Load example script into the textarea
 * @param {string} type - 'demographics' or 'correlation'
 */
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

/**
 * Submit analysis job to the server
 */
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

/**
 * Check the status and results of the current job
 */
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
