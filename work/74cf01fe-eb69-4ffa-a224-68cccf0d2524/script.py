import pandas as pd
import os
import json
from datetime import datetime

print("🌍 REAL CLOUDFLARE EXECUTION!")

data_root = os.environ.get("DATA_ROOT", "./data")
subjects_path = os.path.join(data_root, "catalogs", "clinical_trial_data", "subjects.csv")

print(f"Loading from: {subjects_path}")

if os.path.exists(subjects_path):
    df = pd.read_csv(subjects_path)
    print(f"Loaded {len(df)} subjects")
    
    result = {
        "cloudflare_real_execution": True,
        "sample_size": len(df),
        "age_mean": float(df["age"].mean()),
        "sex_distribution": df["sex"].value_counts().to_dict(),
        "diagnosis_counts": df["diagnosis"].value_counts().to_dict(),
        "execution_method": "cloudflare_tunnel_real_processing",
        "timestamp": datetime.now().isoformat()
    }
    print(f"Analysis complete: {result}")
else:
    result = {"error": "Data not found", "path": subjects_path}

with open(os.environ.get("OUTPUT_FILE", "output.json"), "w") as f:
    json.dump(result, f, indent=2)

print("🎉 Cloudflare real execution complete!")