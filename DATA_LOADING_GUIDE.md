# Data Loading Guide

## Overview

The StimNet platform now provides a **simplified data loading system** that eliminates the need for users to know or specify file paths. Users simply select a dataset from the dropdown, and the system automatically loads the data for them.

## Key Benefits

✅ **No file paths needed** - Users don't need to know where data is stored  
✅ **Security** - Data locations are hidden from users  
✅ **Simplicity** - Just select a dataset and start analyzing  
✅ **Flexibility** - Works with any dataset defined in the manifest  

## How It Works

### 1. User Selects Dataset

In the web interface, users select a dataset from the dropdown:

```
Data Catalog: [Parkinson's Disease Dataset ▼]
```

### 2. System Loads Data Automatically

Behind the scenes, the system:
1. Reads the selected catalog from `data/data_manifest.json`
2. Loads all files defined in that catalog
3. Makes the data available to the script via the `data_loader` module

### 3. Script Accesses Data

Scripts use the `data_loader` module to access data:

```python
# Import the data loader
import sys
sys.path.insert(0, '/Users/savirmadan/Development/StimNet/distributed_node')
from data_loader import load_data, save_results

# Load data (automatically loads from selected catalog)
data = load_data()

# Access data by name
subjects = data['subjects']
outcomes = data['outcomes']

# Your analysis here
result = {
    "n_subjects": len(subjects),
    "mean_age": float(subjects['age'].mean())
}

# Save results
save_results(result)
```

## Data Loader API

### `load_data()`

Loads all data files from the selected catalog.

**Returns:** Dictionary mapping file names to pandas DataFrames

**Example:**
```python
data = load_data()
# data = {
#     'subjects': DataFrame(...),
#     'outcomes': DataFrame(...),
#     'scan_metadata': DataFrame(...)
# }
```

### `save_results(results)`

Saves analysis results to the output file.

**Parameters:**
- `results` (dict): Dictionary of results to save

**Example:**
```python
save_results({
    "mean_age": 45.2,
    "n_subjects": 150,
    "significant": True
})
```

### `get_catalog_info()`

Gets metadata about the selected catalog.

**Returns:** Dictionary with catalog information

**Example:**
```python
info = get_catalog_info()
print(f"Catalog: {info['name']}")
print(f"Description: {info['description']}")
print(f"Privacy Level: {info['privacy_level']}")
```

## Complete Example Script

```python
# Import data loading helper
import sys
sys.path.insert(0, '/Users/savirmadan/Development/StimNet/distributed_node')
from data_loader import load_data, save_results

print("🔍 Starting analysis...")

# Load data from selected catalog
data = load_data()

# Access your data
subjects = data['subjects']
outcomes = data['outcomes']

# Merge datasets
merged = subjects.merge(outcomes, on=['subject_id', 'visit'])

# Your analysis
result = {
    "n_subjects": len(subjects),
    "n_outcomes": len(outcomes),
    "n_merged": len(merged),
    "mean_age": float(subjects['age'].mean()),
    "sex_distribution": subjects['sex'].value_counts().to_dict()
}

# Save results
save_results(result)
print("✅ Analysis complete!")
```

## Comparison: Old vs New

### ❌ Old Way (with file paths)

```python
import pandas as pd
import os

# User had to know the exact path
data_root = os.environ.get('DATA_ROOT', './data')
subjects = pd.read_csv(f'{data_root}/catalogs/clinical_trial_data/subjects.csv')
outcomes = pd.read_csv(f'{data_root}/catalogs/clinical_trial_data/outcomes.csv')

# Analysis...
```

**Problems:**
- Users need to know file paths
- Security risk (exposes data structure)
- Hard to maintain (paths might change)
- Error-prone (typos in paths)

### ✅ New Way (automatic loading)

```python
from data_loader import load_data, save_results

# System automatically loads the right data
data = load_data()
subjects = data['subjects']
outcomes = data['outcomes']

# Analysis...
```

**Benefits:**
- No file paths needed
- Secure (paths hidden)
- Easy to maintain
- Less error-prone

## Security Benefits

### Before
- Users could see data file paths
- Users could potentially access other files
- Data structure was exposed

### After
- Users only see dataset names
- File paths are completely hidden
- System controls what data is accessible
- Better separation of concerns

## Adding New Datasets

To add a new dataset, simply update `data/data_manifest.json`:

```json
{
  "catalogs": [
    {
      "id": "my_new_study",
      "name": "My New Study",
      "description": "Description of my study",
      "files": [
        {
          "name": "participants",
          "path": "data/catalogs/my_study/participants.csv",
          "type": "csv"
        }
      ]
    }
  ]
}
```

That's it! Users can now access this dataset by selecting "My New Study" from the dropdown.

## Troubleshooting

### "JOB_CONFIG not found"
- Make sure you're running the script through the StimNet job system
- Don't run scripts directly in your terminal

### "Catalog 'X' not found"
- Check that the catalog ID in your selection matches one in `data/data_manifest.json`
- Make sure the manifest file exists

### "No data files could be loaded"
- Verify that the files listed in the manifest actually exist
- Check file permissions

## Best Practices

1. **Always use `load_data()`** - Don't try to load files manually
2. **Use `save_results()`** - Ensures results are saved correctly
3. **Check data availability** - Use `get_catalog_info()` to see what's available
4. **Handle missing data** - Check if expected keys exist in the data dictionary

## Example: Robust Script

```python
from data_loader import load_data, save_results, get_catalog_info

try:
    # Get catalog info
    info = get_catalog_info()
    print(f"Analyzing: {info['name']}")
    
    # Load data
    data = load_data()
    
    # Check required data exists
    if 'subjects' not in data:
        raise ValueError("Subjects data not found")
    
    # Analysis
    subjects = data['subjects']
    result = {
        "n_subjects": len(subjects),
        "columns": list(subjects.columns)
    }
    
    # Save results
    save_results(result)
    print("✅ Success!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    save_results({"error": str(e)})
```

## Summary

The new data loading system makes it easier and more secure for users to analyze data:

- ✅ No file paths needed
- ✅ Data locations hidden
- ✅ Simple API
- ✅ Better security
- ✅ Easier to maintain

Users just select a dataset and start analyzing!

