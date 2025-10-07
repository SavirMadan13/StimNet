"""
Privacy and security manager for data access control
"""
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Union
import hashlib
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PrivacyManager:
    """Manages privacy controls and data anonymization"""
    
    def __init__(
        self,
        min_cohort_size: int = 10,
        enable_differential_privacy: bool = False,
        privacy_epsilon: float = 1.0,
        max_precision: int = 3
    ):
        self.min_cohort_size = min_cohort_size
        self.enable_differential_privacy = enable_differential_privacy
        self.privacy_epsilon = privacy_epsilon
        self.max_precision = max_precision
        self.access_history = []
    
    def check_cohort_size(self, data: Union[pd.DataFrame, List, int]) -> Dict[str, Any]:
        """Check if data meets minimum cohort size requirements"""
        if isinstance(data, pd.DataFrame):
            size = len(data)
        elif isinstance(data, list):
            size = len(data)
        elif isinstance(data, int):
            size = data
        else:
            size = 0
        
        is_valid = size >= self.min_cohort_size
        
        return {
            "is_valid": is_valid,
            "cohort_size": size,
            "min_required": self.min_cohort_size,
            "message": "OK" if is_valid else f"Cohort size {size} below minimum {self.min_cohort_size}"
        }
    
    def apply_privacy_controls(
        self,
        data: Union[Dict[str, Any], pd.DataFrame],
        result_type: str = "summary"
    ) -> Dict[str, Any]:
        """Apply privacy controls to results"""
        
        if isinstance(data, pd.DataFrame):
            cohort_check = self.check_cohort_size(data)
            if not cohort_check["is_valid"]:
                return {
                    "blocked": True,
                    "reason": cohort_check["message"],
                    "cohort_size": cohort_check["cohort_size"]
                }
            
            # Apply differential privacy if enabled
            if self.enable_differential_privacy:
                data = self._add_differential_privacy_noise(data)
            
            # Return only summary statistics
            return self._create_summary_result(data)
        
        elif isinstance(data, dict):
            # Check if result contains individual-level data
            if self._contains_individual_data(data):
                return {
                    "blocked": True,
                    "reason": "Individual-level data not permitted",
                    "summary_only": True
                }
            
            # Apply precision limits and noise
            return self._sanitize_result_dict(data)
        
        return data
    
    def _contains_individual_data(self, data: Dict[str, Any]) -> bool:
        """Check if data contains individual-level information"""
        # Look for patterns that suggest individual data
        suspicious_keys = [
            "subject_id", "patient_id", "participant_id", "id",
            "name", "email", "phone", "address", "ssn",
            "birth_date", "dob", "age_exact"
        ]
        
        def check_nested(obj, depth=0):
            if depth > 3:  # Limit recursion depth
                return False
            
            if isinstance(obj, dict):
                for key in obj.keys():
                    if any(sus_key in key.lower() for sus_key in suspicious_keys):
                        return True
                    if isinstance(obj[key], (dict, list)):
                        if check_nested(obj[key], depth + 1):
                            return True
            elif isinstance(obj, list) and obj:
                if check_nested(obj[0], depth + 1):
                    return True
            
            return False
        
        return check_nested(data)
    
    def _sanitize_result_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize result dictionary"""
        sanitized = {}
        
        for key, value in data.items():
            if isinstance(value, float):
                # Round to max precision
                sanitized[key] = round(value, self.max_precision)
                
                # Add differential privacy noise if enabled
                if self.enable_differential_privacy:
                    noise = np.random.laplace(0, 1/self.privacy_epsilon)
                    sanitized[key] = round(sanitized[key] + noise, self.max_precision)
            
            elif isinstance(value, int):
                sanitized[key] = value
                
                # Add noise to counts if DP enabled
                if self.enable_differential_privacy and key.lower() in ['count', 'n', 'size']:
                    noise = int(np.random.laplace(0, 1/self.privacy_epsilon))
                    sanitized[key] = max(0, sanitized[key] + noise)
            
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_result_dict(value)
            
            elif isinstance(value, list):
                # Only allow aggregate lists, not individual records
                if len(value) > self.min_cohort_size:
                    sanitized[key] = f"<list of {len(value)} items>"
                else:
                    sanitized[key] = value
            
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _create_summary_result(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Create summary statistics from DataFrame"""
        summary = {
            "n": len(df),
            "columns": list(df.columns),
            "data_types": df.dtypes.to_dict()
        }
        
        # Numeric summaries
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            summary["numeric_summary"] = {}
            for col in numeric_cols:
                col_summary = {
                    "mean": round(df[col].mean(), self.max_precision),
                    "std": round(df[col].std(), self.max_precision),
                    "min": round(df[col].min(), self.max_precision),
                    "max": round(df[col].max(), self.max_precision),
                    "median": round(df[col].median(), self.max_precision),
                    "count": int(df[col].count())
                }
                
                # Add differential privacy noise if enabled
                if self.enable_differential_privacy:
                    for stat_key in ["mean", "std", "median"]:
                        noise = np.random.laplace(0, 1/self.privacy_epsilon)
                        col_summary[stat_key] = round(col_summary[stat_key] + noise, self.max_precision)
                
                summary["numeric_summary"][col] = col_summary
        
        # Categorical summaries
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        if len(categorical_cols) > 0:
            summary["categorical_summary"] = {}
            for col in categorical_cols:
                value_counts = df[col].value_counts()
                
                # Only show categories with sufficient counts
                filtered_counts = value_counts[value_counts >= self.min_cohort_size]
                
                summary["categorical_summary"][col] = {
                    "unique_values": int(df[col].nunique()),
                    "top_categories": filtered_counts.head(10).to_dict(),
                    "total_categories_shown": len(filtered_counts)
                }
        
        return summary
    
    def _add_differential_privacy_noise(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add differential privacy noise to numeric columns"""
        df_noisy = df.copy()
        
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            # Add Laplace noise
            sensitivity = df[col].std()  # Simple sensitivity estimate
            scale = sensitivity / self.privacy_epsilon
            noise = np.random.laplace(0, scale, size=len(df))
            df_noisy[col] = df[col] + noise
        
        return df_noisy
    
    def anonymize_identifiers(self, data: pd.DataFrame, id_columns: List[str]) -> pd.DataFrame:
        """Anonymize identifier columns"""
        df_anon = data.copy()
        
        for col in id_columns:
            if col in df_anon.columns:
                # Replace with hash
                df_anon[col] = df_anon[col].apply(
                    lambda x: hashlib.sha256(str(x).encode()).hexdigest()[:8]
                )
        
        return df_anon
    
    def validate_query_safety(self, query: str, query_type: str = "sql") -> Dict[str, Any]:
        """Validate if a query is safe for execution"""
        safety_check = {
            "is_safe": True,
            "warnings": [],
            "blocked_patterns": []
        }
        
        if query_type.lower() == "sql":
            # Check for dangerous SQL patterns
            dangerous_patterns = [
                "DROP", "DELETE", "UPDATE", "INSERT", "CREATE", "ALTER", "TRUNCATE",
                "EXEC", "EXECUTE", "xp_", "sp_", "INFORMATION_SCHEMA", "sys."
            ]
            
            query_upper = query.upper()
            for pattern in dangerous_patterns:
                if pattern in query_upper:
                    safety_check["blocked_patterns"].append(pattern)
                    safety_check["warnings"].append(f"Dangerous pattern detected: {pattern}")
            
            # Check for attempts to access system tables
            system_patterns = ["pg_", "mysql.", "sqlite_master", "sysobjects"]
            for pattern in system_patterns:
                if pattern.lower() in query.lower():
                    safety_check["warnings"].append(f"System table access detected: {pattern}")
        
        # Determine if query should be blocked
        if safety_check["blocked_patterns"]:
            safety_check["is_safe"] = False
        
        return safety_check
    
    def log_data_access(
        self,
        catalog_id: int,
        user_info: Dict[str, Any],
        access_type: str,
        data_size: int,
        filters_applied: Optional[Dict[str, Any]] = None
    ):
        """Log data access for audit purposes"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "catalog_id": catalog_id,
            "user_info": user_info,
            "access_type": access_type,
            "data_size": data_size,
            "filters_applied": filters_applied or {},
            "privacy_controls_applied": {
                "min_cohort_size": self.min_cohort_size,
                "differential_privacy": self.enable_differential_privacy,
                "epsilon": self.privacy_epsilon if self.enable_differential_privacy else None
            }
        }
        
        self.access_history.append(log_entry)
        logger.info(f"Data access logged: catalog={catalog_id}, type={access_type}, size={data_size}")
    
    def get_privacy_report(self) -> Dict[str, Any]:
        """Generate privacy compliance report"""
        if not self.access_history:
            return {"message": "No data access recorded"}
        
        total_accesses = len(self.access_history)
        unique_catalogs = len(set(entry["catalog_id"] for entry in self.access_history))
        
        # Calculate time range
        timestamps = [entry["timestamp"] for entry in self.access_history]
        time_range = {
            "start": min(timestamps),
            "end": max(timestamps)
        }
        
        # Access patterns
        access_types = {}
        for entry in self.access_history:
            access_type = entry["access_type"]
            access_types[access_type] = access_types.get(access_type, 0) + 1
        
        return {
            "total_accesses": total_accesses,
            "unique_catalogs_accessed": unique_catalogs,
            "time_range": time_range,
            "access_types": access_types,
            "privacy_settings": {
                "min_cohort_size": self.min_cohort_size,
                "differential_privacy_enabled": self.enable_differential_privacy,
                "privacy_epsilon": self.privacy_epsilon,
                "max_precision": self.max_precision
            }
        }