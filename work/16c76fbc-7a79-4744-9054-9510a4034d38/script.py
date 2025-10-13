from data_loader import load_data, save_results
print("Starting analysis...")
data = load_data()
subjects = data["subjects"]
print(f"Loaded {len(subjects)} subjects")
result = {"sample_size": len(subjects), "analysis": "complete"}
save_results(result)
print("Done!")