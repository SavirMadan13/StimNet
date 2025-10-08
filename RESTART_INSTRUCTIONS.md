t# 🔄 StimNet Restart Instructions

## 🚀 Quick Restart (Choose One)

### **Option 1: Python Script (Recommended)**
```bash
python restart_all.py
```

### **Option 2: Bash Script**
```bash
./restart.sh
```

### **Option 3: Manual Commands**
```bash
# Stop everything
pkill -f "python.*run_server"
pkill -f "python.*tunnel_manager" 
pkill -f "cloudflared"

# Start server
source venv/bin/activate
python run_server.py &

# Start tunnel (in new terminal)
source venv/bin/activate  
python tunnel_manager.py --type cloudflare --port 8000 &
```

## 🛠️ **Available Commands**

### **Full Restart:**
```bash
python restart_all.py          # Complete restart
./restart.sh                   # Same thing, bash version
```

### **Stop Only:**
```bash
python restart_all.py --stop   # Stop all services
./restart.sh --stop            # Same thing, bash version
```

### **Status Check:**
```bash
python restart_all.py --status # Show current status
./restart.sh --status          # Same thing, bash version
```

### **Help:**
```bash
python restart_all.py --help   # Show help
./restart.sh --help            # Same thing, bash version
```

## 📊 **What Gets Restarted**

### **Processes Killed:**
- ✅ StimNet server (`run_server.py`)
- ✅ Tunnel manager (`tunnel_manager.py`)
- ✅ Cloudflared tunnel process
- ✅ Any uvicorn processes
- ✅ Any related Python processes

### **Services Started:**
- ✅ **StimNet Server** on port 8000
- ✅ **Cloudflare Tunnel** with new random URL
- ✅ **Real Script Execution** enabled
- ✅ **Web Interface** at root URL
- ✅ **API Documentation** at /docs

## 🎯 **After Restart**

You'll get output like:
```
🚀 StimNet Research Platform - Complete Restart
============================================================
🛑 Stopping all servers and tunnels...
✅ All processes stopped
📦 Checking dependencies...
✅ Dependencies OK
🚀 Starting StimNet server...
✅ Server started successfully!
🌐 Starting Cloudflare tunnel...
✅ Tunnel established: https://new-random-url.trycloudflare.com
🧪 Testing system functionality...
✅ Local server responding
✅ Tunnel working

📊 STIMNET STATUS
============================================================
🌐 Global Access: https://new-random-url.trycloudflare.com
🌐 Web Interface: https://new-random-url.trycloudflare.com
📚 API Docs: https://new-random-url.trycloudflare.com/docs
🏠 Local Access: http://localhost:8000
🏠 Local Web Interface: http://localhost:8000
📚 Local API Docs: http://localhost:8000/docs
❤️  Health Check: http://localhost:8000/health

🎯 How to Use:
1. Visit the web interface URL above
2. Click 'Load Demographics Example'
3. Click '🚀 Run Analysis'
4. See real results from 150 subjects!

🎉 StimNet restart complete!
Press Ctrl+C to stop all services
```

## 🆘 **Troubleshooting**

### **If restart fails:**
```bash
# Check what's running
ps aux | grep python | grep StimNet

# Manual cleanup
pkill -9 -f "python.*StimNet"
pkill -9 -f "cloudflared"

# Check port usage
lsof -i :8000

# Try restart again
python restart_all.py
```

### **If dependencies missing:**
```bash
# Reinstall dependencies
source venv/bin/activate
pip install -r requirements_core.txt
pip install pandas numpy scipy pydantic-settings requests
```

### **If tunnel fails:**
```bash
# Try different tunnel type
python tunnel_manager.py --type localtunnel

# Or just run locally
python restart_all.py --stop
source venv/bin/activate
python run_server.py
# Then visit: http://localhost:8000
```

## 🎉 **Success Indicators**

✅ **Server Working**: `curl http://localhost:8000/health` returns JSON  
✅ **Tunnel Working**: Random URL accessible from different WiFi  
✅ **Web Interface**: Beautiful form interface loads  
✅ **Real Execution**: Scripts process actual 150-subject dataset  
✅ **Cross-Network**: External IPs appear in server logs  

## 🔧 **Quick Commands Reference**

```bash
# Full restart with status
python restart_all.py

# Just stop everything  
python restart_all.py --stop

# Check if running
python restart_all.py --status

# Manual server start
source venv/bin/activate && python run_server.py

# Manual tunnel start
source venv/bin/activate && python tunnel_manager.py --type cloudflare --port 8000

# Get current tunnel URL
source venv/bin/activate && python get_public_url.py
```

**Your StimNet platform can now be restarted with a single command!** 🚀
