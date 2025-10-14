#!/usr/bin/env python3
"""
Script to populate the database with default score/timeline options for each data catalog
"""
import sys
import os
sys.path.append('/workspace')

from distributed_node.database import get_db, init_db
from distributed_node.models import ScoreTimelineOption
from sqlalchemy.orm import Session

def populate_score_timeline_options():
    """Populate database with default score/timeline options"""
    
    # Initialize database
    init_db()
    
    # Get database session
    db = next(get_db())
    
    # Define options for each catalog
    options = [
        # Clinical Trial Data options
        {
            "data_catalog_id": "clinical_trial_data",
            "option_type": "score",
            "option_name": "UPDRS Total Score",
            "option_description": "Total UPDRS score (0-108) as primary outcome measure",
            "option_value": "UPDRS_total",
            "is_default": True,
            "is_active": True
        },
        {
            "data_catalog_id": "clinical_trial_data",
            "option_type": "score",
            "option_name": "UPDRS Motor Score",
            "option_description": "Motor subscale score (0-56) for motor symptoms",
            "option_value": "UPDRS_motor",
            "is_default": False,
            "is_active": True
        },
        {
            "data_catalog_id": "clinical_trial_data",
            "option_type": "score",
            "option_name": "Quality of Life Score",
            "option_description": "Quality of life assessment (0-100)",
            "option_value": "quality_of_life",
            "is_default": False,
            "is_active": True
        },
        {
            "data_catalog_id": "clinical_trial_data",
            "option_type": "timeline",
            "option_name": "Baseline to 6 months",
            "option_description": "Change from baseline to 6-month follow-up",
            "option_value": "baseline_6months",
            "is_default": True,
            "is_active": True
        },
        {
            "data_catalog_id": "clinical_trial_data",
            "option_type": "timeline",
            "option_name": "Baseline to 12 months",
            "option_description": "Change from baseline to 12-month follow-up",
            "option_value": "baseline_12months",
            "is_default": False,
            "is_active": True
        },
        {
            "data_catalog_id": "clinical_trial_data",
            "option_type": "timeline",
            "option_name": "6 to 12 months",
            "option_description": "Change from 6-month to 12-month follow-up",
            "option_value": "6months_12months",
            "is_default": False,
            "is_active": True
        },
        
        # Imaging Data options
        {
            "data_catalog_id": "imaging_data",
            "option_type": "score",
            "option_name": "Quality Rating",
            "option_description": "Overall scan quality rating (1-5)",
            "option_value": "quality_rating",
            "is_default": True,
            "is_active": True
        },
        {
            "data_catalog_id": "imaging_data",
            "option_type": "score",
            "option_name": "Motion Score",
            "option_description": "Motion artifact score (0-1, lower is better)",
            "option_value": "motion_score",
            "is_default": False,
            "is_active": True
        },
        {
            "data_catalog_id": "imaging_data",
            "option_type": "timeline",
            "option_name": "Single Timepoint",
            "option_description": "Cross-sectional analysis at single timepoint",
            "option_value": "single_timepoint",
            "is_default": True,
            "is_active": True
        },
        {
            "data_catalog_id": "imaging_data",
            "option_type": "timeline",
            "option_name": "Longitudinal Analysis",
            "option_description": "Analysis across multiple timepoints",
            "option_value": "longitudinal",
            "is_default": False,
            "is_active": True
        },
        
        # DBS VTA Analysis options
        {
            "data_catalog_id": "dbs_vta_analysis",
            "option_type": "score",
            "option_name": "Clinical Improvement",
            "option_description": "UPDRS improvement percentage",
            "option_value": "clinical_improvement",
            "is_default": True,
            "is_active": True
        },
        {
            "data_catalog_id": "dbs_vta_analysis",
            "option_type": "score",
            "option_name": "Baseline UPDRS",
            "option_description": "Baseline UPDRS-III score",
            "option_value": "baseline_updrs",
            "is_default": False,
            "is_active": True
        },
        {
            "data_catalog_id": "dbs_vta_analysis",
            "option_type": "score",
            "option_name": "Follow-up UPDRS",
            "option_description": "Follow-up UPDRS-III score",
            "option_value": "followup_updrs",
            "is_default": False,
            "is_active": True
        },
        {
            "data_catalog_id": "dbs_vta_analysis",
            "option_type": "timeline",
            "option_name": "Pre to Post DBS",
            "option_description": "Comparison before and after DBS surgery",
            "option_value": "pre_post_dbs",
            "is_default": True,
            "is_active": True
        },
        {
            "data_catalog_id": "dbs_vta_analysis",
            "option_type": "timeline",
            "option_name": "Stimulation Optimization",
            "option_description": "Analysis during stimulation parameter optimization",
            "option_value": "stim_optimization",
            "is_default": False,
            "is_active": True
        },
        
        # Demo Dataset options
        {
            "data_catalog_id": "demo_dataset",
            "option_type": "score",
            "option_name": "Value Score",
            "option_description": "Primary value metric for demo data",
            "option_value": "value",
            "is_default": True,
            "is_active": True
        },
        {
            "data_catalog_id": "demo_dataset",
            "option_type": "timeline",
            "option_name": "Cross-sectional",
            "option_description": "Single timepoint analysis",
            "option_value": "cross_sectional",
            "is_default": True,
            "is_active": True
        }
    ]
    
    # Clear existing options
    db.query(ScoreTimelineOption).delete()
    
    # Insert new options
    for option_data in options:
        option = ScoreTimelineOption(**option_data)
        db.add(option)
    
    db.commit()
    print(f"✅ Populated {len(options)} score/timeline options")
    
    # Print summary
    for catalog_id in ["clinical_trial_data", "imaging_data", "dbs_vta_analysis", "demo_dataset"]:
        score_count = db.query(ScoreTimelineOption).filter(
            ScoreTimelineOption.data_catalog_id == catalog_id,
            ScoreTimelineOption.option_type == "score"
        ).count()
        timeline_count = db.query(ScoreTimelineOption).filter(
            ScoreTimelineOption.data_catalog_id == catalog_id,
            ScoreTimelineOption.option_type == "timeline"
        ).count()
        print(f"📊 {catalog_id}: {score_count} score options, {timeline_count} timeline options")

if __name__ == "__main__":
    populate_score_timeline_options()