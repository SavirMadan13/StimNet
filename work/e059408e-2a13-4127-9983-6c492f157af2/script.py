# Import data loading helper
from data_loader import load_data, save_results

print("📊 Demographics Analysis Starting...")

# Load data from selected catalog (no paths needed!)
data = load_data()
subjects = data['subjects']

print(f"📂 Loaded {len(subjects)} subjects")

# Calculate demographics
result = {
    "analysis_type": "demographics",
    "total_subjects": len(subjects),
    "age_statistics": {
        "mean": float(subjects['age'].mean()),
        "std": float(subjects['age'].std()),
        "min": int(subjects['age'].min()),
        "max": int(subjects['age'].max())
    },
    "sex_distribution": subjects['sex'].value_counts().to_dict(),
    "diagnosis_breakdown": subjects['diagnosis'].value_counts().to_dict(),
    "visit_distribution": subjects['visit'].value_counts().to_dict()
}

print(f"✅ Demographics analysis complete!")
print(f"👥 {result['total_subjects']} subjects analyzed")

# Save results
save_results(result)