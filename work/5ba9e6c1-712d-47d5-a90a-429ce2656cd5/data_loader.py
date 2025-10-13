"""
Data loading helper for user scripts.
This module provides a simple interface for scripts to load data
without needing to know file paths.
"""
import os
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional


def load_data() -> Dict[str, Any]:
    """
    Load all data files from the selected catalog and any uploaded files.
    
    Returns:
        Dictionary mapping file names to DataFrames or other data objects
        
    Example:
        data = load_data()
        subjects = data['subjects']  # From catalog
        my_map = data['uploaded_connectivity_map']  # From uploaded file
    """
    # Read job configuration
    config_path = os.environ.get('JOB_CONFIG')
    if not config_path or not os.path.exists(config_path):
        raise ValueError("JOB_CONFIG not found. Cannot load data.")
    
    with open(config_path, 'r') as f:
        job_config = json.load(f)
    
    # Get catalog ID
    catalog_id = job_config.get('data_catalog_id')
    if not catalog_id:
        raise ValueError("No data catalog specified in job configuration")
    
    # Get uploaded file IDs if any
    uploaded_file_ids = job_config.get('uploaded_file_ids', [])
    
    # Read manifest to find catalog files
    # Use absolute path to project root (go up 3 levels from job directory to project root)
    # Job directory structure: project_root/work/job_id/data_loader.py
    # So we need to go up 3 levels to get to project_root
    project_root = Path(__file__).parent.parent.parent
    manifest_path = project_root / "data" / "data_manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"Data manifest not found at {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Find the catalog
    catalog = None
    for cat in manifest.get('catalogs', []):
        if cat['id'] == catalog_id:
            catalog = cat
            break
    
    if not catalog:
        raise ValueError(f"Catalog '{catalog_id}' not found in manifest")
    
    # Load all files from the catalog
    data = {}
    for file_info in catalog.get('files', []):
        # Resolve path relative to project root
        file_path = project_root / file_info['path']
        
        if not file_path.exists():
            print(f"Warning: File {file_path} not found, skipping...")
            continue
        
        # Load based on file type
        if file_info['type'] == 'csv':
            try:
                df = pd.read_csv(file_path)
                data[file_info['name']] = df
                print(f"✓ Loaded {file_info['name']}: {len(df)} rows, {len(df.columns)} columns")
            except Exception as e:
                print(f"Error loading {file_info['name']}: {e}")
        elif file_info['type'] == 'tsv':
            try:
                df = pd.read_csv(file_path, sep='\t')
                data[file_info['name']] = df
                print(f"✓ Loaded {file_info['name']}: {len(df)} rows, {len(df.columns)} columns")
            except Exception as e:
                print(f"Error loading {file_info['name']}: {e}")
        elif file_info['type'] == 'json':
            try:
                df = pd.read_json(file_path)
                data[file_info['name']] = df
                print(f"✓ Loaded {file_info['name']}: {len(df)} rows, {len(df.columns)} columns")
            except Exception as e:
                print(f"Error loading {file_info['name']}: {e}")
        elif file_info['type'] in ['nii', 'nii.gz', 'nifti']:
            try:
                import nibabel as nib
                img = nib.load(file_path)
                data[file_info['name']] = img
                print(f"✓ Loaded {file_info['name']}: {img.shape} volume")
            except ImportError:
                print(f"Warning: nibabel not installed. Cannot load {file_info['name']}")
            except Exception as e:
                print(f"Error loading {file_info['name']}: {e}")
        else:
            print(f"Warning: Unsupported file type '{file_info['type']}' for {file_info['name']}")
    
    if not data:
        raise ValueError(f"No data files could be loaded from catalog '{catalog_id}'")
    
    print(f"\n✓ Successfully loaded {len(data)} data file(s) from '{catalog['name']}'")
    
    # Load uploaded files if any
    if uploaded_file_ids:
        print(f"\n📂 Loading {len(uploaded_file_ids)} uploaded file(s)...")
        uploaded_files_path = project_root / "uploads" / "uploaded_files.json"
        
        if uploaded_files_path.exists():
            with open(uploaded_files_path, 'r') as f:
                uploaded_files_info = json.load(f)
            
            for file_id in uploaded_file_ids:
                # Find the file info
                file_info = None
                for f in uploaded_files_info.get('files', []):
                    if f.get('file_id') == file_id:
                        file_info = f
                        break
                
                if not file_info:
                    print(f"Warning: Uploaded file {file_id} not found")
                    continue
                
                # Load the file based on type
                file_path = Path(file_info['path'])
                file_type = file_info['type']
                file_name = f"uploaded_{Path(file_info['filename']).stem}"
                
                if file_type in ['csv', 'tsv']:
                    try:
                        df = pd.read_csv(file_path, sep='\t' if file_type == 'tsv' else ',')
                        data[file_name] = df
                        print(f"✓ Loaded uploaded file: {file_name} ({len(df)} rows)")
                    except Exception as e:
                        print(f"Error loading uploaded file {file_name}: {e}")
                elif file_type in ['nii', 'nii.gz', 'nifti']:
                    try:
                        import nibabel as nib
                        img = nib.load(file_path)
                        data[file_name] = img
                        print(f"✓ Loaded uploaded file: {file_name} ({img.shape} volume)")
                    except ImportError:
                        print(f"Warning: nibabel not installed. Cannot load {file_name}")
                    except Exception as e:
                        print(f"Error loading uploaded file {file_name}: {e}")
                else:
                    print(f"Warning: Unsupported uploaded file type '{file_type}' for {file_name}")
        
        print(f"\n✓ Successfully loaded {len(uploaded_file_ids)} uploaded file(s)")
    
    return data


def get_catalog_info() -> Dict[str, Any]:
    """
    Get information about the selected catalog.
    
    Returns:
        Dictionary with catalog metadata
        
    Example:
        info = get_catalog_info()
        print(f"Catalog: {info['name']}")
        print(f"Description: {info['description']}")
    """
    # Read job configuration
    config_path = os.environ.get('JOB_CONFIG')
    if not config_path or not os.path.exists(config_path):
        raise ValueError("JOB_CONFIG not found. Cannot get catalog info.")
    
    with open(config_path, 'r') as f:
        job_config = json.load(f)
    
    # Get catalog ID
    catalog_id = job_config.get('data_catalog_id')
    if not catalog_id:
        raise ValueError("No data catalog specified in job configuration")
    
    # Read manifest
    # Use absolute path to project root (go up 3 levels from job directory to project root)
    project_root = Path(__file__).parent.parent.parent
    manifest_path = project_root / "data" / "data_manifest.json"
    if not manifest_path.exists():
        raise ValueError(f"Data manifest not found at {manifest_path}")
    
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    # Find the catalog
    for cat in manifest.get('catalogs', []):
        if cat['id'] == catalog_id:
            return {
                'id': cat['id'],
                'name': cat['name'],
                'description': cat['description'],
                'data_type': cat.get('data_type', 'unknown'),
                'privacy_level': cat.get('privacy_level', 'unknown'),
                'min_cohort_size': cat.get('min_cohort_size', 0),
                'files': cat.get('files', [])
            }
    
    raise ValueError(f"Catalog '{catalog_id}' not found in manifest")


def save_results(results: Dict[str, Any]) -> None:
    """
    Save analysis results to the output file.
    
    Args:
        results: Dictionary of results to save
        
    Example:
        save_results({
            'mean_age': 45.2,
            'n_subjects': 150,
            'summary': 'Analysis complete'
        })
    """
    output_file = os.environ.get('OUTPUT_FILE')
    if not output_file:
        raise ValueError("OUTPUT_FILE not set. Cannot save results.")
    
    # Convert numpy types to Python types for JSON serialization
    def convert_to_python_types(obj):
        """Recursively convert numpy types to Python types"""
        import numpy as np
        if isinstance(obj, dict):
            return {k: convert_to_python_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert_to_python_types(item) for item in obj]
        elif isinstance(obj, (np.integer, np.floating)):
            return obj.item()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        else:
            return obj
    
    # Convert results to Python types
    results_clean = convert_to_python_types(results)
    
    with open(output_file, 'w') as f:
        json.dump(results_clean, f, indent=2)
    
    print(f"✓ Results saved to {output_file}")

