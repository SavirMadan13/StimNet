#!/usr/bin/env python3
"""
Get the public ngrok URL for cross-network testing
"""
import requests
import json
import time
import sys

def get_ngrok_url():
    """Get the public ngrok URL"""
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

def wait_for_ngrok(max_wait=30):
    """Wait for ngrok to start and return the URL"""
    print("🔍 Looking for ngrok tunnel...")
    
    for i in range(max_wait):
        url = get_ngrok_url()
        if url:
            return url
        
        if i == 0:
            print("⏳ Waiting for ngrok to start...")
        elif i % 5 == 0:
            print(f"   Still waiting... ({i}s)")
        
        time.sleep(1)
    
    return None

def main():
    """Main function"""
    print("🌍 Cross-Network Testing Setup")
    print("=" * 40)
    
    # Check if ngrok is running
    url = get_ngrok_url()
    
    if not url:
        print("❌ Ngrok not detected. Starting setup...")
        print("\n📋 To test across different WiFi networks:")
        print("1. Make sure your server is running:")
        print("   python run_server.py")
        print("\n2. In another terminal, start ngrok:")
        print("   ngrok http 8000")
        print("\n3. Run this script again to get your public URL")
        print("\n4. Use that URL to test from any device/network!")
        
        # Try to wait for ngrok
        url = wait_for_ngrok()
    
    if url:
        print(f"🎉 Found ngrok tunnel!")
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
        print("❌ Could not find ngrok tunnel.")
        print("Make sure ngrok is running: ngrok http 8000")

if __name__ == "__main__":
    main()
