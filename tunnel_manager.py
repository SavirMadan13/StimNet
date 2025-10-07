#!/usr/bin/env python3
"""
Alternative tunnel solutions to replace ngrok
Supports SSH tunnels, Cloudflare tunnels, and cloud deployment
"""
import subprocess
import requests
import json
import time
import sys
import os
import signal
import threading
from pathlib import Path
from typing import Optional, Dict, Any
import tempfile

class TunnelManager:
    """Manages different types of tunnels for cross-machine communication"""
    
    def __init__(self):
        self.tunnel_process = None
        self.tunnel_type = None
        self.public_url = None
        self.local_port = 8000
        
    def setup_ssh_tunnel(self, remote_host: str, remote_port: int = 80, 
                        ssh_user: str = None, ssh_key: str = None) -> Optional[str]:
        """
        Set up SSH reverse tunnel
        Args:
            remote_host: Remote server hostname/IP
            remote_port: Port on remote server to bind to
            ssh_user: SSH username (defaults to current user)
            ssh_key: Path to SSH private key
        """
        try:
            ssh_user = ssh_user or os.getenv('USER', 'ubuntu')
            
            # Build SSH command
            ssh_cmd = ['ssh', '-N', '-R', f'{remote_port}:localhost:{self.local_port}']
            
            if ssh_key:
                ssh_cmd.extend(['-i', ssh_key])
            
            ssh_cmd.extend(['-o', 'StrictHostKeyChecking=no'])
            ssh_cmd.extend(['-o', 'ServerAliveInterval=30'])
            ssh_cmd.extend(['-o', 'ServerAliveCountMax=3'])
            ssh_cmd.append(f'{ssh_user}@{remote_host}')
            
            print(f"🔗 Starting SSH tunnel to {remote_host}:{remote_port}")
            print(f"   Command: {' '.join(ssh_cmd)}")
            
            self.tunnel_process = subprocess.Popen(
                ssh_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Give it a moment to establish
            time.sleep(3)
            
            if self.tunnel_process.poll() is None:
                self.tunnel_type = "ssh"
                self.public_url = f"http://{remote_host}:{remote_port}"
                print(f"✅ SSH tunnel established!")
                print(f"📡 Public URL: {self.public_url}")
                return self.public_url
            else:
                stderr = self.tunnel_process.stderr.read().decode()
                print(f"❌ SSH tunnel failed: {stderr}")
                return None
                
        except Exception as e:
            print(f"❌ SSH tunnel error: {e}")
            return None
    
    def setup_cloudflare_tunnel(self, tunnel_name: str = None) -> Optional[str]:
        """
        Set up Cloudflare tunnel (requires cloudflared binary)
        """
        try:
            # Check if cloudflared is installed
            result = subprocess.run(['which', 'cloudflared'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                print("❌ cloudflared not found. Installing...")
                self._install_cloudflared()
            
            tunnel_name = tunnel_name or f"distributed-node-{int(time.time())}"
            
            # Create tunnel
            print(f"🔗 Creating Cloudflare tunnel: {tunnel_name}")
            
            cmd = [
                'cloudflared', 'tunnel', 
                '--url', f'http://localhost:{self.local_port}',
                '--name', tunnel_name
            ]
            
            self.tunnel_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for tunnel URL
            url = self._wait_for_cloudflare_url()
            if url:
                self.tunnel_type = "cloudflare"
                self.public_url = url
                print(f"✅ Cloudflare tunnel established!")
                print(f"📡 Public URL: {self.public_url}")
                return self.public_url
            else:
                print("❌ Failed to get Cloudflare tunnel URL")
                return None
                
        except Exception as e:
            print(f"❌ Cloudflare tunnel error: {e}")
            return None
    
    def _install_cloudflared(self):
        """Install cloudflared binary"""
        try:
            import platform
            system = platform.system().lower()
            arch = platform.machine().lower()
            
            if system == "linux":
                if "x86_64" in arch or "amd64" in arch:
                    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
                elif "arm64" in arch or "aarch64" in arch:
                    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
                else:
                    raise Exception(f"Unsupported architecture: {arch}")
            elif system == "darwin":  # macOS
                if "arm64" in arch:
                    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz"
                else:
                    url = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz"
            else:
                raise Exception(f"Unsupported system: {system}")
            
            print(f"📥 Downloading cloudflared from {url}")
            
            # Download to /usr/local/bin or ~/bin
            bin_dir = Path.home() / "bin"
            bin_dir.mkdir(exist_ok=True)
            cloudflared_path = bin_dir / "cloudflared"
            
            # Download
            subprocess.run(['curl', '-L', url, '-o', str(cloudflared_path)], check=True)
            subprocess.run(['chmod', '+x', str(cloudflared_path)], check=True)
            
            # Add to PATH if not already there
            if str(bin_dir) not in os.environ.get('PATH', ''):
                print(f"⚠️  Add {bin_dir} to your PATH:")
                print(f"   export PATH=\"{bin_dir}:$PATH\"")
            
            print("✅ cloudflared installed successfully!")
            
        except Exception as e:
            print(f"❌ Failed to install cloudflared: {e}")
            print("Please install manually: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/")
            raise
    
    def _wait_for_cloudflare_url(self, timeout: int = 30) -> Optional[str]:
        """Wait for Cloudflare tunnel to provide URL"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.tunnel_process.poll() is not None:
                # Process died
                stderr = self.tunnel_process.stderr.read()
                print(f"❌ Cloudflare tunnel process died: {stderr}")
                return None
            
            # Read output line by line
            try:
                line = self.tunnel_process.stderr.readline()
                if line and "trycloudflare.com" in line:
                    # Extract URL from line
                    import re
                    url_match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
                    if url_match:
                        return url_match.group(0)
            except:
                pass
            
            time.sleep(1)
        
        return None
    
    def setup_localtunnel(self, subdomain: str = None) -> Optional[str]:
        """
        Set up localtunnel.me tunnel (requires npm/node)
        """
        try:
            # Check if lt is installed
            result = subprocess.run(['which', 'lt'], capture_output=True, text=True)
            if result.returncode != 0:
                print("📦 Installing localtunnel...")
                subprocess.run(['npm', 'install', '-g', 'localtunnel'], check=True)
            
            cmd = ['lt', '--port', str(self.local_port)]
            if subdomain:
                cmd.extend(['--subdomain', subdomain])
            
            print(f"🔗 Starting localtunnel...")
            
            self.tunnel_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for URL
            url = self._wait_for_localtunnel_url()
            if url:
                self.tunnel_type = "localtunnel"
                self.public_url = url
                print(f"✅ Localtunnel established!")
                print(f"📡 Public URL: {self.public_url}")
                return self.public_url
            else:
                print("❌ Failed to get localtunnel URL")
                return None
                
        except Exception as e:
            print(f"❌ Localtunnel error: {e}")
            return None
    
    def _wait_for_localtunnel_url(self, timeout: int = 30) -> Optional[str]:
        """Wait for localtunnel to provide URL"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.tunnel_process.poll() is not None:
                return None
            
            try:
                line = self.tunnel_process.stdout.readline()
                if line and "https://" in line and "localtunnel.me" in line:
                    import re
                    url_match = re.search(r'https://[a-zA-Z0-9-]+\.loca\.lt', line)
                    if url_match:
                        return url_match.group(0)
            except:
                pass
            
            time.sleep(1)
        
        return None
    
    def get_public_url(self) -> Optional[str]:
        """Get the current public URL"""
        return self.public_url
    
    def test_connection(self) -> bool:
        """Test if the tunnel is working"""
        if not self.public_url:
            return False
        
        try:
            response = requests.get(f"{self.public_url}/health", timeout=10)
            return response.status_code == 200
        except:
            return False
    
    def stop(self):
        """Stop the tunnel"""
        if self.tunnel_process:
            print(f"🛑 Stopping {self.tunnel_type} tunnel...")
            self.tunnel_process.terminate()
            try:
                self.tunnel_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.tunnel_process.kill()
            self.tunnel_process = None
        
        self.tunnel_type = None
        self.public_url = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


def main():
    """CLI interface for tunnel manager"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Tunnel Manager - ngrok alternative")
    parser.add_argument('--type', choices=['ssh', 'cloudflare', 'localtunnel'], 
                       default='cloudflare', help='Tunnel type')
    parser.add_argument('--port', type=int, default=8000, help='Local port')
    
    # SSH options
    parser.add_argument('--ssh-host', help='SSH remote host')
    parser.add_argument('--ssh-port', type=int, default=80, help='SSH remote port')
    parser.add_argument('--ssh-user', help='SSH username')
    parser.add_argument('--ssh-key', help='SSH private key path')
    
    # Other options
    parser.add_argument('--subdomain', help='Subdomain for localtunnel')
    parser.add_argument('--name', help='Tunnel name')
    
    args = parser.parse_args()
    
    tunnel_manager = TunnelManager()
    tunnel_manager.local_port = args.port
    
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down tunnel...")
        tunnel_manager.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if args.type == 'ssh':
            if not args.ssh_host:
                print("❌ SSH host required for SSH tunnel")
                sys.exit(1)
            
            url = tunnel_manager.setup_ssh_tunnel(
                args.ssh_host, args.ssh_port, args.ssh_user, args.ssh_key
            )
        
        elif args.type == 'cloudflare':
            url = tunnel_manager.setup_cloudflare_tunnel(args.name)
        
        elif args.type == 'localtunnel':
            url = tunnel_manager.setup_localtunnel(args.subdomain)
        
        if url:
            print(f"\n🌍 Tunnel active: {url}")
            print("🔍 Testing connection...")
            
            # Wait a moment for server to be ready
            time.sleep(2)
            
            if tunnel_manager.test_connection():
                print("✅ Connection test successful!")
            else:
                print("⚠️  Connection test failed - server might not be ready")
            
            print("\n📋 Usage:")
            print(f"   Health check: curl {url}/health")
            print(f"   API docs: {url}/docs")
            print(f"   Client test: python examples/remote_client_test.py {url}")
            
            print("\n⏳ Tunnel running... Press Ctrl+C to stop")
            
            # Keep running
            while True:
                time.sleep(1)
                
                # Check if tunnel is still alive
                if tunnel_manager.tunnel_process and tunnel_manager.tunnel_process.poll() is not None:
                    print("❌ Tunnel process died")
                    break
        else:
            print("❌ Failed to establish tunnel")
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    finally:
        tunnel_manager.stop()


if __name__ == "__main__":
    main()