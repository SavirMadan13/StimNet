#!/usr/bin/env python3
"""
Professional deployment options for the distributed framework
More trustworthy than random tunnel URLs
"""
import subprocess
import sys
import os
from pathlib import Path

def setup_custom_domain():
    """Guide for setting up with custom domain"""
    print("🏢 Professional Domain Setup")
    print("=" * 40)
    print()
    print("For a professional, trustworthy setup:")
    print()
    print("1. 🌐 Get a domain name:")
    print("   - Namecheap, GoDaddy, Google Domains")
    print("   - Example: yourresearch.org")
    print()
    print("2. 🔧 Set up Cloudflare (free):")
    print("   - Add your domain to Cloudflare")
    print("   - Create subdomain: api.yourresearch.org")
    print()
    print("3. 🚀 Deploy to cloud:")
    print("   - Railway.app (free tier)")
    print("   - Render.com (free tier)")
    print("   - Fly.io (free tier)")
    print()
    print("Result: https://api.yourresearch.org")
    print("Much more professional and trustworthy!")

def setup_railway_deployment():
    """Set up Railway deployment"""
    print("🚂 Railway Deployment (Free)")
    print("=" * 30)
    print()
    print("Railway gives you a professional URL like:")
    print("https://your-app-name.railway.app")
    print()
    print("Steps:")
    print("1. Install Railway CLI:")
    print("   npm install -g @railway/cli")
    print()
    print("2. Login and deploy:")
    print("   railway login")
    print("   railway init")
    print("   railway up")
    print()
    print("3. Get professional URL:")
    print("   https://distributed-framework-production.railway.app")

def setup_render_deployment():
    """Set up Render deployment"""
    print("🎨 Render Deployment (Free)")
    print("=" * 25)
    print()
    print("Render gives you URLs like:")
    print("https://your-app-name.onrender.com")
    print()
    print("Steps:")
    print("1. Connect GitHub repo to Render")
    print("2. Deploy automatically")
    print("3. Get URL: https://research-node.onrender.com")

def create_professional_config():
    """Create configuration for professional deployment"""
    
    # Create Procfile for Heroku/Railway
    with open("Procfile", "w") as f:
        f.write("web: python run_server.py\n")
    
    # Create railway.json
    railway_config = {
        "build": {
            "builder": "NIXPACKS"
        },
        "deploy": {
            "startCommand": "python run_server.py",
            "healthcheckPath": "/health"
        }
    }
    
    with open("railway.json", "w") as f:
        import json
        json.dump(railway_config, f, indent=2)
    
    # Create render.yaml
    render_config = """services:
  - type: web
    name: distributed-framework
    env: python
    buildCommand: pip install -r requirements_core.txt && pip install pandas numpy scipy pydantic-settings requests
    startCommand: python run_server.py
    healthCheckPath: /health
    envVars:
      - key: NODE_ID
        value: production-node
      - key: NODE_NAME
        value: Research Data Node
      - key: INSTITUTION_NAME
        value: Your Institution
"""
    
    with open("render.yaml", "w") as f:
        f.write(render_config)
    
    print("✅ Created professional deployment configs:")
    print("   - Procfile (for Railway/Heroku)")
    print("   - railway.json (for Railway)")
    print("   - render.yaml (for Render)")

def show_security_comparison():
    """Show security comparison of different options"""
    print("🔒 Security & Trust Comparison")
    print("=" * 35)
    print()
    
    options = [
        {
            "name": "Random Cloudflare Tunnel",
            "url": "https://random-words-123.trycloudflare.com",
            "trust": "⚠️  Low (looks suspicious)",
            "security": "🔒 High (encrypted)",
            "cost": "💰 Free",
            "professional": "❌ No"
        },
        {
            "name": "Custom Domain + Cloudflare",
            "url": "https://api.yourresearch.org",
            "trust": "✅ High (your domain)",
            "security": "🔒 High (encrypted)",
            "cost": "💰 $10-15/year",
            "professional": "✅ Yes"
        },
        {
            "name": "Railway Deployment",
            "url": "https://research-node.railway.app",
            "trust": "✅ Good (railway.app)",
            "security": "🔒 High (encrypted)",
            "cost": "💰 Free tier",
            "professional": "✅ Yes"
        },
        {
            "name": "Render Deployment",
            "url": "https://research-node.onrender.com",
            "trust": "✅ Good (onrender.com)",
            "security": "🔒 High (encrypted)",
            "cost": "💰 Free tier",
            "professional": "✅ Yes"
        }
    ]
    
    for option in options:
        print(f"📋 {option['name']}")
        print(f"   URL: {option['url']}")
        print(f"   Trust: {option['trust']}")
        print(f"   Security: {option['security']}")
        print(f"   Cost: {option['cost']}")
        print(f"   Professional: {option['professional']}")
        print()

def main():
    """Main function"""
    print("🎯 Professional Distributed Framework Setup")
    print("=" * 45)
    print()
    print("You're right to be concerned about suspicious URLs!")
    print("Let's set up something more professional and trustworthy.")
    print()
    
    while True:
        print("Choose an option:")
        print("1. 🌐 Custom domain setup guide")
        print("2. 🚂 Railway deployment (free)")
        print("3. 🎨 Render deployment (free)")
        print("4. 🔒 Security comparison")
        print("5. ⚙️  Create deployment configs")
        print("6. 🚪 Exit")
        print()
        
        choice = input("Enter choice (1-6): ").strip()
        
        if choice == "1":
            setup_custom_domain()
        elif choice == "2":
            setup_railway_deployment()
        elif choice == "3":
            setup_render_deployment()
        elif choice == "4":
            show_security_comparison()
        elif choice == "5":
            create_professional_config()
            print("\n✅ Professional configs created!")
        elif choice == "6":
            break
        else:
            print("❌ Invalid choice")
        
        print("\n" + "="*50 + "\n")
    
    print("🎉 Ready for professional deployment!")
    print("Your distributed framework will have a trustworthy URL!")

if __name__ == "__main__":
    main()
