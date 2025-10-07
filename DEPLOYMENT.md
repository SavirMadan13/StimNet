# Deployment Guide

This guide covers deploying the Distributed Data Access and Remote Execution Framework in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Multi-Node Setup](#multi-node-setup)
6. [Security Configuration](#security-configuration)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended), macOS, or Windows with WSL2
- **Python**: 3.9 or higher
- **Docker**: 20.10+ (for script execution sandboxing)
- **Memory**: Minimum 4GB RAM, 8GB+ recommended
- **Storage**: At least 10GB free space for data and containers
- **Network**: Outbound internet access for package installation

### Required Services

- **Database**: PostgreSQL 12+ (SQLite for development)
- **Cache/Queue**: Redis 6.0+
- **Web Server**: Nginx (for production)
- **SSL Certificates**: Let's Encrypt or commercial certificates

## Local Development Setup

### 1. Clone and Install

```bash
# Clone the repository
git clone <repository-url>
cd distributed-framework

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file:

```bash
# Development configuration
NODE_ID=dev-node
NODE_NAME=Development Node
INSTITUTION_NAME=Development Institution
SECRET_KEY=dev-secret-key-change-in-production
DEBUG=true

# Database (SQLite for development)
DATABASE_URL=sqlite:///./dev_distributed_node.db

# Redis (optional for development)
REDIS_URL=redis://localhost:6379/0

# Data paths
DATA_ROOT=./data
WORK_DIR=./work

# Privacy settings
MIN_COHORT_SIZE=5
ENABLE_DIFFERENTIAL_PRIVACY=false

# Resource limits
MAX_EXECUTION_TIME=300
MAX_MEMORY_MB=2048
MAX_CPU_CORES=2
```

### 3. Initialize Database and Demo Data

```bash
# Set up demo data and catalogs
python examples/setup_demo_data.py

# Start the server
python -m distributed_node.main
```

### 4. Test the Installation

```bash
# In another terminal, run the examples
python examples/basic_usage.py
```

The server should be running at `http://localhost:8000` with API documentation at `http://localhost:8000/docs`.

## Production Deployment

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.9 python3.9-venv python3-pip nginx postgresql redis-server docker.io

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Create application user
sudo useradd -m -s /bin/bash distributed-app
sudo mkdir -p /opt/distributed-framework
sudo chown distributed-app:distributed-app /opt/distributed-framework
```

### 2. Application Deployment

```bash
# Switch to application user
sudo su - distributed-app

# Clone and setup application
cd /opt/distributed-framework
git clone <repository-url> .
python3.9 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Database Setup

```bash
# Create PostgreSQL database
sudo -u postgres createuser distributed_app
sudo -u postgres createdb distributed_framework -O distributed_app
sudo -u postgres psql -c "ALTER USER distributed_app PASSWORD 'secure_password';"
```

### 4. Production Environment Configuration

Create `/opt/distributed-framework/.env`:

```bash
# Production configuration
NODE_ID=prod-institution-node
NODE_NAME=Production Institution Node
INSTITUTION_NAME=My Research Institution
SECRET_KEY=very-secure-secret-key-generate-new-one
DEBUG=false

# Database
DATABASE_URL=postgresql://distributed_app:secure_password@localhost/distributed_framework

# Redis
REDIS_URL=redis://localhost:6379/0

# Network
HOST=0.0.0.0
PORT=8000
REQUIRE_TLS=true
TRUSTED_NODES=node1.partner.edu,node2.partner.org

# Data paths
DATA_ROOT=/opt/distributed-framework/data
WORK_DIR=/opt/distributed-framework/work

# Privacy settings
MIN_COHORT_SIZE=20
ENABLE_DIFFERENTIAL_PRIVACY=true
PRIVACY_EPSILON=1.0

# Resource limits
MAX_EXECUTION_TIME=3600
MAX_MEMORY_MB=8192
MAX_CPU_CORES=4

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/distributed-framework/app.log
ENABLE_AUDIT_LOG=true
AUDIT_LOG_FILE=/var/log/distributed-framework/audit.log
```

### 5. SSL Certificate Setup

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 6. Nginx Configuration

Create `/etc/nginx/sites-available/distributed-framework`:

```nginx
upstream distributed_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;

    # Proxy settings
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # API endpoints
    location / {
        proxy_pass http://distributed_app;
        proxy_timeout 300s;
        proxy_read_timeout 300s;
    }

    # Health check
    location /health {
        proxy_pass http://distributed_app;
        access_log off;
    }

    # Static files (if any)
    location /static/ {
        alias /opt/distributed-framework/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/distributed-framework /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 7. Systemd Service

Create `/etc/systemd/system/distributed-framework.service`:

```ini
[Unit]
Description=Distributed Framework Node
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=exec
User=distributed-app
Group=distributed-app
WorkingDirectory=/opt/distributed-framework
Environment=PATH=/opt/distributed-framework/venv/bin
ExecStart=/opt/distributed-framework/venv/bin/python -m distributed_node.main
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths=/opt/distributed-framework/data /opt/distributed-framework/work /var/log/distributed-framework

[Install]
WantedBy=multi-user.target
```

Start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable distributed-framework
sudo systemctl start distributed-framework
sudo systemctl status distributed-framework
```

## Docker Deployment

### 1. Update Docker Compose

Update `docker-compose.yml`:

```yaml
version: "3.9"

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/distributed_framework
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./data:/app/data
      - ./work:/app/work
      - /var/run/docker.sock:/var/run/docker.sock
    depends_on:
      - db
      - redis
    restart: unless-stopped

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=distributed_framework
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:6-alpine
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/nginx/certs:ro
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
```

### 2. Create Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p data work

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "-m", "distributed_node.main"]
```

### 3. Deploy with Docker

```bash
# Build and start services
docker-compose up -d

# View logs
docker-compose logs -f app

# Scale if needed
docker-compose up -d --scale app=3
```

## Multi-Node Setup

### 1. Node Discovery Configuration

Each node needs to know about other nodes. Create a `nodes.json` file:

```json
{
  "known_nodes": [
    {
      "node_id": "hospital-a",
      "name": "Hospital A",
      "institution": "Medical Center A",
      "endpoint_url": "https://node-a.medical-center.edu",
      "public_key": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
    },
    {
      "node_id": "hospital-b", 
      "name": "Hospital B",
      "institution": "Medical Center B",
      "endpoint_url": "https://node-b.research-hospital.org",
      "public_key": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
    }
  ]
}
```

### 2. Network Configuration

Ensure nodes can communicate:

```bash
# Test connectivity
curl -k https://partner-node.example.com/health

# Check DNS resolution
nslookup partner-node.example.com

# Test specific ports
telnet partner-node.example.com 443
```

### 3. Firewall Configuration

```bash
# Allow HTTPS traffic
sudo ufw allow 443/tcp

# Allow specific IPs only (recommended)
sudo ufw allow from 192.168.1.100 to any port 443
```

## Security Configuration

### 1. Generate Secure Keys

```bash
# Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate RSA key pair for node authentication
openssl genrsa -out private_key.pem 2048
openssl rsa -in private_key.pem -pubout -out public_key.pem
```

### 2. Configure mTLS (Optional)

For enhanced security between nodes:

```bash
# Create CA certificate
openssl req -new -x509 -days 365 -key ca-key.pem -out ca-cert.pem

# Create client certificate
openssl req -new -key client-key.pem -out client-cert.csr
openssl x509 -req -in client-cert.csr -CA ca-cert.pem -CAkey ca-key.pem -out client-cert.pem
```

Update Nginx configuration for mTLS:

```nginx
server {
    # ... existing configuration ...
    
    # Client certificate verification
    ssl_client_certificate /etc/nginx/certs/ca-cert.pem;
    ssl_verify_client on;
    
    location /api/ {
        # Only allow authenticated clients
        if ($ssl_client_verify != SUCCESS) {
            return 403;
        }
        proxy_pass http://distributed_app;
    }
}
```

### 3. Security Hardening

```bash
# Disable root login
sudo passwd -l root

# Configure fail2ban
sudo apt install fail2ban
sudo systemctl enable fail2ban

# Set up automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

## Monitoring and Logging

### 1. Application Logging

Configure structured logging in production:

```python
# In your .env file
LOG_LEVEL=INFO
LOG_FILE=/var/log/distributed-framework/app.log
ENABLE_AUDIT_LOG=true
AUDIT_LOG_FILE=/var/log/distributed-framework/audit.log
```

### 2. System Monitoring

Install monitoring tools:

```bash
# Install Prometheus Node Exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.3.1/node_exporter-1.3.1.linux-amd64.tar.gz
tar xvfz node_exporter-1.3.1.linux-amd64.tar.gz
sudo cp node_exporter-1.3.1.linux-amd64/node_exporter /usr/local/bin/
sudo useradd -rs /bin/false node_exporter
```

Create systemd service for node_exporter:

```ini
[Unit]
Description=Node Exporter
After=network.target

[Service]
User=node_exporter
Group=node_exporter
Type=simple
ExecStart=/usr/local/bin/node_exporter

[Install]
WantedBy=multi-user.target
```

### 3. Log Rotation

Configure logrotate:

```bash
sudo tee /etc/logrotate.d/distributed-framework << EOF
/var/log/distributed-framework/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 distributed-app distributed-app
    postrotate
        systemctl reload distributed-framework
    endscript
}
EOF
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test connection
psql -h localhost -U distributed_app -d distributed_framework

# Check logs
sudo tail -f /var/log/postgresql/postgresql-13-main.log
```

#### 2. Docker Permission Issues

```bash
# Add user to docker group
sudo usermod -aG docker distributed-app

# Restart session or run
newgrp docker

# Test Docker access
docker ps
```

#### 3. SSL Certificate Issues

```bash
# Check certificate validity
openssl x509 -in /etc/letsencrypt/live/your-domain.com/fullchain.pem -text -noout

# Renew certificate
sudo certbot renew --dry-run

# Check Nginx configuration
sudo nginx -t
```

#### 4. Memory Issues

```bash
# Check memory usage
free -h
htop

# Check application memory usage
ps aux | grep python

# Adjust resource limits in .env
MAX_MEMORY_MB=4096
```

#### 5. Network Connectivity

```bash
# Test node connectivity
curl -k https://partner-node.example.com/health

# Check firewall
sudo ufw status

# Check DNS
nslookup partner-node.example.com
```

### Performance Tuning

#### 1. Database Optimization

```sql
-- PostgreSQL tuning
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
SELECT pg_reload_conf();
```

#### 2. Redis Optimization

```bash
# In /etc/redis/redis.conf
maxmemory 512mb
maxmemory-policy allkeys-lru
```

#### 3. Application Tuning

```bash
# In .env file
MAX_CPU_CORES=4
MAX_MEMORY_MB=8192
MAX_EXECUTION_TIME=3600
```

### Backup and Recovery

#### 1. Database Backup

```bash
# Create backup script
#!/bin/bash
BACKUP_DIR="/opt/backups/distributed-framework"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
pg_dump -h localhost -U distributed_app distributed_framework > $BACKUP_DIR/db_backup_$DATE.sql
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Keep only last 30 days
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +30 -delete
```

#### 2. Data Backup

```bash
# Backup data directory
tar -czf /opt/backups/data_backup_$(date +%Y%m%d).tar.gz /opt/distributed-framework/data/
```

#### 3. Configuration Backup

```bash
# Backup configuration
cp /opt/distributed-framework/.env /opt/backups/env_backup_$(date +%Y%m%d)
```

This deployment guide should help you set up the distributed framework in various environments. Remember to customize the configuration based on your specific requirements and security policies.