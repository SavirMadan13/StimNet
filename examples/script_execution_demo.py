#!/usr/bin/env python3
"""
Comprehensive demo of script execution capabilities
"""
import asyncio
import sys
import os
import json
import tempfile
from pathlib import Path

# Add the parent directory to the path so we can import the client SDK
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client_sdk import DistributedClient


async def demo_python_script_execution():
    """Demo executing Python scripts with data"""
    print("\n🐍 Python Script Execution Demo")
    print("=" * 50)
    
    # Simple Python script
    python_script = """
# Simple data analysis script
import numpy as np
import pandas as pd

print("🔬 Starting Python analysis...")

# Use provided parameters
analysis_name = parameters.get('analysis_name', 'demo')
sample_size = parameters.get('sample_size', 100)

print(f"Analysis: {analysis_name}")
print(f"Sample size: {sample_size}")

# Generate some sample data
np.random.seed(42)
data = np.random.normal(0, 1, sample_size)

# Perform analysis
mean_val = np.mean(data)
std_val = np.std(data)
median_val = np.median(data)

# Save results
save_result('mean', float(mean_val))
save_result('std', float(std_val))
save_result('median', float(median_val))
save_result('sample_size', sample_size)
save_result('analysis_complete', True)

print(f"✅ Analysis complete: mean={mean_val:.3f}, std={std_val:.3f}")
"""
    
    return {
        "script": python_script,
        "parameters": {
            "analysis_name": "statistical_summary",
            "sample_size": 150
        }
    }


async def demo_r_script_execution():
    """Demo executing R scripts"""
    print("\n📊 R Script Execution Demo")
    print("=" * 50)
    
    r_script = """
# R statistical analysis script
cat("🔬 Starting R analysis...\\n")

# Access parameters
analysis_name <- "correlation_test"
n_samples <- 200

cat("Analysis:", analysis_name, "\\n")
cat("Sample size:", n_samples, "\\n")

# Generate sample data
set.seed(42)
x <- rnorm(n_samples, mean = 5, sd = 2)
y <- 0.7 * x + rnorm(n_samples, mean = 0, sd = 1)

# Perform correlation analysis
cor_result <- cor.test(x, y)

# Save results
save_result("correlation", cor_result$estimate)
save_result("p_value", cor_result$p.value)
save_result("confidence_interval", cor_result$conf.int)
save_result("sample_size", n_samples)
save_result("significant", cor_result$p.value < 0.05)

cat("✅ R analysis complete: r =", cor_result$estimate, ", p =", cor_result$p.value, "\\n")
"""
    
    return {
        "script": r_script,
        "parameters": {
            "analysis_type": "correlation",
            "significance_level": 0.05
        }
    }


async def demo_shell_script_execution():
    """Demo executing shell scripts"""
    print("\n🐚 Shell Script Execution Demo")
    print("=" * 50)
    
    shell_script = """
# Shell script for system analysis
echo "🔧 Starting shell script analysis..."

# Create some sample files
echo "Creating sample data files..."
echo "sample,value,category" > data1.csv
echo "A,10,group1" >> data1.csv
echo "B,15,group2" >> data1.csv
echo "C,20,group1" >> data1.csv

echo "name,score" > data2.csv
echo "Alice,85" >> data2.csv
echo "Bob,92" >> data2.csv
echo "Charlie,78" >> data2.csv

# Count files and lines
file_count=$(ls *.csv | wc -l)
total_lines=$(cat *.csv | wc -l)

echo "📊 Analysis Results:"
echo "Files created: $file_count"
echo "Total lines: $total_lines"

# Create a summary report
cat > analysis_summary.txt << EOF
Shell Script Analysis Report
============================
Execution Date: $(date)
Files processed: $file_count
Total lines: $total_lines
Working directory: $(pwd)
Available files: $(ls -la)
EOF

echo "✅ Shell script analysis complete!"
cat analysis_summary.txt
"""
    
    return {
        "script": shell_script,
        "parameters": {
            "create_report": True,
            "include_timestamps": True
        }
    }


async def demo_nodejs_script_execution():
    """Demo executing Node.js scripts"""
    print("\n🟨 Node.js Script Execution Demo")
    print("=" * 50)
    
    nodejs_script = """
// Node.js data processing script
console.log("🚀 Starting Node.js analysis...");

// Access environment data
const analysisName = parameters.analysis_name || "data_processing";
const iterations = parameters.iterations || 1000;

console.log(`Analysis: ${analysisName}`);
console.log(`Iterations: ${iterations}`);

// Simulate data processing
const results = [];
let sum = 0;

for (let i = 0; i < iterations; i++) {
    const value = Math.random() * 100;
    results.push(value);
    sum += value;
}

const average = sum / iterations;
const max = Math.max(...results);
const min = Math.min(...results);

// Calculate standard deviation
const variance = results.reduce((acc, val) => acc + Math.pow(val - average, 2), 0) / iterations;
const stdDev = Math.sqrt(variance);

// Save results
saveResult("average", average);
saveResult("max", max);
saveResult("min", min);
saveResult("standard_deviation", stdDev);
saveResult("sample_count", iterations);
saveResult("processing_complete", true);

console.log(`✅ Node.js analysis complete: avg=${average.toFixed(3)}, std=${stdDev.toFixed(3)}`);
"""
    
    return {
        "script": nodejs_script,
        "parameters": {
            "analysis_name": "random_data_stats",
            "iterations": 5000
        }
    }


async def demo_data_file_processing():
    """Demo processing uploaded data files"""
    print("\n📁 Data File Processing Demo")
    print("=" * 50)
    
    # Create sample data files
    sample_data1 = [
        {"name": "Alice", "age": 25, "score": 85, "category": "A"},
        {"name": "Bob", "age": 30, "score": 92, "category": "B"},
        {"name": "Charlie", "age": 35, "score": 78, "category": "A"},
        {"name": "Diana", "age": 28, "score": 96, "category": "B"},
        {"name": "Eve", "age": 32, "score": 88, "category": "A"}
    ]
    
    sample_data2 = [
        {"product": "Widget A", "sales": 150, "region": "North"},
        {"product": "Widget B", "sales": 200, "region": "South"},
        {"product": "Widget C", "sales": 175, "region": "East"},
        {"product": "Widget A", "sales": 180, "region": "West"},
        {"product": "Widget B", "sales": 220, "region": "North"}
    ]
    
    # Create temporary files
    temp_dir = tempfile.mkdtemp()
    
    file1_path = os.path.join(temp_dir, "people_data.json")
    file2_path = os.path.join(temp_dir, "sales_data.json")
    
    with open(file1_path, "w") as f:
        json.dump(sample_data1, f, indent=2)
    
    with open(file2_path, "w") as f:
        json.dump(sample_data2, f, indent=2)
    
    # Analysis script that processes uploaded files
    analysis_script = """
import json
import pandas as pd
import numpy as np

print("📊 Processing uploaded data files...")

# Load and analyze people data
try:
    people_df = pd.DataFrame(load_file("people_data.json"))
    print(f"Loaded people data: {len(people_df)} records")
    
    # Analyze people data
    avg_age = people_df['age'].mean()
    avg_score = people_df['score'].mean()
    category_counts = people_df['category'].value_counts().to_dict()
    
    save_result("people_analysis", {
        "total_people": len(people_df),
        "average_age": float(avg_age),
        "average_score": float(avg_score),
        "category_distribution": category_counts
    })
    
except Exception as e:
    print(f"Error processing people data: {e}")

# Load and analyze sales data
try:
    sales_df = pd.DataFrame(load_file("sales_data.json"))
    print(f"Loaded sales data: {len(sales_df)} records")
    
    # Analyze sales data
    total_sales = sales_df['sales'].sum()
    avg_sales = sales_df['sales'].mean()
    sales_by_region = sales_df.groupby('region')['sales'].sum().to_dict()
    sales_by_product = sales_df.groupby('product')['sales'].sum().to_dict()
    
    save_result("sales_analysis", {
        "total_sales": int(total_sales),
        "average_sales": float(avg_sales),
        "sales_by_region": sales_by_region,
        "sales_by_product": sales_by_product
    })
    
except Exception as e:
    print(f"Error processing sales data: {e}")

# Cross-analysis
try:
    # Simulate some cross-analysis
    efficiency_score = (avg_score / 100) * (avg_sales / 200)
    
    save_result("cross_analysis", {
        "efficiency_score": float(efficiency_score),
        "data_quality": "high",
        "files_processed": 2
    })
    
    print("✅ Multi-file analysis complete!")
    
except Exception as e:
    print(f"Error in cross-analysis: {e}")
"""
    
    return {
        "script": analysis_script,
        "files": [file1_path, file2_path],
        "parameters": {
            "analysis_type": "multi_file_processing",
            "include_cross_analysis": True
        },
        "temp_dir": temp_dir
    }


async def demo_quick_analysis():
    """Demo quick analysis without file upload"""
    print("\n⚡ Quick Analysis Demo")
    print("=" * 50)
    
    # Sample data for quick analysis
    sample_data = [
        {"name": "Product A", "price": 29.99, "sales": 150, "rating": 4.2},
        {"name": "Product B", "price": 39.99, "sales": 200, "rating": 4.5},
        {"name": "Product C", "price": 19.99, "sales": 300, "rating": 3.8},
        {"name": "Product D", "price": 49.99, "sales": 100, "rating": 4.7},
        {"name": "Product E", "price": 24.99, "sales": 250, "rating": 4.1}
    ]
    
    analysis_script = """
# Quick analysis of product data
print("📈 Performing quick product analysis...")

# Convert to DataFrame
df = pd.DataFrame(data)
print(f"Analyzing {len(df)} products")

# Calculate metrics
avg_price = df['price'].mean()
avg_sales = df['sales'].mean()
avg_rating = df['rating'].mean()

# Find best performers
best_seller = df.loc[df['sales'].idxmax()]
highest_rated = df.loc[df['rating'].idxmax()]
most_expensive = df.loc[df['price'].idxmax()]

# Price-sales correlation
price_sales_corr = df['price'].corr(df['sales'])
rating_sales_corr = df['rating'].corr(df['sales'])

# Save comprehensive results
save_result("summary_stats", {
    "average_price": float(avg_price),
    "average_sales": float(avg_sales),
    "average_rating": float(avg_rating),
    "total_products": len(df)
})

save_result("best_performers", {
    "best_seller": best_seller.to_dict(),
    "highest_rated": highest_rated.to_dict(),
    "most_expensive": most_expensive.to_dict()
})

save_result("correlations", {
    "price_vs_sales": float(price_sales_corr),
    "rating_vs_sales": float(rating_sales_corr)
})

save_result("insights", {
    "price_sales_relationship": "negative" if price_sales_corr < 0 else "positive",
    "rating_impact": "high" if abs(rating_sales_corr) > 0.5 else "moderate"
})

print("✅ Quick analysis complete!")
"""
    
    return {
        "data": sample_data,
        "script": analysis_script,
        "parameters": {
            "analysis_type": "product_performance",
            "include_correlations": True
        }
    }


async def run_all_demos():
    """Run all script execution demos"""
    print("🚀 Distributed Script Execution Framework - Comprehensive Demo")
    print("=" * 70)
    
    node_url = "http://localhost:8000"
    print(f"Connecting to node: {node_url}")
    
    async with DistributedClient(node_url, verify_ssl=False) as client:
        try:
            # Check node health
            health = await client.health_check()
            print(f"✅ Node health: {health['status']}")
            
            # Authenticate
            print("\n🔐 Authenticating...")
            auth_success = await client.authenticate("demo", "demo")
            if not auth_success:
                print("❌ Authentication failed!")
                return
            print("✅ Authentication successful!")
            
            # Get analysis templates
            print("\n📋 Available Analysis Templates:")
            templates = await client.get_analysis_templates()
            for name, template in templates["templates"].items():
                print(f"  - {template['name']}: {template['description']}")
            
            demos = []
            
            # 1. Python Script Demo
            python_demo = await demo_python_script_execution()
            job_id = await client.execute_script(
                python_demo["script"],
                script_type="python",
                parameters=python_demo["parameters"],
                timeout=120
            )
            demos.append(("Python Analysis", job_id))
            print(f"✅ Python script submitted: {job_id}")
            
            # 2. R Script Demo
            r_demo = await demo_r_script_execution()
            job_id = await client.execute_script(
                r_demo["script"],
                script_type="r",
                parameters=r_demo["parameters"],
                timeout=120
            )
            demos.append(("R Analysis", job_id))
            print(f"✅ R script submitted: {job_id}")
            
            # 3. Shell Script Demo
            shell_demo = await demo_shell_script_execution()
            job_id = await client.execute_script(
                shell_demo["script"],
                script_type="shell",
                parameters=shell_demo["parameters"],
                timeout=60
            )
            demos.append(("Shell Analysis", job_id))
            print(f"✅ Shell script submitted: {job_id}")
            
            # 4. Node.js Script Demo
            nodejs_demo = await demo_nodejs_script_execution()
            job_id = await client.execute_script(
                nodejs_demo["script"],
                script_type="nodejs",
                parameters=nodejs_demo["parameters"],
                timeout=120
            )
            demos.append(("Node.js Analysis", job_id))
            print(f"✅ Node.js script submitted: {job_id}")
            
            # 5. Data File Processing Demo
            file_demo = await demo_data_file_processing()
            job_id = await client.submit_data_with_script(
                file_demo["script"],
                file_demo["files"],
                parameters=file_demo["parameters"]
            )
            demos.append(("File Processing", job_id))
            print(f"✅ Data file processing submitted: {job_id}")
            
            # 6. Quick Analysis Demo
            quick_demo = await demo_quick_analysis()
            result = await client.quick_analysis(
                quick_demo["data"],
                quick_demo["script"],
                parameters=quick_demo["parameters"]
            )
            print(f"✅ Quick analysis completed: {result['status']}")
            if result['status'] == 'completed':
                print("📊 Quick Analysis Results:")
                for key, value in result['results'].items():
                    print(f"   {key}: {value}")
            
            # Wait for all jobs to complete and show results
            print("\n⏳ Waiting for jobs to complete...")
            for demo_name, job_id in demos:
                print(f"\n📋 {demo_name} Results:")
                try:
                    result = await client.wait_for_job(job_id, timeout=300, poll_interval=3)
                    
                    if result.status == "completed":
                        print(f"   ✅ Status: {result.status}")
                        print(f"   ⏱️  Execution time: {result.execution_time:.2f}s")
                        
                        if result.result_data:
                            print("   📊 Results:")
                            for key, value in result.result_data.items():
                                if isinstance(value, dict):
                                    print(f"      {key}:")
                                    for k, v in value.items():
                                        print(f"        {k}: {v}")
                                else:
                                    print(f"      {key}: {value}")
                    else:
                        print(f"   ❌ Status: {result.status}")
                        if result.error_message:
                            print(f"   Error: {result.error_message}")
                
                except Exception as e:
                    print(f"   ❌ Error getting results: {e}")
            
            # Cleanup temporary files
            if 'file_demo' in locals():
                import shutil
                shutil.rmtree(file_demo["temp_dir"], ignore_errors=True)
            
            print("\n🎉 All demos completed successfully!")
            
        except Exception as e:
            print(f"❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    print("Script Execution Framework - Comprehensive Demo")
    print("This demo showcases the ability to execute various types of scripts")
    print("with data processing capabilities in a secure, sandboxed environment.")
    print()
    
    try:
        asyncio.run(run_all_demos())
    except KeyboardInterrupt:
        print("\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        sys.exit(1)
    
    print("\n✅ Demo completed successfully!")