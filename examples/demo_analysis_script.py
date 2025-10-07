# Demo Analysis Script for Remote Execution
# This script demonstrates how to analyze uploaded data files

import pandas as pd
import numpy as np
from scipy import stats
import json

# This script will have access to:
# - workspace: temporary directory path
# - data_files: list of uploaded file paths  
# - parameters: user-provided parameters
# - results: dictionary to store results

print("🔬 Starting remote data analysis...")
print(f"Workspace: {workspace}")
print(f"Data files: {data_files}")
print(f"Parameters: {parameters}")

try:
    # Process each uploaded file
    all_data = []
    
    for file_path in data_files:
        filename = os.path.basename(file_path)
        print(f"📁 Processing file: {filename}")
        
        if filename.endswith('.csv'):
            df = pd.read_csv(file_path)
            all_data.append(df)
            print(f"   Loaded CSV with {len(df)} rows, {len(df.columns)} columns")
        
        elif filename.endswith('.json'):
            with open(file_path, 'r') as f:
                json_data = json.load(f)
            if isinstance(json_data, list):
                df = pd.DataFrame(json_data)
                all_data.append(df)
                print(f"   Loaded JSON with {len(df)} records")
    
    if all_data:
        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True)
        print(f"📊 Combined dataset: {len(combined_df)} rows, {len(combined_df.columns)} columns")
        
        # Basic analysis
        numeric_cols = combined_df.select_dtypes(include=[np.number]).columns
        
        analysis_results = {
            "total_records": len(combined_df),
            "total_columns": len(combined_df.columns),
            "numeric_columns": len(numeric_cols),
            "column_names": list(combined_df.columns),
            "data_types": {col: str(dtype) for col, dtype in combined_df.dtypes.items()}
        }
        
        # Descriptive statistics for numeric columns
        if len(numeric_cols) > 0:
            desc_stats = {}
            for col in numeric_cols:
                desc_stats[col] = {
                    "mean": float(combined_df[col].mean()),
                    "median": float(combined_df[col].median()),
                    "std": float(combined_df[col].std()),
                    "min": float(combined_df[col].min()),
                    "max": float(combined_df[col].max()),
                    "count": int(combined_df[col].count()),
                    "null_count": int(combined_df[col].isnull().sum())
                }
            
            analysis_results["descriptive_statistics"] = desc_stats
        
        # Correlation analysis if multiple numeric columns
        if len(numeric_cols) >= 2:
            corr_matrix = combined_df[numeric_cols].corr()
            
            # Find highest correlations
            correlations = []
            for i in range(len(numeric_cols)):
                for j in range(i+1, len(numeric_cols)):
                    col1, col2 = numeric_cols[i], numeric_cols[j]
                    corr_value = corr_matrix.iloc[i, j]
                    correlations.append({
                        "variable1": col1,
                        "variable2": col2,
                        "correlation": float(corr_value)
                    })
            
            # Sort by absolute correlation
            correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
            analysis_results["top_correlations"] = correlations[:5]
        
        # Custom analysis based on parameters
        analysis_type = parameters.get("analysis_type", "basic")
        
        if analysis_type == "summary":
            # Generate summary report
            summary = {
                "dataset_overview": f"Dataset contains {len(combined_df)} records with {len(combined_df.columns)} variables",
                "data_quality": {
                    "complete_records": int(combined_df.dropna().shape[0]),
                    "missing_data_percentage": float((combined_df.isnull().sum().sum() / (len(combined_df) * len(combined_df.columns))) * 100)
                }
            }
            analysis_results["summary_report"] = summary
        
        elif analysis_type == "statistical_test":
            # Perform statistical tests if specified
            test_column = parameters.get("test_column")
            group_column = parameters.get("group_column")
            
            if test_column and group_column and test_column in combined_df.columns and group_column in combined_df.columns:
                groups = combined_df[group_column].unique()
                
                if len(groups) == 2:
                    # Two-sample t-test
                    group1_data = combined_df[combined_df[group_column] == groups[0]][test_column].dropna()
                    group2_data = combined_df[combined_df[group_column] == groups[1]][test_column].dropna()
                    
                    if len(group1_data) > 0 and len(group2_data) > 0:
                        t_stat, p_value = stats.ttest_ind(group1_data, group2_data)
                        
                        analysis_results["statistical_test"] = {
                            "test_type": "two_sample_t_test",
                            "test_column": test_column,
                            "group_column": group_column,
                            "groups": list(groups),
                            "group1_mean": float(group1_data.mean()),
                            "group2_mean": float(group2_data.mean()),
                            "t_statistic": float(t_stat),
                            "p_value": float(p_value),
                            "significant_at_0.05": p_value < 0.05
                        }
        
        # Store results
        results.update(analysis_results)
        
        print("✅ Analysis completed successfully!")
        print(f"📈 Generated {len(analysis_results)} result categories")
        
    else:
        results["error"] = "No valid data files found"
        print("❌ No valid data files to process")

except Exception as e:
    error_msg = f"Analysis failed: {str(e)}"
    results["error"] = error_msg
    print(f"❌ {error_msg}")
    import traceback
    traceback.print_exc()

print("🏁 Analysis script completed")