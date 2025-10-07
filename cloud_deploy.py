#!/usr/bin/env python3
"""
Cloud deployment utilities for the distributed framework
Supports various cloud providers as ngrok alternatives
"""
import subprocess
import json
import os
import sys
from pathlib import Path
import tempfile
import yaml

class CloudDeployment:
    """Manages cloud deployments for permanent cross-machine access"""
    
    def __init__(self):
        self.project_dir = Path.cwd()
    
    def deploy_to_railway(self):
        """Deploy to Railway (free tier available)"""
        print("🚂 Deploying to Railway...")
        
        # Check if railway CLI is installed
        if not self._check_command('railway'):
            print("📦 Installing Railway CLI...")
            subprocess.run(['npm', 'install', '-g', '@railway/cli'], check=True)
        
        # Create railway.json if it doesn't exist
        railway_config = {
            "build": {
                "builder": "NIXPACKS"
            },
            "deploy": {
                "startCommand": "python run_server.py",
                "healthcheckPath": "/health",
                "restartPolicyType": "ON_FAILURE"
            }
        }
        
        with open('railway.json', 'w') as f:
            json.dump(railway_config, f, indent=2)
        
        # Create Procfile
        with open('Procfile', 'w') as f:
            f.write("web: python run_server.py\n")
        
        # Create railway.toml
        railway_toml = """
[build]
builder = "nixpacks"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 100
restartPolicyType = "ON_FAILURE"
"""
        with open('railway.toml', 'w') as f:
            f.write(railway_toml.strip())
        
        print("📋 Railway configuration created")
        print("🔗 Next steps:")
        print("   1. railway login")
        print("   2. railway init")
        print("   3. railway up")
        
        return True
    
    def deploy_to_render(self):
        """Deploy to Render (free tier available)"""
        print("🎨 Setting up Render deployment...")
        
        # Create render.yaml
        render_config = {
            'services': [{
                'type': 'web',
                'name': 'distributed-framework',
                'env': 'python',
                'buildCommand': 'pip install -r requirements.txt',
                'startCommand': 'python run_server.py',
                'healthCheckPath': '/health',
                'envVars': [
                    {'key': 'PORT', 'value': '10000'},
                    {'key': 'HOST', 'value': '0.0.0.0'},
                    {'key': 'NODE_ID', 'value': 'render-node-1'},
                    {'key': 'INSTITUTION_NAME', 'value': 'Cloud Institution'}
                ]
            }]
        }
        
        with open('render.yaml', 'w') as f:
            yaml.dump(render_config, f, default_flow_style=False)
        
        print("📋 Render configuration created (render.yaml)")
        print("🔗 Next steps:")
        print("   1. Push code to GitHub")
        print("   2. Connect repository at https://render.com")
        print("   3. Deploy as Web Service")
        
        return True
    
    def deploy_to_fly(self):
        """Deploy to Fly.io (free tier available)"""
        print("🪰 Setting up Fly.io deployment...")
        
        # Check if flyctl is installed
        if not self._check_command('flyctl'):
            print("📦 Installing Fly CLI...")
            subprocess.run(['curl', '-L', 'https://fly.io/install.sh'], check=True)
            print("⚠️  Please restart your terminal and run flyctl auth login")
            return False
        
        # Create fly.toml
        fly_config = """
app = "distributed-framework"
kill_signal = "SIGINT"
kill_timeout = 5
processes = []

[env]
  PORT = "8080"
  HOST = "0.0.0.0"
  NODE_ID = "fly-node-1"
  INSTITUTION_NAME = "Fly.io Institution"

[experimental]
  auto_rollback = true

[[services]]
  http_checks = []
  internal_port = 8080
  processes = ["app"]
  protocol = "tcp"
  script_checks = []
  [services.concurrency]
    hard_limit = 25
    soft_limit = 20
    type = "connections"

  [[services.ports]]
    force_https = true
    handlers = ["http"]
    port = 80

  [[services.ports]]
    handlers = ["tls", "http"]
    port = 443

  [[services.tcp_checks]]
    grace_period = "1s"
    interval = "15s"
    restart_limit = 0
    timeout = "2s"

  [[services.http_checks]]
    interval = "10s"
    grace_period = "5s"
    method = "get"
    path = "/health"
    protocol = "http"
    timeout = "2s"
    tls_skip_verify = false
"""
        
        with open('fly.toml', 'w') as f:
            f.write(fly_config.strip())
        
        # Create Dockerfile for Fly
        dockerfile_content = """
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data work

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["python", "run_server.py"]
"""
        
        with open('Dockerfile', 'w') as f:
            f.write(dockerfile_content.strip())
        
        print("📋 Fly.io configuration created")
        print("🔗 Next steps:")
        print("   1. flyctl auth login")
        print("   2. flyctl launch")
        print("   3. flyctl deploy")
        
        return True
    
    def deploy_to_heroku(self):
        """Deploy to Heroku"""
        print("🟣 Setting up Heroku deployment...")
        
        # Check if heroku CLI is installed
        if not self._check_command('heroku'):
            print("❌ Heroku CLI not found. Please install it first:")
            print("   https://devcenter.heroku.com/articles/heroku-cli")
            return False
        
        # Create Procfile
        with open('Procfile', 'w') as f:
            f.write("web: python run_server.py\n")
        
        # Create runtime.txt
        with open('runtime.txt', 'w') as f:
            f.write("python-3.11.0\n")
        
        # Create app.json for Heroku Button
        app_config = {
            "name": "Distributed Data Framework",
            "description": "Secure distributed data access and remote execution framework",
            "repository": "https://github.com/your-username/distributed-framework",
            "keywords": ["python", "data", "distributed", "research"],
            "env": {
                "NODE_ID": {
                    "description": "Unique node identifier",
                    "value": "heroku-node-1"
                },
                "INSTITUTION_NAME": {
                    "description": "Institution name",
                    "value": "Heroku Institution"
                },
                "SECRET_KEY": {
                    "description": "Secret key for JWT tokens",
                    "generator": "secret"
                }
            },
            "addons": ["heroku-postgresql:mini"],
            "buildpacks": [
                {"url": "heroku/python"}
            ]
        }
        
        with open('app.json', 'w') as f:
            json.dump(app_config, f, indent=2)
        
        print("📋 Heroku configuration created")
        print("🔗 Next steps:")
        print("   1. heroku login")
        print("   2. heroku create your-app-name")
        print("   3. git push heroku main")
        
        return True
    
    def setup_docker_compose_cloud(self):
        """Create docker-compose for cloud deployment"""
        print("🐳 Setting up Docker Compose for cloud...")
        
        compose_config = {
            'version': '3.8',
            'services': {
                'app': {
                    'build': '.',
                    'ports': ['8000:8000'],
                    'environment': [
                        'NODE_ID=docker-node-1',
                        'INSTITUTION_NAME=Docker Institution',
                        'HOST=0.0.0.0',
                        'PORT=8000'
                    ],
                    'volumes': [
                        './data:/app/data',
                        './work:/app/work'
                    ],
                    'restart': 'unless-stopped',
                    'healthcheck': {
                        'test': ['CMD', 'curl', '-f', 'http://localhost:8000/health'],
                        'interval': '30s',
                        'timeout': '10s',
                        'retries': 3
                    }
                },
                'nginx': {
                    'image': 'nginx:alpine',
                    'ports': ['80:80', '443:443'],
                    'volumes': [
                        './nginx/nginx.conf:/etc/nginx/nginx.conf:ro',
                        './certs:/etc/nginx/certs:ro'
                    ],
                    'depends_on': ['app'],
                    'restart': 'unless-stopped'
                }
            }
        }
        
        with open('docker-compose.cloud.yml', 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False)
        
        # Create production Dockerfile
        dockerfile_content = """
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    curl \\
    docker.io \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements*.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data work

# Create non-root user
RUN useradd -m -u 1001 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["python", "run_server.py"]
"""
        
        with open('Dockerfile.cloud', 'w') as f:
            f.write(dockerfile_content.strip())
        
        # Create nginx config
        nginx_dir = Path('nginx')
        nginx_dir.mkdir(exist_ok=True)
        
        nginx_config = r"""
events {
    worker_connections 1024;
}

http {
    upstream app {
        server app:8000;
    }
    
    server {
        listen 80;
        server_name _;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name _;
        
        ssl_certificate /etc/nginx/certs/cert.pem;
        ssl_certificate_key /etc/nginx/certs/key.pem;
        
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        
        client_max_body_size 200M;
        
        location / {
            proxy_pass http://app;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
        }
        
        location /health {
            proxy_pass http://app/health;
            access_log off;
        }
    }
}
"""
        
        with open(nginx_dir / 'nginx.conf', 'w') as f:
            f.write(nginx_config.strip())
        
        print("📋 Docker Compose cloud configuration created")
        print("🔗 Usage:")
        print("   docker-compose -f docker-compose.cloud.yml up -d")
        
        return True
    
    def create_vps_setup_script(self):
        """Create setup script for VPS deployment"""
        print("🖥️  Creating VPS setup script...")
        
        setup_script = r"""#!/bin/bash

# VPS Setup Script for Distributed Framework
# Run this on a fresh Ubuntu/Debian server

set -e

echo "🖥️  Setting up Distributed Framework on VPS..."

# Update system
apt-get update && apt-get upgrade -y

# Install dependencies
apt-get install -y \\
    python3 \\
    python3-pip \\
    python3-venv \\
    git \\
    curl \\
    nginx \\
    certbot \\
    python3-certbot-nginx \\
    docker.io \\
    docker-compose

# Start and enable services
systemctl start docker
systemctl enable docker
systemctl start nginx
systemctl enable nginx

# Add user to docker group
usermod -aG docker $USER

# Clone repository (replace with your repo)
cd /opt
git clone https://github.com/your-username/distributed-framework.git
cd distributed-framework

# Set up Python environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Create systemd service
cat > /etc/systemd/system/distributed-framework.service << EOF
[Unit]
Description=Distributed Data Framework
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/distributed-framework
Environment=PATH=/opt/distributed-framework/venv/bin
Environment=NODE_ID=vps-node-1
Environment=INSTITUTION_NAME=VPS Institution
Environment=HOST=0.0.0.0
Environment=PORT=8000
ExecStart=/opt/distributed-framework/venv/bin/python run_server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Set permissions
chown -R www-data:www-data /opt/distributed-framework

# Configure nginx
cat > /etc/nginx/sites-available/distributed-framework << EOF
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /health {
        proxy_pass http://localhost:8000/health;
        access_log off;
    }
}
EOF

# Enable site
ln -sf /etc/nginx/sites-available/distributed-framework /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test nginx config
nginx -t

# Start services
systemctl daemon-reload
systemctl start distributed-framework
systemctl enable distributed-framework
systemctl reload nginx

echo "✅ Setup complete!"
echo "🌐 Your server is running on http://$(curl -s ifconfig.me)"
echo "📋 Next steps:"
echo "   1. Set up SSL: certbot --nginx -d your-domain.com"
echo "   2. Configure firewall: ufw allow 80,443/tcp"
echo "   3. Check status: systemctl status distributed-framework"
"""
        
        with open('setup_vps.sh', 'w') as f:
            f.write(setup_script.strip())
        
        os.chmod('setup_vps.sh', 0o755)
        
        print("📋 VPS setup script created (setup_vps.sh)")
        print("🔗 Usage on VPS:")
        print("   curl -sSL https://your-repo.com/setup_vps.sh | bash")
        
        return True
    
    def _check_command(self, command):
        """Check if a command is available"""
        try:
            subprocess.run(['which', command], check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError:
            return False


def main():
    """CLI interface for cloud deployment"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Cloud Deployment Manager")
    parser.add_argument('provider', choices=['railway', 'render', 'fly', 'heroku', 'docker', 'vps'], 
                       help='Cloud provider')
    
    args = parser.parse_args()
    
    deployer = CloudDeployment()
    
    if args.provider == 'railway':
        deployer.deploy_to_railway()
    elif args.provider == 'render':
        deployer.deploy_to_render()
    elif args.provider == 'fly':
        deployer.deploy_to_fly()
    elif args.provider == 'heroku':
        deployer.deploy_to_heroku()
    elif args.provider == 'docker':
        deployer.setup_docker_compose_cloud()
    elif args.provider == 'vps':
        deployer.create_vps_setup_script()
    
    print(f"\n🎉 {args.provider.title()} deployment configuration ready!")


if __name__ == "__main__":
    main()