#!/bin/bash

# StimNet Research Platform - Quick Restart Script
# Kills all servers and restarts them

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 StimNet Research Platform - Restart${NC}"
echo "=================================================="

# Function to kill processes
kill_servers() {
    echo -e "${YELLOW}🛑 Stopping all servers...${NC}"
    
    # Kill various server processes
    pkill -f "python.*run_server" 2>/dev/null || true
    pkill -f "python.*tunnel_manager" 2>/dev/null || true
    pkill -f "uvicorn.*distributed_node" 2>/dev/null || true
    pkill -f "cloudflared.*tunnel" 2>/dev/null || true
    pkill -f "python.*real_main" 2>/dev/null || true
    
    # Wait for graceful shutdown
    sleep 2
    
    # Force kill if needed
    pkill -9 -f "python.*StimNet" 2>/dev/null || true
    
    echo -e "${GREEN}✅ All servers stopped${NC}"
}

# Function to start server
start_server() {
    echo -e "${BLUE}🚀 Starting StimNet server...${NC}"
    
    cd /Users/savirmadan/Development/StimNet
    source venv/bin/activate
    
    # Start server in background
    python run_server.py &
    SERVER_PID=$!
    
    # Wait for server to start
    echo -e "${YELLOW}⏳ Waiting for server...${NC}"
    for i in {1..10}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Server started (PID: $SERVER_PID)${NC}"
            return 0
        fi
        sleep 1
        echo "   Waiting... ($i/10)"
    done
    
    echo -e "${RED}❌ Server failed to start${NC}"
    return 1
}

# Function to start tunnel
start_tunnel() {
    echo -e "${BLUE}🌐 Starting Cloudflare tunnel...${NC}"
    
    cd /Users/savirmadan/Development/StimNet
    source venv/bin/activate
    
    # Start tunnel in background
    python tunnel_manager.py --type cloudflare --port 8000 &
    TUNNEL_PID=$!
    
    # Wait for tunnel
    echo -e "${YELLOW}⏳ Waiting for tunnel...${NC}"
    for i in {1..15}; do
        if python get_public_url.py 2>/dev/null | grep -q "Connection successful"; then
            echo -e "${GREEN}✅ Tunnel established (PID: $TUNNEL_PID)${NC}"
            return 0
        fi
        sleep 1
        echo "   Waiting... ($i/15)"
    done
    
    echo -e "${YELLOW}⚠️  Tunnel may still be establishing...${NC}"
    return 0
}

# Function to show status
show_status() {
    echo -e "\n${BLUE}📊 STIMNET STATUS${NC}"
    echo "================================"
    
    # Local status
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Local Server: http://localhost:8000${NC}"
        echo -e "${GREEN}🌐 Web Interface: http://localhost:8000${NC}"
        echo -e "${GREEN}📚 API Docs: http://localhost:8000/docs${NC}"
    else
        echo -e "${RED}❌ Local server not responding${NC}"
    fi
    
    # Tunnel status
    cd /Users/savirmadan/Development/StimNet
    source venv/bin/activate
    
    TUNNEL_OUTPUT=$(python get_public_url.py 2>/dev/null || echo "")
    if echo "$TUNNEL_OUTPUT" | grep -q "📡 Public URL:"; then
        TUNNEL_URL=$(echo "$TUNNEL_OUTPUT" | grep "📡 Public URL:" | sed 's/.*📡 Public URL: //')
        echo -e "${GREEN}✅ Global Access: $TUNNEL_URL${NC}"
        echo -e "${GREEN}🌐 Global Web Interface: $TUNNEL_URL${NC}"
        echo -e "${GREEN}📚 Global API Docs: $TUNNEL_URL/docs${NC}"
    else
        echo -e "${YELLOW}⚠️  Tunnel status unknown${NC}"
    fi
    
    echo -e "\n${BLUE}🎯 Quick Start:${NC}"
    echo "1. Visit the web interface URL above"
    echo "2. Click 'Load Demographics Example'"
    echo "3. Click '🚀 Run Analysis'"
    echo "4. See real results from 150 subjects!"
}

# Handle command line arguments
case "${1:-}" in
    --stop)
        echo -e "${YELLOW}🛑 Stopping StimNet services...${NC}"
        kill_servers
        echo -e "${GREEN}✅ All services stopped${NC}"
        exit 0
        ;;
    --status)
        show_status
        exit 0
        ;;
    --help)
        echo "StimNet Restart Script"
        echo "Usage:"
        echo "  ./restart.sh          # Full restart"
        echo "  ./restart.sh --stop   # Stop all services"
        echo "  ./restart.sh --status # Show status"
        echo "  ./restart.sh --help   # Show this help"
        exit 0
        ;;
esac

# Main restart sequence
echo -e "${BLUE}Starting complete restart...${NC}"

# Step 1: Kill existing processes
kill_servers

# Step 2: Start server
if ! start_server; then
    echo -e "${RED}❌ Failed to start server${NC}"
    exit 1
fi

# Step 3: Start tunnel
start_tunnel

# Step 4: Show final status
show_status

echo -e "\n${GREEN}🎉 StimNet restart complete!${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop all services${NC}"

# Keep script running and handle Ctrl+C
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down StimNet...${NC}"
    kill_servers
    echo -e "${GREEN}✅ StimNet stopped${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM

# Wait for user interrupt
while true; do
    sleep 1
done
