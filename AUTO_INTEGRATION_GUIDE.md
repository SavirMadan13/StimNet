# Auto-Integration for Uploaded Files

## Overview

When users upload data files through the web interface, they are **automatically integrated** into the data catalog system and immediately available for analysis scripts.

## How It Works

### 1. **Upload Process**
- User uploads a file (e.g., `connectivity_map.nii.gz`)
- File is saved to `uploads/data/` directory
- File is **automatically added** to the `data_manifest.json`
- File becomes available in the "User Uploaded Files" catalog

### 2. **Automatic Manifest Update**
When a file is uploaded, the system:
- Creates a "User Uploaded Files" catalog (if it doesn't exist)
- Adds the file to the catalog with metadata
- Updates the manifest timestamp
- Makes the file immediately available to all analysis scripts

### 3. **Access in Scripts**
Scripts can access uploaded files using the standard `data_loader`:

```python
from data_loader import load_data, save_results

# Load data from "User Uploaded Files" catalog
data = load_data()

# Access uploaded files by name
connectivity_map = data['connectivity_map']  # Automatically loaded!
```

## Example Workflow

### Step 1: Upload a Connectivity Map
```bash
# Via web interface or API
POST /api/v1/upload/data
# File: my_connectivity_map.nii.gz
```

### Step 2: File is Auto-Integrated
The manifest is automatically updated:
```json
{
  "catalogs": [
    {
      "id": "user_uploaded_files",
      "name": "User Uploaded Files",
      "files": [
        {
          "name": "my_connectivity_map",
          "path": "uploads/data/uuid_my_connectivity_map.nii.gz",
          "type": "nii.gz",
          "description": "User uploaded file: my_connectivity_map.nii.gz",
          "uploaded_at": "2025-10-13T12:00:00"
        }
      ]
    }
  ]
}
```

### Step 3: Use in Analysis Script
```python
from data_loader import load_data, save_results
import nibabel as nib

# Load user uploaded files
data = load_data()

# Access the uploaded connectivity map
connectivity_map = data['my_connectivity_map']

# Use it in your analysis
print(f"Map shape: {connectivity_map.shape}")
# ... your analysis ...
```

## Benefits

✅ **No Manual Configuration** - Files are automatically available  
✅ **Immediate Access** - No restart needed  
✅ **Consistent Interface** - Same `load_data()` for all files  
✅ **Secure** - Files are tracked and audited  
✅ **Version Controlled** - Manifest shows upload history  

## Supported File Types

- **Imaging**: `.nii`, `.nii.gz`
- **Tabular**: `.csv`, `.tsv`
- **Arrays**: `.npy`, `.npz`
- **Structured**: `.json`
- **MATLAB**: `.mat`

## API Response

When you upload a file, you get:
```json
{
  "file_id": "abc-123",
  "filename": "connectivity_map.nii.gz",
  "saved_as": "uuid_connectivity_map.nii.gz",
  "size_bytes": 1048576,
  "path": "uploads/data/uuid_connectivity_map.nii.gz",
  "type": ".nii.gz",
  "manifest_updated": true,
  "catalog": "user_uploaded_files",
  "message": "File uploaded and added to 'User Uploaded Files' catalog"
}
```

## Files Modified

1. **`distributed_node/real_main.py`**
   - Added `add_uploaded_file_to_manifest()` function
   - Updated `/api/v1/upload/data` endpoint to auto-integrate

2. **`data/data_manifest.json`**
   - Dynamically updated when files are uploaded
   - Contains "User Uploaded Files" catalog

3. **`distributed_node/data_loader.py`**
   - Already supports reading from manifest
   - Automatically loads user-uploaded files

## Testing

### Test Upload Integration
```bash
# Upload a file
curl -X POST http://localhost:8000/api/v1/upload/data \
  -F "file=@my_data.csv"

# Check manifest was updated
cat data/data_manifest.json | grep -A 5 "user_uploaded_files"

# Run analysis with uploaded file
# Select "User Uploaded Files" catalog in web interface
```

## Security Notes

- Files are stored in `uploads/data/` with UUID prefixes
- Original filenames are preserved in metadata
- All uploads are logged
- Files are accessible only through the `data_loader` module

## Future Enhancements

- File deduplication (detect duplicate uploads)
- File validation (check file integrity)
- File expiration (auto-delete old uploads)
- User-specific catalogs (multi-user support)

