#!/usr/bin/env python3
"""
Set up demo data catalogs and sample data for testing
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from distributed_node.database import SessionLocal, init_db
from distributed_node.models import DataCatalog


def create_demo_data():
    """Create demo datasets"""
    
    # Create data directories
    data_dir = Path("data/catalogs")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Demo dataset 1: Clinical trial data
    clinical_dir = data_dir / "clinical_trial_data"
    clinical_dir.mkdir(exist_ok=True)
    
    # Generate synthetic subjects data
    np.random.seed(42)
    n_subjects = 150
    
    subjects_data = {
        'subject_id': [f"SUBJ_{i:04d}" for i in range(1, n_subjects + 1)],
        'age': np.random.normal(45, 15, n_subjects).astype(int),
        'sex': np.random.choice(['M', 'F'], n_subjects),
        'diagnosis': np.random.choice(['PD', 'ET', 'Control'], n_subjects, p=[0.4, 0.3, 0.3]),
        'visit': np.random.choice(['baseline', '6mo', '12mo'], n_subjects, p=[0.5, 0.3, 0.2])
    }
    
    subjects_df = pd.DataFrame(subjects_data)
    subjects_df.to_csv(clinical_dir / "subjects.csv", index=False)
    
    # Generate synthetic outcomes data
    outcomes_data = {
        'subject_id': subjects_data['subject_id'],
        'visit': subjects_data['visit'],
        'UPDRS_total': np.random.normal(30, 10, n_subjects),
        'UPDRS_change': np.random.normal(-5, 8, n_subjects),
        'quality_of_life': np.random.uniform(40, 90, n_subjects),
        'treatment_response': np.random.choice([0, 1], n_subjects, p=[0.6, 0.4])
    }
    
    outcomes_df = pd.DataFrame(outcomes_data)
    outcomes_df.to_csv(clinical_dir / "outcomes.csv", index=False)
    
    print(f"Created clinical trial dataset with {n_subjects} subjects")
    
    # Demo dataset 2: Imaging data catalog
    imaging_dir = data_dir / "imaging_data"
    imaging_dir.mkdir(exist_ok=True)
    
    # Generate synthetic imaging metadata
    imaging_data = {
        'subject_id': subjects_data['subject_id'][:100],  # Subset for imaging
        'scan_type': np.random.choice(['T1', 'DTI', 'fMRI'], 100),
        'scan_quality': np.random.uniform(0.7, 1.0, 100),
        'motion_score': np.random.uniform(0, 2.5, 100),
        'file_path': [f"/data/imaging/subj_{i:04d}_scan.nii.gz" for i in range(1, 101)]
    }
    
    imaging_df = pd.DataFrame(imaging_data)
    imaging_df.to_csv(imaging_dir / "scan_metadata.csv", index=False)
    
    print(f"Created imaging dataset with {len(imaging_data['subject_id'])} scans")


def create_demo_catalogs():
    """Create demo data catalog entries in the database"""
    
    # Initialize database
    init_db()
    
    db = SessionLocal()
    
    try:
        # Clinical trial data catalog
        clinical_catalog = DataCatalog(
            name="clinical_trial_data",
            description="Synthetic clinical trial dataset for Parkinson's disease research",
            data_type="tabular",
            schema_definition={
                "subjects": {
                    "subject_id": {"type": "string", "description": "Unique subject identifier"},
                    "age": {"type": "integer", "description": "Age in years"},
                    "sex": {"type": "string", "description": "Biological sex (M/F)"},
                    "diagnosis": {"type": "string", "description": "Primary diagnosis"},
                    "visit": {"type": "string", "description": "Study visit"}
                },
                "outcomes": {
                    "subject_id": {"type": "string", "description": "Subject identifier"},
                    "visit": {"type": "string", "description": "Study visit"},
                    "UPDRS_total": {"type": "float", "description": "Total UPDRS score"},
                    "UPDRS_change": {"type": "float", "description": "Change from baseline"},
                    "quality_of_life": {"type": "float", "description": "Quality of life score"},
                    "treatment_response": {"type": "integer", "description": "Treatment response (0/1)"}
                }
            },
            access_level="public",
            total_records=150
        )
        
        # Check if catalog already exists
        existing = db.query(DataCatalog).filter(DataCatalog.name == "clinical_trial_data").first()
        if not existing:
            db.add(clinical_catalog)
            print("Created clinical trial data catalog")
        else:
            print("Clinical trial data catalog already exists")
        
        # Imaging data catalog
        imaging_catalog = DataCatalog(
            name="imaging_data",
            description="Synthetic neuroimaging dataset with T1, DTI, and fMRI scans",
            data_type="imaging",
            schema_definition={
                "scan_metadata": {
                    "subject_id": {"type": "string", "description": "Subject identifier"},
                    "scan_type": {"type": "string", "description": "Type of scan (T1/DTI/fMRI)"},
                    "scan_quality": {"type": "float", "description": "Quality score (0-1)"},
                    "motion_score": {"type": "float", "description": "Motion artifact score"},
                    "file_path": {"type": "string", "description": "Path to scan file"}
                }
            },
            access_level="restricted",
            total_records=100
        )
        
        existing = db.query(DataCatalog).filter(DataCatalog.name == "imaging_data").first()
        if not existing:
            db.add(imaging_catalog)
            print("Created imaging data catalog")
        else:
            print("Imaging data catalog already exists")
        
        # Public demo catalog
        demo_catalog = DataCatalog(
            name="demo_dataset",
            description="Small public dataset for testing and demonstrations",
            data_type="mixed",
            schema_definition={
                "description": "Simple dataset for API testing",
                "fields": ["id", "value", "category", "timestamp"]
            },
            access_level="public",
            total_records=50
        )
        
        existing = db.query(DataCatalog).filter(DataCatalog.name == "demo_dataset").first()
        if not existing:
            db.add(demo_catalog)
            print("Created demo dataset catalog")
        else:
            print("Demo dataset catalog already exists")
        
        db.commit()
        print("All data catalogs created successfully!")
        
    except Exception as e:
        print(f"Error creating catalogs: {e}")
        db.rollback()
    finally:
        db.close()


def main():
    """Main setup function"""
    print("Setting up demo data for Distributed Framework")
    print("=" * 50)
    
    try:
        # Create demo data files
        print("Creating demo datasets...")
        create_demo_data()
        
        # Create database catalogs
        print("\nCreating data catalog entries...")
        create_demo_catalogs()
        
        print("\nDemo setup completed successfully!")
        print("\nYou can now:")
        print("1. Start the node server: python -m distributed_node.main")
        print("2. Run the client example: python examples/simple_client.py")
        
    except Exception as e:
        print(f"Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
