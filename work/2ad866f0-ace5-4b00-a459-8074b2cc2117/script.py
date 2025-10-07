import pandas as pd
import numpy as np
from scipy import stats
import os
import json
from datetime import datetime

print("📈 Correlation Analysis Starting...")

# Load data
data_root = os.environ.get('DATA_ROOT', './data')
subjects = pd.read_csv(f'{data_root}/catalogs/clinical_trial_data/subjects.csv')
outcomes = pd.read_csv(f'{data_root}/catalogs/clinical_trial_data/outcomes.csv')

print(f"📂 Loaded {len(subjects)} subjects, {len(outcomes)} outcomes")

# Merge datasets
data = subjects.merge(outcomes, on=['subject_id', 'visit'], how='inner')
print(f"🔗 Merged dataset: {len(data)} records")

# Correlation analysis
if len(data) >= 10:
    corr_age_updrs, p_age_updrs = stats.pearsonr(data['age'], data['UPDRS_total'])
    corr_qol_updrs, p_qol_updrs = stats.pearsonr(data['quality_of_life'], data['UPDRS_change'])
    
    result = {
        "analysis_type": "correlation_analysis",
        "sample_size": len(data),
        "correlations": {
            "age_vs_UPDRS_total": {
                "correlation": float(corr_age_updrs),
                "p_value": float(p_age_updrs),
                "significant": p_age_updrs < 0.05
            },
            "quality_of_life_vs_UPDRS_change": {
                "correlation": float(corr_qol_updrs), 
                "p_value": float(p_qol_updrs),
                "significant": p_qol_updrs < 0.05
            }
        },
        "timestamp": datetime.now().isoformat()
    }
    
    print(f"✅ Correlation analysis complete!")
    print(f"📊 Age vs UPDRS: r={corr_age_updrs:.3f}, p={p_age_updrs:.3f}")
    print(f"📊 QoL vs UPDRS change: r={corr_qol_updrs:.3f}, p={p_qol_updrs:.3f}")
else:
    result = {"error": "Insufficient data for correlation analysis"}

# Save results
with open(os.environ.get('OUTPUT_FILE', 'output.json'), 'w') as f:
    json.dump(result, f, indent=2)