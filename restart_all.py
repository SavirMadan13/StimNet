#!/usr/bin/env python3
"""
Complete restart script for StimNet Research Platform
Kills all servers and restarts them cleanly
"""
import subprocess
import time
import sys
import os
import signal
from pathlib import Path

def run_command(cmd, description="", ignore_errors=True):
    """Run a command and handle errors"""
    print(f"🔧 {description}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0 and not ignore_errors:
            print(f"❌ Error: {result.stderr}")
            return False
        elif result.stdout.strip():
            print(f"   {result.stdout.strip()}")
        return True
    except Exception as e:
        if not ignore_errors:
            print(f"❌ Exception: {e}")
            return False
        return True

def kill_processes():
    """Kill all related processes"""
    print("🛑 Stopping all servers and tunnels...")
    
    # List of process patterns to kill
    patterns = [
        "python.*run_server",
        "python.*tunnel_manager", 
        "uvicorn.*distributed_node",
        "cloudflared.*tunnel",
        "python.*real_main",
        "python.*simple_main"
    ]
    
    for pattern in patterns:
        run_command(f"pkill -f '{pattern}'", f"Killing {pattern}", ignore_errors=True)
    
    # Give processes time to shut down gracefully
    print("⏳ Waiting for graceful shutdown...")
    time.sleep(3)
    
    # Force kill if needed
    run_command("pkill -9 -f 'python.*StimNet'", "Force killing remaining processes", ignore_errors=True)
    
    print("✅ All processes stopped")

def check_dependencies():
    """Check if all dependencies are available"""
    print("📦 Checking dependencies...")
    
    # Check Python virtual environment
    if not os.path.exists("venv/bin/activate"):
        print("❌ Virtual environment not found. Please run: python3 -m venv venv")
        return False
    
    # Check if required packages are installed
    result = subprocess.run(
        "source venv/bin/activate && python -c 'import fastapi, uvicorn, pandas'",
        shell=True, capture_output=True
    )
    
    if result.returncode != 0:
        print("❌ Required packages not installed. Please run:")
        print("   source venv/bin/activate")
        print("   pip install -r requirements_core.txt")
        print("   pip install pandas numpy scipy pydantic-settings requests")
        return False
    
    print("✅ Dependencies OK")
    return True

def start_server():
    """Start the main server"""
    print("🚀 Starting StimNet server...")
    
    # Start server in background
    server_process = subprocess.Popen([
        "bash", "-c", "cd /Users/savirmadan/Development/StimNet && source venv/bin/activate && python run_server.py"
    ])
    
    # Wait for server to start
    print("⏳ Waiting for server to start...")
    for i in range(10):
        time.sleep(1)
        try:
            result = subprocess.run(
                "curl -s http://localhost:8000/health", 
                shell=True, capture_output=True
            )
            if result.returncode == 0:
                print("✅ Server started successfully!")
                return server_process
        except:
            pass
        print(f"   Waiting... ({i+1}/10)")
    
    print("❌ Server failed to start")
    return None

def start_tunnel():
    """Start the Cloudflare tunnel"""
    print("🌐 Starting Cloudflare tunnel...")
    
    # Start tunnel with direct cloudflared command (more reliable)
    tunnel_process = subprocess.Popen([
        "cloudflared", "tunnel", "--url", "http://localhost:8000"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    # Wait for tunnel to establish
    print("⏳ Waiting for tunnel to establish...")
    tunnel_url = None
    
    for i in range(20):
        time.sleep(1)
        
        # Check if process is still running
        if tunnel_process.poll() is not None:
            print("❌ Tunnel process died")
            break
        
        # Try to get URL from our detection script
        try:
            result = subprocess.run(
                "source venv/bin/activate && python get_public_url.py",
                shell=True, capture_output=True, text=True, cwd="/Users/savirmadan/Development/StimNet"
            )
            if "📡 Public URL:" in result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    if "📡 Public URL:" in line:
                        tunnel_url = line.split("📡 Public URL: ")[1].strip()
                        print(f"✅ Tunnel established: {tunnel_url}")
                        return tunnel_process, tunnel_url
        except:
            pass
        
        # Also check tunnel.log if it exists
        try:
            if os.path.exists("tunnel.log"):
                with open("tunnel.log", "r") as f:
                    content = f.read()
                    import re
                    match = re.search(r'https://[a-zA-Z0-9-]*\.trycloudflare\.com', content)
                    if match:
                        tunnel_url = match.group(0)
                        print(f"✅ Tunnel found in logs: {tunnel_url}")
                        return tunnel_process, tunnel_url
        except:
            pass
        
        if i % 5 == 0:
            print(f"   Still waiting... ({i+1}/20)")
    
    if tunnel_url:
        print(f"✅ Tunnel established: {tunnel_url}")
        return tunnel_process, tunnel_url
    else:
        print("⚠️  Tunnel may still be establishing (check manually)")
        return tunnel_process, None

def test_system():
    """Test that everything is working"""
    print("🧪 Testing system functionality...")
    
    # Test local server
    result = subprocess.run("curl -s http://localhost:8000/health", shell=True, capture_output=True)
    if result.returncode == 0:
        print("✅ Local server responding")
    else:
        print("❌ Local server not responding")
        return False
    
    # Test tunnel
    try:
        result = subprocess.run(
            "source venv/bin/activate && python get_public_url.py",
            shell=True, capture_output=True, text=True
        )
        if "Connection successful!" in result.stdout:
            print("✅ Tunnel working")
        else:
            print("⚠️  Tunnel may still be establishing...")
    except:
        print("⚠️  Tunnel status unknown")
    
    return True

def show_status():
    """Show current system status"""
    print("\n" + "="*60)
    print("📊 STIMNET RESEARCH PLATFORM - STATUS")
    print("="*60)
    
    # Get current URLs
    try:
        result = subprocess.run(
            "source venv/bin/activate && python get_public_url.py",
            shell=True, capture_output=True, text=True
        )
        
        if "📡 Public URL:" in result.stdout:
            lines = result.stdout.split('\n')
            for line in lines:
                if "📡 Public URL:" in line:
                    url = line.split("📡 Public URL: ")[1].strip()
                    print(f"🌐 Global Access: {url}")
                    print(f"🌐 Web Interface: {url}")
                    print(f"📚 API Docs: {url}/docs")
                    break
    except:
        pass
    
    print(f"🏠 Local Access: http://localhost:8000")
    print(f"🏠 Local Web Interface: http://localhost:8000")
    print(f"📚 Local API Docs: http://localhost:8000/docs")
    print(f"❤️  Health Check: http://localhost:8000/health")
    
    print(f"\n🎯 How to Use:")
    print(f"1. Visit the web interface URL above")
    print(f"2. Click 'Load Demographics Example'")
    print(f"3. Click '🚀 Run Analysis'")
    print(f"4. See real results from 150 subjects!")
    
    print(f"\n🔧 Management:")
    print(f"- Restart everything: python restart_all.py")
    print(f"- Stop everything: python restart_all.py --stop")
    print(f"- Status check: python restart_all.py --status")

def main():
    """Main restart function"""
    
    # Handle command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--stop":
            print("🛑 Stopping all StimNet services...")
            kill_processes()
            print("✅ All services stopped")
            return
        elif sys.argv[1] == "--status":
            show_status()
            return
        elif sys.argv[1] == "--help":
            print("StimNet Restart Script")
            print("Usage:")
            print("  python restart_all.py          # Full restart")
            print("  python restart_all.py --stop   # Stop all services")
            print("  python restart_all.py --status # Show status")
            print("  python restart_all.py --help   # Show this help")
            return
    
    print("🚀 StimNet Research Platform - Complete Restart")
    print("="*60)
    
    # Step 1: Kill all existing processes
    kill_processes()
    
    # Step 2: Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed. Please fix dependencies first.")
        sys.exit(1)
    
    # Step 3: Start server
    server_process = start_server()
    if not server_process:
        print("❌ Failed to start server")
        sys.exit(1)
    
    # Step 4: Start tunnel
    tunnel_process, tunnel_url = start_tunnel()
    
    # Step 5: Test system
    if test_system():
        print("✅ System restart successful!")
    else:
        print("⚠️  System may have issues")
    
    # Step 6: Show status
    show_status()
    
    print(f"\n🎉 StimNet is now running!")
    print(f"Press Ctrl+C to stop all services")
    
    # Keep script running and handle Ctrl+C
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n🛑 Shutting down StimNet...")
        
        # Kill processes
        if server_process:
            server_process.terminate()
        if tunnel_process:
            tunnel_process.terminate()
        
        kill_processes()
        print("✅ StimNet stopped")

if __name__ == "__main__":
    main()
