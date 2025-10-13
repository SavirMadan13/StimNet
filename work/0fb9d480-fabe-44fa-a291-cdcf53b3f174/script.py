# Import data loading helper (automatically available)
import sys
sys.path.insert(0, '/Users/savirmadan/Development/StimNet/distributed_node')
from data_loader import load_data, save_results

print("🔍 Starting analysis...")

# Load data from selected catalog (no paths needed!)
data = load_data()

# Access your data by name
subjects = data['subjects']
print(f"📊 Loaded {len(subjects)} subjects")

# Your analysis here
result = {
    "sample_size": len(subjects),
    "age_mean": float(subjects['age'].mean()),
    "sex_distribution": subjects['sex'].value_counts().to_dict(),
    "analysis_complete": True
}

# Save results
save_results(result)
print(f"✅ Analysis complete!")
