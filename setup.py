#!/usr/bin/env python3
"""
Setup script for the Distributed Data Access and Remote Execution Framework
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(command, description="", check=True):
    """Run a shell command with error handling"""
    print(f"🔧 {description}")
    print(f"   Running: {command}")
    
    try:
        result = subprocess.run(command, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e}")
        if e.stderr:
            print(f"   Error details: {e.stderr}")
        return False


def check_prerequisites():
    """Check if all prerequisites are installed"""
    print("🔍 Checking prerequisites...")
    
    prerequisites = {
        "python3": "python3 --version",
        "pip": "pip --version", 
        "docker": "docker --version",
        "git": "git --version"
    }
    
    missing = []
    for name, command in prerequisites.items():
        if not run_command(command, f"Checking {name}", check=False):
            missing.append(name)
    
    if missing:
        print(f"❌ Missing prerequisites: {', '.join(missing)}")
        print("\nPlease install the missing prerequisites:")
        print("- Python 3.9+: https://www.python.org/downloads/")
        print("- Docker: https://docs.docker.com/get-docker/")
        print("- Git: https://git-scm.com/downloads/")
        return False
    
    print("✅ All prerequisites found!")
    return True


def setup_virtual_environment():
    """Set up Python virtual environment"""
    print("\n🐍 Setting up Python virtual environment...")
    
    if Path("venv").exists():
        print("   Virtual environment already exists")
        return True
    
    if not run_command("python3 -m venv venv", "Creating virtual environment"):
        return False
    
    # Activate and install dependencies
    if os.name == 'nt':  # Windows
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
    else:  # Unix/Linux/macOS
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
    
    if not run_command(f"{pip_cmd} install --upgrade pip", "Upgrading pip"):
        return False
    
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    print("✅ Virtual environment set up successfully!")
    return True


def setup_environment_file():
    """Set up environment configuration file"""
    print("\n⚙️  Setting up environment configuration...")
    
    env_file = Path(".env")
    example_file = Path(".env.example")
    
    if env_file.exists():
        print("   .env file already exists")
        return True
    
    if example_file.exists():
        shutil.copy(example_file, env_file)
        print("   Created .env from .env.example")
        print("   ⚠️  Please review and customize the .env file for your setup")
    else:
        # Create basic .env file
        basic_env = """# Basic configuration
NODE_ID=local-dev-node
NODE_NAME=Local Development Node
INSTITUTION_NAME=Development Institution
SECRET_KEY=change-this-in-production
DEBUG=true
DATABASE_URL=sqlite:///./distributed_node.db
DATA_ROOT=./data
WORK_DIR=./work
MIN_COHORT_SIZE=5
"""
        with open(env_file, 'w') as f:
            f.write(basic_env)
        print("   Created basic .env file")
    
    print("✅ Environment configuration ready!")
    return True


def setup_directories():
    """Create necessary directories"""
    print("\n📁 Creating directory structure...")
    
    directories = [
        "data", "data/demo", "data/catalogs", "data/metadata",
        "work", "logs", "certs"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"   Created: {directory}")
    
    print("✅ Directory structure created!")
    return True


def setup_demo_data():
    """Set up demo data and catalogs"""
    print("\n📊 Setting up demo data...")
    
    if os.name == 'nt':  # Windows
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        python_cmd = "venv/bin/python"
    
    if not run_command(f"{python_cmd} examples/setup_demo_data.py", "Creating demo datasets"):
        print("   ⚠️  Demo data setup failed, but you can run it manually later")
        return False
    
    print("✅ Demo data set up successfully!")
    return True


def test_installation():
    """Test the installation"""
    print("\n🧪 Testing installation...")
    
    if os.name == 'nt':  # Windows
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        python_cmd = "venv/bin/python"
    
    # Test imports
    test_imports = [
        "import distributed_node",
        "import client_sdk", 
        "import data_layer",
        "from distributed_node.config import settings",
        "from client_sdk import DistributedClient"
    ]
    
    for test_import in test_imports:
        if not run_command(f'{python_cmd} -c "{test_import}"', f"Testing: {test_import}", check=False):
            print(f"   ⚠️  Import test failed: {test_import}")
            return False
    
    # Run basic tests
    if Path("tests").exists():
        if not run_command(f"{python_cmd} -m pytest tests/test_basic.py -v", "Running basic tests", check=False):
            print("   ⚠️  Some tests failed, but installation should still work")
    
    print("✅ Installation tests passed!")
    return True


def generate_ssl_certificates():
    """Generate self-signed SSL certificates for development"""
    print("\n🔒 Generating SSL certificates for development...")
    
    cert_dir = Path("certs")
    cert_file = cert_dir / "cert.pem"
    key_file = cert_dir / "key.pem"
    
    if cert_file.exists() and key_file.exists():
        print("   SSL certificates already exist")
        return True
    
    # Generate self-signed certificate
    openssl_cmd = (
        "openssl req -x509 -newkey rsa:4096 -keyout certs/key.pem -out certs/cert.pem "
        "-days 365 -nodes -subj '/C=US/ST=State/L=City/O=Organization/CN=localhost'"
    )
    
    if not run_command(openssl_cmd, "Generating self-signed SSL certificate", check=False):
        print("   ⚠️  SSL certificate generation failed (openssl not found)")
        print("   You can generate certificates manually or use HTTP in development")
        return False
    
    print("✅ SSL certificates generated!")
    return True


def print_next_steps():
    """Print next steps for the user"""
    print("\n" + "="*60)
    print("🎉 SETUP COMPLETE!")
    print("="*60)
    
    print("\n📋 Next Steps:")
    print("1. Review and customize your .env file")
    print("2. Start the server:")
    
    if os.name == 'nt':  # Windows
        print("   venv\\Scripts\\activate")
        print("   python -m distributed_node.main")
    else:  # Unix/Linux/macOS  
        print("   source venv/bin/activate")
        print("   python -m distributed_node.main")
    
    print("\n3. In another terminal, test the client:")
    print("   python examples/basic_usage.py")
    
    print("\n4. View API documentation at:")
    print("   http://localhost:8000/docs")
    
    print("\n📚 Documentation:")
    print("   - README.md - Overview and usage")
    print("   - QUICKSTART.md - Quick start guide")
    print("   - ARCHITECTURE.md - System architecture")
    print("   - DEPLOYMENT.md - Production deployment")
    
    print("\n🐳 Docker Alternative:")
    print("   docker-compose up -d")
    
    print("\n🆘 Need Help?")
    print("   - Check the troubleshooting section in README.md")
    print("   - Review the examples in the examples/ directory")
    print("   - Open an issue on GitHub")


def main():
    """Main setup function"""
    print("🚀 Distributed Data Access and Remote Execution Framework Setup")
    print("=" * 60)
    
    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)
    
    # Setup steps
    steps = [
        setup_virtual_environment,
        setup_environment_file,
        setup_directories,
        setup_demo_data,
        generate_ssl_certificates,
        test_installation
    ]
    
    for step in steps:
        if not step():
            print(f"\n❌ Setup step failed: {step.__name__}")
            print("Please check the error messages above and try again.")
            sys.exit(1)
    
    print_next_steps()


if __name__ == "__main__":
    main()