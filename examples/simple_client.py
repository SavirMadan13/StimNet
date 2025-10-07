#!/usr/bin/env python3
"""
Simple example of using the Distributed Client SDK
"""
import asyncio
import sys
import os

# Add the parent directory to the path so we can import the client SDK
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client_sdk import DistributedClient, JobSubmission


async def main():
    """Main example function"""
    
    # Connect to the local node
    node_url = "http://localhost:8000"
    
    print(f"Connecting to node: {node_url}")
    
    async with DistributedClient(node_url, verify_ssl=False) as client:
        try:
            # Check node health
            health = await client.health_check()
            print(f"Node health: {health['status']}")
            print(f"Node ID: {health['node_id']}")
            print(f"Active jobs: {health['active_jobs']}")
            
            # Authenticate (using demo credentials)
            print("\nAuthenticating...")
            auth_success = await client.authenticate("demo", "demo")
            if not auth_success:
                print("Authentication failed!")
                return
            print("Authentication successful!")
            
            # Discover available data
            print("\nDiscovering node capabilities...")
            node_info = await client.discover_node()
            
            print("Available data catalogs:")
            for catalog in node_info.data_catalogs:
                print(f"  - {catalog.name}: {catalog.description}")
                print(f"    Type: {catalog.data_type}, Records: {catalog.total_records}")
            
            if not node_info.data_catalogs:
                print("No data catalogs available. Please set up data catalogs first.")
                return
            
            # Submit a simple Python analysis
            print("\nSubmitting analysis job...")
            
            analysis_script = """
import json
import numpy as np
import pandas as pd
from datetime import datetime

# Simulate some analysis
print("Starting analysis...")

# Generate some mock results
np.random.seed(42)
sample_size = np.random.randint(50, 200)
correlation = np.random.uniform(0.3, 0.8)
p_value = np.random.uniform(0.001, 0.05)

result = {
    "analysis_type": "correlation_analysis",
    "sample_size": int(sample_size),
    "correlation_coefficient": float(correlation),
    "p_value": float(p_value),
    "significant": p_value < 0.05,
    "timestamp": datetime.now().isoformat(),
    "message": "Analysis completed successfully"
}

print(f"Analysis complete. Sample size: {sample_size}, r={correlation:.3f}, p={p_value:.3f}")
"""
            
            job = JobSubmission(
                target_node_id="node-1",  # Use the default node ID
                data_catalog_name=node_info.data_catalogs[0].name,  # Use first available catalog
                script_type="python",
                script_content=analysis_script,
                parameters={
                    "analysis_name": "demo_correlation",
                    "researcher": "demo_user"
                },
                filters={
                    "include_test_data": True
                }
            )
            
            job_id = await client.submit_job(job)
            print(f"Job submitted successfully! Job ID: {job_id}")
            
            # Monitor job progress
            print("\nMonitoring job progress...")
            result = await client.wait_for_job(job_id, timeout=300, poll_interval=2)
            
            print(f"\nJob completed with status: {result.status}")
            
            if result.status == "completed":
                print("Results:")
                if result.result_data:
                    for key, value in result.result_data.items():
                        print(f"  {key}: {value}")
                
                print(f"\nExecution details:")
                print(f"  Execution time: {result.execution_time:.2f} seconds")
                if result.memory_used_mb:
                    print(f"  Memory used: {result.memory_used_mb:.1f} MB")
                if result.records_processed:
                    print(f"  Records processed: {result.records_processed}")
            
            elif result.status == "failed":
                print(f"Job failed with error: {result.error_message}")
            
            elif result.status == "blocked":
                print("Job results blocked due to privacy constraints")
                if result.result_data:
                    print(f"Reason: {result.result_data.get('message', 'Unknown')}")
            
            # List recent jobs
            print("\nRecent jobs:")
            recent_jobs = await client.list_jobs(limit=5)
            for job in recent_jobs:
                print(f"  {job.job_id}: {job.status} ({job.script_type})")
        
        except Exception as e:
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("Distributed Data Access Framework - Client Example")
    print("=" * 50)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExample interrupted by user")
    except Exception as e:
        print(f"Example failed: {e}")
        sys.exit(1)
    
    print("\nExample completed successfully!")
