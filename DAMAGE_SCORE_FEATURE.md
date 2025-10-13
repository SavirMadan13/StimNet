# DBS VTA Damage Score Analysis Feature

## Overview

A new analysis script has been added to analyze Deep Brain Stimulation (DBS) Voxel-based Treatment Atlas (VTA) data and correlate damage scores with clinical outcomes.

## What It Does

The damage score analysis:
1. **Loads VTA metadata** - Subject information, target regions, and clinical scores
2. **Loads connectivity map** - Group-average connectivity map (nii file)
3. **Calculates damage scores** - Overlap between each VTA and the connectivity map
4. **Correlates with outcomes** - Statistical correlation between damage scores and clinical improvement

## How to Use

### Via Web Interface

1. Visit `http://localhost:8000/`
2. Select **"DBS VTA Damage Score Analysis"** from the data catalog dropdown
3. Click **"🧠 Load Damage Score Example"** button
4. Click **"🚀 Run Analysis"**

### Via API

```python
from client_sdk import DistributedClient

async with DistributedClient("http://localhost:8000") as client:
    await client.authenticate("demo", "demo")
    
    job_id = await client.submit_script(
        script_content=damage_score_script,

        
        target_node_id="node-1",
        data_catalog_name="dbs_vta_analysis"
    )
    
    result = await client.wait_for_job(job_id)
```

## Example Output

```json
{
  "analysis_type": "dbs_damage_score",
  "sample_size": 40,
  "correlation": {
    "correlation_coefficient": -0.138,
    "p_value": 0.396,
    "significant": false
  },
  "summary_statistics": {
    "mean_damage_score": 0.496,
    "mean_clinical_improvement": 51.2,
    "damage_score_range": [0.088, 1.005],
    "improvement_range": [29.9, 73.3]
  }
}
```

## Data Structure

### VTA Metadata CSV
- `subject_id`: Unique subject identifier
- `vta_file`: Path to VTA nii file
- `target_region`: STN or GPi
- `laterality`: L/R/Bilateral
- `baseline_updrs`: Baseline UPDRS-III score
- `followup_updrs`: Follow-up UPDRS-III score
- `clinical_improvement`: UPDRS improvement (%)
- `stimulation_voltage`: Stimulation voltage (V)
- `stimulation_freq`: Stimulation frequency (Hz)

### Connectivity Map
- **Format**: NIfTI (.nii.gz)
- **Dimensions**: 91x109x91 voxels (MNI space)
- **Description**: Group-average connectivity map for target region

## Files Modified

1. **`data/data_manifest.json`** - Added `dbs_vta_analysis` catalog
2. **`data/catalogs/dbs_vta_analysis/vta_metadata.csv`** - VTA metadata (40 subjects)
3. **`data/catalogs/dbs_vta_analysis/connectivity_map.nii.gz`** - Connectivity map
4. **`distributed_node/data_loader.py`** - Added nii file support
5. **`distributed_node/web_interface.py`** - Added damage score button
6. **`distributed_node/static/app.js`** - Added damage score example script

## Requirements

- **nibabel**: For reading nii files
- **numpy**: For array operations
- **scipy**: For statistical analysis
- **pandas**: For data manipulation

## Real-World Usage

In production, users would:
1. Upload their own VTA files (nii format)
2. Upload their connectivity map
3. Provide clinical scores
4. Run the analysis to find optimal stimulation targets

The system handles all file paths automatically - users don't need to know where files are stored.

