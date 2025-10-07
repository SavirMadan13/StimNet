# Cross-Network Testing Guide

This guide shows you how to test the distributed framework across different WiFi networks and internet connections.

## 🌍 **Method 1: Ngrok Tunnel (Easiest)**

### **Step 1: Start Ngrok Tunnel**

With your server running on port 8000, open a new terminal and run:

```bash
ngrok http 8000
```

You'll see output like:
```
ngrok                                                                                                                                                                                                                     
                                                                                                                                                                                                                          
Build better APIs with ngrok. Early access: ngrok.com/early-access                                                                                                                                                       
                                                                                                                                                                                                                          
Session Status                online                                                                                                                                                                                      
Account                       your-email@example.com (Plan: Free)                                                                                                                                                        
Version                       3.30.0                                                                                                                                                                                      
Region                        United States (us)                                                                                                                                                                          
Latency                       -                                                                                                                                                                                           
Web Interface                 http://127.0.0.1:4040                                                                                                                                                                      
Forwarding                    https://abc123def456.ngrok-free.app -> http://localhost:8000                                                                                                                               
                                                                                                                                                                                                                          
Connections                   ttl     opn     rt1     rt5     p50     p90                                                                                                                                                 
                              0       0       0.00    0.00    0.00    0.00   
```

### **Step 2: Copy Your Public URL**

Look for the "Forwarding" line - your public URL will be something like:
`https://abc123def456.ngrok-free.app`

### **Step 3: Test from Any Device/Network**

Now you can test from:
- **Different WiFi networks**
- **Mobile data (4G/5G)**
- **Different countries**
- **Colleague's computers**
- **Cloud servers**

## 🧪 **Testing Commands**

### **Basic Health Check:**
```bash
# Replace with your actual ngrok URL
curl https://your-ngrok-url.ngrok-free.app/health
```

### **Web Interface:**
Open in any browser:
```
https://your-ngrok-url.ngrok-free.app/docs
```

### **Python Client Test:**
```python
import asyncio
from client_sdk import DistributedClient

async def test_remote():
    # Replace with your actual ngrok URL
    url = "https://your-ngrok-url.ngrok-free.app"
    
    async with DistributedClient(url) as client:
        health = await client.health_check()
        print(f"Connected to remote node: {health}")

asyncio.run(test_remote())
```

## 🌐 **Method 2: Cloud Deployment**

### **Deploy to Cloud Provider:**

#### **Option A: Railway (Free Tier)**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

#### **Option B: Heroku**
```bash
# Create Procfile
echo "web: python run_server.py" > Procfile

# Deploy
heroku create your-app-name
git push heroku main
```

#### **Option C: DigitalOcean App Platform**
```bash
# Create app.yaml
cat > app.yaml << EOF
name: distributed-framework
services:
- name: api
  source_dir: /
  github:
    repo: your-username/your-repo
    branch: main
  run_command: python run_server.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  http_port: 8000
EOF
```

## 🔧 **Method 3: VPS/Server Deployment**

### **Deploy to Your Own Server:**

```bash
# On your server (Ubuntu/Debian)
sudo apt update
sudo apt install python3 python3-pip python3-venv nginx

# Clone your code
git clone https://github.com/your-username/distributed-framework.git
cd distributed-framework

# Set up environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements_core.txt
pip install pandas numpy scipy pydantic-settings

# Configure for production
cat > .env << EOF
NODE_ID=production-node-1
NODE_NAME=Production Research Node
INSTITUTION_NAME=Your Institution
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
HOST=0.0.0.0
PORT=8000
EOF

# Start server
python run_server.py
```

### **Configure Nginx (Optional):**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📱 **Method 4: Mobile Testing**

### **Test from Mobile Device:**

1. **Install Termux** (Android) or **iSH** (iOS)
2. **Install Python and dependencies:**
   ```bash
   pkg install python
   pip install httpx asyncio
   ```

3. **Create mobile test script:**
   ```python
   # mobile_test.py
   import asyncio
   import httpx
   
   async def test_mobile():
       url = "https://your-ngrok-url.ngrok-free.app"
       
       async with httpx.AsyncClient() as client:
           # Health check
           response = await client.get(f"{url}/health")
           print(f"Health: {response.json()}")
           
           # Authentication
           auth_response = await client.post(
               f"{url}/api/v1/auth/token",
               data={"username": "demo", "password": "demo"}
           )
           token = auth_response.json()["access_token"]
           
           # Submit job
           headers = {"Authorization": f"Bearer {token}"}
           job_response = await client.post(
               f"{url}/api/v1/jobs",
               json={
                   "target_node_id": "node-1",
                   "data_catalog_name": "demo_dataset",
                   "script_type": "python",
                   "script_content": "result = {'mobile_test': True}"
               },
               headers=headers
           )
           
           print(f"Job submitted from mobile: {job_response.json()}")
   
   asyncio.run(test_mobile())
   ```

## 🌍 **Method 5: International Testing**

### **Test from Different Countries:**

Use cloud providers in different regions:

```bash
# AWS EC2 in different regions
aws ec2 run-instances --region us-west-2 --image-id ami-12345
aws ec2 run-instances --region eu-west-1 --image-id ami-67890
aws ec2 run-instances --region ap-southeast-1 --image-id ami-abcde

# Test latency and performance
curl -w "@curl-format.txt" -o /dev/null -s https://your-url.com/health
```

Create `curl-format.txt`:
```
     time_namelookup:  %{time_namelookup}\n
        time_connect:  %{time_connect}\n
     time_appconnect:  %{time_appconnect}\n
    time_pretransfer:  %{time_pretransfer}\n
       time_redirect:  %{time_redirect}\n
  time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
          time_total:  %{time_total}\n
```

## 🔒 **Security Considerations**

### **For Public Testing:**

1. **Change default credentials:**
   ```bash
   # Update authentication in your code
   # Use strong passwords
   # Enable rate limiting
   ```

2. **Use HTTPS:**
   ```bash
   # Ngrok provides HTTPS automatically
   # For custom domains, use Let's Encrypt
   certbot --nginx -d your-domain.com
   ```

3. **Firewall rules:**
   ```bash
   # Only allow necessary ports
   sudo ufw allow 80
   sudo ufw allow 443
   sudo ufw enable
   ```

## 📊 **Performance Testing Across Networks**

### **Latency Test Script:**
```python
import asyncio
import time
import httpx

async def test_latency(url, num_tests=10):
    async with httpx.AsyncClient() as client:
        times = []
        for i in range(num_tests):
            start = time.time()
            response = await client.get(f"{url}/health")
            end = time.time()
            times.append(end - start)
            print(f"Test {i+1}: {(end-start)*1000:.2f}ms")
        
        avg = sum(times) / len(times)
        print(f"Average latency: {avg*1000:.2f}ms")

# Test from different networks
asyncio.run(test_latency("https://your-ngrok-url.ngrok-free.app"))
```

## 🎯 **Real-World Scenarios**

### **Scenario 1: Multi-Institution Collaboration**
```python
# Institution A (Hospital)
NODE_ID=hospital-a PORT=8000 python run_server.py

# Institution B (University) 
NODE_ID=university-b PORT=8001 python run_server.py

# Institution C (Research Center)
NODE_ID=research-c PORT=8002 python run_server.py
```

### **Scenario 2: Home Office Testing**
```python
# Work from home, connect to office server
async with DistributedClient("https://office-server.company.com") as client:
    # Submit analysis to office data
    job_id = await client.submit_job(...)
```

### **Scenario 3: Conference Demo**
```python
# Live demo at conference with audience participation
# Audience connects via QR code to ngrok URL
# Real-time collaborative analysis
```

## 🚀 **Quick Start Commands**

```bash
# Terminal 1: Start your server
source venv/bin/activate
python run_server.py

# Terminal 2: Start ngrok tunnel  
ngrok http 8000

# Terminal 3: Test from "remote" location
python examples/remote_client_test.py https://your-ngrok-url.ngrok-free.app
```

## 📞 **Getting Help**

If you encounter issues:

1. **Check ngrok status:** Visit `http://localhost:4040`
2. **Test local first:** Ensure `http://localhost:8000/health` works
3. **Check firewall:** Ensure ports are open
4. **Verify credentials:** Test authentication separately
5. **Monitor logs:** Check server logs for errors

Your distributed framework is now ready for global testing! 🌍
