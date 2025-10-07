"""
Basic usage examples for the distributed framework
"""
import asyncio
import pandas as pd
from client_sdk import DistributedClient, ScriptType


async def basic_client_example():
    """Basic example of using the distributed client"""
    
    # Create client
    client = DistributedClient()
    
    # Add a node
    client.add_node("node1", "http://localhost:8000")
    
    # Authenticate (in production, use proper credentials)
    success = client.authenticate("node1", "demo_user", "demo_password")
    if not success:
        print("Authentication failed")
        return
    
    # Discover node capabilities
    discovery = await client.discover_node("node1")
    print(f"Found {len(discovery.data_catalogs)} data catalogs")
    
    for catalog in discovery.data_catalogs:
        print(f"- {catalog.name}: {catalog.description} ({catalog.total_records} records)")
    
    # Check node health
    health = await client.get_health_status("node1")
    print(f"Node health: {health.status}, uptime: {health.uptime:.1f}s")
    
    # Submit a simple Python job
    if discovery.data_catalogs:
        catalog_name = discovery.data_catalogs[0].name
        
        script = """
import pandas as pd
import numpy as np

# This script will have access to the data through the data provider
# For this example, we'll create some mock analysis

result = {
    "message": "Analysis completed successfully",
    "analysis_type": "basic_statistics",
    "timestamp": pd.Timestamp.now().isoformat(),
    "sample_data": {
        "mean_value": np.random.normal(10, 2),
        "std_value": np.random.normal(3, 0.5),
        "count": np.random.randint(50, 200)
    }
}
"""
        
        print(f"Submitting job to analyze catalog: {catalog_name}")
        job_id = await client.submit_job(
            node_id="node1",
            data_catalog_name=catalog_name,
            script_type=ScriptType.PYTHON,
            script_content=script,
            parameters={"analysis_type": "basic"}
        )
        
        print(f"Job submitted with ID: {job_id}")
        
        # Wait for completion
        print("Waiting for job completion...")
        result = await client.wait_for_job_completion("node1", job_id, timeout=300)
        
        print(f"Job completed with status: {result.status}")
        if result.result_data:
            print("Results:")
            for key, value in result.result_data.items():
                print(f"  {key}: {value}")


async def data_analysis_example():
    """Example of running data analysis"""
    
    client = DistributedClient()
    client.add_node("node1", "http://localhost:8000")
    
    # Authenticate
    if not client.authenticate("node1", "demo_user", "demo_password"):
        print("Authentication failed")
        return
    
    # Advanced Python analysis script
    analysis_script = """
import pandas as pd
import numpy as np
from scipy import stats
import json

# Load data using the data provider (this would be injected in real execution)
# For demo purposes, we'll simulate loading data

# Simulate loading a dataset
np.random.seed(42)
n_samples = 150
data = {
    'age': np.random.normal(45, 15, n_samples),
    'treatment_group': np.random.choice(['A', 'B', 'control'], n_samples),
    'outcome_score': np.random.normal(75, 20, n_samples)
}

df = pd.DataFrame(data)

# Add treatment effect
treatment_effect = {'A': 10, 'B': 5, 'control': 0}
for group, effect in treatment_effect.items():
    mask = df['treatment_group'] == group
    df.loc[mask, 'outcome_score'] += effect + np.random.normal(0, 2, mask.sum())

# Perform analysis
results = {}

# Basic statistics
results['sample_size'] = len(df)
results['age_stats'] = {
    'mean': float(df['age'].mean()),
    'std': float(df['age'].std()),
    'median': float(df['age'].median())
}

# Treatment group analysis
group_stats = df.groupby('treatment_group')['outcome_score'].agg(['count', 'mean', 'std']).round(3)
results['treatment_groups'] = group_stats.to_dict('index')

# Statistical test
groups = [df[df['treatment_group'] == group]['outcome_score'] for group in ['A', 'B', 'control']]
f_stat, p_value = stats.f_oneway(*groups)

results['anova_test'] = {
    'f_statistic': float(f_stat),
    'p_value': float(p_value),
    'significant': p_value < 0.05
}

# Effect sizes
control_mean = df[df['treatment_group'] == 'control']['outcome_score'].mean()
results['effect_sizes'] = {}
for group in ['A', 'B']:
    group_mean = df[df['treatment_group'] == group]['outcome_score'].mean()
    effect_size = (group_mean - control_mean) / df['outcome_score'].std()
    results['effect_sizes'][group] = float(effect_size)

# Set the result variable that will be captured
result = results
"""
    
    print("Running advanced data analysis...")
    
    # Submit the analysis job
    job_result = await client.run_python_script(
        node_id="node1",
        data_catalog_name="demo_catalog",  # This would need to exist
        script_content=analysis_script,
        parameters={
            "analysis_type": "treatment_comparison",
            "alpha": 0.05
        },
        wait_for_completion=True,
        timeout=300
    )
    
    print(f"Analysis completed with status: {job_result.status}")
    
    if job_result.status == "completed" and job_result.result_data:
        print("\nAnalysis Results:")
        print(f"Sample size: {job_result.result_data.get('sample_size')}")
        
        if 'treatment_groups' in job_result.result_data:
            print("\nTreatment Group Statistics:")
            for group, stats in job_result.result_data['treatment_groups'].items():
                print(f"  {group}: n={stats['count']}, mean={stats['mean']:.2f}, std={stats['std']:.2f}")
        
        if 'anova_test' in job_result.result_data:
            anova = job_result.result_data['anova_test']
            print(f"\nANOVA Test: F={anova['f_statistic']:.3f}, p={anova['p_value']:.3f}")
            print(f"Significant difference: {anova['significant']}")
        
        if 'effect_sizes' in job_result.result_data:
            print("\nEffect Sizes (Cohen's d):")
            for group, effect in job_result.result_data['effect_sizes'].items():
                print(f"  {group} vs control: {effect:.3f}")
    
    else:
        print(f"Analysis failed: {job_result.error_message}")


async def multi_node_example():
    """Example of working with multiple nodes"""
    
    client = DistributedClient()
    
    # Add multiple nodes
    nodes = {
        "hospital_a": "http://hospital-a.example.com:8000",
        "hospital_b": "http://hospital-b.example.com:8000",
        "research_center": "http://research.example.com:8000"
    }
    
    for node_id, endpoint in nodes.items():
        client.add_node(node_id, endpoint)
    
    # Discover all nodes
    print("Discovering all nodes...")
    discoveries = await client.discover_all_nodes()
    
    for node_id, discovery in discoveries.items():
        print(f"\nNode: {node_id}")
        print(f"  Data catalogs: {len(discovery.data_catalogs)}")
        for catalog in discovery.data_catalogs:
            print(f"    - {catalog.name} ({catalog.total_records} records)")
    
    # Run the same analysis on multiple nodes
    analysis_script = """
# Simple aggregation analysis
import pandas as pd
import numpy as np

# This would access the actual data in a real scenario
# For demo, simulate data
np.random.seed(42)
n = np.random.randint(100, 500)

result = {
    "site_summary": {
        "total_subjects": n,
        "mean_age": float(np.random.normal(50, 15)),
        "gender_distribution": {
            "male": int(n * 0.45),
            "female": int(n * 0.55)
        },
        "primary_outcome_mean": float(np.random.normal(75, 20))
    }
}
"""
    
    # Submit to all nodes (in practice, you'd authenticate first)
    job_ids = {}
    for node_id in nodes.keys():
        try:
            job_id = await client.submit_job(
                node_id=node_id,
                data_catalog_name="patient_data",
                script_type=ScriptType.PYTHON,
                script_content=analysis_script
            )
            job_ids[node_id] = job_id
            print(f"Submitted job to {node_id}: {job_id}")
        except Exception as e:
            print(f"Failed to submit to {node_id}: {e}")
    
    # Wait for all jobs to complete
    results = {}
    for node_id, job_id in job_ids.items():
        try:
            result = await client.wait_for_job_completion(node_id, job_id, timeout=300)
            results[node_id] = result
            print(f"Job completed on {node_id}: {result.status}")
        except Exception as e:
            print(f"Job failed on {node_id}: {e}")
    
    # Aggregate results
    print("\nAggregated Results:")
    total_subjects = 0
    age_sum = 0
    outcome_sum = 0
    
    for node_id, result in results.items():
        if result.status == "completed" and result.result_data:
            site_data = result.result_data.get("site_summary", {})
            subjects = site_data.get("total_subjects", 0)
            total_subjects += subjects
            age_sum += site_data.get("mean_age", 0) * subjects
            outcome_sum += site_data.get("primary_outcome_mean", 0) * subjects
    
    if total_subjects > 0:
        print(f"Total subjects across all sites: {total_subjects}")
        print(f"Weighted mean age: {age_sum / total_subjects:.1f}")
        print(f"Weighted mean outcome: {outcome_sum / total_subjects:.1f}")


if __name__ == "__main__":
    print("=== Basic Usage Example ===")
    asyncio.run(basic_client_example())
    
    print("\n=== Data Analysis Example ===")
    asyncio.run(data_analysis_example())
    
    print("\n=== Multi-Node Example ===")
    asyncio.run(multi_node_example())