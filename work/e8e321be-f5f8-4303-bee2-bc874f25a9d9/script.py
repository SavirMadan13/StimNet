
import pandas as pd
import os
import json
from datetime import datetime

print("🔍 REAL EXECUTION: Starting analysis...")

# Load actual data
data_root = os.environ.get('DATA_ROOT', './data')
subjects_path = os.path.join(data_root, 'catalogs', 'clinical_trial_data', 'subjects.csv')

print(f"📂 Loading data from: {subjects_path}")

if os.path.exists(subjects_path):
    df = pd.read_csv(subjects_path)
    print(f"📊 Loaded {len(df)} subjects")
    
    # Real analysis
    result = {
        "analysis_type": "real_data_analysis",
        "timestamp": datetime.now().isoformat(),
        "sample_size": len(df),
        "columns": list(df.columns),
        "age_mean": float(df['age'].mean()) if 'age' in df.columns else None,
        "sex_counts": df['sex'].value_counts().to_dict() if 'sex' in df.columns else None,
        "execution_mode": "REAL_PROCESSING"
    }
    
    print(f"✅ Analysis complete: {result['sample_size']} subjects processed")
    
    # Save results
    output_file = os.environ.get('OUTPUT_FILE', 'output.json')
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
else:
    print(f"❌ Data file not found: {subjects_path}")
    result = {"error": "Data file not found"}
    
    output_file = os.environ.get('OUTPUT_FILE', 'output.json')
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

print("🏁 Script execution complete")
