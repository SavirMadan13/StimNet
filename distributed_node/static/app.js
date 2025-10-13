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
            option.value = catalog.id || catalog.name;
            const recordInfo = catalog.total_records ? ` - ${catalog.total_records} records` : '';
            option.textContent = `${catalog.name}${recordInfo}`;
            catalogSelect.appendChild(option);
        });
        
        // Update the catalog information display
        const catalogsInfo = document.getElementById('catalogsInfo');
        if (catalogs.length === 0) {
            catalogsInfo.innerHTML = '<p>No data catalogs available.</p>';
        } else {
            let html = '<div class="grid">';
            catalogs.forEach(catalog => {
                const icon = catalog.id.includes('clinical') ? '🏥' : 
                           catalog.id.includes('imaging') ? '🧠' : '📊';
                const recordCount = catalog.total_records || 'Unknown';
                
                // Build files list with column details
                let filesHtml = '';
                if (catalog.files && catalog.files.length > 0) {
                    filesHtml = '<div style="font-size: 0.85em; margin: 10px 0;">';
                    catalog.files.forEach(file => {
                        const count = file.actual_record_count || file.record_count || '?';
                        const status = file.exists ? '✅' : '❌';
                        
                        // Build column information
                        let columnsHtml = '';
                        if (file.columns && file.columns.length > 0) {
                            columnsHtml = '<ul style="margin: 5px 0; padding-left: 25px; font-size: 0.9em; color: #555;">';
                            file.columns.forEach(col => {
                                // If column is an object with type info
                                if (typeof col === 'object' && col.name) {
                                    const type = col.type || 'unknown';
                                    const typeColor = type === 'float' ? '#0066cc' : 
                                                    type === 'int' ? '#009900' : 
                                                    type === 'string' ? '#cc6600' : '#666';
                                    columnsHtml += `<li><code style="color: ${typeColor}; font-weight: 600;">${col.name}</code> <span style="color: #999;">(${type})</span>${col.description ? `: ${col.description}` : ''}</li>`;
                                } else {
                                    // If column is just a string name
                                    columnsHtml += `<li><code style="color: #666;">${col}</code></li>`;
                                }
                            });
                            columnsHtml += '</ul>';
                        }
                        
                        filesHtml += `
                            <div style="margin-bottom: 12px; padding: 8px; background: #f9f9f9; border-radius: 4px;">
                                <div style="font-weight: 600; margin-bottom: 4px;">
                                    ${status} <strong>${file.name}</strong> <span style="color: #666;">(${count} records)</span>
                                </div>
                                ${file.description ? `<div style="color: #666; font-size: 0.9em; margin-bottom: 4px;">${file.description}</div>` : ''}
                                ${columnsHtml}
                            </div>
                        `;
                    });
                    filesHtml += '</div>';
                }
                
                // Build metadata display
                let metadataHtml = '';
                if (catalog.metadata) {
                    const meta = catalog.metadata;
                    if (meta.study_name) metadataHtml += `<p style="font-size: 0.85em;"><strong>Study:</strong> ${meta.study_name}</p>`;
                    if (meta.date_range) metadataHtml += `<p style="font-size: 0.85em;"><strong>Period:</strong> ${meta.date_range}</p>`;
                }
                
                html += `
                    <div>
                        <h4>${icon} ${catalog.name}</h4>
                        <p><strong>${catalog.description}</strong></p>
                        <p style="font-size: 0.9em; color: #666;">
                            📊 ${recordCount} total records | 
                            🔒 Privacy: ${catalog.privacy_level || 'high'} | 
                            👥 Min cohort: ${catalog.min_cohort_size || 10}
                        </p>
                        ${filesHtml}
                        ${metadataHtml}
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
        textarea.value = `# Import data loading helper
from data_loader import load_data, save_results

print("📊 Demographics Analysis Starting...")

# Load data from selected catalog (no paths needed!)
data = load_data()
subjects = data['subjects']

print(f"📂 Loaded {len(subjects)} subjects")

# Calculate demographics
result = {
    "analysis_type": "demographics",
    "total_subjects": len(subjects),
    "age_statistics": {
        "mean": float(subjects['age'].mean()),
        "std": float(subjects['age'].std()),
        "min": int(subjects['age'].min()),
        "max": int(subjects['age'].max())
    },
    "sex_distribution": subjects['sex'].value_counts().to_dict(),
    "diagnosis_breakdown": subjects['diagnosis'].value_counts().to_dict(),
    "visit_distribution": subjects['visit'].value_counts().to_dict()
}

print(f"✅ Demographics analysis complete!")
print(f"👥 {result['total_subjects']} subjects analyzed")

# Save results
save_results(result)`;
    } else if (type === 'correlation') {
        textarea.value = `# Import data loading helper
from data_loader import load_data, save_results
from scipy import stats

print("📈 Correlation Analysis Starting...")

# Load data from selected catalog (no paths needed!)
data_dict = load_data()
subjects = data_dict['subjects']
outcomes = data_dict['outcomes']

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
        }
    }
    
    print(f"✅ Correlation analysis complete!")
    print(f"📊 Age vs UPDRS: r={corr_age_updrs:.3f}, p={p_age_updrs:.3f}")
    print(f"📊 QoL vs UPDRS change: r={corr_qol_updrs:.3f}, p={p_qol_updrs:.3f}")
else:
    result = {"error": "Insufficient data for correlation analysis"}

# Save results
save_results(result)`;
    } else if (type === 'damage_score') {
        textarea.value = `# Import data loading helper
from data_loader import load_data, save_results
from scipy import stats
import numpy as np
import nibabel as nib

print("🧠 DBS VTA Damage Score Analysis Starting...")

# Load data from selected catalog
data = load_data()
vta_metadata = data['vta_metadata']
connectivity_map = data['connectivity_map']

print(f"📂 Loaded {len(vta_metadata)} VTA subjects")
print(f"📂 Loaded connectivity map: {connectivity_map.shape}")

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

print(f"✅ Damage score analysis complete!")
print(f"📊 Damage-Outcome correlation: r={corr:.3f}, p={p_val:.3f}")
print(f"📊 Mean damage score: {mean_damage:.3f}")
print(f"📊 Mean clinical improvement: {mean_improvement:.1f}%")

# Save results
save_results(result)`;
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
