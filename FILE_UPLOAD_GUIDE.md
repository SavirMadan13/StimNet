# File Upload Guide

## Overview
StimNet now supports uploading both **script files** (.py, .R) and **data files** (.nii, .csv, etc.) directly through the web interface!

## 🎯 **What You Can Upload**

### **📝 Script Files**
- **Python scripts** (`.py`)
- **R scripts** (`.r`, `.R`)

### **📊 Data Files**
- **Neuroimaging**: `.nii`, `.nii.gz`
- **Tabular data**: `.csv`, `.tsv`
- **NumPy arrays**: `.npy`, `.npz`
- **MATLAB**: `.mat`
- **JSON**: `.json`

## 🚀 **How to Use**

### **Method 1: Web Interface**

1. **Visit**: http://localhost:8000
2. **Upload Script**:
   - Click "📁 Upload Script File"
   - Select your `.py` or `.R` file
   - Script content automatically populates the textarea
3. **Upload Data**:
   - Click "📊 Upload Data File"
   - Select your data file (.nii, .csv, etc.)
   - File path is shown for use in your script
4. **Run Analysis**:
   - Click "🚀 Run Analysis"
   - Your script runs with access to uploaded data

### **Method 2: API Endpoints**

#### **Upload Script**
```bash
curl -X POST http://localhost:8000/api/v1/upload/script \
  -F "file=@my_analysis.py"
```

**Response:**
```json
{
  "file_id": "abc123...",
  "filename": "my_analysis.py",
  "saved_as": "abc123_my_analysis.py",
  "size_bytes": 1234,
  "content": "import pandas as pd\n...",
  "path": "uploads/scripts/abc123_my_analysis.py"
}
```

#### **Upload Data**
```bash
curl -X POST http://localhost:8000/api/v1/upload/data \
  -F "file=@brain_scan.nii.gz"
```

**Response:**
```json
{
  "file_id": "xyz789...",
  "filename": "brain_scan.nii.gz",
  "saved_as": "xyz789_brain_scan.nii.gz",
  "size_bytes": 5242880,
  "path": "uploads/data/xyz789_brain_scan.nii.gz",
  "type": ".nii.gz"
}
```

#### **List Uploaded Files**
```bash
# List scripts
curl http://localhost:8000/api/v1/uploads/scripts

# List data files
curl http://localhost:8000/api/v1/uploads/data
```

## 📝 **Using Uploaded Files in Your Scripts**

### **Example 1: Using Uploaded NIfTI File**

**Upload a file via web interface**, then use it:

```python
import nibabel as nib
import numpy as np
import os
import json

# Path to your uploaded file (shown in web interface after upload)
nifti_path = "uploads/data/abc123_brain_scan.nii.gz"

# Load the NIfTI file
img = nib.load(nifti_path)
data = img.get_fdata()

# Perform analysis
mean_intensity = float(np.mean(data))
max_intensity = float(np.max(data))
volume_shape = data.shape

result = {
    "mean_intensity": mean_intensity,
    "max_intensity": max_intensity,
    "volume_shape": list(volume_shape),
    "voxel_count": int(np.prod(volume_shape))
}

# Save results
with open(os.environ.get('OUTPUT_FILE', 'output.json'), 'w') as f:
    json.dump(result, f, indent=2)

print(f"✅ Analysis complete: {result}")
```

### **Example 2: Using Uploaded CSV**

```python
import pandas as pd
import os
import json

# Path to your uploaded CSV
csv_path = "uploads/data/xyz789_my_data.csv"

# Load the CSV
df = pd.read_csv(csv_path)

# Perform analysis
result = {
    "rows": len(df),
    "columns": list(df.columns),
    "summary_stats": df.describe().to_dict()
}

# Save results
with open(os.environ.get('OUTPUT_FILE', 'output.json'), 'w') as f:
    json.dump(result, f, indent=2)

print(f"✅ Analyzed {len(df)} rows")
```

### **Example 3: Combining Uploaded Data with Catalog Data**

```python
import pandas as pd
import os
import json

# Load catalog data (from database)
data_root = os.environ.get('DATA_ROOT', './data')
subjects = pd.read_csv(f'{data_root}/catalogs/clinical_trial_data/subjects.csv')

# Load your uploaded data
uploaded_data = pd.read_csv('uploads/data/abc123_additional_measures.csv')

# Merge datasets
merged = subjects.merge(uploaded_data, on='subject_id', how='inner')

result = {
    "catalog_subjects": len(subjects),
    "uploaded_subjects": len(uploaded_data),
    "merged_subjects": len(merged),
    "new_columns": list(uploaded_data.columns)
}

with open(os.environ.get('OUTPUT_FILE', 'output.json'), 'w') as f:
    json.dump(result, f, indent=2)
```

## 🔒 **Security Features**

### **File Validation**
- **Extension checking**: Only allowed file types accepted
- **Unique naming**: Files renamed with UUID to prevent conflicts
- **Size limits**: (Can be configured in future)

### **Allowed Extensions**
```python
# Scripts
ALLOWED_SCRIPT_EXTENSIONS = {".py", ".r", ".R"}

# Data
ALLOWED_DATA_EXTENSIONS = {
    ".nii", ".nii.gz",  # Neuroimaging
    ".csv", ".tsv",      # Tabular
    ".npy", ".npz",      # NumPy
    ".mat",              # MATLAB
    ".json"              # JSON
}
```

### **File Storage**
```
uploads/
├── scripts/          # Uploaded analysis scripts
│   └── {uuid}_{filename}.py
└── data/            # Uploaded data files
    └── {uuid}_{filename}.nii.gz
```

## 🎨 **Web Interface Features**

### **Script Upload**
- ✅ Drag & drop support
- ✅ Automatic script type detection
- ✅ Content preview in textarea
- ✅ Syntax validation (future)

### **Data Upload**
- ✅ Multiple file format support
- ✅ File size display
- ✅ Path shown for easy copying
- ✅ Auto-generates example code
- ✅ Upload progress indicator

## 📊 **Example Workflow**

### **Complete Analysis with Uploads**

**Step 1: Create your script** (`analysis.py`):
```python
import nibabel as nib
import numpy as np
import os
import json

# Load uploaded NIfTI file
nifti_path = os.environ.get('UPLOADED_FILE', 'uploads/data/brain.nii.gz')
img = nib.load(nifti_path)
data = img.get_fdata()

# Analysis
result = {
    "mean": float(np.mean(data)),
    "std": float(np.std(data)),
    "shape": list(data.shape)
}

with open(os.environ.get('OUTPUT_FILE', 'output.json'), 'w') as f:
    json.dump(result, f)
```

**Step 2: Upload via web interface**:
1. Go to http://localhost:8000
2. Upload `analysis.py` → Script field populated
3. Upload `brain.nii.gz` → Path shown
4. Update script with correct path
5. Click "🚀 Run Analysis"

**Step 3: Get results**:
```json
{
  "mean": 245.67,
  "std": 89.23,
  "shape": [256, 256, 180]
}
```

## 🧪 **Testing File Uploads**

### **Test 1: Upload Python Script**
```bash
# Create test script
echo 'print("Hello from uploaded script!")' > test.py

# Upload via API
curl -X POST http://localhost:8000/api/v1/upload/script \
  -F "file=@test.py"

# Should return file info with content
```

### **Test 2: Upload CSV Data**
```bash
# Create test CSV
echo 'id,value\n1,100\n2,200' > test.csv

# Upload via API
curl -X POST http://localhost:8000/api/v1/upload/data \
  -F "file=@test.csv"

# Should return file info with path
```

### **Test 3: List Uploaded Files**
```bash
# List all uploaded scripts
curl http://localhost:8000/api/v1/uploads/scripts | python -m json.tool

# List all uploaded data
curl http://localhost:8000/api/v1/uploads/data | python -m json.tool
```

## 🐛 **Troubleshooting**

### **Problem: "Invalid file type" error**

**Cause**: File extension not in allowed list

**Solution**:
```python
# Check allowed extensions in real_main.py
ALLOWED_SCRIPT_EXTENSIONS = {".py", ".r", ".R"}
ALLOWED_DATA_EXTENSIONS = {".nii", ".nii.gz", ".csv", ...}
```

### **Problem: Uploaded file not found in script**

**Cause**: Incorrect path

**Solution**:
```python
# Use the exact path shown in web interface
file_path = "uploads/data/abc123_myfile.nii.gz"

# Or check if file exists
import os
if os.path.exists(file_path):
    print(f"✅ File found: {file_path}")
else:
    print(f"❌ File not found: {file_path}")
```

### **Problem: Large file upload fails**

**Cause**: File size limit (default: 100MB in FastAPI)

**Solution**: Configure in `real_main.py`:
```python
from fastapi import FastAPI

app = FastAPI()
app.add_middleware(
    ...,
    max_upload_size=500 * 1024 * 1024  # 500MB
)
```

### **Problem: Upload button not working**

**Cause**: JavaScript not loaded

**Solution**:
1. Check browser console (F12) for errors
2. Verify `/static/app.js` is loading
3. Hard refresh (Ctrl+Shift+R)

## 🚀 **Advanced Usage**

### **Python Client SDK**

```python
from client_sdk import DistributedClient
import asyncio

async def upload_and_analyze():
    async with DistributedClient("http://localhost:8000") as client:
        # Authenticate
        await client.authenticate("demo", "demo")
        
        # Upload script
        with open("my_analysis.py", "rb") as f:
            script_response = await client.upload_script(f)
        
        # Upload data
        with open("brain_scan.nii.gz", "rb") as f:
            data_response = await client.upload_data(f)
        
        # Submit job with uploaded script
        job_id = await client.submit_job(
            script_content=script_response["content"],
            data_catalog_name="clinical_trial_data"
        )
        
        # Wait for results
        result = await client.wait_for_job(job_id)
        print(result)

asyncio.run(upload_and_analyze())
```

### **Batch Upload Multiple Files**

```bash
# Upload multiple data files
for file in data/*.nii.gz; do
    curl -X POST http://localhost:8000/api/v1/upload/data \
      -F "file=@$file"
    echo "Uploaded: $file"
done
```

### **Cleanup Old Uploads**

```python
# cleanup_uploads.py
from pathlib import Path
from datetime import datetime, timedelta

UPLOAD_DIR = Path("uploads")
MAX_AGE_DAYS = 7

def cleanup_old_files():
    cutoff = datetime.now() - timedelta(days=MAX_AGE_DAYS)
    
    for file_path in UPLOAD_DIR.rglob("*"):
        if file_path.is_file():
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if mtime < cutoff:
                print(f"Deleting old file: {file_path}")
                file_path.unlink()

if __name__ == "__main__":
    cleanup_old_files()
```

## 📖 **API Reference**

### **POST /api/v1/upload/script**
Upload an analysis script file

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (binary)

**Response:**
```json
{
  "file_id": "uuid",
  "filename": "original_name.py",
  "saved_as": "uuid_original_name.py",
  "size_bytes": 1234,
  "content": "script content...",
  "path": "uploads/scripts/uuid_original_name.py"
}
```

### **POST /api/v1/upload/data**
Upload a data file

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (binary)

**Response:**
```json
{
  "file_id": "uuid",
  "filename": "original_name.nii.gz",
  "saved_as": "uuid_original_name.nii.gz",
  "size_bytes": 5242880,
  "path": "uploads/data/uuid_original_name.nii.gz",
  "type": ".nii.gz"
}
```

### **GET /api/v1/uploads/scripts**
List all uploaded scripts

**Response:**
```json
[
  {
    "filename": "uuid_script.py",
    "size_bytes": 1234,
    "uploaded_at": "2025-10-08T10:20:30"
  }
]
```

### **GET /api/v1/uploads/data**
List all uploaded data files

**Response:**
```json
[
  {
    "filename": "uuid_data.nii.gz",
    "size_bytes": 5242880,
    "uploaded_at": "2025-10-08T10:25:45"
  }
]
```

## ✅ **Benefits**

1. **Convenience** - Upload files directly from browser
2. **Flexibility** - Use your own data in analyses
3. **Reproducibility** - Scripts stored with exact content
4. **Security** - File validation and unique naming
5. **Integration** - Works seamlessly with existing workflows

## 🎯 **Future Enhancements**

- [ ] File size limits configuration
- [ ] Automatic file cleanup after X days
- [ ] File versioning
- [ ] Compressed upload support
- [ ] Direct S3/cloud storage integration
- [ ] File preview for common formats
- [ ] Drag & drop interface
- [ ] Progress bars for large uploads
- [ ] Batch upload support
- [ ] File sharing between users

---

**Last Updated**: October 8, 2025  
**Version**: 1.0.0  
**Status**: Fully Operational
