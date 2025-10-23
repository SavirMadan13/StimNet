/**
 * StimNet Research Platform - Web Interface JavaScript
 * Handles form submission, job execution, and results display
 */

let currentRequestId = null;
let uploadedFileIds = []; // Track uploaded file IDs

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
                
                // Build files and columns list
                let filesHtml = '';
                if (catalog.files && catalog.files.length > 0) {
                    filesHtml = '<ul class="option-list">';
                    catalog.files.forEach(file => {
                        const exists = file.exists !== false ? '✓' : '✗';
                        filesHtml += `<li>${exists} ${file.name} (${file.type})</li>`;
                    });
                    filesHtml += '</ul>';
                } else {
                    filesHtml = '<p style="color: #999; font-style: italic;">No files available</p>';
                }
                
                // Build columns list for all files
                let columnsHtml = '';
                if (catalog.files && catalog.files.length > 0) {
                    columnsHtml = '<div class="files-columns">';
                    catalog.files.forEach(file => {
                        if (file.columns && file.columns.length > 0) {
                            columnsHtml += `<div class="file-columns">`;
                            columnsHtml += `<h6 style="margin: 8px 0 4px 0; color: #666; font-size: 12px;">${file.name} (${file.type})</h6>`;
                            columnsHtml += '<ul class="option-list" style="margin-bottom: 12px;">';
                            file.columns.forEach(col => {
                                const typeBadge = `<span class="type-badge">${col.type}</span>`;
                                columnsHtml += `<li>${typeBadge} <strong>${col.name}</strong></li>`;
                            });
                            columnsHtml += '</ul></div>';
                        }
                    });
                    columnsHtml += '</div>';
                }
                
                html += `
                    <div class="catalog-item">
                        <div class="catalog-header" onclick="toggleCatalog('${catalog.id}')">
                            <h3 class="catalog-title">${catalog.name}</h3>
                            <div class="catalog-meta">
                                <strong>${recordCount}</strong> records | 
                                <span style="color: #666;">${catalog.access_level}</span>
                                <span class="toggle-icon" id="toggle-${catalog.id}">▼</span>
                            </div>
                        </div>
                        <div class="catalog-content" id="content-${catalog.id}" style="display: none;">
                            <div class="catalog-description">${catalog.description || 'No description available'}</div>
                            <div class="catalog-options">
                                <div class="options-grid">
                                    <div class="option-group">
                                        <h5>Files</h5>
                                        ${filesHtml}
                                    </div>
                                    <div class="option-group">
                                        <h5>Columns</h5>
                                        ${columnsHtml || '<p style="color: #999; font-style: italic;">No column information available</p>'}
                                    </div>
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
        updateScriptTypeOptions(false); // Reset script type options
        return;
    }
    
    try {
        // First, get catalog details to check for imaging data
        const catalogResponse = await fetch('/api/v1/data-catalogs-with-options');
        const catalogs = await catalogResponse.json();
        const selectedCatalog = catalogs.find(cat => cat.id === catalogId);
        
        // Check if dataset has imaging data (look for imaging file)
        const hasImaging = selectedCatalog && selectedCatalog.files && 
            selectedCatalog.files.some(file => file.name === 'imaging' && file.type === 'csv');
        
        // Update script type options based on imaging availability
        updateScriptTypeOptions(hasImaging);
        
        // Load score/timeline options
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
        console.log(`Dataset has imaging data: ${hasImaging}`);
    } catch (error) {
        console.error('Error loading score/timeline options:', error);
    }
}

/**
 * Update script type dropdown options based on imaging data availability
 */
function updateScriptTypeOptions(hasImaging) {
    const scriptTypeSelect = document.getElementById('script_type');
    const currentValue = scriptTypeSelect.value;
    
    // Clear existing options
    scriptTypeSelect.innerHTML = '<option value="">Select a script type...</option>';
    
    // Always add demographics and custom options
    const demographicsOption = document.createElement('option');
    demographicsOption.value = 'demographics';
    demographicsOption.textContent = 'Demographics';
    scriptTypeSelect.appendChild(demographicsOption);
    
    // Add damage score option only if dataset has imaging data
    if (hasImaging) {
        const damageScoreOption = document.createElement('option');
        damageScoreOption.value = 'damage_score';
        damageScoreOption.textContent = 'DBS Damage Score';
        scriptTypeSelect.appendChild(damageScoreOption);
    }
    
    // Always add custom option
    const customOption = document.createElement('option');
    customOption.value = 'custom';
    customOption.textContent = 'Custom Script';
    scriptTypeSelect.appendChild(customOption);
    
    // Restore previous selection if it's still valid
    if (currentValue && scriptTypeSelect.querySelector(`option[value="${currentValue}"]`)) {
        scriptTypeSelect.value = currentValue;
    } else {
        scriptTypeSelect.value = '';
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
        
        // Track the uploaded file ID
        uploadedFileIds.push(result.file_id);
        console.log('Uploaded file ID added:', result.file_id);
        console.log('Current uploaded file IDs:', uploadedFileIds);
        
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
        textarea.value = `# DBS VTA Damage Score Analysis
import numpy as np
import pandas as pd
import numpy as np
from scipy import stats
from scipy import ndimage
import nibabel as nib
from data_loader import load_data, save_results
import os

print("DBS VTA Damage Score Analysis Starting...")

try:
    # Load the data using the new data_loader approach
    data = load_data()
    print("DEBUG: Data loaded successfully, keys:", list(data.keys()))
    
    imaging_data = data['imaging']
    outcomes_data = data['outcomes']
    print("DEBUG: Imaging data shape:", imaging_data.shape)
    print("DEBUG: Outcomes data shape:", outcomes_data.shape)
    print("DEBUG: Outcomes columns:", list(outcomes_data.columns))
    print("DEBUG: Outcomes dtypes:", outcomes_data.dtypes.to_dict())

    # Get the selected score column from the frontend
    # This should be passed as a parameter, but for now we'll use the first numeric column
    print("DEBUG: Looking for numeric columns...")
    score_columns = [col for col in outcomes_data.columns if outcomes_data[col].dtype in ['int64', 'float64']]
    print("DEBUG: Found numeric columns:", score_columns)
    if not score_columns:
        raise ValueError("No numeric score columns found in outcomes data")
    selected_score = score_columns[0]  # Use first numeric column
    print("Using score column:", selected_score)
    print("Note: In the future, this will use the score selected in the frontend dropdown")

    # Get VTA file paths and scores
    vta_paths = imaging_data['VTA'].values
    scores = outcomes_data[selected_score].values

    print("Found", len(vta_paths), "VTA files")
    print("Score range:", np.min(scores), "to", np.max(scores))
    print("DEBUG: About to check for connectivity map...")

    # Check if connectivity map was uploaded
    connectivity_map_path = None
    connectivity_data = None

    # Look for uploaded connectivity map in the data
    print("DEBUG: Checking for uploaded_connectivity_map in data keys:", list(data.keys()))
    if 'uploaded_connectivity_map' in data:
        print("DEBUG: Found uploaded_connectivity_map in data")
        connectivity_img = data['uploaded_connectivity_map']
        connectivity_data = connectivity_img.get_fdata()
        print("Using uploaded connectivity map:", connectivity_img.shape)
        
        # Find the actual filename from the uploaded files
        for key in data.keys():
            if key != 'uploaded_connectivity_map' and key.endswith('.nii'):
                connectivity_map_path = key
                print("Found connectivity map filename:", connectivity_map_path)
                break
        if connectivity_map_path is None:
            connectivity_map_path = "uploaded_connectivity_map.nii"
            print("Using default filename for uploaded connectivity map")
    else:
        print("DEBUG: No uploaded_connectivity_map found, checking directory...")
        # Fallback: look for .nii files in current directory
        uploaded_files = os.listdir('.')
        print("DEBUG: Files in current directory:", uploaded_files)
        nii_files = [f for f in uploaded_files if f.endswith('.nii') or f.endswith('.nii.gz')]
        print("DEBUG: Found NIfTI files:", nii_files)
        if nii_files:
            connectivity_map_path = nii_files[-1]
            print("Found connectivity map:", connectivity_map_path)
            connectivity_img = nib.load(connectivity_map_path)
            connectivity_data = connectivity_img.get_fdata()
        else:
            raise ValueError("No connectivity map (.nii file) uploaded. Please upload a connectivity map.")

    print("Connectivity map shape:", connectivity_data.shape)

    def resample_to_match(source_data, target_shape):
        """Resample source data to match target shape."""
        # Calculate scaling factors
        scale_factors = [target_shape[i] / source_data.shape[i] for i in range(3)]
        
        # Resample using scipy
        resampled_data = ndimage.zoom(source_data, scale_factors, order=1)
        
        return resampled_data

    # Calculate damage scores (overlap between VTA and connectivity map)
    print("Starting damage score calculation...")
    damage_scores = []
    valid_indices = []

    for i, vta_path in enumerate(vta_paths):
        print("Processing VTA", i+1, "/", len(vta_paths), ":", vta_path)
        try:
            # Load VTA file
            if os.path.exists(vta_path):
                print("  Loading VTA file...")
                vta_img = nib.load(vta_path)
                vta_data = vta_img.get_fdata()
                print("  VTA shape:", vta_data.shape)
                
                # Handle dimension mismatch by resampling VTA to match connectivity map
                if vta_data.shape != connectivity_data.shape:
                    print("  Resampling VTA from", vta_data.shape, "to", connectivity_data.shape)
                    vta_resampled = resample_to_match(vta_data, connectivity_data.shape)
                else:
                    vta_resampled = vta_data
                
                # Calculate overlap (element-wise multiplication and sum)
                overlap = np.sum(vta_resampled * connectivity_data)
                damage_scores.append(overlap)
                valid_indices.append(i)
                print("  ✓ Overlap calculated:", overlap)
            else:
                print("  Warning: VTA file not found:", vta_path)
        except Exception as e:
            print("  Error processing VTA", vta_path, ":", e)
            import traceback
            traceback.print_exc()

    if len(damage_scores) == 0:
        raise ValueError("No valid VTA files found or processed")

    # Convert to numpy arrays
    damage_scores = np.array(damage_scores)
    valid_scores = scores[valid_indices]

    print("Successfully processed", len(damage_scores), "VTA files")

    # Calculate correlation between damage scores and clinical scores
    # Handle case where all damage scores are identical (zero variance)
    if len(set(damage_scores)) == 1:
        print("Warning: All damage scores are identical (", damage_scores[0], "). Cannot calculate meaningful correlation.")
        corr = 0.0
        p_val = 1.0
    else:
        corr, p_val = stats.pearsonr(damage_scores, valid_scores)

    # Calculate summary statistics
    mean_damage = float(np.mean(damage_scores))
    std_damage = float(np.std(damage_scores))

    # Save results
    results = {
        "analysis_type": "dbs_damage_score",
        "correlation_coefficient": float(corr),
        "p_value": float(p_val),
        "n_subjects": len(damage_scores),
        "score_column_used": selected_score,
        "connectivity_map_used": connectivity_map_path,
        "summary_statistics": {
            "mean_damage_score": mean_damage,
            "std_damage_score": std_damage,
            "damage_score_range": [float(np.min(damage_scores)), float(np.max(damage_scores))],
            "score_range": [float(np.min(valid_scores)), float(np.max(valid_scores))]
        },
        "interpretation": "Correlation between VTA-connectivity overlap and " + selected_score + ": r=" + str(corr) + ", p=" + str(p_val)
    }

    save_results(results)
    print("Damage score analysis complete!")
    print("Correlation: r=", corr, ", p=", p_val)
    print("Mean damage score:", mean_damage)
    print("Score column used:", selected_score)

except Exception as e:
    print("ERROR:", e)
    import traceback
    traceback.print_exc()
    # Save error result
    save_results({"error": str(e), "traceback": traceback.format_exc()})`;
    }
}

/**
 * Submit analysis request to the server
 */
async function submitRequest() {
    console.log('Submit button clicked');
    
    // Check if all form elements exist
    const requiredElements = ['requester_name', 'requester_institution', 'requester_email', 
                             'analysis_title', 'analysis_description', 'data_catalog', 'script_type'];
    
    for (const elementId of requiredElements) {
        const element = document.getElementById(elementId);
        if (!element) {
            console.error(`Required form element not found: ${elementId}`);
            alert(`Form error: Required field ${elementId} not found. Please refresh the page.`);
            return;
        }
        console.log(`Element ${elementId} exists, value:`, element.value);
    }
    
    // Get script content based on selection
    const scriptTypeSelection = document.getElementById('script_type').value;
    let scriptContent = '';
    
    console.log('Script type selected:', scriptTypeSelection);
    
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
        scriptContent = `# DBS VTA Damage Score Analysis
import numpy as np
import pandas as pd
import numpy as np
from scipy import stats
from scipy import ndimage
import nibabel as nib
from data_loader import load_data, save_results
import os

print("DBS VTA Damage Score Analysis Starting...")

# Load data from selected catalog
data = load_data()
imaging_data = data['imaging']
outcomes_data = data['outcomes']

print("DEBUG: Data loaded successfully, keys: " + str(list(data.keys())))
print("DEBUG: Imaging data shape: " + str(imaging_data.shape))
print("DEBUG: Outcomes data shape: " + str(outcomes_data.shape))
print("DEBUG: Outcomes columns: " + str(list(outcomes_data.columns)))
print("DEBUG: Outcomes dtypes: " + str(outcomes_data.dtypes.to_dict()))
print("DEBUG: Looking for numeric columns...")
score_columns = [col for col in outcomes_data.columns if outcomes_data[col].dtype in ['int64', 'float64']]
print("DEBUG: Found numeric columns: " + str(score_columns))

# Select the first numeric column as the score
selected_score = score_columns[0]
scores = outcomes_data[selected_score].values
print("Using score column:", selected_score)

# Get VTA file paths
vta_paths = imaging_data['VTA'].tolist()
print("Found", len(vta_paths), "VTA files")

# Check if connectivity map was uploaded
connectivity_map_path = None
connectivity_data = None
print("DEBUG: About to check for connectivity map...")
# Look for uploaded connectivity map in the data
print("DEBUG: Checking for uploaded_connectivity_map in data keys: " + str(list(data.keys())))
if 'uploaded_connectivity_map' in data:
    print("DEBUG: Found uploaded_connectivity_map in data")
    connectivity_img = data['uploaded_connectivity_map']
    connectivity_data = connectivity_img.get_fdata()
    print("Using uploaded connectivity map:", connectivity_img.shape)
    
    # Find the actual filename from the uploaded files
    for key in data.keys():
        if key != 'uploaded_connectivity_map' and key.endswith('.nii'):
            connectivity_map_path = key
            print("Found connectivity map filename:", connectivity_map_path)
            break
    if connectivity_map_path is None:
        connectivity_map_path = "uploaded_connectivity_map.nii"
        print("Using default filename for uploaded connectivity map")
else:
    print("DEBUG: No uploaded_connectivity_map found, checking directory...")
    # Fallback: look for .nii files in current directory
    uploaded_files = os.listdir('.')
    print("DEBUG: Files in current directory: " + str(uploaded_files))
    nii_files = [f for f in uploaded_files if f.endswith('.nii') or f.endswith('.nii.gz')]
    print("DEBUG: Found NIfTI files: " + str(nii_files))
    if nii_files:
        connectivity_map_path = nii_files[-1]
        print("Found connectivity map:", connectivity_map_path)
        connectivity_img = nib.load(connectivity_map_path)
        connectivity_data = connectivity_img.get_fdata()
    else:
        raise ValueError("No connectivity map (.nii file) uploaded. Please upload a connectivity map.")

print("Connectivity map shape:", connectivity_data.shape)

# Function to resample data to match target shape
def resample_to_match(data, target_shape):
    """Resample data to match target shape using scipy.ndimage.zoom"""
    zoom_factors = [target_shape[i] / data.shape[i] for i in range(len(target_shape))]
    return ndimage.zoom(data, zoom_factors, order=1)
        
# Calculate damage scores (overlap between VTA and connectivity map)
print("Starting damage score calculation...")
damage_scores = []
valid_indices = []

for i, vta_path in enumerate(vta_paths):
    print("Processing VTA", i+1, "/", len(vta_paths), ":", vta_path)
    try:
        # Load VTA file
        if os.path.exists(vta_path):
            print("  Loading VTA file...")
            vta_img = nib.load(vta_path)
            vta_data = vta_img.get_fdata()
            print("  VTA shape:", vta_data.shape)
            
            # Resample if dimensions don't match
            if vta_data.shape != connectivity_data.shape:
                print("  Resampling VTA to match connectivity map...")
                vta_resampled = resample_to_match(vta_data, connectivity_data.shape)
            else:
                vta_resampled = vta_data
            
            # Calculate overlap (element-wise multiplication and sum)
            overlap = np.sum(vta_resampled * connectivity_data)
            damage_scores.append(overlap)
            valid_indices.append(i)
            print("  ✓ Overlap calculated:", overlap)
        else:
            print("  Warning: VTA file not found:", vta_path)
    except Exception as e:
        print("  Error processing VTA", vta_path, ":", e)
        import traceback
        traceback.print_exc()

if len(damage_scores) == 0:
    raise ValueError("No valid VTA files found or processed")

# Convert to numpy arrays
damage_scores = np.array(damage_scores)
valid_scores = scores[valid_indices]

print("Successfully processed", len(damage_scores), "VTA files")

# Calculate correlation between damage scores and clinical scores
# Handle case where all damage scores are identical (zero variance)
if len(set(damage_scores)) == 1:
    print("Warning: All damage scores are identical (" + str(damage_scores[0]) + "). Cannot calculate meaningful correlation.")
    corr = 0.0
    p_val = 1.0
else:
    corr, p_val = stats.pearsonr(damage_scores, valid_scores)

# Calculate summary statistics
mean_damage = float(np.mean(damage_scores))
std_damage = float(np.std(damage_scores))

# Save results
results = {
    "analysis_type": "dbs_damage_score",
    "correlation_coefficient": float(corr),
    "p_value": float(p_val),
    "n_subjects": len(damage_scores),
    "score_column_used": selected_score,
    "connectivity_map_used": connectivity_map_path,
    "summary_statistics": {
        "mean_damage_score": mean_damage,
        "std_damage_score": std_damage,
        "damage_score_range": [float(np.min(damage_scores)), float(np.max(damage_scores))],
        "score_range": [float(np.min(valid_scores)), float(np.max(valid_scores))]
    },
    "interpretation": "Correlation between VTA-connectivity overlap and " + selected_score + ": r=" + str(corr) + ", p=" + str(p_val)
}

save_results(results)
print("Damage score analysis complete!")
print("Correlation: r=", corr, ", p=", p_val)
print("Mean damage score:", mean_damage)
print("Score column used:", selected_score)`;
    }

    // Get form data
    const formData = {
        requester_name: document.getElementById('requester_name').value,
        requester_institution: document.getElementById('requester_institution').value,
        requester_email: document.getElementById('requester_email').value,
        requester_affiliation: document.getElementById('requester_affiliation').value,
        analysis_title: document.getElementById('analysis_title').value,
        analysis_description: document.getElementById('analysis_description').value,
        target_node_id: 'default-node', // Use the actual default node ID
        data_catalog_name: document.getElementById('data_catalog').value,
        selected_score: document.getElementById('selected_score').value,
        selected_timeline: document.getElementById('selected_timeline').value,
        script_type: 'python', // Always Python
        script_content: scriptContent,
        priority: document.getElementById('priority').value,
        estimated_duration: document.getElementById('estimated_duration').value,
        uploaded_file_ids: uploadedFileIds // Include uploaded file IDs
    };
    
    console.log('Submitting form with uploaded_file_ids:', uploadedFileIds);
    
    // Validate required fields
    const requiredFields = ['requester_name', 'requester_institution', 'requester_email', 
                           'analysis_title', 'analysis_description', 'data_catalog_name'];
    
    // Add script_content to validation only if custom script is selected
    const scriptType = document.getElementById('script_type').value;
    if (scriptType === 'custom') {
        requiredFields.push('script_content');
    }
    
    console.log('Validating form data:', formData);
    console.log('Required fields:', requiredFields);
    
    for (const field of requiredFields) {
        console.log(`Checking field ${field}:`, formData[field]);
        if (!formData[field] || formData[field].trim() === '') {
            alert(`Please fill in the required field: ${field.replace('_', ' ')}`);
            return;
        }
    }
    
    console.log('Form validation passed, submitting...');
    
    try {
        // Submit request
        console.log('Sending POST request to /api/v1/analysis-requests');
        console.log('Request body:', JSON.stringify(formData, null, 2));
        
        const response = await fetch('/api/v1/analysis-requests', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        console.log('Response status:', response.status);
        console.log('Response ok:', response.ok);
        
        if (!response.ok) {
            const errorData = await response.json();
            console.error('Error response:', errorData);
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
    // alert('viewResults function called!');
    
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

/**
 * Toggle catalog content visibility
 */
function toggleCatalog(catalogId) {
    const content = document.getElementById(`content-${catalogId}`);
    const toggle = document.getElementById(`toggle-${catalogId}`);
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        toggle.textContent = '▲';
    } else {
        content.style.display = 'none';
        toggle.textContent = '▼';
    }
}