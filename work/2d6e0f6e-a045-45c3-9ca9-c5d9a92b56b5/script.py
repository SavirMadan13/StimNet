from data_loader import load_data, save_results

print("🧪 Testing uploaded file access...")

data = load_data()
print(f"📂 Loaded {len(data)} file(s)")
print(f"📋 Available files: {list(data.keys())}")

if "test_upload" in data:
    df = data["test_upload"]
    print(f"\n✅ Successfully loaded uploaded file!")
    print(f"   Rows: {len(df)}")
    print(f"   Columns: {list(df.columns)}")
    print(f"\n   First few rows:")
    print(df.head())
    
    result = {
        "total_subjects": len(df),
        "mean_age": float(df["age"].mean()),
        "mean_score": float(df["score"].mean()),
        "file_source": "User Uploaded Files"
    }
    
    print(f"\n📊 Analysis Results:")
    print(f"   Total subjects: {result["total_subjects"]}")
    print(f"   Mean age: {result["mean_age"]:.2f}")
    print(f"   Mean score: {result["mean_score"]:.2f}")
    
    save_results(result)
else:
    print("❌ test_upload file not found in data")
    save_results({"error": "test_upload file not found"})
