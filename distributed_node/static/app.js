/**
 * StimNet Research Platform - Web Interface JavaScript
 * Handles form submission, job execution, and results display
 */

let currentRequestId = null;

/**
 * Load available data catalogs with score/timeline options
 */
async function loadDataCatalogs() {
    try {
        const response = await fetch('/api/v1/data-catalogs-with-options');
        const catalogs = await response.json();
        
        // Update the dropdown
        const catalogSelect = document.getElementById('data_catalog');
        catalogSelect.innerHTML = '<option value="">Select a dataset...</option>';
        
        catalogs.forEach(catalog => {
            const option = document.createElement('option');
            option.value = catalog.id;
            option.textContent = catalog.name;
            catalogSelect.appendChild(option);
        });
        
        // Update the catalog information display with clean layout
        const catalogsInfo = document.getElementById('catalogsInfo');
        if (catalogs.length === 0) {
            catalogsInfo.innerHTML = '<p>No data catalogs available.</p>';
        } else {
            let html = '<div class="catalog-list">';
            catalogs.forEach(catalog => {
                const recordCount = catalog.total_records || 'Unknown';
                
                // Build score options list
                let scoreOptionsHtml = '';
                if (catalog.score_options && catalog.score_options.length > 0) {
                    scoreOptionsHtml = '<ul class="option-list">';
                    catalog.score_options.forEach(option => {
                        scoreOptionsHtml += `<li>${option.option_name}${option.is_default ? ' (default)' : ''}</li>`;
                    });
                    scoreOptionsHtml += '</ul>';
                } else {
                    scoreOptionsHtml = '<p style="color: #999; font-style: italic;">No score options available</p>';
                }
                
                // Build timeline options list
                let timelineOptionsHtml = '';
                if (catalog.timeline_options && catalog.timeline_options.length > 0) {
                    timelineOptionsHtml = '<ul class="option-list">';
                    catalog.timeline_options.forEach(option => {
                        timelineOptionsHtml += `<li>${option.option_name}${option.is_default ? ' (default)' : ''}</li>`;
                    });
                    timelineOptionsHtml += '</ul>';
                } else {
                    timelineOptionsHtml = '<p style="color: #999; font-style: italic;">No timeline options available</p>';
                }
                
                html += `
                    <div class="catalog-item">
                        <div class="catalog-header">
                            <h3 class="catalog-title">${catalog.name}</h3>
                            <div class="catalog-meta">
                                <strong>${recordCount}</strong> records | 
                                <span style="color: #666;">${catalog.access_level}</span>
                            </div>
                        </div>
                        <div class="catalog-description">${catalog.description || 'No description available'}</div>
                        <div class="catalog-options">
                            <div class="options-grid">
                                <div class="option-group">
                                    <h5>Score Options</h5>
                                    ${scoreOptionsHtml}
                                </div>
                                <div class="option-group">
                                    <h5>Timeline Options</h5>
                                    ${timelineOptionsHtml}
                                </div>
                            </div>
                        </div>
                    </div>
                `;
            });
            html += '</div>';
            catalogsInfo.innerHTML = html;
        }
        
        console.log(`Loaded ${catalogs.length} data catalogs with options`);
    } catch (error) {
        console.error('Error loading data catalogs:', error);
        
        // Fallback to basic display
        const catalogSelect = document.getElementById('data_catalog');
        catalogSelect.innerHTML = `
            <option value="">Select a dataset...</option>
            <option value="clinical_trial_data">Clinical Trial Data</option>
            <option value="imaging_data">Imaging Data</option>
            <option value="dbs_vta_analysis">DBS VTA Analysis</option>
            <option value="demo_dataset">Demo Dataset</option>
        `;
        
        const catalogsInfo = document.getElementById('catalogsInfo');
        catalogsInfo.innerHTML = '<p style="color: orange;">⚠️ Could not load catalog information from server. Using defaults.</p>';
    }
}

/**
 * Load score and timeline options for selected catalog
 */
async function loadScoreTimelineOptions() {
    const catalogId = document.getElementById('data_catalog').value;
    if (!catalogId) {
        // Clear options
        document.getElementById('selected_score').innerHTML = '<option value="">Select score option...</option>';
        document.getElementById('selected_timeline').innerHTML = '<option value="">Select timeline option...</option>';
        return;
    }
    
    try {
        const response = await fetch(`/api/v1/score-timeline-options/${catalogId}`);
        const options = await response.json();
        
        // Separate score and timeline options
        const scoreOptions = options.filter(opt => opt.option_type === 'score');
        const timelineOptions = options.filter(opt => opt.option_type === 'timeline');
        
        // Update score dropdown
        const scoreSelect = document.getElementById('selected_score');
        scoreSelect.innerHTML = '<option value="">Select score option...</option>';
        scoreOptions.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option.option_value;
            optionElement.textContent = option.option_name;
            if (option.is_default) {
                optionElement.selected = true;
            }
            scoreSelect.appendChild(optionElement);
        });
        
        // Update timeline dropdown
        const timelineSelect = document.getElementById('selected_timeline');
        timelineSelect.innerHTML = '<option value="">Select timeline option...</option>';
        timelineOptions.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option.option_value;
            optionElement.textContent = option.option_name;
            if (option.is_default) {
                optionElement.selected = true;
            }
            timelineSelect.appendChild(optionElement);
        });
        
        console.log(`Loaded ${scoreOptions.length} score options and ${timelineOptions.length} timeline options`);
    } catch (error) {
        console.error('Error loading score/timeline options:', error);
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
        
        // Script type is always Python
        console.log('Script uploaded - will be processed as Python');
        
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
 * Handle script type dropdown change
 */
function handleScriptTypeChange() {
    const scriptType = document.getElementById('script_type').value;
    const scriptContentGroup = document.getElementById('script_content_group');
    const scriptContent = document.getElementById('script_content');
    
    if (scriptType === 'custom') {
        // Show the script content textarea for custom scripts
        scriptContentGroup.style.display = 'block';
        scriptContent.required = true;
        scriptContent.value = ''; // Clear any existing content
    } else if (scriptType && scriptType !== 'custom') {
        // Load the selected example script
        scriptContentGroup.style.display = 'block';
        scriptContent.required = true;
        loadExample(scriptType);
    } else {
        // Hide the script content textarea
        scriptContentGroup.style.display = 'none';
        scriptContent.required = false;
        scriptContent.value = '';
    }
}

/**
 * Load example script into the textarea
 * @param {string} type - 'demographics', 'correlation', or 'damage_score'
 */
function loadExample(type) {
    const textarea = document.getElementById('script_content');
    
    if (type === 'demographics') {
        textarea.value = `# Import data loading helper
from data_loader import load_data, save_results

print("Demographics Analysis Starting...")

# Load data from selected catalog (no paths needed!)
data = load_data()
subjects = data['subjects']

print(f"Loaded {len(subjects)} subjects")

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

print(f"Demographics analysis complete!")
print(f"{result['total_subjects']} subjects analyzed")

# Save results
save_results(result)`;
    } else if (type === 'correlation') {
        textarea.value = `# Import data loading helper
from data_loader import load_data, save_results
from scipy import stats

print("Correlation Analysis Starting...")

# Load data from selected catalog (no paths needed!)
data_dict = load_data()
subjects = data_dict['subjects']
outcomes = data_dict['outcomes']

print(f"Loaded {len(subjects)} subjects, {len(outcomes)} outcomes")

# Merge datasets
data = subjects.merge(outcomes, on=['subject_id', 'visit'], how='inner')
print(f"Merged dataset: {len(data)} records")

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
    
    print(f"Correlation analysis complete!")
    print(f"Age vs UPDRS: r={corr_age_updrs:.3f}, p={p_age_updrs:.3f}")
    print(f"QoL vs UPDRS change: r={corr_qol_updrs:.3f}, p={p_qol_updrs:.3f}")
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
save_results(result)`;
    }
}

/**
 * Submit analysis request to the server
 */
async function submitRequest() {
    // Get script content based on selection
    const scriptTypeSelection = document.getElementById('script_type').value;
    let scriptContent = '';
    
    if (scriptTypeSelection === 'custom') {
        scriptContent = document.getElementById('script_content').value;
    } else if (scriptTypeSelection === 'demographics') {
        scriptContent = `# Import data loading helper
from data_loader import load_data, save_results

print("Demographics Analysis Starting...")

# Load data from selected catalog (no paths needed!)
data = load_data()
subjects = data['subjects']

print(f"Loaded {len(subjects)} subjects")

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
    "diagnosis_breakdown": subjects['diagnosis'].value_counts().to_dict()
}

print(f"Demographics analysis complete!")
print(f"Total subjects: {result['total_subjects']}")
print(f"Age range: {result['age_statistics']['min']}-{result['age_statistics']['max']}")

# Save results
save_results(result)`;
    } else if (scriptTypeSelection === 'correlation') {
        scriptContent = `# Import data loading helper
from data_loader import load_data, save_results
from scipy import stats
import numpy as np

print("Correlation Analysis Starting...")

# Load data from selected catalog (no paths needed!)
data_dict = load_data()
subjects = data_dict['subjects']
outcomes = data_dict['outcomes']

print(f"📂 Loaded {len(subjects)} subjects and {len(outcomes)} outcome records")

# Merge datasets
data = subjects.merge(outcomes, on=['subject_id', 'visit'])

# Correlation analysis
corr, p_val = stats.pearsonr(data['age'], data['UPDRS_total'])

result = {
    "analysis_type": "correlation",
    "correlation": float(corr),
    "p_value": float(p_val),
    "sample_size": len(data),
    "significant": p_val < 0.05
}

print(f"Correlation analysis complete!")
print(f"Age-UPDRS correlation: r={corr:.3f}, p={p_val:.3f}")
print(f"Sample size: {len(data)}")

# Save results
save_results(result)`;
    } else if (scriptTypeSelection === 'damage_score') {
        scriptContent = `# Import data loading helper
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
save_results(result)`;
    }

    // Get form data
    const formData = {
        requester_name: document.getElementById('requester_name').value,
        requester_institution: document.getElementById('requester_institution').value,
        requester_email: document.getElementById('requester_email').value,
        requester_affiliation: document.getElementById('requester_affiliation').value,
        analysis_title: document.getElementById('analysis_title').value,
        analysis_description: document.getElementById('analysis_description').value,
        target_node_id: 'node-1', // For now, assume this node
        data_catalog_name: document.getElementById('data_catalog').value,
        selected_score: document.getElementById('selected_score').value,
        selected_timeline: document.getElementById('selected_timeline').value,
        script_type: 'python', // Always Python
        script_content: scriptContent,
        priority: document.getElementById('priority').value,
        estimated_duration: document.getElementById('estimated_duration').value
    };
    
    // Validate required fields
    const requiredFields = ['requester_name', 'requester_institution', 'requester_email', 
                           'analysis_title', 'analysis_description', 'data_catalog_name'];
    
    // Add script_content to validation only if custom script is selected
    const scriptType = document.getElementById('script_type').value;
    if (scriptType === 'custom') {
        requiredFields.push('script_content');
    }
    
    for (const field of requiredFields) {
        if (!formData[field] || formData[field].trim() === '') {
            alert(`Please fill in the required field: ${field.replace('_', ' ')}`);
            return;
        }
    }
    
    try {
        // Submit request
        const response = await fetch('/api/v1/analysis-requests', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || 'Request submission failed');
        }
        
        const result = await response.json();
        currentRequestId = result.request_id;
        
        document.getElementById('results').style.display = 'block';
        document.getElementById('resultsContent').innerHTML = `
            <div class="request-status pending">
                <h3>Analysis Request Submitted</h3>
                <p><strong>Request ID:</strong> ${result.request_id}</p>
                <p><strong>Status:</strong> Pending Review</p>
                <p><strong>Title:</strong> ${result.analysis_title}</p>
                <p><strong>Submitted:</strong> ${new Date(result.submitted_at).toLocaleString()}</p>
                <p>Your request has been submitted and is awaiting approval from the data host. You will be notified once it's reviewed.</p>
                <button onclick="checkRequestStatus()">🔄 Check Status</button>
            </div>
        `;
        
        // Auto-check status after a delay
        setTimeout(checkRequestStatus, 5000);
        
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
 * Check the status of the current request
 */
async function checkRequestStatus() {
    if (!currentRequestId) return;
    
    try {
        const response = await fetch(`/api/v1/analysis-requests/${currentRequestId}`);
        const result = await response.json();
        
        let statusClass = 'pending';
        if (result.status === 'approved') statusClass = 'approved';
        if (result.status === 'denied') statusClass = 'denied';
        
        let content = `
            <div class="request-status ${statusClass}">
                <h3>Analysis Request Status</h3>
                <p><strong>Request ID:</strong> ${result.request_id}</p>
                <p><strong>Status:</strong> ${result.status.toUpperCase()}</p>
                <p><strong>Title:</strong> ${result.analysis_title}</p>
                <p><strong>Submitted:</strong> ${new Date(result.submitted_at).toLocaleString()}</p>
        `;
        
        if (result.status === 'approved') {
            content += `
                <p><strong>Approved by:</strong> ${result.approved_by || 'System'}</p>
                <p><strong>Approved at:</strong> ${result.approved_at ? new Date(result.approved_at).toLocaleString() : 'N/A'}</p>
                <p>✅ Your request has been approved and the analysis is now running!</p>
                <button onclick="checkRequestStatus()">🔄 Check Status</button>
            `;
        } else if (result.status === 'denied') {
            content += `
                <p><strong>Denied by:</strong> ${result.approved_by || 'System'}</p>
                <p><strong>Reason:</strong> ${result.approval_notes || 'No reason provided'}</p>
                <p>❌ Your request has been denied. Please review the feedback and submit a new request if needed.</p>
            `;
        } else {
            content += `
                <p>⏳ Your request is still pending review. Please check back later.</p>
                <button onclick="checkRequestStatus()">🔄 Check Again</button>
            `;
        }
        
        content += '</div>';
        document.getElementById('resultsContent').innerHTML = content;
        
    } catch (error) {
        document.getElementById('resultsContent').innerHTML = `
            <div class="error">Error checking request status: ${error.message}</div>
        `;
    }
}

/**
 * View analysis results for a specific request ID
 */
async function viewResults() {
    console.log('viewResults function called!');
    alert('viewResults function called!');
    
    const requestId = document.getElementById('request_id_input').value.trim();
    console.log('Viewing results for request ID:', requestId);
    
    if (!requestId) {
        alert('Please enter a request ID');
        return;
    }
    
    try {
        console.log('Fetching request details...');
        // First get the request details
        const requestResponse = await fetch(`/api/v1/analysis-requests/${requestId}`);
        if (!requestResponse.ok) {
            throw new Error('Request not found');
        }
        const request = await requestResponse.json();
        console.log('Request details:', request);
        
        // Then get the results
        console.log('Fetching results...');
        const resultsResponse = await fetch(`/api/v1/analysis-requests/${requestId}/results`);
        if (!resultsResponse.ok) {
            throw new Error('Results not found');
        }
        const results = await resultsResponse.json();
        console.log('Results:', results);
        
        // Display the results
        console.log('Displaying results...');
        document.getElementById('resultsView').style.display = 'block';
        
        let content = `
            <div class="request-info">
                <h4>Request Information</h4>
                <p><strong>Request ID:</strong> ${request.request_id}</p>
                <p><strong>Title:</strong> ${request.analysis_title}</p>
                <p><strong>Status:</strong> ${request.status.toUpperCase()}</p>
                <p><strong>Submitted:</strong> ${new Date(request.submitted_at).toLocaleString()}</p>
            </div>
        `;
        
        if (results.results && results.results.length > 0) {
            content += `
                <div class="results-section">
                    <h4>Analysis Results (${results.total_results} result${results.total_results !== 1 ? 's' : ''})</h4>
            `;
            
            results.results.forEach((result, index) => {
                content += `
                    <div class="result-item">
                        <h5>Result ${index + 1}: ${result.result_type}</h5>
                        <p><strong>Created:</strong> ${new Date(result.created_at).toLocaleString()}</p>
                        <div class="result-data">
                            <pre>${JSON.stringify(result.result_data, null, 2)}</pre>
                        </div>
                    </div>
                `;
            });
            
            content += '</div>';
        } else {
            content += `
                <div class="no-results">
                    <p>📭 No results available yet. The analysis may still be running or hasn't been completed.</p>
                    <p><strong>Job Status:</strong> ${results.job_status || 'Unknown'}</p>
                </div>
            `;
        }
        
        console.log('Setting content:', content);
        document.getElementById('resultsViewContent').innerHTML = content;
        console.log('Content set successfully');
        
    } catch (error) {
        document.getElementById('resultsView').style.display = 'block';
        document.getElementById('resultsViewContent').innerHTML = `
            <div class="error">
                <h4>❌ Error Loading Results</h4>
                <p><strong>Error:</strong> ${error.message}</p>
                <p>Please check that the request ID is correct and that the analysis has been completed.</p>
            </div>
        `;
    }
}