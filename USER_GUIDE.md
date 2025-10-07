# 🚀 How to Use the Distributed Data Access Framework

## For End Users (Non-Technical)

### 🌐 **Easy Web Interface**

**Just visit this URL in your browser:**
- **Local**: http://localhost:8000
- **Remote**: https://restructuring-composed-reward-feel.trycloudflare.com

You'll see a simple web page where you can:
1. **Choose a dataset** (Clinical Trial Data, Imaging Data, etc.)
2. **Write or paste your analysis script**
3. **Click "Run Analysis"**
4. **See results in real-time**

### 📊 **What You Can Do:**

#### **Option 1: Use Example Scripts**
- Click **"Load Demographics Example"** for basic statistics
- Click **"Load Correlation Example"** for relationship analysis
- Click **"Run Analysis"** to execute

#### **Option 2: Write Custom Analysis**
```python
# Simple example - paste this into the web interface:
import pandas as pd
import os
import json

# Load the clinical trial data
data_root = os.environ.get('DATA_ROOT', './data')
subjects = pd.read_csv(f'{data_root}/catalogs/clinical_trial_data/subjects.csv')

# Your analysis
result = {
    "total_patients": len(subjects),
    "average_age": float(subjects['age'].mean()),
    "male_female_ratio": subjects['sex'].value_counts().to_dict()
}

# Save results (required)
with open(os.environ.get('OUTPUT_FILE', 'output.json'), 'w') as f:
    json.dump(result, f)
```

### 🎯 **Step-by-Step Instructions:**

1. **Open the website** in your browser
2. **Choose "Clinical Trial Data"** from the dropdown
3. **Keep "Python" selected** as script type
4. **Click "Load Demographics Example"** to get a working script
5. **Click "🚀 Run Analysis"**
6. **Wait 2-3 seconds** for results
7. **See the analysis results** appear below

## For Developers (Technical)

### 🐍 **Python Client SDK**

```python
import asyncio
from client_sdk import DistributedClient, JobSubmission

async def run_analysis():
    # Connect to the server
    async with DistributedClient("https://restructuring-composed-reward-feel.trycloudflare.com") as client:
        # Authenticate
        await client.authenticate("demo", "demo")
        
        # Submit analysis
        job_id = await client.submit_job(JobSubmission(
            target_node_id="node-1",
            data_catalog_name="clinical_trial_data",
            script_type="python",
            script_content="""
import pandas as pd
import os
import json

# Your analysis code here
data_root = os.environ.get('DATA_ROOT', './data')
df = pd.read_csv(f'{data_root}/catalogs/clinical_trial_data/subjects.csv')

result = {
    "sample_size": len(df),
    "mean_age": float(df['age'].mean())
}

with open(os.environ.get('OUTPUT_FILE', 'output.json'), 'w') as f:
    json.dump(result, f)
""",
            parameters={"analysis_type": "custom"}
        ))
        
        # Get results
        result = await client.wait_for_job(job_id)
        print(f"Results: {result.result_data}")

# Run it
asyncio.run(run_analysis())
```

### 🔧 **Direct API Usage**

```bash
# 1. Authenticate
curl -X POST https://restructuring-composed-reward-feel.trycloudflare.com/api/v1/auth/token \
  -d "username=demo&password=demo"

# 2. Submit job (use token from step 1)
curl -X POST https://restructuring-composed-reward-feel.trycloudflare.com/api/v1/jobs \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "target_node_id": "node-1",
    "data_catalog_name": "clinical_trial_data",
    "script_type": "python", 
    "script_content": "import pandas as pd\n# Your script here"
  }'

# 3. Check results
curl https://restructuring-composed-reward-feel.trycloudflare.com/api/v1/jobs/JOB_ID
```

## 📋 **Available Data**

### **Clinical Trial Data (150 subjects)**
```
Columns: subject_id, age, sex, diagnosis, visit
Additional: UPDRS_total, UPDRS_change, quality_of_life, treatment_response
```

### **Imaging Data (100 scans)**
```
Columns: subject_id, scan_type, scan_quality, motion_score, file_path
Types: T1, DTI, fMRI scans
```

## 🛡️ **Privacy & Security**

- **Your data never leaves the server** - only analysis results are returned
- **Minimum sample size enforced** - results blocked if < 5 subjects
- **Script security validation** - dangerous operations blocked
- **Audit logging** - all operations tracked
- **Sandboxed execution** - scripts run in isolated environment

## 🧪 **Example Use Cases**

### **1. Quick Demographics**
```python
# Get basic statistics about the population
subjects = pd.read_csv(f'{data_root}/catalogs/clinical_trial_data/subjects.csv')
result = {
    "total_subjects": len(subjects),
    "age_range": [int(subjects['age'].min()), int(subjects['age'].max())],
    "sex_breakdown": subjects['sex'].value_counts().to_dict()
}
```

### **2. Treatment Response Analysis**
```python
# Analyze treatment effectiveness
subjects = pd.read_csv(f'{data_root}/catalogs/clinical_trial_data/subjects.csv')
outcomes = pd.read_csv(f'{data_root}/catalogs/clinical_trial_data/outcomes.csv')
data = subjects.merge(outcomes, on=['subject_id', 'visit'])

# Calculate response rates
response_rate = data['treatment_response'].mean()
result = {"response_rate": float(response_rate)}
```

### **3. Correlation Studies**
```python
# Find relationships between variables
from scipy import stats
data = subjects.merge(outcomes, on=['subject_id', 'visit'])
corr, p_val = stats.pearsonr(data['age'], data['UPDRS_change'])
result = {"correlation": float(corr), "p_value": float(p_val)}
```

## 🚀 **Getting Started (Easiest)**

1. **Visit**: https://restructuring-composed-reward-feel.trycloudflare.com
2. **Click "Load Demographics Example"**
3. **Click "🚀 Run Analysis"**
4. **See real results from 150 subjects!**

That's it! You're now running distributed data analysis! 🎉

## 🆘 **Need Help?**

- **Web Interface**: Just visit the main URL and click buttons
- **API Documentation**: Add `/docs` to any URL
- **Health Check**: Add `/health` to any URL
- **Data Catalogs**: Add `/api/v1/data-catalogs` to any URL

The system is designed to be **intuitive and self-explanatory** - just visit the main URL and start exploring! 🌟
