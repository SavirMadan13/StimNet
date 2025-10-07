#!/usr/bin/env python3
"""
Enhanced Remote Client for Data Submission and Processing

This client allows users to easily submit data to the distributed framework
from any machine and get analysis results back.
"""

import requests
import json
import time
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import pandas as pd
import argparse
from datetime import datetime


class RemoteDataClient:
    """Client for submitting data and analysis scripts to remote nodes"""
    
    def __init__(self, base_url: str, username: str = "demo", password: str = "demo"):
        """
        Initialize the remote client
        
        Args:
            base_url: Base URL of the remote node (e.g., your Cloudflare URL)
            username: Username for authentication
            password: Password for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.auth_token = None
        
        # Authenticate on initialization
        self.authenticate()
    
    def authenticate(self):
        """Authenticate with the remote server"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/v1/auth/token",
                data={"username": self.username, "password": self.password}
            )
            response.raise_for_status()
            
            data = response.json()
            self.auth_token = data["access_token"]
            self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
            
            print(f"✅ Successfully authenticated with {self.base_url}")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def health_check(self):
        """Check if the remote server is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            
            health_data = response.json()
            print(f"🏥 Server Health: {health_data['status']}")
            print(f"   Node ID: {health_data['node_id']}")
            print(f"   Uptime: {health_data['uptime']:.1f} seconds")
            print(f"   Active Jobs: {health_data['active_jobs']}")
            
            return health_data
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Health check failed: {e}")
            return None
    
    def submit_files_for_analysis(self, files: List[str], analysis_script: str, 
                                parameters: Dict[str, Any] = None, 
                                analysis_type: str = "python") -> Optional[str]:
        """
        Submit data files and analysis script for processing
        
        Args:
            files: List of file paths to upload
            analysis_script: Python script to execute on the data
            parameters: Optional parameters for the analysis
            analysis_type: Type of analysis ("python", "r", etc.)
        
        Returns:
            Job ID if successful, None if failed
        """
        
        if not files:
            print("❌ No files provided")
            return None
        
        # Validate files exist
        for file_path in files:
            if not os.path.exists(file_path):
                print(f"❌ File not found: {file_path}")
                return None
        
        try:
            # Prepare files for upload
            upload_files = []
            for file_path in files:
                upload_files.append(('files', (os.path.basename(file_path), open(file_path, 'rb'))))
            
            # Prepare form data
            form_data = {
                'script_content': analysis_script,
                'parameters': json.dumps(parameters or {}),
                'analysis_type': analysis_type
            }
            
            print(f"📤 Uploading {len(files)} files for analysis...")
            
            response = self.session.post(
                f"{self.base_url}/api/v1/remote/submit-data",
                data=form_data,
                files=upload_files
            )
            
            # Close file handles
            for _, (_, file_handle) in upload_files:
                file_handle.close()
            
            response.raise_for_status()
            result = response.json()
            
            job_id = result['job_id']
            print(f"✅ Data submitted successfully!")
            print(f"   Job ID: {job_id}")
            print(f"   Files uploaded: {result['files_received']}")
            print(f"   Estimated processing time: {result['estimated_processing_time']}")
            
            return job_id
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to submit data: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"   Error details: {error_detail}")
                except:
                    print(f"   Response: {e.response.text}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return None
    
    def submit_json_data(self, data: Union[Dict, List], analysis_script: str, 
                        parameters: Dict[str, Any] = None) -> Optional[str]:
        """
        Submit JSON data for quick analysis (no file upload)
        
        Args:
            data: Data as dictionary or list of dictionaries
            analysis_script: Python script to execute on the data
            parameters: Optional parameters for the analysis
        
        Returns:
            Job ID if successful, None if failed
        """
        
        try:
            payload = {
                "data": data,
                "analysis_script": analysis_script,
                "parameters": parameters or {}
            }
            
            print("📊 Submitting JSON data for quick analysis...")
            
            response = self.session.post(
                f"{self.base_url}/api/v1/remote/quick-analysis",
                json=payload
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result['status'] == 'completed':
                print("✅ Quick analysis completed!")
                print(f"   Job ID: {result['job_id']}")
                print(f"   Execution time: {result['execution_time']}s")
                print(f"   Records processed: {result['records_processed']}")
                return result
            else:
                print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to submit JSON data: {e}")
            return None
    
    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get the status of a submitted job"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/remote/job/{job_id}/status")
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to get job status: {e}")
            return None
    
    def get_job_results(self, job_id: str) -> Optional[Dict]:
        """Get the results of a completed job"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/remote/job/{job_id}/results")
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to get job results: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"   Error details: {error_detail}")
                except:
                    print(f"   Response: {e.response.text}")
            return None
    
    def wait_for_results(self, job_id: str, timeout: int = 300, poll_interval: int = 5) -> Optional[Dict]:
        """
        Wait for job completion and return results
        
        Args:
            job_id: Job ID to wait for
            timeout: Maximum time to wait in seconds
            poll_interval: How often to check status in seconds
        
        Returns:
            Job results if successful, None if failed or timed out
        """
        
        print(f"⏳ Waiting for job {job_id} to complete...")
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_job_status(job_id)
            
            if not status:
                print("❌ Failed to get job status")
                return None
            
            print(f"   Status: {status['status']}")
            
            if status['status'] == 'completed':
                print("✅ Job completed! Getting results...")
                return self.get_job_results(job_id)
            elif status['status'] == 'failed':
                print(f"❌ Job failed: {status.get('error', 'Unknown error')}")
                return None
            elif status['status'] in ['cancelled']:
                print(f"⚠️ Job was cancelled")
                return None
            
            time.sleep(poll_interval)
        
        print(f"⏰ Job timed out after {timeout} seconds")
        return None
    
    def get_analysis_templates(self) -> Optional[Dict]:
        """Get pre-built analysis templates"""
        try:
            response = self.session.get(f"{self.base_url}/api/v1/remote/analysis-templates")
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to get analysis templates: {e}")
            return None
    
    def run_template_analysis(self, template_name: str, data: Union[List[str], Dict, List], 
                            parameters: Dict[str, Any] = None) -> Optional[Dict]:
        """
        Run a pre-built analysis template
        
        Args:
            template_name: Name of the template to use
            data: Either list of file paths or JSON data
            parameters: Template-specific parameters
        
        Returns:
            Analysis results if successful
        """
        
        # Get available templates
        templates = self.get_analysis_templates()
        if not templates or template_name not in templates['templates']:
            print(f"❌ Template '{template_name}' not found")
            available = list(templates['templates'].keys()) if templates else []
            print(f"   Available templates: {available}")
            return None
        
        template = templates['templates'][template_name]
        script = template['script']
        
        print(f"🧪 Running template analysis: {template['name']}")
        print(f"   Description: {template['description']}")
        
        # Determine if data is files or JSON
        if isinstance(data, list) and all(isinstance(item, str) for item in data):
            # Assume it's file paths
            job_id = self.submit_files_for_analysis(data, script, parameters)
            if job_id:
                return self.wait_for_results(job_id)
        else:
            # Assume it's JSON data
            return self.submit_json_data(data, script, parameters)
        
        return None


def main():
    """Command-line interface for the remote client"""
    parser = argparse.ArgumentParser(description="Remote Data Analysis Client")
    parser.add_argument("--url", required=True, help="Base URL of the remote server")
    parser.add_argument("--username", default="demo", help="Username for authentication")
    parser.add_argument("--password", default="demo", help="Password for authentication")
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Health check command
    health_parser = subparsers.add_parser('health', help='Check server health')
    
    # Submit files command
    submit_parser = subparsers.add_parser('submit', help='Submit files for analysis')
    submit_parser.add_argument('files', nargs='+', help='Files to upload')
    submit_parser.add_argument('--script', required=True, help='Analysis script file')
    submit_parser.add_argument('--params', help='Parameters as JSON string')
    submit_parser.add_argument('--wait', action='store_true', help='Wait for results')
    
    # Quick analysis command
    quick_parser = subparsers.add_parser('quick', help='Quick analysis with JSON data')
    quick_parser.add_argument('--data', required=True, help='JSON data file or string')
    quick_parser.add_argument('--script', required=True, help='Analysis script file')
    quick_parser.add_argument('--params', help='Parameters as JSON string')
    
    # Template analysis command
    template_parser = subparsers.add_parser('template', help='Run template analysis')
    template_parser.add_argument('--name', required=True, help='Template name')
    template_parser.add_argument('--data', required=True, help='Data file (CSV/JSON)')
    template_parser.add_argument('--params', help='Parameters as JSON string')
    
    # List templates command
    list_parser = subparsers.add_parser('templates', help='List available templates')
    
    # Job status command
    status_parser = subparsers.add_parser('status', help='Check job status')
    status_parser.add_argument('job_id', help='Job ID to check')
    
    # Get results command
    results_parser = subparsers.add_parser('results', help='Get job results')
    results_parser.add_argument('job_id', help='Job ID to get results for')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Create client
    client = RemoteDataClient(args.url, args.username, args.password)
    
    if args.command == 'health':
        client.health_check()
    
    elif args.command == 'submit':
        # Read script
        with open(args.script, 'r') as f:
            script_content = f.read()
        
        # Parse parameters
        params = {}
        if args.params:
            params = json.loads(args.params)
        
        job_id = client.submit_files_for_analysis(args.files, script_content, params)
        
        if job_id and args.wait:
            results = client.wait_for_results(job_id)
            if results:
                print("\n📋 Results:")
                print(json.dumps(results, indent=2))
    
    elif args.command == 'quick':
        # Read script
        with open(args.script, 'r') as f:
            script_content = f.read()
        
        # Read data
        if os.path.exists(args.data):
            with open(args.data, 'r') as f:
                data = json.load(f)
        else:
            data = json.loads(args.data)
        
        # Parse parameters
        params = {}
        if args.params:
            params = json.loads(args.params)
        
        results = client.submit_json_data(data, script_content, params)
        if results:
            print("\n📋 Results:")
            print(json.dumps(results, indent=2))
    
    elif args.command == 'template':
        # Read data
        if args.data.endswith('.csv'):
            data = pd.read_csv(args.data).to_dict('records')
        elif args.data.endswith('.json'):
            with open(args.data, 'r') as f:
                data = json.load(f)
        else:
            # Assume it's a file path for file-based templates
            data = [args.data]
        
        # Parse parameters
        params = {}
        if args.params:
            params = json.loads(args.params)
        
        results = client.run_template_analysis(args.name, data, params)
        if results:
            print("\n📋 Results:")
            print(json.dumps(results, indent=2))
    
    elif args.command == 'templates':
        templates = client.get_analysis_templates()
        if templates:
            print("\n🧪 Available Analysis Templates:")
            for name, template in templates['templates'].items():
                print(f"\n  {name}:")
                print(f"    Description: {template['description']}")
                print(f"    Data Format: {template['data_format']}")
                if template['parameters']:
                    print(f"    Parameters: {template['parameters']}")
    
    elif args.command == 'status':
        status = client.get_job_status(args.job_id)
        if status:
            print(f"\n📊 Job Status for {args.job_id}:")
            print(json.dumps(status, indent=2))
    
    elif args.command == 'results':
        results = client.get_job_results(args.job_id)
        if results:
            print(f"\n📋 Results for {args.job_id}:")
            print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()