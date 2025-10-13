# Import data loading helper
from data_loader import load_data, save_results
from scipy import stats

print("📈 Correlation Analysis Starting...")

# Load data from selected catalog (no paths needed!)
data_dict = load_data()
subjects = data_dict['subjects']
outcomes = data_dict['outcomes']

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
        }
    }
    
    print(f"✅ Correlation analysis complete!")
    print(f"📊 Age vs UPDRS: r={corr_age_updrs:.3f}, p={p_age_updrs:.3f}")
    print(f"📊 QoL vs UPDRS change: r={corr_qol_updrs:.3f}, p={p_qol_updrs:.3f}")
else:
    result = {"error": "Insufficient data for correlation analysis"}

# Save results
save_results(result)