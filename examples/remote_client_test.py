#!/usr/bin/env python3
"""
Test client for connecting to remote distributed nodes
"""
import asyncio
import sys
import os

# Add the parent directory to the path so we can import the client SDK
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client_sdk import DistributedClient, JobSubmission


async def test_remote_node(node_url):
    """Test connecting to a remote node"""
    
    print(f"Testing connection to remote node: {node_url}")
    
    try:
        async with DistributedClient(node_url, verify_ssl=False) as client:
            # Test health check
            health = await client.health_check()
            print(f"✅ Health check successful: {health['status']}")
            print(f"   Node ID: {health['node_id']}")
            print(f"   Institution: {health.get('institution', 'Unknown')}")
            
            # Test authentication
            print("\n🔐 Testing authentication...")
            auth_success = await client.authenticate("demo", "demo")
            if auth_success:
                print("✅ Authentication successful")
            else:
                print("❌ Authentication failed")
                return
            
            # Test discovery
            print("\n🔍 Discovering node capabilities...")
            node_info = await client.discover_node()
            print(f"✅ Found {len(node_info.data_catalogs)} data catalogs:")
            for catalog in node_info.data_catalogs:
                print(f"   - {catalog.name}: {catalog.total_records} records")
            
            # Test job submission
            if node_info.data_catalogs:
                print("\n📊 Testing job submission...")
                
                job = JobSubmission(
                    target_node_id="node-1",
                    data_catalog_name=node_info.data_catalogs[0].name,
                    script_type="python",
                    script_content="""
# Remote analysis test
import json
from datetime import datetime

result = {
    "remote_test": True,
    "timestamp": datetime.now().isoformat(),
    "message": "Successfully executed on remote node!",
    "sample_analysis": {
        "mean": 42.5,
        "std": 12.3,
        "n": 100
    }
}

print("Remote analysis completed successfully!")
""",
                    parameters={"test_type": "remote_connection"},
                    filters={"remote": True}
                )
                
                job_id = await client.submit_job(job)
                print(f"✅ Job submitted: {job_id}")
                
                # Wait for results
                print("⏳ Waiting for job completion...")
                result = await client.wait_for_job(job_id, timeout=60)
                
                print(f"✅ Job completed with status: {result.status}")
                if result.result_data:
                    print("📋 Results:")
                    for key, value in result.result_data.items():
                        print(f"   {key}: {value}")
                
                print(f"\n📈 Performance:")
                print(f"   Execution time: {result.execution_time:.2f}s")
                if result.records_processed:
                    print(f"   Records processed: {result.records_processed}")
            
            print(f"\n🎉 All tests passed for {node_url}!")
            
    except Exception as e:
        print(f"❌ Error testing {node_url}: {e}")
        import traceback
        traceback.print_exc()


async def test_multiple_nodes():
    """Test connecting to multiple nodes"""
    
    # List of nodes to test (add your remote IPs here)
    nodes = [
        "http://localhost:8000",  # Local node
        "http://10.214.14.11:8000",  # Same machine via network IP
        # Add more nodes here as you set them up:
        # "http://192.168.1.100:8000",  # Another machine
        # "http://colleague-laptop.local:8000",  # Another colleague's machine
    ]
    
    print("🌐 Multi-Node Distributed Testing")
    print("=" * 50)
    
    for i, node_url in enumerate(nodes, 1):
        print(f"\n🖥️  Testing Node {i}: {node_url}")
        print("-" * 40)
        await test_remote_node(node_url)
        
        if i < len(nodes):
            print("\n" + "="*50)
    
    print(f"\n🏁 Testing complete! Tested {len(nodes)} nodes.")


if __name__ == "__main__":
    print("Distributed Framework - Multi-Device Testing")
    print("=" * 50)
    
    # You can test a specific node or multiple nodes
    import sys
    
    if len(sys.argv) > 1:
        # Test specific node from command line
        node_url = sys.argv[1]
        asyncio.run(test_remote_node(node_url))
    else:
        # Test all configured nodes
        asyncio.run(test_multiple_nodes())
