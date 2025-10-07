"""
Example correlation analysis script for the distributed framework
This script demonstrates how to write analysis code that works with the framework
"""
import pandas as pd
import numpy as np
from scipy import stats
import json
import os
from datetime import datetime


def load_data():
    """Load data from the data catalog"""
    # The framework provides access to data through the /data mount
    data_root = os.environ.get('DATA_ROOT', '/data')
    
    # Load subjects and outcomes data
    subjects_path = os.path.join(data_root, 'catalogs', 'clinical_trial_data', 'subjects.csv')
    outcomes_path = os.path.join(data_root, 'catalogs', 'clinical_trial_data', 'outcomes.csv')
    
    if not os.path.exists(subjects_path) or not os.path.exists(outcomes_path):
        raise FileNotFoundError("Required data files not found")
    
    subjects = pd.read_csv(subjects_path)
    outcomes = pd.read_csv(outcomes_path)
    
    # Merge the datasets
    data = subjects.merge(outcomes, on=['subject_id', 'visit'], how='inner')
    
    return data


def apply_filters(data, filters):
    """Apply any filters specified in the job parameters"""
    filtered_data = data.copy()
    
    for key, value in filters.items():
        if key in filtered_data.columns:
            if isinstance(value, list):
                filtered_data = filtered_data[filtered_data[key].isin(value)]
            else:
                filtered_data = filtered_data[filtered_data[key] == value]
    
    return filtered_data


def correlation_analysis(data, outcome_var='UPDRS_change', predictor_vars=None):
    """Perform correlation analysis"""
    
    if predictor_vars is None:
        # Default predictors
        predictor_vars = ['age', 'quality_of_life']
    
    # Filter to only include rows with valid data
    analysis_vars = [outcome_var] + predictor_vars
    clean_data = data.dropna(subset=analysis_vars)
    
    if len(clean_data) < 10:
        raise ValueError("Insufficient data for analysis after filtering")
    
    results = {
        'outcome_variable': outcome_var,
        'predictor_variables': predictor_vars,
        'sample_size': len(clean_data),
        'correlations': {},
        'p_values': {},
        'descriptive_stats': {}
    }
    
    # Calculate descriptive statistics
    for var in analysis_vars:
        results['descriptive_stats'][var] = {
            'mean': float(clean_data[var].mean()),
            'std': float(clean_data[var].std()),
            'min': float(clean_data[var].min()),
            'max': float(clean_data[var].max()),
            'n_valid': int(clean_data[var].count())
        }
    
    # Calculate correlations
    outcome_data = clean_data[outcome_var]
    
    for predictor in predictor_vars:
        predictor_data = clean_data[predictor]
        
        # Pearson correlation
        r, p = stats.pearsonr(outcome_data, predictor_data)
        
        results['correlations'][predictor] = {
            'pearson_r': float(r),
            'p_value': float(p),
            'significant': p < 0.05,
            'effect_size': 'small' if abs(r) < 0.3 else 'medium' if abs(r) < 0.5 else 'large'
        }
    
    return results


def main():
    """Main analysis function"""
    
    # Load job configuration if available
    config_file = os.environ.get('JOB_CONFIG', '/workspace/job_config.json')
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        parameters = config.get('parameters', {})
        filters = config.get('filters', {})
    else:
        # Default parameters for testing
        parameters = {
            'outcome_variable': 'UPDRS_change',
            'predictor_variables': ['age', 'quality_of_life']
        }
        filters = {}
    
    try:
        # Load and filter data
        print("Loading data...")
        data = load_data()
        print(f"Loaded {len(data)} records")
        
        if filters:
            print(f"Applying filters: {filters}")
            data = apply_filters(data, filters)
            print(f"After filtering: {len(data)} records")
        
        # Perform analysis
        print("Running correlation analysis...")
        results = correlation_analysis(
            data,
            outcome_var=parameters.get('outcome_variable', 'UPDRS_change'),
            predictor_vars=parameters.get('predictor_variables', ['age', 'quality_of_life'])
        )
        
        # Add metadata
        results['analysis_info'] = {
            'analysis_type': 'correlation_analysis',
            'timestamp': datetime.now().isoformat(),
            'filters_applied': filters,
            'parameters': parameters
        }
        
        # Privacy check - ensure minimum sample size
        min_sample_size = int(os.environ.get('MIN_COHORT_SIZE', '10'))
        if results['sample_size'] < min_sample_size:
            results = {
                'error': f'Sample size ({results["sample_size"]}) below minimum threshold ({min_sample_size})',
                'sample_size': results['sample_size'],
                'blocked': True
            }
        
        print(f"Analysis complete. Sample size: {results.get('sample_size', 'unknown')}")
        
        # Save results
        output_file = os.environ.get('OUTPUT_FILE', '/workspace/output.json')
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"Results saved to {output_file}")
        
        # Also set global result variable for framework
        globals()['result'] = results
        
    except Exception as e:
        error_result = {
            'error': str(e),
            'analysis_type': 'correlation_analysis',
            'timestamp': datetime.now().isoformat(),
            'failed': True
        }
        
        output_file = os.environ.get('OUTPUT_FILE', '/workspace/output.json')
        with open(output_file, 'w') as f:
            json.dump(error_result, f, indent=2)
        
        print(f"Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()
