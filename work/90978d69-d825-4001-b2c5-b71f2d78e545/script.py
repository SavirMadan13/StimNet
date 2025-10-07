import pandas as pd
import os
import json
from datetime import datetime

print("🌐 WEB INTERFACE TEST via Cloudflare!")

data_root = os.environ.get("DATA_ROOT", "./data")
subjects_path = os.path.join(data_root, "catalogs", "clinical_trial_data", "subjects.csv")

if os.path.exists(subjects_path):
    df = pd.read_csv(subjects_path)
    result = {
        "web_interface_test": True,
        "via_cloudflare": True,
        "sample_size": len(df),
        "age_mean": float(df["age"].mean()),
        "sex_counts": df["sex"].value_counts().to_dict(),
        "diagnosis_counts": df["diagnosis"].value_counts().to_dict(),
        "message": "Web interface working through Cloudflare tunnel!",
        "timestamp": datetime.now().isoformat()
    }
    print(f"Web interface test complete: {result}")
else:
    result = {"error": "Data not found"}

with open(os.environ.get("OUTPUT_FILE", "output.json"), "w") as f:
    json.dump(result, f, indent=2)