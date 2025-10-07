#!/usr/bin/env python3
"""
Simple script execution example
"""
import asyncio
import sys
import os

# Add the parent directory to the path so we can import the client SDK
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client_sdk import DistributedClient


async def simple_python_example():
    """Simple Python script execution example"""
    
    node_url = "http://localhost:8000"
    
    async with DistributedClient(node_url, verify_ssl=False) as client:
        # Authenticate
        await client.authenticate("demo", "demo")
        
        # Simple Python script
        script = """
print("Hello from remote Python execution!")

# Use parameters
name = parameters.get('name', 'World')
count = parameters.get('count', 1)

for i in range(count):
    print(f"Iteration {i+1}: Hello, {name}!")

# Save results
save_result('greeting', f'Hello, {name}!')
save_result('iterations', count)
save_result('message', 'Script executed successfully')
"""
        
        # Execute script
        job_id = await client.execute_script(
            script,
            script_type="python",
            parameters={"name": "Remote Execution", "count": 3}
        )
        
        print(f"Job submitted: {job_id}")
        
        # Wait for results
        result = await client.wait_for_job(job_id)
        
        print(f"Status: {result.status}")
        if result.result_data:
            print("Results:", result.result_data)


async def quick_data_analysis():
    """Quick data analysis without files"""
    
    node_url = "http://localhost:8000"
    
    async with DistributedClient(node_url, verify_ssl=False) as client:
        # Authenticate
        await client.authenticate("demo", "demo")
        
        # Sample data
        data = [
            {"name": "Alice", "score": 85},
            {"name": "Bob", "score": 92},
            {"name": "Charlie", "score": 78},
            {"name": "Diana", "score": 96}
        ]
        
        # Analysis script
        script = """
# Analyze the data
df = pd.DataFrame(data)
avg_score = df['score'].mean()
max_score = df['score'].max()
min_score = df['score'].min()

save_result('average_score', float(avg_score))
save_result('max_score', int(max_score))
save_result('min_score', int(min_score))
save_result('total_students', len(df))

print(f"Analyzed {len(df)} students")
print(f"Average score: {avg_score:.1f}")
"""
        
        # Quick analysis
        result = await client.quick_analysis(data, script)
        
        print("Quick Analysis Results:")
        print(f"Status: {result['status']}")
        if result.get('results'):
            for key, value in result['results'].items():
                print(f"  {key}: {value}")


if __name__ == "__main__":
    print("Simple Script Execution Examples")
    print("=" * 40)
    
    print("\n1. Python Script Execution:")
    asyncio.run(simple_python_example())
    
    print("\n2. Quick Data Analysis:")
    asyncio.run(quick_data_analysis())
    
    print("\n✅ Examples completed!")