"""
Script to set up demo data for testing the distributed framework
"""
import os
import pandas as pd
import numpy as np
import json
from pathlib import Path
from data_layer.catalog_manager import DataCatalogManager


def create_demo_datasets():
    """Create demo datasets for testing"""
    
    # Create data directory
    data_dir = Path("./data/demo")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Set random seed for reproducible data
    np.random.seed(42)
    
    # Dataset 1: Patient Demographics and Outcomes
    print("Creating patient demographics dataset...")
    n_patients = 250
    
    patients_data = {
        'patient_id': [f'P{i:04d}' for i in range(1, n_patients + 1)],
        'age': np.random.normal(55, 15, n_patients).clip(18, 90).astype(int),
        'gender': np.random.choice(['M', 'F'], n_patients, p=[0.48, 0.52]),
        'diagnosis': np.random.choice(['Type1', 'Type2', 'Control'], n_patients, p=[0.3, 0.4, 0.3]),
        'baseline_score': np.random.normal(50, 15, n_patients).clip(0, 100),
        'followup_score': np.random.normal(55, 18, n_patients).clip(0, 100),
        'treatment_duration_days': np.random.normal(180, 30, n_patients).clip(30, 365).astype(int),
        'site': np.random.choice(['Site_A', 'Site_B', 'Site_C'], n_patients, p=[0.4, 0.35, 0.25])
    }
    
    # Add treatment effects
    for i, diagnosis in enumerate(patients_data['diagnosis']):
        if diagnosis == 'Type1':
            patients_data['followup_score'][i] += np.random.normal(10, 5)
        elif diagnosis == 'Type2':
            patients_data['followup_score'][i] += np.random.normal(5, 3)
    
    patients_df = pd.DataFrame(patients_data)
    patients_df['followup_score'] = patients_df['followup_score'].clip(0, 100)
    patients_df['improvement'] = patients_df['followup_score'] - patients_df['baseline_score']
    
    patients_df.to_csv(data_dir / "patient_data.csv", index=False)
    print(f"Created patient_data.csv with {len(patients_df)} records")
    
    # Dataset 2: Laboratory Results
    print("Creating laboratory results dataset...")
    n_lab_results = n_patients * 3  # Multiple tests per patient
    
    lab_data = {
        'patient_id': np.random.choice(patients_data['patient_id'], n_lab_results),
        'test_date': pd.date_range('2023-01-01', '2023-12-31', periods=n_lab_results),
        'test_type': np.random.choice(['HbA1c', 'Glucose', 'Cholesterol', 'BP_Systolic', 'BP_Diastolic'], n_lab_results),
        'result_value': np.random.normal(100, 25, n_lab_results).clip(50, 200),
        'reference_range_low': 80,
        'reference_range_high': 120,
        'lab_site': np.random.choice(['Lab_Central', 'Lab_Regional'], n_lab_results, p=[0.7, 0.3])
    }
    
    lab_df = pd.DataFrame(lab_data)
    lab_df['abnormal'] = (lab_df['result_value'] < lab_df['reference_range_low']) | (lab_df['result_value'] > lab_df['reference_range_high'])
    
    lab_df.to_csv(data_dir / "lab_results.csv", index=False)
    print(f"Created lab_results.csv with {len(lab_df)} records")
    
    # Dataset 3: Imaging Data (metadata only)
    print("Creating imaging metadata dataset...")
    n_scans = n_patients * 2  # 2 scans per patient on average
    
    imaging_data = {
        'patient_id': np.random.choice(patients_data['patient_id'], n_scans),
        'scan_date': pd.date_range('2023-01-01', '2023-12-31', periods=n_scans),
        'scan_type': np.random.choice(['MRI', 'CT', 'PET'], n_scans, p=[0.5, 0.3, 0.2]),
        'scan_quality': np.random.choice(['Excellent', 'Good', 'Fair'], n_scans, p=[0.6, 0.3, 0.1]),
        'radiologist': np.random.choice(['Dr_Smith', 'Dr_Jones', 'Dr_Brown'], n_scans),
        'findings_score': np.random.normal(2.5, 1.5, n_scans).clip(0, 5),
        'file_path': [f'/imaging/scans/{i:06d}.nii.gz' for i in range(n_scans)]
    }
    
    imaging_df = pd.DataFrame(imaging_data)
    imaging_df.to_csv(data_dir / "imaging_metadata.csv", index=False)
    print(f"Created imaging_metadata.csv with {len(imaging_df)} records")
    
    # Dataset 4: Genomic Data (simulated)
    print("Creating genomic data dataset...")
    n_variants = 1000
    n_samples = min(100, n_patients)  # Subset of patients with genomic data
    
    genomic_data = {
        'sample_id': np.random.choice(patients_data['patient_id'][:n_samples], n_variants),
        'chromosome': np.random.choice(range(1, 23), n_variants),
        'position': np.random.randint(1000000, 250000000, n_variants),
        'ref_allele': np.random.choice(['A', 'T', 'G', 'C'], n_variants),
        'alt_allele': np.random.choice(['A', 'T', 'G', 'C'], n_variants),
        'genotype': np.random.choice(['0/0', '0/1', '1/1'], n_variants, p=[0.7, 0.25, 0.05]),
        'quality_score': np.random.uniform(20, 99, n_variants),
        'variant_type': np.random.choice(['SNP', 'INDEL'], n_variants, p=[0.9, 0.1])
    }
    
    genomic_df = pd.DataFrame(genomic_data)
    genomic_df.to_csv(data_dir / "genomic_variants.csv", index=False)
    print(f"Created genomic_variants.csv with {len(genomic_df)} records")
    
    # Create JSON metadata file
    metadata = {
        "datasets": {
            "patient_data": {
                "description": "Patient demographics and clinical outcomes",
                "file": "patient_data.csv",
                "primary_key": "patient_id",
                "record_count": len(patients_df),
                "data_types": {
                    "demographics": ["age", "gender"],
                    "clinical": ["diagnosis", "baseline_score", "followup_score", "improvement"],
                    "administrative": ["treatment_duration_days", "site"]
                }
            },
            "lab_results": {
                "description": "Laboratory test results",
                "file": "lab_results.csv",
                "foreign_key": "patient_id",
                "record_count": len(lab_df),
                "test_types": ["HbA1c", "Glucose", "Cholesterol", "BP_Systolic", "BP_Diastolic"]
            },
            "imaging_metadata": {
                "description": "Medical imaging scan metadata",
                "file": "imaging_metadata.csv",
                "foreign_key": "patient_id",
                "record_count": len(imaging_df),
                "scan_types": ["MRI", "CT", "PET"]
            },
            "genomic_variants": {
                "description": "Genomic variant data",
                "file": "genomic_variants.csv",
                "foreign_key": "sample_id",
                "record_count": len(genomic_df),
                "variant_types": ["SNP", "INDEL"]
            }
        },
        "created_date": pd.Timestamp.now().isoformat(),
        "total_patients": n_patients,
        "data_version": "1.0"
    }
    
    with open(data_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nDemo data created in {data_dir}")
    print("Files created:")
    for file in data_dir.glob("*"):
        print(f"  - {file.name}")
    
    return data_dir


def register_demo_catalogs():
    """Register demo datasets as data catalogs"""
    
    print("\nRegistering demo data catalogs...")
    
    # Initialize catalog manager
    catalog_manager = DataCatalogManager("./data")
    
    data_dir = Path("./data/demo")
    
    # Register each dataset
    catalogs = [
        {
            "name": "patient_demographics",
            "description": "Patient demographics and clinical outcomes data",
            "data_source": str(data_dir / "patient_data.csv"),
            "data_type": "csv",
            "access_level": "restricted"
        },
        {
            "name": "laboratory_results",
            "description": "Laboratory test results and biomarkers",
            "data_source": str(data_dir / "lab_results.csv"),
            "data_type": "csv",
            "access_level": "restricted"
        },
        {
            "name": "imaging_metadata",
            "description": "Medical imaging scan metadata and findings",
            "data_source": str(data_dir / "imaging_metadata.csv"),
            "data_type": "csv",
            "access_level": "private"
        },
        {
            "name": "genomic_variants",
            "description": "Genomic variant data for research",
            "data_source": str(data_dir / "genomic_variants.csv"),
            "data_type": "csv",
            "access_level": "private"
        }
    ]
    
    catalog_ids = []
    for catalog_info in catalogs:
        try:
            catalog_id = catalog_manager.create_catalog(**catalog_info)
            catalog_ids.append(catalog_id)
            print(f"Registered catalog '{catalog_info['name']}' with ID {catalog_id}")
        except Exception as e:
            print(f"Failed to register catalog '{catalog_info['name']}': {e}")
    
    print(f"\nRegistered {len(catalog_ids)} data catalogs")
    
    # List all catalogs
    all_catalogs = catalog_manager.list_catalogs()
    print(f"\nAll available catalogs ({len(all_catalogs)}):")
    for catalog in all_catalogs:
        print(f"  {catalog.id}: {catalog.name} ({catalog.access_level}) - {catalog.total_records} records")
    
    return catalog_ids


def create_sample_scripts():
    """Create sample analysis scripts"""
    
    scripts_dir = Path("./examples/scripts")
    scripts_dir.mkdir(parents=True, exist_ok=True)
    
    # Script 1: Basic statistics
    basic_stats_script = '''
"""
Basic statistical analysis of patient data
"""
import pandas as pd
import numpy as np
from scipy import stats

# Load patient data (this would be provided by the data provider in actual execution)
# For demo purposes, we'll simulate the data loading

# Simulated data loading
np.random.seed(42)
n = 200
data = {
    'age': np.random.normal(55, 15, n),
    'baseline_score': np.random.normal(50, 15, n),
    'followup_score': np.random.normal(55, 18, n),
    'diagnosis': np.random.choice(['Type1', 'Type2', 'Control'], n, p=[0.3, 0.4, 0.3])
}
df = pd.DataFrame(data)
df['improvement'] = df['followup_score'] - df['baseline_score']

# Perform analysis
results = {}

# Basic demographics
results['sample_size'] = len(df)
results['age_stats'] = {
    'mean': float(df['age'].mean()),
    'std': float(df['age'].std()),
    'median': float(df['age'].median()),
    'range': [float(df['age'].min()), float(df['age'].max())]
}

# Diagnosis distribution
diagnosis_counts = df['diagnosis'].value_counts()
results['diagnosis_distribution'] = diagnosis_counts.to_dict()

# Improvement analysis
results['improvement_stats'] = {
    'mean': float(df['improvement'].mean()),
    'std': float(df['improvement'].std()),
    'median': float(df['improvement'].median())
}

# Statistical test for improvement
t_stat, p_value = stats.ttest_1samp(df['improvement'], 0)
results['improvement_test'] = {
    't_statistic': float(t_stat),
    'p_value': float(p_value),
    'significant': p_value < 0.05
}

# Group comparisons
group_stats = df.groupby('diagnosis')['improvement'].agg(['count', 'mean', 'std']).round(3)
results['group_comparisons'] = group_stats.to_dict('index')

# ANOVA test
groups = [df[df['diagnosis'] == diag]['improvement'] for diag in df['diagnosis'].unique()]
f_stat, p_value = stats.f_oneway(*groups)
results['anova_test'] = {
    'f_statistic': float(f_stat),
    'p_value': float(p_value),
    'significant': p_value < 0.05
}

# Set result for framework to capture
result = results
'''
    
    with open(scripts_dir / "basic_statistics.py", 'w') as f:
        f.write(basic_stats_script)
    
    # Script 2: Correlation analysis
    correlation_script = '''
"""
Correlation analysis between variables
"""
import pandas as pd
import numpy as np
from scipy import stats

# Simulated data loading
np.random.seed(123)
n = 150

# Create correlated data
age = np.random.normal(55, 15, n)
baseline = np.random.normal(50, 15, n)
# Add some correlation between age and baseline
baseline += age * 0.1 + np.random.normal(0, 5, n)
# Followup correlated with baseline
followup = baseline + np.random.normal(5, 10, n)

df = pd.DataFrame({
    'age': age,
    'baseline_score': baseline,
    'followup_score': followup,
    'improvement': followup - baseline
})

# Correlation analysis
results = {}

# Correlation matrix
corr_matrix = df.corr()
results['correlation_matrix'] = corr_matrix.round(3).to_dict()

# Specific correlations with significance tests
correlations = {}
variables = ['age', 'baseline_score', 'followup_score', 'improvement']

for i, var1 in enumerate(variables):
    for var2 in variables[i+1:]:
        r, p = stats.pearsonr(df[var1], df[var2])
        correlations[f'{var1}_vs_{var2}'] = {
            'correlation': float(r),
            'p_value': float(p),
            'significant': p < 0.05
        }

results['pairwise_correlations'] = correlations

# Linear regression: predict improvement from baseline
from scipy.stats import linregress
slope, intercept, r_value, p_value, std_err = linregress(df['baseline_score'], df['improvement'])

results['regression_analysis'] = {
    'predictor': 'baseline_score',
    'outcome': 'improvement',
    'slope': float(slope),
    'intercept': float(intercept),
    'r_squared': float(r_value**2),
    'p_value': float(p_value),
    'std_error': float(std_err)
}

result = results
'''
    
    with open(scripts_dir / "correlation_analysis.py", 'w') as f:
        f.write(correlation_script)
    
    # Script 3: Survival analysis (simplified)
    survival_script = '''
"""
Simplified survival/time-to-event analysis
"""
import pandas as pd
import numpy as np
from scipy import stats

# Simulated time-to-event data
np.random.seed(456)
n = 100

# Simulate treatment groups
treatment = np.random.choice(['Treatment', 'Control'], n, p=[0.5, 0.5])

# Simulate time to event (days)
# Treatment group has longer survival times
time_to_event = np.where(
    treatment == 'Treatment',
    np.random.exponential(200, n//2),  # Longer survival
    np.random.exponential(150, n//2)   # Shorter survival
)

# Some patients are censored (didn't experience event during study)
censored = np.random.choice([True, False], n, p=[0.3, 0.7])
observed_time = np.where(censored, 
                        np.random.uniform(50, 365, n),  # Censoring time
                        time_to_event)

df = pd.DataFrame({
    'patient_id': [f'P{i:03d}' for i in range(n)],
    'treatment': treatment,
    'time': observed_time,
    'event': ~censored  # True if event occurred
})

# Analysis
results = {}

# Basic statistics
results['sample_size'] = len(df)
results['events_observed'] = int(df['event'].sum())
results['censoring_rate'] = float((~df['event']).mean())

# Group statistics
group_stats = df.groupby('treatment').agg({
    'time': ['count', 'mean', 'median', 'std'],
    'event': 'sum'
}).round(2)

results['group_statistics'] = {}
for treatment_group in df['treatment'].unique():
    group_data = df[df['treatment'] == treatment_group]
    results['group_statistics'][treatment_group] = {
        'n': len(group_data),
        'events': int(group_data['event'].sum()),
        'mean_time': float(group_data['time'].mean()),
        'median_time': float(group_data['time'].median())
    }

# Compare survival times between groups (using events only)
treatment_times = df[(df['treatment'] == 'Treatment') & df['event']]['time']
control_times = df[(df['treatment'] == 'Control') & df['event']]['time']

if len(treatment_times) > 0 and len(control_times) > 0:
    t_stat, p_value = stats.ttest_ind(treatment_times, control_times)
    results['survival_comparison'] = {
        'test': 't-test',
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'significant': p_value < 0.05,
        'treatment_mean': float(treatment_times.mean()),
        'control_mean': float(control_times.mean())
    }

result = results
'''
    
    with open(scripts_dir / "survival_analysis.py", 'w') as f:
        f.write(survival_script)
    
    print(f"\nCreated sample scripts in {scripts_dir}")
    print("Scripts created:")
    for script in scripts_dir.glob("*.py"):
        print(f"  - {script.name}")


if __name__ == "__main__":
    print("Setting up demo data for distributed framework...")
    
    # Create demo datasets
    data_dir = create_demo_datasets()
    
    # Register as catalogs
    catalog_ids = register_demo_catalogs()
    
    # Create sample scripts
    create_sample_scripts()
    
    print("\n" + "="*50)
    print("Demo setup complete!")
    print("="*50)
    print(f"Data location: {data_dir}")
    print(f"Registered {len(catalog_ids)} data catalogs")
    print("\nNext steps:")
    print("1. Start the distributed node server: python -m distributed_node.main")
    print("2. Run example scripts: python examples/basic_usage.py")
    print("3. Use the client SDK to interact with the node")