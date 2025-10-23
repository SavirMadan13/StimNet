# StimNet Current Startup Guide

## Quick Start Instructions

This guide provides step-by-step instructions to start the StimNet server and get a public URL for remote access.

### Prerequisites

- Python 3.13+ with virtual environment
- Cloudflare tunnel (cloudflared) installed
- StimNet project directory

### 1. Start the Server

```bash
# Navigate to the StimNet directory
cd /path/to/StimNet

# Activate the virtual environment
source venv/bin/activate

# Start the server
python -m distributed_node.real_main
```

**Expected Output:**
```
INFO:     Started server process [XXXXX]
INFO:     Waiting for application startup.
2025-10-23 10:11:51,432 - distributed_node.real_main - INFO - Starting StimNet Research Platform v1.0.0 - REAL EXECUTION MODE
2025-10-23 10:11:51,432 - distributed_node.real_main - INFO - Node ID: default-node
2025-10-23 10:11:51,432 - distributed_node.real_main - INFO - Institution: Default Institution
2025-10-23 10:11:51,432 - distributed_node.real_main - INFO - 🚀 Real script execution enabled!
2025-10-23 10:11:51,436 - distributed_node.database - INFO - Database tables created successfully
2025-10-23 10:11:51,444 - distributed_node.real_main - INFO - Application startup complete
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 2. Get Public URL (in a new terminal)

```bash
# Navigate to the StimNet directory
cd /path/to/StimNet

# Activate the virtual environment
source venv/bin/activate

# Start Cloudflare tunnel
cloudflared tunnel --url http://localhost:8000 --logfile tunnel.log
```

**Expected Output:**
```
2025-10-23T08:39:03Z INF +--------------------------------------------------------------------------------------------+
2025-10-23T08:39:03Z INF |  Your quick Tunnel has been created! Visit it at (it may take some time to be reachable):  |
2025-10-23T08:39:03Z INF |  https://your-unique-url.trycloudflare.com                            |
2025-10-10-23T08:39:03Z INF +--------------------------------------------------------------------------------------------+
```

### 3. Alternative: Use Helper Script

If you have the helper script available:

```bash
cd /path/to/StimNet
source venv/bin/activate
python get_public_url.py
```

### 4. Test the Setup

1. **Local Access**: Visit `http://localhost:8000` in your browser
2. **Public Access**: Visit the Cloudflare tunnel URL (e.g., `https://your-unique-url.trycloudflare.com`)
3. **Health Check**: Visit `http://localhost:8000/health` to verify the server is running

### 5. Verify Everything is Working

The server should show:
- ✅ Database tables created successfully
- ✅ Real script execution enabled
- ✅ Application startup complete
- ✅ Uvicorn running on http://0.0.0.0:8000

The tunnel should show:
- ✅ Tunnel connection established
- ✅ Public URL generated
- ✅ No connection errors

## Troubleshooting

### Server Won't Start

1. **Check if port 8000 is already in use:**
   ```bash
   lsof -i :8000
   ```

2. **Kill existing processes:**
   ```bash
   pkill -f "python.*real_main"
   ```

3. **Check virtual environment:**
   ```bash
   which python
   source venv/bin/activate
   which python
   ```

### Tunnel Connection Issues

1. **Restart tunnel:**
   ```bash
   pkill -f "cloudflared"
   cloudflared tunnel --url http://localhost:8000
   ```

2. **Check tunnel logs:**
   ```bash
   tail -f tunnel.log
   ```

3. **Verify server is running:**
   ```bash
   curl http://localhost:8000/health
   ```

### Database Issues

If you see database errors:
1. **Check database file exists:**
   ```bash
   ls -la distributed_node.db
   ```

2. **Restart server to recreate database:**
   ```bash
   rm distributed_node.db
   python -m distributed_node.real_main
   ```

## Background Threading Status

The current setup includes the **completely fixed background threading system** that:

- ✅ Uses fresh database sessions for each operation
- ✅ Prevents database transaction errors
- ✅ Handles job execution reliably
- ✅ Supports concurrent job processing
- ✅ Provides proper error handling and logging

## Security Notes

- The tunnel URL is temporary and will expire
- For production use, consider setting up a permanent Cloudflare tunnel
- The server runs on all interfaces (0.0.0.0:8000) - ensure firewall settings are appropriate

## Next Steps

Once both the server and tunnel are running:

1. **Access the web interface** via the public URL
2. **Submit analysis requests** through the web interface
3. **Monitor job execution** in the server logs
4. **Share the public URL** with collaborators for remote access

## Support

If you encounter issues:
1. Check the server logs for error messages
2. Verify the tunnel connection status
3. Ensure all dependencies are installed
4. Check that the virtual environment is activated
