#!/usr/bin/env python3
"""
Simple test of real script execution
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client_sdk import DistributedClient, JobSubmission


async def test_real_execution():
    """Test real script execution"""
    
    print("🧪 Testing REAL Script Execution")
    print("=" * 50)
    
    async with DistributedClient("http://localhost:8000") as client:
        await client.authenticate("demo", "demo")
        print("✅ Authenticated")
        
        # Simple real analysis script
        real_script = """
import pandas as pd
import os
import json
from datetime import datetime

print("🔍 REAL EXECUTION: Starting analysis...")

# Load actual data
data_root = os.environ.get('DATA_ROOT', './data')
subjects_path = os.path.join(data_root, 'catalogs', 'clinical_trial_data', 'subjects.csv')

print(f"📂 Loading data from: {subjects_path}")

if os.path.exists(subjects_path):
    df = pd.read_csv(subjects_path)
    print(f"📊 Loaded {len(df)} subjects")
    
    # Real analysis
    result = {
        "analysis_type": "real_data_analysis",
        "timestamp": datetime.now().isoformat(),
        "sample_size": len(df),
        "columns": list(df.columns),
        "age_mean": float(df['age'].mean()) if 'age' in df.columns else None,
        "sex_counts": df['sex'].value_counts().to_dict() if 'sex' in df.columns else None,
        "execution_mode": "REAL_PROCESSING"
    }
    
    print(f"✅ Analysis complete: {result['sample_size']} subjects processed")
    
    # Save results
    output_file = os.environ.get('OUTPUT_FILE', 'output.json')
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
else:
    print(f"❌ Data file not found: {subjects_path}")
    result = {"error": "Data file not found"}
    
    output_file = os.environ.get('OUTPUT_FILE', 'output.json')
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)

print("🏁 Script execution complete")
"""
        
        job = JobSubmission(
            target_node_id="node-1",
            data_catalog_name="clinical_trial_data",
            script_type="python",
            script_content=real_script,
            parameters={"test": "real_execution"}
        )
        
        print("📤 Submitting job for REAL execution...")
        job_id = await client.submit_job(job)
        print(f"✅ Job submitted: {job_id}")
        
        print("⏳ Waiting for execution...")
        result = await client.wait_for_job(job_id, timeout=60)
        
        print(f"\n🎉 REAL EXECUTION RESULTS:")
        print(f"Status: {result.status}")
        print(f"Execution time: {result.execution_time:.2f}s")
        print(f"Records processed: {result.records_processed}")
        
        if result.result_data:
            print("\n📊 Analysis Results:")
            import json
            print(json.dumps(result.result_data, indent=2))
        
        if result.error_message:
            print(f"\n❌ Error: {result.error_message}")


if __name__ == "__main__":
    asyncio.run(test_real_execution())
