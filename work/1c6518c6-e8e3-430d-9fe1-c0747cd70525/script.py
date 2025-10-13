from data_loader import load_data, save_results
print("Test script")
data = load_data()
result = {"test": "success"}
save_results(result)