# StimNet Deployment Guide

## Table of Contents
1. [Overview](#overview)
2. [Deployment Options](#deployment-options)
3. [Single Institution Deployment](#single-institution-deployment)
4. [Multi-Institutional Setup](#multi-institutional-setup)
5. [Configuration](#configuration)
6. [Domain & SSL Setup](#domain--ssl-setup)
7. [Data Management](#data-management)
8. [Security Best Practices](#security-best-practices)
9. [Monitoring & Maintenance](#monitoring--maintenance)

---

## Overview

This guide covers deploying StimNet Research Platform to production environments, moving from temporary Cloudflare tunnels to permanent hosting solutions. It also explains how multiple institutions can independently host their own StimNet instances.

### Current Setup (Temporary)
- **Cloudflare Quick Tunnels**: Free but temporary URLs that change on restart
- **Local Development**: Running on your local machine
- **Limited Access**: Random subdomains like `prescribed-none-dosage-breeds.trycloudflare.com`

### Production Setup (Permanent)
- **Dedicated Server**: Always-on cloud server
- **Custom Domain**: Professional URL like `stimnet.yourinstitution.edu`
- **SSL Certificate**: Automatic HTTPS encryption
- **Scalable**: Handle multiple concurrent users

---

## Deployment Options

### Option 1: Railway.app (Recommended for Quick Start)
**Best for**: Quick deployment, minimal configuration
- **Cost**: $5-20/month
- **Setup Time**: 15-30 minutes
- **Pros**: 
  - Automatic SSL certificates
  - Easy Git integration
  - Built-in monitoring
  - Free tier available for testing
- **Cons**: 
  - Can be more expensive at scale
  - Less control over infrastructure

### Option 2: Render.com
**Best for**: Free tier testing, simple deployments
- **Cost**: Free tier available, $7-25/month for production
- **Setup Time**: 20-40 minutes
- **Pros**:
  - Generous free tier
  - Automatic HTTPS
  - Easy database setup
- **Cons**:
  - Free tier has limitations (spins down after inactivity)
  - Slower cold starts on free tier

### Option 3: DigitalOcean
**Best for**: Full control, predictable pricing
- **Cost**: $6-12/month (basic droplet)
- **Setup Time**: 45-60 minutes
- **Pros**:
  - Full server control
  - Predictable pricing
  - Good documentation
  - Can scale easily
- **Cons**:
  - Requires more technical knowledge
  - Manual SSL setup (though Let's Encrypt makes it easy)

### Option 4: AWS/GCP/Azure
**Best for**: Enterprise deployments, high availability
- **Cost**: Variable ($10-100+/month depending on usage)
- **Setup Time**: 2-4 hours
- **Pros**:
  - Highly scalable
  - Enterprise features
  - Global CDN
- **Cons**:
  - Complex setup
  - Can be expensive
  - Requires cloud expertise

### Option 5: Institutional Server
**Best for**: Universities/hospitals with existing infrastructure
- **Cost**: Free (uses existing resources)
- **Setup Time**: 1-2 hours (depends on IT approval)
- **Pros**:
  - No additional cost
  - Institutional domain
  - IT support available
- **Cons**:
  - Requires IT approval
  - May have restrictions
  - Less flexibility

---

## Single Institution Deployment

### Prerequisites
- Git repository of StimNet code
- Account on chosen hosting platform
- Domain name (optional but recommended)
- SSH access (for VPS deployments)

### Step 1: Prepare Your Code

1. **Ensure all dependencies are listed**:
   ```bash
   pip freeze > requirements.txt
   ```

2. **Create a `.gitignore`** (if not exists):
   ```
   venv/
   __pycache__/
   *.pyc
   .env
   distributed_node.db
   uploads/
   work/
   *.log
   ```

3. **Push to Git**:
   ```bash
   git add .
   git commit -m "Production deployment ready"
   git push origin main
   ```

### Step 2: Deploy to Railway.app

#### A. Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub
3. Click "New Project"

#### B. Deploy from GitHub
1. Click "Deploy from GitHub repo"
2. Select your StimNet repository
3. Railway will auto-detect Python and start building

#### C. Configure Environment Variables
Add these in Railway dashboard → Variables:
```bash
NODE_ID=production-node-1
INSTITUTION_NAME=Your Institution Name
DATABASE_URL=sqlite:///./distributed_node.db
```

#### D. Set Up Custom Domain (Optional)
1. Go to Settings → Domains
2. Add your custom domain (e.g., `stimnet.yourinstitution.edu`)
3. Follow DNS configuration instructions
4. Railway automatically provisions SSL certificate

#### E. Configure Start Command
In Railway dashboard → Settings → Deploy:
```bash
python run_server.py
```

### Step 3: Deploy to Render.com

#### A. Create Render Account
1. Go to [render.com](https://render.com)
2. Sign up with GitHub
3. Click "New +" → "Web Service"

#### B. Connect Repository
1. Select your StimNet repository
2. Render will auto-detect settings

#### C. Configure Service
- **Name**: stimnet
- **Region**: Choose closest to users
- **Branch**: main
- **Root Directory**: (leave empty)
- **Environment**: Python 3
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python run_server.py`

#### D. Add Environment Variables
In Environment section:
```bash
NODE_ID=production-node-1
INSTITUTION_NAME=Your Institution Name
PORT=8000
```

#### E. Add Custom Domain
1. Go to Settings → Custom Domains
2. Add your domain
3. Configure DNS as instructed
4. SSL certificate auto-provisioned

### Step 4: Deploy to DigitalOcean Droplet

#### A. Create Droplet
1. Go to [digitalocean.com](https://digitalocean.com)
2. Create → Droplets
3. Choose:
   - **Image**: Ubuntu 22.04 LTS
   - **Plan**: Basic $6/month (1GB RAM)
   - **Region**: Closest to users
   - **Authentication**: SSH key (recommended)

#### B. Initial Server Setup
```bash
# SSH into your droplet
ssh root@your-droplet-ip

# Update system
apt update && apt upgrade -y

# Install Python and dependencies
apt install -y python3 python3-pip python3-venv git nginx

# Install cloudflared (optional, for tunnel alternative)
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared-linux-amd64.deb
```

#### C. Deploy StimNet
```bash
# Create app directory
mkdir -p /opt/stimnet
cd /opt/stimnet

# Clone repository
git clone https://github.com/yourusername/stimnet.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cat > .env << EOF
NODE_ID=production-node-1
INSTITUTION_NAME=Your Institution Name
DATABASE_URL=sqlite:///./distributed_node.db
EOF

# Test run
python run_server.py
```

#### D. Set Up Systemd Service
```bash
# Create service file
cat > /etc/systemd/system/stimnet.service << EOF
[Unit]
Description=StimNet Research Platform
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/stimnet
Environment="PATH=/opt/stimnet/venv/bin"
ExecStart=/opt/stimnet/venv/bin/python run_server.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
systemctl daemon-reload
systemctl enable stimnet
systemctl start stimnet
systemctl status stimnet
```

#### E. Set Up Nginx Reverse Proxy
```bash
# Create Nginx config
cat > /etc/nginx/sites-available/stimnet << EOF
server {
    listen 80;
    server_name stimnet.yourinstitution.edu;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Enable site
ln -s /etc/nginx/sites-available/stimnet /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

#### F. Set Up SSL with Let's Encrypt
```bash
# Install Certbot
apt install -y certbot python3-certbot-nginx

# Obtain certificate
certbot --nginx -d stimnet.yourinstitution.edu

# Certbot will auto-configure Nginx for HTTPS
# Certificates auto-renew via cron job
```

---

## Multi-Institutional Setup

### Architecture Overview

Each institution runs an **independent** StimNet instance with its own:
- Server and domain
- Database
- Data catalogs
- User authentication
- Uploaded files

```
┌─────────────────────────────────────────────────────────────┐
│                    Institution A (Harvard)                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  StimNet Server                                       │  │
│  │  • Domain: stimnet.harvard.edu                        │  │
│  │  • Data: Harvard's clinical data                      │  │
│  │  • Users: Harvard researchers                         │  │
│  │  • Database: harvard_stimnet.db                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                  Institution B (MIT)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  StimNet Server                                       │  │
│  │  • Domain: stimnet.mit.edu                            │  │
│  │  • Data: MIT's imaging data                           │  │
│  │  • Users: MIT researchers                             │  │
│  │  • Database: mit_stimnet.db                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              Institution C (Mass General)                    │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  StimNet Server                                       │  │
│  │  • Domain: stimnet.mgh.harvard.edu                    │  │
│  │  • Data: MGH patient data                             │  │
│  │  • Users: MGH clinicians                              │  │
│  │  • Database: mgh_stimnet.db                           │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Benefits of Multi-Institutional Setup

1. **Data Sovereignty**: Each institution controls its own data
2. **Compliance**: Easier to meet institutional data governance policies
3. **Independence**: No single point of failure
4. **Customization**: Each institution can customize for their needs
5. **Security**: Data never leaves institutional infrastructure

### Setup Instructions for Each Institution

#### Step 1: Clone Repository
```bash
git clone https://github.com/yourusername/stimnet.git
cd stimnet
```

#### Step 2: Configure Institution-Specific Settings

Edit `distributed_node/config.py`:
```python
# Institution A (Harvard)
NODE_ID = "harvard-node-1"
INSTITUTION_NAME = "Harvard Medical School"
DATABASE_URL = "sqlite:///./harvard_stimnet.db"
```

Edit `distributed_node/web_interface.py`:
```python
# Update page title
<title>StimNet - Harvard Medical School</title>
```

#### Step 3: Set Up Data Catalogs

Create institution-specific data in `data/data_manifest.json`:
```json
{
  "version": "1.0",
  "last_updated": "2025-01-15",
  "catalogs": [
    {
      "id": "harvard_clinical_trial",
      "name": "Harvard Clinical Trial Data",
      "description": "Harvard's Parkinson's disease clinical trial data",
      "institution": "Harvard Medical School",
      "data_type": "tabular",
      "privacy_level": "high",
      "min_cohort_size": 10,
      "files": [
        {
          "name": "subjects",
          "path": "data/catalogs/harvard_clinical_trial/subjects.csv",
          "type": "csv",
          "description": "Harvard subject demographics",
          "columns": [...],
          "record_count": 200
        }
      ]
    }
  ]
}
```

#### Step 4: Deploy to Institution's Server

Follow deployment steps from [Single Institution Deployment](#single-institution-deployment) using:
- Institution's domain (e.g., `stimnet.harvard.edu`)
- Institution's server infrastructure
- Institution-specific configuration

#### Step 5: Set Up Authentication (Optional but Recommended)

Each institution can implement its own authentication:

**Option A: Simple Username/Password**
Already implemented in StimNet. Edit `distributed_node/real_main.py`:
```python
@app.post("/api/v1/auth/token")
async def login(credentials: LoginRequest, db: Session = Depends(get_db)):
    # Replace with your authentication logic
    if credentials.username == "harvard_researcher" and credentials.password == "secure_password":
        # Generate JWT token
        token = create_access_token(data={"sub": credentials.username})
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Invalid credentials")
```

**Option B: LDAP/Active Directory**
Integrate with institutional authentication:
```python
import ldap

def authenticate_ldap(username, password):
    ldap_server = "ldap.harvard.edu"
    base_dn = "ou=People,dc=harvard,dc=edu"
    
    try:
        conn = ldap.initialize(f"ldap://{ldap_server}")
        conn.simple_bind_s(f"uid={username},{base_dn}", password)
        return True
    except:
        return False
```

**Option C: OAuth/SAML**
Integrate with institutional SSO:
```python
# Example using python-saml
from onelogin.saml2.auth import OneLogin_Saml2_Auth

@app.post("/api/v1/auth/saml")
async def saml_login(request: Request):
    # SAML authentication logic
    pass
```

### Cross-Institutional Collaboration (Future Enhancement)

While each institution runs independently, you can enable cross-institutional data sharing:

#### Option 1: Federated Queries
Institutions can query each other's data catalogs (with permission):
```python
# Query Harvard's data catalog from MIT's instance
harvard_catalogs = requests.get("https://stimnet.harvard.edu/api/v1/data-catalogs")
```

#### Option 2: Data Sharing Agreements
- Institutions sign data sharing agreements
- Each institution exposes specific datasets via API
- Researchers from other institutions can request access
- Access is logged and audited

#### Option 3: Common Data Model
- All institutions adopt same data schema
- Enables meta-analyses across institutions
- Privacy-preserving federated learning

---

## Configuration

### Environment Variables

Create a `.env` file in your project root:

```bash
# Node Configuration
NODE_ID=production-node-1
INSTITUTION_NAME=Your Institution Name

# Database
DATABASE_URL=sqlite:///./distributed_node.db
# For PostgreSQL: DATABASE_URL=postgresql://user:password@localhost/stimnet

# Server Configuration
HOST=0.0.0.0
PORT=8000

# Security
SECRET_KEY=your-secret-key-here-change-this
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# Data Directories
DATA_DIR=./data
UPLOADS_DIR=./uploads
WORK_DIR=./work

# Privacy Controls
MIN_COHORT_SIZE=10
MAX_SCRIPT_EXECUTION_TIME=300  # seconds

# Logging
LOG_LEVEL=INFO
LOG_FILE=stimnet.log
```

### Production Settings

Edit `distributed_node/config.py` for production:

```python
import os
from pathlib import Path

class Settings:
    # Application
    app_name: str = "StimNet Research Platform"
    version: str = "1.0.0"
    
    # Node Configuration
    node_id: str = os.getenv("NODE_ID", "production-node-1")
    institution_name: str = os.getenv("INSTITUTION_NAME", "Your Institution")
    
    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", 8000))
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./distributed_node.db")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "change-this-secret-key")
    jwt_algorithm: str = os.getenv("JWT_ALGORITHM", "HS256")
    jwt_expiration_hours: int = int(os.getenv("JWT_EXPIRATION_HOURS", 24))
    
    # Directories
    base_dir: Path = Path(__file__).parent.parent
    data_dir: Path = base_dir / "data"
    uploads_dir: Path = base_dir / "uploads"
    work_dir: Path = base_dir / "work"
    
    # Privacy
    min_cohort_size: int = int(os.getenv("MIN_COHORT_SIZE", 10))
    max_script_execution_time: int = int(os.getenv("MAX_SCRIPT_EXECUTION_TIME", 300))
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    log_file: str = os.getenv("LOG_FILE", "stimnet.log")

settings = Settings()
```

---

## Domain & SSL Setup

### Option 1: Automatic SSL (Railway/Render)
Both Railway and Render automatically provision SSL certificates when you add a custom domain. Just:
1. Add domain in platform dashboard
2. Configure DNS as instructed
3. Wait 5-10 minutes for SSL provisioning

### Option 2: Manual SSL with Let's Encrypt (VPS)

#### Step 1: Configure DNS
Add A record pointing to your server IP:
```
Type: A
Name: stimnet
Value: YOUR_SERVER_IP
TTL: 3600
```

#### Step 2: Install Certbot
```bash
apt install -y certbot python3-certbot-nginx
```

#### Step 3: Obtain Certificate
```bash
certbot --nginx -d stimnet.yourinstitution.edu
```

#### Step 4: Auto-Renewal
Certbot sets up auto-renewal automatically. Test with:
```bash
certbot renew --dry-run
```

---

## Data Management

### Data Organization

```
stimnet/
├── data/
│   ├── data_manifest.json          # Central catalog definition
│   └── catalogs/
│       ├── clinical_trial_data/
│       │   ├── subjects.csv
│       │   └── outcomes.csv
│       ├── imaging_data/
│       │   └── scan_metadata.csv
│       └── institution_specific/
│           └── custom_data.csv
├── uploads/
│   ├── scripts/                    # User-uploaded scripts
│   ├── data/                       # User-uploaded data files
│   └── uploaded_files.json        # Upload metadata
└── work/                           # Temporary job execution directories
    └── job_*/
```

### Backup Strategy

#### Automated Backups (Recommended)

Create backup script `/opt/stimnet/backup.sh`:
```bash
#!/bin/bash

BACKUP_DIR="/opt/stimnet/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
cp /opt/stimnet/distributed_node.db $BACKUP_DIR/db_$DATE.db

# Backup data directory
tar -czf $BACKUP_DIR/data_$DATE.tar.gz /opt/stimnet/data/

# Backup uploads
tar -czf $BACKUP_DIR/uploads_$DATE.tar.gz /opt/stimnet/uploads/

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

Make executable and add to cron:
```bash
chmod +x /opt/stimnet/backup.sh
crontab -e
# Add: 0 2 * * * /opt/stimnet/backup.sh >> /var/log/stimnet_backup.log 2>&1
```

#### Cloud Backups

Upload backups to cloud storage:
```bash
# Install AWS CLI or rclone
apt install -y awscli

# Configure AWS credentials
aws configure

# Upload to S3
aws s3 sync /opt/stimnet/backups/ s3://your-stimnet-backups/
```

---

## Security Best Practices

### 1. Authentication & Authorization

**Implement proper authentication**:
```python
# Use strong password hashing
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

**Implement role-based access control**:
```python
from enum import Enum

class UserRole(str, Enum):
    ADMIN = "admin"
    RESEARCHER = "researcher"
    VIEWER = "viewer"

def require_role(required_role: UserRole):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Check user role
            if current_user.role != required_role:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### 2. Input Validation

**Validate all user inputs**:
```python
from pydantic import BaseModel, validator

class ScriptSubmission(BaseModel):
    script_content: str
    
    @validator('script_content')
    def validate_script(cls, v):
        if len(v) > 100000:  # 100KB limit
            raise ValueError('Script too large')
        if 'eval(' in v or '__import__' in v:
            raise ValueError('Dangerous code detected')
        return v
```

### 3. Network Security

**Use HTTPS only**:
```python
# Force HTTPS in production
@app.middleware("http")
async def force_https(request: Request, call_next):
    if request.url.scheme != "https" and not request.url.hostname == "localhost":
        return RedirectResponse(
            url=str(request.url).replace("http://", "https://"),
            status_code=301
        )
    return await call_next(request)
```

**Set security headers**:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://stimnet.yourinstitution.edu"],  # Specific origins only
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

### 4. Script Execution Security

**Sandbox script execution**:
```python
import resource

def set_resource_limits():
    # Limit CPU time (300 seconds)
    resource.setrlimit(resource.RLIMIT_CPU, (300, 300))
    
    # Limit memory (2GB)
    resource.setrlimit(resource.RLIMIT_AS, (2 * 1024**3, 2 * 1024**3))
    
    # Limit file size (100MB)
    resource.setrlimit(resource.RLIMIT_FSIZE, (100 * 1024**2, 100 * 1024**2))
```

### 5. Audit Logging

**Log all sensitive operations**:
```python
import logging

audit_logger = logging.getLogger("audit")

def log_audit_event(user: str, action: str, details: dict):
    audit_logger.info(f"User: {user}, Action: {action}, Details: {details}")
    
# Example usage
log_audit_event(
    user="researcher@institution.edu",
    action="DATA_ACCESS",
    details={"dataset": "clinical_trial_data", "records": 150}
)
```

### 6. Data Encryption

**Encrypt sensitive data at rest**:
```python
from cryptography.fernet import Fernet

def encrypt_data(data: str, key: bytes) -> bytes:
    f = Fernet(key)
    return f.encrypt(data.encode())

def decrypt_data(encrypted_data: bytes, key: bytes) -> str:
    f = Fernet(key)
    return f.decrypt(encrypted_data).decode()
```

---

## Monitoring & Maintenance

### Health Checks

Implement health check endpoint:
```python
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.version,
        "node_id": settings.node_id,
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Monitoring with Prometheus (Optional)

Install Prometheus metrics:
```bash
pip install prometheus-fastapi-instrumentator
```

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### Log Rotation

Configure log rotation:
```bash
# Edit /etc/logrotate.d/stimnet
/opt/stimnet/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        systemctl reload stimnet
    endscript
}
```

### Performance Monitoring

Monitor server resources:
```bash
# Install monitoring tools
apt install -y htop iotop nethogs

# Check disk space
df -h

# Check memory usage
free -h

# Check running processes
ps aux | grep stimnet
```

---

## Troubleshooting

### Server Won't Start

1. Check logs:
   ```bash
   journalctl -u stimnet -n 100
   ```

2. Verify dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Check port availability:
   ```bash
   netstat -tulpn | grep 8000
   ```

### Database Errors

1. Check database file permissions:
   ```bash
   ls -la distributed_node.db
   chmod 644 distributed_node.db
   ```

2. Recreate database:
   ```bash
   rm distributed_node.db
   python run_server.py
   ```

### SSL Certificate Issues

1. Check certificate expiration:
   ```bash
   certbot certificates
   ```

2. Renew certificate:
   ```bash
   certbot renew
   ```

3. Check Nginx configuration:
   ```bash
   nginx -t
   systemctl reload nginx
   ```

---

## Support & Resources

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Uvicorn Documentation](https://www.uvicorn.org/)

### Community
- GitHub Issues: Report bugs and request features
- Discussions: Ask questions and share ideas

### Professional Support
For enterprise deployments, consider:
- Consulting services for custom integrations
- Training for your IT team
- Priority support and SLA

---

## Quick Reference

### Deployment Checklist

- [ ] Code pushed to Git repository
- [ ] Dependencies listed in `requirements.txt`
- [ ] Environment variables configured
- [ ] Domain DNS configured
- [ ] SSL certificate obtained
- [ ] Database initialized
- [ ] Data catalogs configured
- [ ] Authentication set up
- [ ] Backup strategy implemented
- [ ] Monitoring configured
- [ ] Security headers configured
- [ ] Logging configured
- [ ] Documentation updated

### Common Commands

```bash
# Start server
python run_server.py

# Start with systemd
systemctl start stimnet

# Check logs
journalctl -u stimnet -f

# Restart server
systemctl restart stimnet

# Backup database
cp distributed_node.db backups/db_$(date +%Y%m%d).db

# Update code
git pull origin main
systemctl restart stimnet
```

---

**Last Updated**: January 2025  
**Version**: 1.0  
**Maintained by**: StimNet Development Team

