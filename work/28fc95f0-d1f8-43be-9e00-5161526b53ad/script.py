import pandas as pd
import os
import json
from datetime import datetime

print("🌍 CLOUDFLARE TUNNEL TEST!")

data_root = os.environ.get("DATA_ROOT", "./data")
subjects_path = os.path.join(data_root, "catalogs", "clinical_trial_data", "subjects.csv")

if os.path.exists(subjects_path):
    df = pd.read_csv(subjects_path)
    result = {
        "tunnel_test": True,
        "sample_size": len(df),
        "age_mean": float(df["age"].mean()),
        "execution_via": "cloudflare_tunnel",
        "timestamp": datetime.now().isoformat()
    }
else:
    result = {"error": "Data not found"}

with open(os.environ.get("OUTPUT_FILE", "output.json"), "w") as f:
    json.dump(result, f)

print(f"Tunnel test complete: {result}")