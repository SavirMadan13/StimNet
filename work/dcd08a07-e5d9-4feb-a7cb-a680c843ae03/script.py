import pandas as pd
import os
import json
from datetime import datetime

print("🔍 Starting analysis...")

# Load data
data_root = os.environ.get('DATA_ROOT', './data')
subjects_path = os.path.join(data_root, 'catalogs', 'clinical_trial_data', 'subjects.csv')

if os.path.exists(subjects_path):
    df = pd.read_csv(subjects_path)
    print(f"📊 Loaded {len(df)} subjects")
    
    # Your analysis here
    result = {
        "sample_size": len(df),
        "age_mean": float(df['age'].mean()),
        "sex_distribution": df['sex'].value_counts().to_dict(),
        "analysis_complete": True,
        "timestamp": datetime.now().isoformat()
    }
    
    # Save results
    with open(os.environ.get('OUTPUT_FILE', 'output.json'), 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"✅ Analysis complete: {result}")
else:
    print("❌ Data not found")
