# Auto Column Detection Guide

## 🎯 **Overview**

The StimNet platform now automatically detects column names and types from your data files, eliminating the need to manually define columns in the data manifest.

## 🚀 **How It Works**

### **1. Simplified Manifest Structure**

You only need to define the basic structure in `data/data_manifest.json`:

```json
{
  "version": "1.0",
  "catalogs": [
    {
      "id": "my_study",
      "name": "My Study Dataset",
      "description": "Description of your dataset",
      "institution": "Your Institution",
      "files": [
        {
          "name": "data",
          "path": "data/catalogs/my_study/data.csv",
          "type": "csv",
          "description": "What this file contains"
        }
      ]
    }
  ]
}
```

### **2. Automatic Column Detection**

The system automatically:
- ✅ **Reads your CSV files**
- ✅ **Detects column names** from headers
- ✅ **Infers data types** (string, int, float, bool, datetime)
- ✅ **Counts actual records**
- ✅ **Enriches the API response** with column information

### **3. Supported Data Types**

| Detected Type | Description | Example |
|---------------|-------------|---------|
| `string` | Text data | "PD", "M/F", "sub-001" |
| `int` | Whole numbers | 65, 1, 0 |
| `float` | Decimal numbers | 3.14, 0.5, 87.3 |
| `bool` | Boolean values | true, false |
| `datetime` | Date/time values | "2023-01-15" |

## 🔧 **Integration Points**

### **1. API Endpoints Auto-Enhancement**

The following endpoints automatically detect columns:

- **`GET /api/v1/data-catalogs`** - Lists catalogs with auto-detected columns
- **`GET /api/v1/data-catalogs-with-options`** - Enhanced catalog information

### **2. Frontend Display**

The frontend automatically displays:
- Column names and types
- Record counts
- File existence status
- Rich metadata

### **3. Script Execution**

Analysis scripts can access column information through the `data_loader` module:

```python
from data_loader import load_data

# Load data with column information
data = load_data()
subjects = data['subjects']

# Column information is available
print(f"Columns: {list(subjects.columns)}")
print(f"Types: {subjects.dtypes}")
```

## 📝 **Usage Examples**

### **Example 1: Adding a New Dataset**

1. **Create your data file:**
   ```bash
   # Place your CSV in the data directory
   cp my_data.csv data/catalogs/my_study/
   ```

2. **Update the manifest:**
   ```json
   {
     "id": "my_study",
     "name": "My Study",
     "description": "My research dataset",
     "institution": "My Institution",
     "files": [
       {
         "name": "data",
         "path": "data/catalogs/my_study/my_data.csv",
         "type": "csv",
         "description": "Main dataset"
       }
     ]
   }
   ```

3. **That's it!** The system automatically:
   - Detects all columns
   - Infers data types
   - Counts records
   - Makes it available in the frontend

### **Example 2: Multiple Files**

```json
{
  "id": "multi_file_study",
  "name": "Multi-File Study",
  "files": [
    {
      "name": "demographics",
      "path": "data/catalogs/study/demographics.csv",
      "type": "csv",
      "description": "Subject demographics"
    },
    {
      "name": "outcomes",
      "path": "data/catalogs/study/outcomes.csv", 
      "type": "csv",
      "description": "Clinical outcomes"
    },
    {
      "name": "imaging",
      "path": "data/catalogs/study/scans/",
      "type": "nifti",
      "description": "MRI scans"
    }
  ]
}
```

## 🛠 **Manual Generation (Optional)**

If you want to pre-generate the enhanced manifest:

```bash
# Run the auto-generation script
python generate_manifest.py

# This creates data/data_manifest_enhanced.json with all columns detected
```

## 🔍 **API Response Example**

### **Before (Manual Columns):**
```json
{
  "name": "subjects",
  "path": "data/catalogs/study/subjects.csv",
  "type": "csv",
  "columns": [
    {"name": "id", "type": "string", "description": "Subject ID"},
    {"name": "age", "type": "int", "description": "Age in years"}
  ]
}
```

### **After (Auto-Detected):**
```json
{
  "name": "subjects", 
  "path": "data/catalogs/study/subjects.csv",
  "type": "csv",
  "columns": [
    {"name": "id", "type": "string"},
    {"name": "age", "type": "int"},
    {"name": "score", "type": "float"},
    {"name": "diagnosis", "type": "string"}
  ],
  "record_count": 150,
  "exists": true
}
```

## ✅ **Benefits**

1. **No Manual Work**: Just specify file paths, columns are auto-detected
2. **Always Accurate**: Column types reflect actual data
3. **Dynamic Updates**: Changes to files are automatically reflected
4. **Error Prevention**: No typos in column definitions
5. **Time Saving**: No need to manually define hundreds of columns

## 🚨 **Important Notes**

- **File Paths**: Ensure file paths in the manifest are correct
- **File Types**: Currently supports CSV, TSV, JSON, and NIfTI files
- **Performance**: Column detection happens on API calls (cached for performance)
- **Fallback**: If auto-detection fails, files are marked as `exists: false`

## 🔧 **Troubleshooting**

### **File Not Found**
```json
{
  "name": "data",
  "path": "data/catalogs/study/data.csv",
  "exists": false
}
```
**Solution**: Check the file path in your manifest

### **Column Detection Failed**
```json
{
  "columns": [],
  "record_count": 0
}
```
**Solution**: Ensure the file is readable and in a supported format

### **Wrong Data Types**
The system infers types from the first few rows. If types are wrong:
1. Check your data format
2. Consider data cleaning
3. The system will still work, just with different type labels

## 🎯 **Next Steps**

1. **Update your manifest** to use the simplified structure
2. **Test the API endpoints** to see auto-detected columns
3. **Check the frontend** to see the enhanced display
4. **Run analysis scripts** to verify data loading works

The system is now fully automated for column detection! 🚀
