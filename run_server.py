#!/usr/bin/env python3
"""
Simple server runner for the distributed framework
"""
import os
import sys
import uvicorn
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Set up environment
os.environ.setdefault("NODE_ID", "node-1")
os.environ.setdefault("NODE_NAME", "Default Node")
os.environ.setdefault("INSTITUTION_NAME", "Default Institution")
os.environ.setdefault("SECRET_KEY", "demo-secret-key-change-in-production")
os.environ.setdefault("DATABASE_URL", "sqlite:///./distributed_node.db")
os.environ.setdefault("DATA_ROOT", "./data")
os.environ.setdefault("WORK_DIR", "./work")
os.environ.setdefault("MIN_COHORT_SIZE", "5")
os.environ.setdefault("LOG_LEVEL", "INFO")

def main():
    """Main function to run the server"""
    
    # Create necessary directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("work", exist_ok=True)
    
    print("Starting Distributed Data Access Framework")
    print("=" * 50)
    print(f"Node ID: {os.environ['NODE_ID']}")
    print(f"Institution: {os.environ['INSTITUTION_NAME']}")
    print(f"Database: {os.environ['DATABASE_URL']}")
    print("=" * 50)
    
    # Import and initialize the app
    try:
        from distributed_node.simple_main import app
        from distributed_node.database import init_db
        
        # Initialize database
        print("Initializing database...")
        init_db()
        print("Database initialized successfully!")
        
        # Get port from environment or use default
        port = int(os.environ.get("PORT", 8000))
        host = os.environ.get("HOST", "0.0.0.0")
        
        print(f"\nStarting server on http://{host}:{port}")
        print("API Documentation: http://localhost:8000/docs")
        print("Health Check: http://localhost:8000/health")
        print("\nPress Ctrl+C to stop the server")
        
        # Run the server
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=False,
            log_level="info"
        )
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Make sure all dependencies are installed: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
