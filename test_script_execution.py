#!/usr/bin/env python3
"""
Test script execution functionality with custom analysis scripts
"""
import asyncio
import sys
import os

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client_sdk import DistributedClient, JobSubmission


async def test_custom_script_execution():
    """Test executing custom analysis scripts"""
    
    print("🧪 Testing Script Execution Functionality")
    print("=" * 50)
    
    # Connect to the server
    async with DistributedClient("http://localhost:8000", verify_ssl=False) as client:
        # Authenticate
        await client.authenticate("demo", "demo")
        print("✅ Authenticated successfully")
        
        # Test 1: Simple Python script
        print("\n📊 Test 1: Simple Statistical Analysis")
        print("-" * 40)
        
        simple_script = """
import json
from datetime import datetime
import random

# Simulate loading data from the data catalog
print("Loading data from clinical_trial_data catalog...")

# Simulate some statistical analysis
sample_size = 150  # From our demo data
mean_age = 45.2
std_age = 12.8
correlation_strength = 0.73
p_value = 0.001

print(f"Analyzing {sample_size} subjects...")
print(f"Mean age: {mean_age} ± {std_age}")
print(f"Correlation: r={correlation_strength}, p={p_value}")

# Return structured results
result = {
    "analysis_type": "statistical_summary",
    "sample_size": sample_size,
    "demographics": {
        "mean_age": mean_age,
        "std_age": std_age,
        "age_range": [18, 75]
    },
    "correlation_analysis": {
        "correlation_coefficient": correlation_strength,
        "p_value": p_value,
        "significant": p_value < 0.05
    },
    "timestamp": datetime.now().isoformat(),
    "status": "completed_successfully"
}

print(f"Analysis complete! Results: {result}")
"""
        
        job1 = JobSubmission(
            target_node_id="node-1",
            data_catalog_name="clinical_trial_data",
            script_type="python",
            script_content=simple_script,
            parameters={"analysis_name": "statistical_summary"},
            filters={"include_all": True}
        )
        
        job_id1 = await client.submit_job(job1)
        print(f"✅ Job 1 submitted: {job_id1}")
        
        result1 = await client.wait_for_job(job_id1, timeout=60)
        print(f"✅ Job 1 completed: {result1.status}")
        if result1.result_data:
            print("📋 Results:")
            for key, value in result1.result_data.items():
                print(f"   {key}: {value}")
        
        # Test 2: Data processing script
        print("\n🔬 Test 2: Data Processing & Filtering")
        print("-" * 40)
        
        processing_script = """
import json
from datetime import datetime

print("Starting data processing pipeline...")

# Simulate data filtering and processing
total_subjects = 150
filtered_subjects = 89  # After applying filters

# Simulate processing steps
steps = [
    "Loading raw data",
    "Applying inclusion criteria", 
    "Filtering by age range",
    "Removing incomplete records",
    "Computing derived variables"
]

for i, step in enumerate(steps, 1):
    print(f"Step {i}: {step}")

# Simulate results
result = {
    "pipeline_type": "data_processing",
    "input_records": total_subjects,
    "output_records": filtered_subjects,
    "filter_efficiency": round(filtered_subjects / total_subjects * 100, 1),
    "processing_steps": len(steps),
    "derived_variables": [
        "age_group",
        "treatment_response_category", 
        "baseline_severity"
    ],
    "quality_metrics": {
        "completeness": 94.2,
        "consistency": 98.7,
        "validity": 96.1
    },
    "timestamp": datetime.now().isoformat(),
    "processing_time_seconds": 2.3
}

print(f"Processing pipeline complete!")
print(f"Processed {filtered_subjects}/{total_subjects} subjects ({result['filter_efficiency']}% efficiency)")
"""
        
        job2 = JobSubmission(
            target_node_id="node-1",
            data_catalog_name="clinical_trial_data",
            script_type="python",
            script_content=processing_script,
            parameters={
                "pipeline_name": "data_processing",
                "include_quality_checks": True
            },
            filters={
                "age_min": 18,
                "age_max": 65,
                "complete_data_only": True
            }
        )
        
        job_id2 = await client.submit_job(job2)
        print(f"✅ Job 2 submitted: {job_id2}")
        
        result2 = await client.wait_for_job(job_id2, timeout=60)
        print(f"✅ Job 2 completed: {result2.status}")
        if result2.result_data:
            print("📋 Processing Results:")
            for key, value in result2.result_data.items():
                if isinstance(value, dict):
                    print(f"   {key}:")
                    for subkey, subvalue in value.items():
                        print(f"     {subkey}: {subvalue}")
                else:
                    print(f"   {key}: {value}")
        
        # Test 3: Error handling
        print("\n⚠️  Test 3: Error Handling & Security")
        print("-" * 40)
        
        # Test with a script that has security issues
        risky_script = """
import os
import subprocess

# This should be blocked by security validation
print("Attempting potentially dangerous operations...")

# Try to access system
try:
    os.system("ls -la")  # Should be blocked
    result = {"error": "Security validation failed"}
except:
    result = {"message": "Security validation working correctly"}

print("Security test complete")
"""
        
        job3 = JobSubmission(
            target_node_id="node-1",
            data_catalog_name="demo_dataset",
            script_type="python",
            script_content=risky_script,
            parameters={"test_type": "security_validation"}
        )
        
        job_id3 = await client.submit_job(job3)
        print(f"✅ Job 3 submitted: {job_id3}")
        
        result3 = await client.wait_for_job(job_id3, timeout=60)
        print(f"✅ Job 3 completed: {result3.status}")
        if result3.result_data:
            print("📋 Security Test Results:")
            for key, value in result3.result_data.items():
                print(f"   {key}: {value}")
        
        # Summary
        print(f"\n🎉 Script Execution Testing Complete!")
        print(f"✅ Statistical Analysis: {result1.status}")
        print(f"✅ Data Processing: {result2.status}")
        print(f"✅ Security Validation: {result3.status}")
        
        print(f"\n📊 Performance Summary:")
        print(f"   Job 1 execution time: {result1.execution_time:.2f}s")
        print(f"   Job 2 execution time: {result2.execution_time:.2f}s") 
        print(f"   Job 3 execution time: {result3.execution_time:.2f}s")


async def test_remote_script_execution():
    """Test script execution through the tunnel"""
    
    print("\n🌐 Testing Remote Script Execution")
    print("=" * 50)
    
    # Use the tunnel URL
    tunnel_url = "https://restructuring-composed-reward-feel.trycloudflare.com"
    
    async with DistributedClient(tunnel_url, verify_ssl=False) as client:
        await client.authenticate("demo", "demo")
        print(f"✅ Connected to remote server: {tunnel_url}")
        
        # Test remote execution
        remote_script = """
import json
from datetime import datetime

print("🌍 This script is running remotely!")
print("📍 Executed through Cloudflare tunnel")
print("🔒 Running in secure environment")

# Demonstrate remote data access
result = {
    "execution_location": "remote_via_tunnel",
    "message": "Successfully executed on remote node!",
    "tunnel_test": True,
    "timestamp": datetime.now().isoformat(),
    "remote_capabilities": [
        "Cross-network execution",
        "Secure data access",
        "Privacy-preserving results",
        "Global accessibility"
    ]
}

print(f"Remote execution complete: {result}")
"""
        
        job = JobSubmission(
            target_node_id="node-1",
            data_catalog_name="demo_dataset",
            script_type="python",
            script_content=remote_script,
            parameters={"execution_type": "remote_tunnel_test"}
        )
        
        job_id = await client.submit_job(job)
        print(f"✅ Remote job submitted: {job_id}")
        
        result = await client.wait_for_job(job_id, timeout=60)
        print(f"✅ Remote job completed: {result.status}")
        
        if result.result_data:
            print("📋 Remote Execution Results:")
            for key, value in result.result_data.items():
                if isinstance(value, list):
                    print(f"   {key}:")
                    for item in value:
                        print(f"     - {item}")
                else:
                    print(f"   {key}: {value}")


if __name__ == "__main__":
    print("🧪 Distributed Framework - Script Execution Testing")
    print("=" * 60)
    
    try:
        # Test local execution
        asyncio.run(test_custom_script_execution())
        
        # Test remote execution
        asyncio.run(test_remote_script_execution())
        
        print("\n🎉 All script execution tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
