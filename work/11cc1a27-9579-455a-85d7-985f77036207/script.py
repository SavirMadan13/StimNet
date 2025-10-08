import pandas as pd
import os
import json
from datetime import datetime

print("📊 Demographics Analysis Starting...")

# Load clinical data
data_root = os.environ.get('DATA_ROOT', './data')
subjects_path = os.path.join(data_root, 'catalogs', 'clinical_trial_data', 'subjects.csv')

if os.path.exists(subjects_path):
    df = pd.read_csv(subjects_path)
    print(f"📂 Loaded {len(df)} subjects")
    
    # Calculate demographics
    result = {
        "analysis_type": "demographics",
        "total_subjects": len(df),
        "age_statistics": {
            "mean": float(df['age'].mean()),
            "std": float(df['age'].std()),
            "min": int(df['age'].min()),
            "max": int(df['age'].max())
        },
        "sex_distribution": df['sex'].value_counts().to_dict(),
        "diagnosis_breakdown": df['diagnosis'].value_counts().to_dict(),
        "visit_distribution": df['visit'].value_counts().to_dict(),
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"✅ Demographics analysis complete!")
    print(f"👥 {result['total_subjects']} subjects analyzed")
    
    # Save results
    with open(os.environ.get('OUTPUT_FILE', 'output.json'), 'w') as f:
        json.dump(result, f, indent=2)
else:
    print("❌ Data file not found")
    result = {"error": "Data not found"}
    with open(os.environ.get('OUTPUT_FILE', 'output.json'), 'w') as f:
        json.dump(result, f)