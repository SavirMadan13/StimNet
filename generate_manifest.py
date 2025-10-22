#!/usr/bin/env python3
"""
Auto-generate data manifest with column detection
Reads simplified manifest and auto-detects columns from actual files
"""

import pandas as pd
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def infer_column_type(series: pd.Series) -> str:
    """Infer column type from pandas Series"""
    dtype = str(series.dtype)
    
    # Handle different pandas dtypes
    if dtype.startswith('int'):
        return 'int'
    elif dtype.startswith('float'):
        return 'float'
    elif dtype.startswith('bool'):
        return 'bool'
    elif dtype.startswith('datetime'):
        return 'datetime'
    elif dtype == 'object':
        # Check if it's actually numeric but stored as object
        try:
            pd.to_numeric(series, errors='raise')
            return 'float'  # Could be int, but float is safer
        except:
            return 'string'
    else:
        return 'string'

def detect_columns_from_file(file_path: Path, file_type: str) -> List[Dict[str, str]]:
    """Detect columns and types from a file"""
    columns = []
    
    try:
        if file_type in ['csv', 'tsv']:
            # Read CSV/TSV
            sep = '\t' if file_type == 'tsv' else ','
            df = pd.read_csv(file_path, sep=sep, nrows=0)  # Just headers
            
            for col in df.columns:
                col_type = infer_column_type(df[col])
                columns.append({
                    "name": col,
                    "type": col_type
                })
                
        elif file_type == 'json':
            # Read JSON
            df = pd.read_json(file_path, nrows=0)  # Just headers
            
            for col in df.columns:
                col_type = infer_column_type(df[col])
                columns.append({
                    "name": col,
                    "type": col_type
                })
                
        elif file_type in ['nii', 'nii.gz', 'nifti']:
            # For NIfTI files, we can't easily detect columns
            # Return basic metadata
            columns.append({
                "name": "file_path",
                "type": "string"
            })
            
        else:
            logger.warning(f"Unknown file type: {file_type}")
            return []
            
    except Exception as e:
        logger.error(f"Error reading {file_path}: {e}")
        return []
    
    return columns

def count_records(file_path: Path, file_type: str) -> int:
    """Count records in a file"""
    try:
        if file_type in ['csv', 'tsv']:
            sep = '\t' if file_type == 'tsv' else ','
            df = pd.read_csv(file_path, sep=sep)
            return len(df)
        elif file_type == 'json':
            df = pd.read_json(file_path)
            return len(df)
        elif file_type in ['nii', 'nii.gz', 'nifti']:
            # For NIfTI, we can't easily count "records"
            return 1  # Single file
        else:
            return 0
    except Exception as e:
        logger.error(f"Error counting records in {file_path}: {e}")
        return 0

def enhance_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Enhance manifest with auto-detected columns"""
    
    # Read the simplified manifest
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    logger.info(f"Processing {len(manifest.get('catalogs', []))} catalogs...")
    
    # Process each catalog
    for catalog in manifest.get('catalogs', []):
        catalog_id = catalog.get('id', 'unknown')
        logger.info(f"Processing catalog: {catalog_id}")
        
        # Process each file in the catalog
        for file_info in catalog.get('files', []):
            file_path = Path(file_info['path'])
            
            if not file_path.exists():
                logger.warning(f"File not found: {file_path}")
                file_info['exists'] = False
                continue
            
            file_info['exists'] = True
            
            # Auto-detect columns
            file_type = file_info.get('type', 'csv')
            columns = detect_columns_from_file(file_path, file_type)
            file_info['columns'] = columns
            
            # Count actual records
            record_count = count_records(file_path, file_type)
            file_info['record_count'] = record_count
            
            logger.info(f"  ✓ {file_info['name']}: {len(columns)} columns, {record_count} records")
    
    return manifest

def main():
    """Main function to enhance manifest"""
    manifest_path = Path("data/data_manifest.json")
    
    if not manifest_path.exists():
        logger.error(f"Manifest not found: {manifest_path}")
        return
    
    logger.info("🔍 Auto-detecting columns from data files...")
    
    # Enhance the manifest
    enhanced_manifest = enhance_manifest(manifest_path)
    
    # Save enhanced manifest
    output_path = Path("data/data_manifest_enhanced.json")
    with open(output_path, 'w') as f:
        json.dump(enhanced_manifest, f, indent=2)
    
    logger.info(f"✅ Enhanced manifest saved to: {output_path}")
    logger.info("📊 Summary:")
    
    total_files = 0
    total_columns = 0
    total_records = 0
    
    for catalog in enhanced_manifest.get('catalogs', []):
        catalog_files = len(catalog.get('files', []))
        catalog_columns = sum(len(f.get('columns', [])) for f in catalog.get('files', []))
        catalog_records = sum(f.get('record_count', 0) for f in catalog.get('files', []))
        
        total_files += catalog_files
        total_columns += catalog_columns
        total_records += catalog_records
        
        logger.info(f"  📁 {catalog['id']}: {catalog_files} files, {catalog_columns} columns, {catalog_records} records")
    
    logger.info(f"🎯 Total: {total_files} files, {total_columns} columns, {total_records} records")

if __name__ == "__main__":
    main()
