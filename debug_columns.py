#!/usr/bin/env python3
"""
Debug script to test column detection
"""
import sys
import os
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from distributed_node.real_main import detect_column_info
import pandas as pd

def test_berlin_dataset():
    """Test the Berlin dataset file processing"""
    file_path = Path('/Users/savirmadan/Documents/StimNetDocs/berlin_dataset/subjects.csv')
    
    print(f"Testing file: {file_path}")
    print(f"File exists: {file_path.exists()}")
    
    if file_path.exists():
        try:
            df = pd.read_csv(file_path)
            print(f"DataFrame shape: {df.shape}")
            print(f"Columns: {list(df.columns)}")
            
            # Test column detection
            print("\nColumn analysis:")
            for col in df.columns:
                col_info = detect_column_info(df[col])
                if 'constant_value' in col_info:
                    print(f"  ✓ {col}: {col_info}")
                else:
                    print(f"  - {col}: {col_info}")
                    
        except Exception as e:
            print(f"Error reading file: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_berlin_dataset()
