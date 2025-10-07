# 🌐 Tunnel Alternatives to ngrok

This document outlines better alternatives to ngrok for cross-machine communication in the distributed framework.

## 🚀 Quick Start

**The easiest way to get started:**

```bash
./launch.sh
```

This automatically:
- ✅ Sets up your Python environment
- ✅ Builds Docker containers
- ✅ Starts the server
- ✅ Creates a Cloudflare tunnel (free, stable)
- ✅ Tests the connection
- ✅ Provides you with a public URL

## 🔧 Available Alternatives

### 1. 🌟 Cloudflare Tunnels (RECOMMENDED)

**Pros:**
- ✅ Free forever
- ✅ More stable than ngrok
- ✅ No account required
- ✅ HTTPS by default
- ✅ Global CDN

**Usage:**
```bash
# Automatic setup
./launch.sh --tunnel cloudflare

# Manual setup
python tunnel_manager.py --type cloudflare
```

### 2. 🔐 SSH Tunnels (MOST SECURE)

**Pros:**
- ✅ Very secure
- ✅ No third-party service
- ✅ Full control
- ✅ Works with any server

**Requirements:**
- Remote server with SSH access
- Public IP or domain

**Usage:**
```bash
# Automatic setup
./launch.sh --tunnel ssh --ssh-host your-server.com

# Manual setup
python tunnel_manager.py --type ssh --ssh-host your-server.com --ssh-user ubuntu
```

### 3. 🌍 Localtunnel (SIMPLE)

**Pros:**
- ✅ Simple setup
- ✅ No account needed
- ✅ Custom subdomains

**Requirements:**
- Node.js/npm installed

**Usage:**
```bash
# Automatic setup
./launch.sh --tunnel localtunnel --subdomain myapp

# Manual setup
python tunnel_manager.py --type localtunnel --subdomain myapp
```

### 4. ☁️ Cloud Deployment (PRODUCTION)

For permanent, production-ready deployments:

```bash
# Railway (free tier)
python cloud_deploy.py railway

# Render (free tier)
python cloud_deploy.py render

# Fly.io (free tier)
python cloud_deploy.py fly

# Heroku
python cloud_deploy.py heroku

# VPS setup
python cloud_deploy.py vps
```

## 📋 Comparison Table

| Solution | Cost | Stability | Setup | Security | Speed |
|----------|------|-----------|-------|----------|-------|
| Cloudflare | Free | ⭐⭐⭐⭐⭐ | Easy | High | Fast |
| SSH Tunnel | Server cost | ⭐⭐⭐⭐⭐ | Medium | Very High | Fast |
| Localtunnel | Free | ⭐⭐⭐ | Easy | Medium | Medium |
| ngrok | Free/Paid | ⭐⭐⭐ | Easy | Medium | Medium |
| Cloud Deploy | Varies | ⭐⭐⭐⭐⭐ | Medium | High | Fast |

## 🎯 Use Cases

### 🏠 Development & Testing
```bash
# Quick local testing
./launch.sh --tunnel none

# Cross-network testing
./launch.sh --tunnel cloudflare
```

### 🏢 Multi-Institution Research
```bash
# Secure SSH tunnels
./launch.sh --tunnel ssh --ssh-host research-server.university.edu

# Or cloud deployment
python cloud_deploy.py railway
```

### 🎓 Conference Demos
```bash
# Reliable public access
./launch.sh --tunnel cloudflare --name conference-demo
```

### 🔬 Production Research
```bash
# Full cloud deployment
python cloud_deploy.py fly
```

## 🛠️ Advanced Configuration

### Custom Launch Options

```bash
# Custom port
./launch.sh --port 8080

# Development mode (auto-reload)
./launch.sh --dev

# Skip Docker setup
./launch.sh --no-docker

# SSH with custom key
./launch.sh --tunnel ssh --ssh-host server.com --ssh-key ~/.ssh/research_key
```

### Environment Variables

```bash
# Node configuration
export NODE_ID="my-research-node"
export INSTITUTION_NAME="My University"
export SECRET_KEY="your-secret-key"

# Then launch
./launch.sh
```

## 🔍 Monitoring & Debugging

### Check Status
```bash
# Get current public URL
python get_public_url.py

# Check server health
curl http://localhost:8000/health

# View logs
tail -f tunnel.log
tail -f server.log
```

### Troubleshooting

**Tunnel fails to start:**
```bash
# Check dependencies
./launch.sh --help

# Try different tunnel type
./launch.sh --tunnel localtunnel
```

**Connection issues:**
```bash
# Test local server first
curl http://localhost:8000/health

# Check firewall
sudo ufw status

# Verify tunnel logs
cat tunnel.log
```

## 🌍 Cross-Network Testing

### Test from Different Networks

1. **Different WiFi networks**
2. **Mobile data (4G/5G)**
3. **Different countries/regions**
4. **Colleague's computers**
5. **Cloud servers**

### Example Test Script

```python
import asyncio
from client_sdk import DistributedClient

async def test_remote():
    # Replace with your tunnel URL
    url = "https://abc123.trycloudflare.com"
    
    async with DistributedClient(url) as client:
        health = await client.health_check()
        print(f"Connected to remote node: {health}")

asyncio.run(test_remote())
```

## 🔒 Security Considerations

### For Public Tunnels
- ✅ Change default credentials
- ✅ Use HTTPS (automatic with Cloudflare)
- ✅ Enable rate limiting
- ✅ Monitor access logs

### For SSH Tunnels
- ✅ Use key-based authentication
- ✅ Disable password auth
- ✅ Configure firewall rules
- ✅ Use non-standard SSH ports

### For Cloud Deployments
- ✅ Set up proper authentication
- ✅ Use environment variables for secrets
- ✅ Enable HTTPS/TLS
- ✅ Configure monitoring

## 📚 Migration from ngrok

### Old Way (ngrok)
```bash
# Terminal 1
python run_server.py

# Terminal 2
ngrok http 8000

# Terminal 3
python get_public_url.py
```

### New Way (One Command)
```bash
./launch.sh
```

### Update Existing Scripts

Replace ngrok URLs in your scripts:
```python
# Old
url = "https://abc123.ngrok.io"

# New - get from tunnel manager
from tunnel_manager import TunnelManager
tunnel = TunnelManager()
url = tunnel.get_public_url()
```

## 🎉 Benefits Over ngrok

1. **More Reliable**: Cloudflare tunnels rarely disconnect
2. **Faster Setup**: One command starts everything
3. **Better Security**: SSH tunnels, proper HTTPS
4. **More Options**: Multiple tunnel types and cloud deployment
5. **No Rate Limits**: Most alternatives don't have ngrok's restrictions
6. **Production Ready**: Cloud deployment options for permanent use

## 🆘 Getting Help

If you encounter issues:

1. **Check the logs**: `tail -f tunnel.log`
2. **Test locally first**: `curl http://localhost:8000/health`
3. **Try different tunnel type**: `./launch.sh --tunnel localtunnel`
4. **Use cloud deployment**: `python cloud_deploy.py railway`

## 🔄 Legacy Support

The system still supports ngrok if you prefer:
```bash
# Start ngrok separately
ngrok http 8000

# Then run
python get_public_url.py
```

But we strongly recommend using the new launch script for a better experience!