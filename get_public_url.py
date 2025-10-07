#!/usr/bin/env python3
"""
Get the public URL for cross-network testing
Now supports multiple tunnel types as ngrok alternatives
"""
import requests
import json
import time
import sys
import subprocess
import os

def get_ngrok_url():
    """Get the public ngrok URL (legacy support)"""
    try:
        # Try to get ngrok tunnel info
        response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
        if response.status_code == 200:
            tunnels = response.json()
            if tunnels.get('tunnels'):
                for tunnel in tunnels['tunnels']:
                    if tunnel.get('proto') == 'https':
                        return tunnel.get('public_url')
                    elif tunnel.get('proto') == 'http':
                        return tunnel.get('public_url')
        return None
    except Exception as e:
        return None

def get_tunnel_url():
    """Get URL from our tunnel manager"""
    try:
        # Check if tunnel manager is running and has a URL
        if os.path.exists('tunnel.log'):
            with open('tunnel.log', 'r') as f:
                content = f.read()
                
                # Check for different tunnel types
                import re
                
                # Cloudflare tunnel
                cloudflare_match = re.search(r'https://[a-zA-Z0-9-]*\.trycloudflare\.com', content)
                if cloudflare_match:
                    return cloudflare_match.group(0)
                
                # Localtunnel
                localtunnel_match = re.search(r'https://[a-zA-Z0-9-]*\.loca\.lt', content)
                if localtunnel_match:
                    return localtunnel_match.group(0)
        
        return None
    except Exception as e:
        return None

def wait_for_tunnel(max_wait=30):
    """Wait for any tunnel to start and return the URL"""
    print("🔍 Looking for active tunnel...")
    
    for i in range(max_wait):
        # Check new tunnel manager first
        url = get_tunnel_url()
        if url:
            return url, "tunnel_manager"
        
        # Fallback to ngrok
        url = get_ngrok_url()
        if url:
            return url, "ngrok"
        
        if i == 0:
            print("⏳ Waiting for tunnel to start...")
        elif i % 5 == 0:
            print(f"   Still waiting... ({i}s)")
        
        time.sleep(1)
    
    return None, None

def main():
    """Main function"""
    print("🌍 Cross-Network Testing Setup")
    print("=" * 40)
    
    # Check for active tunnels
    url, tunnel_type = wait_for_tunnel(5)  # Quick check first
    
    if not url:
        print("❌ No active tunnel detected.")
        print("\n🚀 Quick Start Options:")
        print("\n1. 🌟 RECOMMENDED: Use our launch script (replaces ngrok)")
        print("   ./launch.sh")
        print("   # Automatically sets up Cloudflare tunnel + server")
        
        print("\n2. 📋 Manual setup with better alternatives:")
        print("   # Cloudflare tunnel (free, stable)")
        print("   python tunnel_manager.py --type cloudflare")
        print("   ")
        print("   # SSH tunnel (secure, needs remote server)")
        print("   python tunnel_manager.py --type ssh --ssh-host your-server.com")
        print("   ")
        print("   # Localtunnel (simple, needs npm)")
        print("   python tunnel_manager.py --type localtunnel")
        
        print("\n3. 🏠 Local development only:")
        print("   ./launch.sh --tunnel none")
        
        print("\n4. ☁️  Cloud deployment (permanent solution):")
        print("   python cloud_deploy.py railway    # Free tier")
        print("   python cloud_deploy.py render     # Free tier")
        print("   python cloud_deploy.py fly        # Free tier")
        
        print("\n5. 🔧 Legacy ngrok (if you prefer):")
        print("   ngrok http 8000")
        
        print("\n" + "="*50)
        print("💡 TIP: The launch script handles everything automatically!")
        print("   Just run: ./launch.sh")
        
        # Try to wait longer for tunnel
        print("\n⏳ Checking for tunnels one more time...")
        url, tunnel_type = wait_for_tunnel(25)
    
    if url:
        tunnel_name = {
            "ngrok": "Ngrok",
            "tunnel_manager": "Tunnel Manager"
        }.get(tunnel_type, "Unknown")
        
        print(f"🎉 Found {tunnel_name} tunnel!")
        print(f"📡 Public URL: {url}")
        print(f"🌐 Web Interface: {url}/docs")
        print(f"❤️  Health Check: {url}/health")
        
        print(f"\n🧪 Test Commands:")
        print(f"# Basic test:")
        print(f"curl {url}/health")
        
        print(f"\n# Python client test:")
        print(f"python examples/remote_client_test.py {url}")
        
        print(f"\n# From any device/network, visit:")
        print(f"{url}/docs")
        
        # Test the connection
        print(f"\n🔍 Testing connection...")
        try:
            response = requests.get(f"{url}/health", timeout=10)
            if response.status_code == 200:
                health = response.json()
                print(f"✅ Connection successful!")
                print(f"   Node ID: {health.get('node_id')}")
                print(f"   Status: {health.get('status')}")
                print(f"   Uptime: {health.get('uptime', 0):.1f}s")
            else:
                print(f"⚠️  Got response code: {response.status_code}")
        except Exception as e:
            print(f"❌ Connection test failed: {e}")
        
        print(f"\n🌍 Your server is now accessible from anywhere!")
        print(f"Share this URL with colleagues for testing: {url}")
        
    else:
        print("❌ Could not find any active tunnel.")
        print("\n🚀 Run './launch.sh' to start everything automatically!")

if __name__ == "__main__":
    main()
