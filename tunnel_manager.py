#!/usr/bin/env python3
"""
Tunnel Manager - Better alternatives to ngrok
Supports Cloudflare tunnels, SSH tunnels, and localtunnel
"""
import subprocess
import sys
import time
import argparse
import os
import signal
import json
import re
from pathlib import Path

class TunnelManager:
    def __init__(self, tunnel_type="cloudflare", port=8000, ssh_host=None, ssh_user=None):
        self.tunnel_type = tunnel_type
        self.port = port
        self.ssh_host = ssh_host
        self.ssh_user = ssh_user or "root"
        self.process = None
        self.log_file = "tunnel.log"
        
    def setup_signal_handlers(self):
        """Set up signal handlers for clean shutdown"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print(f"\n🛑 Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)
    
    def start_cloudflare_tunnel(self):
        """Start Cloudflare tunnel (free, no signup required)"""
        print("🌟 Starting Cloudflare tunnel...")
        print("   ✅ No signup required")
        print("   ✅ Free forever")
        print("   ✅ Fast and reliable")
        
        try:
            # Use cloudflared if available, otherwise use curl method
            cmd = ["cloudflared", "tunnel", "--url", f"http://localhost:{self.port}"]
            
            with open(self.log_file, "w") as log:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            
            # Wait for tunnel to establish
            url = self.wait_for_cloudflare_url()
            if url:
                print(f"🎉 Cloudflare tunnel active: {url}")
                return url
            else:
                print("❌ Failed to get Cloudflare tunnel URL")
                return None
                
        except FileNotFoundError:
            print("📦 Installing cloudflared...")
            if self.install_cloudflared():
                return self.start_cloudflare_tunnel()
            else:
                print("❌ Failed to install cloudflared")
                return None
    
    def install_cloudflared(self):
        """Install cloudflared"""
        try:
            if sys.platform == "darwin":  # macOS
                subprocess.run(["brew", "install", "cloudflared"], check=True)
            elif sys.platform.startswith("linux"):
                # Download and install for Linux
                subprocess.run([
                    "wget", "-O", "/tmp/cloudflared",
                    "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
                ], check=True)
                subprocess.run(["chmod", "+x", "/tmp/cloudflared"], check=True)
                subprocess.run(["sudo", "mv", "/tmp/cloudflared", "/usr/local/bin/"], check=True)
            else:
                print("❌ Unsupported platform for automatic cloudflared installation")
                return False
            return True
        except subprocess.CalledProcessError:
            return False
    
    def wait_for_cloudflare_url(self, timeout=30):
        """Wait for Cloudflare tunnel URL to appear in logs"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if os.path.exists(self.log_file):
                    with open(self.log_file, 'r') as f:
                        content = f.read()
                        
                    # Look for Cloudflare tunnel URL
                    match = re.search(r'https://[a-zA-Z0-9-]*\.trycloudflare\.com', content)
                    if match:
                        return match.group(0)
                
                time.sleep(1)
            except Exception:
                time.sleep(1)
        
        return None
    
    def start_localtunnel(self):
        """Start localtunnel (requires npm)"""
        print("🌐 Starting localtunnel...")
        
        try:
            # Check if lt is installed
            subprocess.run(["lt", "--version"], check=True, capture_output=True)
        except (FileNotFoundError, subprocess.CalledProcessError):
            print("📦 Installing localtunnel...")
            try:
                subprocess.run(["npm", "install", "-g", "localtunnel"], check=True)
            except subprocess.CalledProcessError:
                print("❌ Failed to install localtunnel. Make sure npm is installed.")
                return None
        
        try:
            cmd = ["lt", "--port", str(self.port)]
            
            with open(self.log_file, "w") as log:
                self.process = subprocess.Popen(
                    cmd,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    text=True
                )
            
            # Wait for tunnel URL
            url = self.wait_for_localtunnel_url()
            if url:
                print(f"🎉 Localtunnel active: {url}")
                return url
            else:
                print("❌ Failed to get localtunnel URL")
                return None
                
        except Exception as e:
            print(f"❌ Error starting localtunnel: {e}")
            return None
    
    def wait_for_localtunnel_url(self, timeout=30):
        """Wait for localtunnel URL"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                if os.path.exists(self.log_file):
                    with open(self.log_file, 'r') as f:
                        content = f.read()
                    
                    # Look for localtunnel URL
                    match = re.search(r'https://[a-zA-Z0-9-]*\.loca\.lt', content)
                    if match:
                        return match.group(0)
                
                time.sleep(1)
            except Exception:
                time.sleep(1)
        
        return None
    
    def start_ssh_tunnel(self):
        """Start SSH tunnel"""
        if not self.ssh_host:
            print("❌ SSH host required for SSH tunnel")
            return None
        
        print(f"🔐 Starting SSH tunnel to {self.ssh_host}...")
        
        try:
            # Create reverse SSH tunnel
            cmd = [
                "ssh", "-R", f"80:localhost:{self.port}",
                f"{self.ssh_user}@{self.ssh_host}",
                "-N"  # Don't execute remote command
            ]
            
            self.process = subprocess.Popen(cmd)
            
            # SSH tunnels don't provide a public URL automatically
            # You need to configure your server to serve on port 80
            url = f"http://{self.ssh_host}"
            print(f"🎉 SSH tunnel active: {url}")
            print("   ⚠️  Make sure your server is configured to serve on port 80")
            
            return url
            
        except Exception as e:
            print(f"❌ Error starting SSH tunnel: {e}")
            return None
    
    def start(self):
        """Start the appropriate tunnel type"""
        self.setup_signal_handlers()
        
        print(f"🚀 Starting {self.tunnel_type} tunnel on port {self.port}...")
        
        if self.tunnel_type == "cloudflare":
            return self.start_cloudflare_tunnel()
        elif self.tunnel_type == "localtunnel":
            return self.start_localtunnel()
        elif self.tunnel_type == "ssh":
            return self.start_ssh_tunnel()
        else:
            print(f"❌ Unknown tunnel type: {self.tunnel_type}")
            return None
    
    def stop(self):
        """Stop the tunnel"""
        if self.process:
            print("🛑 Stopping tunnel...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None
    
    def wait(self):
        """Wait for tunnel to finish"""
        if self.process:
            try:
                self.process.wait()
            except KeyboardInterrupt:
                self.stop()


def main():
    parser = argparse.ArgumentParser(description="Tunnel Manager - Better alternatives to ngrok")
    parser.add_argument("--type", choices=["cloudflare", "localtunnel", "ssh"], 
                       default="cloudflare", help="Tunnel type")
    parser.add_argument("--port", type=int, default=8000, help="Local port to tunnel")
    parser.add_argument("--ssh-host", help="SSH host for SSH tunnel")
    parser.add_argument("--ssh-user", default="root", help="SSH user")
    
    args = parser.parse_args()
    
    print("🌍 Tunnel Manager")
    print("=" * 30)
    
    manager = TunnelManager(
        tunnel_type=args.type,
        port=args.port,
        ssh_host=args.ssh_host,
        ssh_user=args.ssh_user
    )
    
    url = manager.start()
    
    if url:
        print(f"\n✅ Tunnel established successfully!")
        print(f"📡 Public URL: {url}")
        print(f"🌐 Web Interface: {url}/docs")
        print(f"❤️  Health Check: {url}/health")
        print(f"\n⏳ Tunnel running... Press Ctrl+C to stop")
        
        # Save URL for other scripts
        with open("tunnel_url.txt", "w") as f:
            f.write(url)
        
        manager.wait()
    else:
        print("❌ Failed to establish tunnel")
        sys.exit(1)


if __name__ == "__main__":
    main()