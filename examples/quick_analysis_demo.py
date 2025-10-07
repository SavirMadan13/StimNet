#!/usr/bin/env python3
"""
Demo script showing how to use the remote client for data analysis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from remote_client import RemoteDataClient
import json

def main():
    # Your Cloudflare URL
    REMOTE_URL = "https://julian-robin-aaron-rss.trycloudflare.com"
    
    print("🚀 Remote Data Analysis Demo")
    print("=" * 50)
    
    # Create client
    client = RemoteDataClient(REMOTE_URL)
    
    # Check server health
    print("\n1. 🏥 Checking server health...")
    health = client.health_check()
    
    if not health:
        print("❌ Server is not accessible. Make sure it's running!")
        return
    
    # Demo 1: Quick JSON analysis
    print("\n2. 📊 Quick JSON Data Analysis")
    print("-" * 30)
    
    sample_data = [
        {"name": "Alice", "age": 25, "score": 85.5, "department": "Engineering"},
        {"name": "Bob", "age": 30, "score": 92.1, "department": "Marketing"},
        {"name": "Charlie", "age": 28, "score": 78.9, "department": "Engineering"},
        {"name": "Diana", "age": 35, "score": 88.7, "department": "Sales"},
        {"name": "Eve", "age": 22, "score": 91.3, "department": "Marketing"}
    ]
    
    quick_script = """
# Quick analysis of employee data
print("Analyzing employee data...")

# Calculate basic statistics
ages = [person['age'] for person in data]
scores = [person['score'] for person in data]

save_result('total_employees', len(data))
save_result('average_age', sum(ages) / len(ages))
save_result('average_score', sum(scores) / len(scores))
save_result('age_range', {'min': min(ages), 'max': max(ages)})
save_result('score_range', {'min': min(scores), 'max': max(scores)})

# Department breakdown
departments = {}
for person in data:
    dept = person['department']
    if dept not in departments:
        departments[dept] = {'count': 0, 'total_score': 0}
    departments[dept]['count'] += 1
    departments[dept]['total_score'] += person['score']

# Calculate average scores by department
for dept in departments:
    departments[dept]['average_score'] = departments[dept]['total_score'] / departments[dept]['count']

save_result('department_breakdown', departments)
"""
    
    result = client.submit_json_data(sample_data, quick_script)
    if result:
        print("✅ Quick analysis results:")
        print(json.dumps(result['results'], indent=2))
    
    # Demo 2: Template analysis
    print("\n3. 🧪 Template Analysis")
    print("-" * 25)
    
    # Get available templates
    templates = client.get_analysis_templates()
    if templates:
        print("Available templates:")
        for name in templates['templates'].keys():
            print(f"  - {name}")
        
        # Run descriptive stats template
        print("\nRunning descriptive statistics template...")
        template_result = client.run_template_analysis(
            "descriptive_stats", 
            sample_data
        )
        if template_result:
            print("✅ Template analysis results:")
            print(json.dumps(template_result['results'], indent=2))
    
    # Demo 3: File upload analysis
    print("\n4. 📁 File Upload Analysis")
    print("-" * 28)
    
    # Check if sample files exist
    csv_file = "examples/sample_data.csv"
    json_file = "examples/sample_data.json"
    script_file = "examples/demo_analysis_script.py"
    
    if os.path.exists(csv_file) and os.path.exists(script_file):
        print(f"Uploading files: {csv_file}, {json_file}")
        
        # Read the analysis script
        with open(script_file, 'r') as f:
            analysis_script = f.read()
        
        # Submit files for analysis
        job_id = client.submit_files_for_analysis(
            [csv_file, json_file],
            analysis_script,
            parameters={
                "analysis_type": "summary",
                "test_column": "score",
                "group_column": "category"
            }
        )
        
        if job_id:
            print(f"📋 Job submitted: {job_id}")
            print("⏳ Waiting for results...")
            
            # Wait for results
            results = client.wait_for_results(job_id, timeout=60)
            if results:
                print("✅ File analysis results:")
                print(json.dumps(results['results'], indent=2))
            else:
                print("❌ Failed to get results or timed out")
    else:
        print(f"❌ Sample files not found. Expected: {csv_file}, {script_file}")
    
    print("\n🎉 Demo completed!")
    print("\nNext steps:")
    print("1. Try the command-line interface:")
    print(f"   python remote_client.py --url {REMOTE_URL} health")
    print("2. Submit your own data files:")
    print(f"   python remote_client.py --url {REMOTE_URL} submit data.csv --script analysis.py --wait")
    print("3. Use templates for common analyses:")
    print(f"   python remote_client.py --url {REMOTE_URL} template --name descriptive_stats --data data.csv")

if __name__ == "__main__":
    main()