# Data Manifest Guide

## Overview
The **data manifest** (`data/data_manifest.json`) is a centralized configuration file that defines all available datasets, their locations, and metadata. The frontend dynamically reads this file to display available data catalogs.

## 🎯 **Why Use a Manifest?**

### **Before (Hardcoded):**
```python
# Had to update database manually
catalog = DataCatalog(
    name="my_dataset",
    description="My description",
    ...
)
db.add(catalog)
db.commit()
```

### **After (Manifest-Based):**
```json
{
  "catalogs": [
    {
      "id": "my_dataset",
      "name": "My Dataset",
      "description": "My description",
      "files": [...]
    }
  ]
}
```

**Benefits:**
- ✅ Single source of truth
- ✅ Easy to add new datasets (just edit JSON)
- ✅ No database updates needed
- ✅ Version controlled
- ✅ Human readable
- ✅ Can be shared across institutions

---

## 📁 **Manifest Structure**

### **Top Level:**
```json
{
  "version": "1.0",
  "last_updated": "2025-10-08",
  "catalogs": [...]
}
```

### **Catalog Entry:**
```json
{
  "id": "clinical_trial_data",
  "name": "Clinical Trial Data",
  "description": "Synthetic clinical trial dataset for Parkinson's disease research",
  "institution": "Default Institution",
  "data_type": "tabular",
  "privacy_level": "high",
  "min_cohort_size": 10,
  "files": [...],
  "metadata": {...}
}
```

### **File Entry:**
```json
{
  "name": "subjects",
  "path": "data/catalogs/clinical_trial_data/subjects.csv",
  "type": "csv",
  "description": "Subject demographics and diagnosis information",
  "columns": ["subject_id", "age", "sex", "diagnosis", "visit"],
  "record_count": 150
}
```

### **Metadata (Optional):**
```json
{
  "study_name": "Parkinson's Disease Progression Study",
  "date_range": "2015-2023",
  "total_subjects": 150,
  "total_visits": 450,
  "primary_endpoint": "UPDRS score change"
}
```

---

## 🚀 **How It Works**

### **1. API Reads Manifest**
```python
# In real_main.py
manifest_path = Path("data/data_manifest.json")
with open(manifest_path, 'r') as f:
    manifest = json.load(f)

# Verify files exist and count records
for catalog in manifest['catalogs']:
    for file_info in catalog['files']:
        if Path(file_info['path']).exists():
            df = pd.read_csv(file_info['path'])
            file_info['actual_record_count'] = len(df)
```

### **2. Frontend Fetches from API**
```javascript
// In app.js
const response = await fetch('/api/v1/data-catalogs');
const catalogs = await response.json();

// Displays:
// - Catalog names
// - File lists with record counts
// - Metadata (study info, date ranges)
// - Privacy settings
```

### **3. Dynamic Display**
```html
🏥 Clinical Trial Data
Synthetic clinical trial dataset for Parkinson's disease research
📊 300 total records | 🔒 Privacy: high | 👥 Min cohort: 10

  ✅ subjects: 150 records
  ✅ outcomes: 150 records

Study: Parkinson's Disease Progression Study
Period: 2015-2023
```

---

## 📝 **Adding a New Dataset**

### **Step 1: Add Your Data Files**

```bash
mkdir -p data/catalogs/my_new_study
cp /path/to/your/data.csv data/catalogs/my_new_study/
```

### **Step 2: Update Manifest**

Edit `data/data_manifest.json`:

```json
{
  "catalogs": [
    {
      "id": "my_new_study",
      "name": "My New Study",
      "description": "Description of my study",
      "institution": "My Institution",
      "data_type": "tabular",
      "privacy_level": "high",
      "min_cohort_size": 10,
      "files": [
        {
          "name": "patient_data",
          "path": "data/catalogs/my_new_study/data.csv",
          "type": "csv",
          "description": "Patient demographic and clinical data",
          "columns": ["patient_id", "age", "diagnosis"],
          "record_count": 200
        }
      ],
      "metadata": {
        "study_name": "My Research Study",
        "date_range": "2020-2024",
        "total_subjects": 200
      }
    }
  ]
}
```

### **Step 3: Refresh Browser**

That's it! The new dataset appears automatically:
- ✅ In the dropdown
- ✅ In the catalog information section
- ✅ With all metadata displayed

**No server restart needed!** (Just refresh the web page)

---

## 🎨 **Supported Data Types**

### **CSV Files (Most Common)**
```json
{
  "name": "my_data",
  "path": "data/catalogs/my_study/data.csv",
  "type": "csv",
  "columns": ["col1", "col2", "col3"],
  "record_count": 100
}
```

### **NIfTI Files (Neuroimaging)**
```json
{
  "name": "brain_scans",
  "path": "data/catalogs/imaging/scans/",
  "type": "nifti",
  "description": "T1-weighted structural MRI scans",
  "file_pattern": "*.nii.gz",
  "record_count": 50
}
```

### **Multiple Files**
```json
{
  "files": [
    {
      "name": "demographics",
      "path": "data/catalogs/study/demographics.csv",
      "type": "csv"
    },
    {
      "name": "biomarkers",
      "path": "data/catalogs/study/biomarkers.csv",
      "type": "csv"
    },
    {
      "name": "imaging",
      "path": "data/catalogs/study/scans/",
      "type": "nifti"
    }
  ]
}
```

---

## 🔍 **Advanced Features**

### **1. File Existence Checking**

The API automatically verifies files exist:

```json
// Response includes existence status
{
  "name": "subjects",
  "path": "data/catalogs/study/subjects.csv",
  "exists": true,  // ✅ File found
  "actual_record_count": 150  // Real count from file
}
```

### **2. Dynamic Record Counting**

For CSV files, the API counts actual records:

```json
{
  "record_count": 150,  // From manifest
  "actual_record_count": 150  // Counted from file
}
```

### **3. Privacy Settings Per Catalog**

```json
{
  "id": "sensitive_data",
  "privacy_level": "high",
  "min_cohort_size": 50,  // Stricter privacy
  ...
}

{
  "id": "public_data",
  "privacy_level": "low",
  "min_cohort_size": 5,  // More lenient
  ...
}
```

### **4. Rich Metadata**

```json
{
  "metadata": {
    "study_name": "Multi-Site Alzheimer's Study",
    "date_range": "2018-2024",
    "total_subjects": 500,
    "sites": ["Boston", "NYC", "SF"],
    "funding": "NIH R01-123456",
    "pi": "Dr. Jane Smith",
    "contact": "jsmith@example.edu",
    "publications": [
      "Smith et al. 2023, Nature Medicine"
    ]
  }
}
```

---

## 🌐 **Multi-Institution Setup**

### **Each Institution Creates Their Own Manifest**

**Hospital A (Boston):**
```json
{
  "catalogs": [
    {
      "id": "mgh_parkinsons",
      "name": "MGH Parkinson's Cohort",
      "institution": "Massachusetts General Hospital",
      "files": [
        {
          "path": "data/catalogs/mgh_parkinsons/subjects.csv",
          "record_count": 150
        }
      ]
    }
  ]
}
```

**Hospital B (NYC):**
```json
{
  "catalogs": [
    {
      "id": "sinai_ms_study",
      "name": "Mount Sinai MS Study",
      "institution": "Mount Sinai Hospital",
      "files": [
        {
          "path": "data/catalogs/sinai_ms/patients.csv",
          "record_count": 200
        }
      ]
    }
  ]
}
```

**Each institution:**
1. Clones the repo
2. Adds their data files
3. Updates `data/data_manifest.json` with their data
4. Starts server
5. Gets their own public URL

**Result:** Each site has its own manifest describing its own data!

---

## 📊 **Example: Complete Manifest**

```json
{
  "version": "1.0",
  "last_updated": "2025-10-08",
  "institution": "Massachusetts General Hospital",
  "contact": "data-admin@mgh.harvard.edu",
  
  "catalogs": [
    {
      "id": "parkinsons_longitudinal",
      "name": "Parkinson's Longitudinal Study",
      "description": "10-year longitudinal study of PD progression",
      "institution": "MGH Neurology",
      "data_type": "tabular",
      "privacy_level": "high",
      "min_cohort_size": 20,
      
      "files": [
        {
          "name": "demographics",
          "path": "data/catalogs/parkinsons/demographics.csv",
          "type": "csv",
          "description": "Patient demographics at baseline",
          "columns": ["patient_id", "age", "sex", "education", "onset_age"],
          "record_count": 250
        },
        {
          "name": "clinical_visits",
          "path": "data/catalogs/parkinsons/visits.csv",
          "type": "csv",
          "description": "Clinical assessments at each visit",
          "columns": ["patient_id", "visit_date", "visit_number", "UPDRS_I", "UPDRS_II", "UPDRS_III", "UPDRS_IV"],
          "record_count": 1500
        },
        {
          "name": "biomarkers",
          "path": "data/catalogs/parkinsons/biomarkers.csv",
          "type": "csv",
          "description": "CSF and blood biomarkers",
          "columns": ["patient_id", "sample_date", "alpha_synuclein", "tau", "amyloid_beta"],
          "record_count": 750
        },
        {
          "name": "imaging_scans",
          "path": "data/catalogs/parkinsons/imaging/",
          "type": "nifti",
          "description": "T1-weighted structural MRI scans",
          "file_pattern": "sub-*/anat/sub-*_T1w.nii.gz",
          "record_count": 250
        }
      ],
      
      "metadata": {
        "study_name": "MGH Parkinson's Progression and Imaging Study (MPPIS)",
        "date_range": "2013-2023",
        "total_subjects": 250,
        "total_visits": 1500,
        "follow_up_years": 10,
        "primary_endpoint": "Rate of motor decline",
        "funding": "NIH R01-NS123456, Michael J. Fox Foundation",
        "pi": "Dr. Jane Smith",
        "contact": "jsmith@mgh.harvard.edu",
        "publications": [
          "Smith et al. 2023, Movement Disorders",
          "Johnson et al. 2022, Brain"
        ],
        "data_use_agreement": "Approved researchers only, IRB required"
      }
    },
    
    {
      "id": "alzheimers_biomarkers",
      "name": "Alzheimer's Biomarker Study",
      "description": "CSF and plasma biomarkers in AD progression",
      "institution": "MGH Memory Disorders",
      "data_type": "tabular",
      "privacy_level": "high",
      "min_cohort_size": 15,
      
      "files": [
        {
          "name": "participants",
          "path": "data/catalogs/alzheimers/participants.csv",
          "type": "csv",
          "description": "Participant demographics and APOE status",
          "columns": ["participant_id", "age", "sex", "education", "apoe_e4", "diagnosis"],
          "record_count": 180
        },
        {
          "name": "biomarkers",
          "path": "data/catalogs/alzheimers/biomarkers.csv",
          "type": "csv",
          "description": "CSF and plasma biomarker measurements",
          "columns": ["participant_id", "timepoint", "csf_abeta42", "csf_tau", "csf_ptau", "plasma_nfl"],
          "record_count": 540
        }
      ],
      
      "metadata": {
        "study_name": "MGH Alzheimer's Biomarker Initiative",
        "date_range": "2015-2024",
        "total_subjects": 180,
        "diagnostic_groups": {
          "cognitively_normal": 60,
          "mci": 60,
          "ad_dementia": 60
        }
      }
    }
  ]
}
```

---

## 🔧 **How to Add Your Data**

### **Option 1: Simple CSV Dataset**

```json
{
  "id": "my_simple_study",
  "name": "My Simple Study",
  "description": "A simple CSV dataset",
  "data_type": "tabular",
  "privacy_level": "high",
  "min_cohort_size": 10,
  "files": [
    {
      "name": "data",
      "path": "data/catalogs/my_study/data.csv",
      "type": "csv",
      "description": "Main dataset",
      "columns": ["id", "age", "outcome"],
      "record_count": 100
    }
  ],
  "metadata": {
    "study_name": "My Study Name",
    "date_range": "2020-2024"
  }
}
```

### **Option 2: Multi-File Dataset**

```json
{
  "id": "complex_study",
  "name": "Complex Multi-Modal Study",
  "description": "Study with multiple data types",
  "data_type": "multimodal",
  "privacy_level": "high",
  "min_cohort_size": 20,
  "files": [
    {
      "name": "demographics",
      "path": "data/catalogs/complex/demographics.csv",
      "type": "csv",
      "columns": ["subject_id", "age", "sex"],
      "record_count": 200
    },
    {
      "name": "clinical_scores",
      "path": "data/catalogs/complex/clinical.csv",
      "type": "csv",
      "columns": ["subject_id", "visit", "score"],
      "record_count": 600
    },
    {
      "name": "mri_scans",
      "path": "data/catalogs/complex/imaging/",
      "type": "nifti",
      "file_pattern": "*.nii.gz",
      "record_count": 200
    },
    {
      "name": "genetic_data",
      "path": "data/catalogs/complex/genetics.vcf",
      "type": "vcf",
      "description": "Whole genome sequencing variants",
      "record_count": 200
    }
  ],
  "metadata": {
    "modalities": ["clinical", "imaging", "genomic"],
    "total_subjects": 200
  }
}
```

### **Option 3: External/Network Storage**

```json
{
  "id": "network_data",
  "name": "Network-Mounted Data",
  "description": "Data on network storage",
  "files": [
    {
      "name": "subjects",
      "path": "/mnt/research_data/study_a/subjects.csv",
      "type": "csv",
      "description": "Subjects on network mount",
      "record_count": 500
    },
    {
      "name": "imaging",
      "path": "/mnt/imaging_archive/study_a/",
      "type": "nifti",
      "description": "Scans on imaging server",
      "record_count": 500
    }
  ]
}
```

---

## 🎯 **Frontend Display**

### **What Users See:**

When they visit your site, the dropdown shows:
```
[Select Data Catalog ▼]
  Clinical Trial Data - 300 records
  Imaging Data - 100 records
  Demo Dataset - 50 records
  My New Study - 200 records  ← Automatically added!
```

And the information panel shows:
```
🏥 Clinical Trial Data
Synthetic clinical trial dataset for Parkinson's disease research
📊 300 total records | 🔒 Privacy: high | 👥 Min cohort: 10

  ✅ subjects: 150 records
  ✅ outcomes: 150 records

Study: Parkinson's Disease Progression Study
Period: 2015-2023
```

---

## 🔄 **Workflow**

### **Traditional (Database-Based):**
```
1. Add data files
2. Write Python script to insert into database
3. Run script
4. Restart server
5. Hope it worked
```

### **New (Manifest-Based):**
```
1. Add data files
2. Edit data_manifest.json
3. Refresh browser
4. Done! ✅
```

---

## 📖 **Manifest Schema Reference**

### **Required Fields:**
```json
{
  "id": "unique_identifier",        // Required, used in API calls
  "name": "Display Name",            // Required, shown in UI
  "description": "Description text", // Required, shown in UI
  "data_type": "tabular",           // Required: tabular, imaging, multimodal
  "files": [...]                     // Required, at least one file
}
```

### **Optional Fields:**
```json
{
  "institution": "Institution Name",     // Optional
  "privacy_level": "high",               // Optional, default: "high"
  "min_cohort_size": 10,                 // Optional, default: 10
  "metadata": {},                        // Optional, any custom fields
  "access_level": "public",              // Optional: public, restricted, private
  "tags": ["parkinsons", "longitudinal"] // Optional, for filtering
}
```

### **File Fields:**
```json
{
  "name": "file_name",              // Required
  "path": "path/to/file.csv",       // Required
  "type": "csv",                    // Required: csv, nifti, json, etc.
  "description": "File description", // Optional
  "columns": ["col1", "col2"],      // Optional, for CSV
  "record_count": 100,              // Optional, estimated count
  "file_pattern": "*.nii.gz"        // Optional, for directories
}
```

---

## 🧪 **Testing**

### **Test 1: Verify Manifest is Valid JSON**
```bash
cat data/data_manifest.json | python -m json.tool
```

### **Test 2: Check API Response**
```bash
curl http://localhost:8000/api/v1/data-catalogs | python -m json.tool
```

### **Test 3: Verify Frontend Display**
1. Visit http://localhost:8000
2. Check dropdown has all catalogs
3. Check information section shows details
4. Open browser console (F12)
5. Look for: `Loaded X data catalogs`

---

## 🎓 **Best Practices**

### **1. Keep Manifest Updated**
- Update `last_updated` field when you make changes
- Update `record_count` when data changes
- Add new files as they're added

### **2. Use Descriptive IDs**
```json
// Good
"id": "parkinsons_longitudinal_2015_2023"

// Bad
"id": "study1"
```

### **3. Include Rich Metadata**
```json
"metadata": {
  "study_name": "Full study name",
  "date_range": "Start-End",
  "total_subjects": 100,
  "pi": "Principal Investigator",
  "contact": "email@institution.edu"
}
```

### **4. Document Your Columns**
```json
"columns": ["patient_id", "age", "diagnosis"],
"column_descriptions": {
  "patient_id": "Unique patient identifier (de-identified)",
  "age": "Age in years at baseline",
  "diagnosis": "Primary diagnosis (PD, MSA, PSP)"
}
```

### **5. Version Your Manifest**
```bash
# Keep history
cp data/data_manifest.json data/data_manifest_v1.0.json

# Make changes
vim data/data_manifest.json

# Update version
"version": "1.1"
```

---

## 🚀 **Quick Start Template**

Copy this template to add your own data:

```json
{
  "version": "1.0",
  "last_updated": "2025-10-08",
  "institution": "YOUR_INSTITUTION_NAME",
  
  "catalogs": [
    {
      "id": "your_study_id",
      "name": "Your Study Name",
      "description": "Brief description of your study",
      "institution": "Your Department/Lab",
      "data_type": "tabular",
      "privacy_level": "high",
      "min_cohort_size": 10,
      
      "files": [
        {
          "name": "main_data",
          "path": "data/catalogs/your_study/data.csv",
          "type": "csv",
          "description": "Main dataset description",
          "columns": ["id", "variable1", "variable2"],
          "record_count": 100
        }
      ],
      
      "metadata": {
        "study_name": "Full Study Name",
        "date_range": "YYYY-YYYY",
        "total_subjects": 100,
        "pi": "Principal Investigator Name",
        "contact": "email@institution.edu"
      }
    }
  ]
}
```

---

## ✅ **Benefits Summary**

| Feature | Before | After |
|---------|--------|-------|
| **Add dataset** | Python script + DB | Edit JSON file |
| **Update metadata** | Database update | Edit JSON file |
| **See changes** | Restart server | Refresh browser |
| **Share config** | Export database | Share JSON file |
| **Version control** | Difficult | Easy (Git) |
| **Human readable** | No (binary DB) | Yes (JSON) |
| **Multi-institution** | Complex | Simple (each has own manifest) |

---

**Last Updated**: October 8, 2025  
**Version**: 1.0.0  
**Status**: Fully Operational
