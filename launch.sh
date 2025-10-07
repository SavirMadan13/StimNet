#!/bin/bash

# Distributed Data Access Framework - Launch Script
# Replaces ngrok with better alternatives and automates startup

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
DEFAULT_PORT=8000
DEFAULT_TUNNEL_TYPE="cloudflare"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORK_DIR="$SCRIPT_DIR"

# Process tracking
PIDS=()
TUNNEL_PID=""
SERVER_PID=""

# Cleanup function
cleanup() {
    echo -e "\n${YELLOW}🛑 Shutting down services...${NC}"
    
    # Kill tunnel
    if [ ! -z "$TUNNEL_PID" ]; then
        echo -e "${BLUE}   Stopping tunnel (PID: $TUNNEL_PID)${NC}"
        kill $TUNNEL_PID 2>/dev/null || true
    fi
    
    # Kill server
    if [ ! -z "$SERVER_PID" ]; then
        echo -e "${BLUE}   Stopping server (PID: $SERVER_PID)${NC}"
        kill $SERVER_PID 2>/dev/null || true
    fi
    
    # Kill any remaining processes
    for pid in "${PIDS[@]}"; do
        kill $pid 2>/dev/null || true
    done
    
    echo -e "${GREEN}✅ Cleanup complete${NC}"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Help function
show_help() {
    cat << EOF
${CYAN}Distributed Data Access Framework - Launch Script${NC}

${YELLOW}USAGE:${NC}
    $0 [OPTIONS]

${YELLOW}OPTIONS:${NC}
    -t, --tunnel TYPE       Tunnel type: cloudflare, ssh, localtunnel, none (default: cloudflare)
    -p, --port PORT         Local server port (default: 8000)
    -h, --ssh-host HOST     SSH remote host (required for SSH tunnel)
    --ssh-port PORT         SSH remote port (default: 80)
    --ssh-user USER         SSH username (default: current user)
    --ssh-key PATH          SSH private key path
    -s, --subdomain NAME    Subdomain for localtunnel
    -n, --name NAME         Tunnel name
    --no-docker             Skip Docker setup
    --no-deps               Skip dependency installation
    --dev                   Development mode (auto-reload)
    --help                  Show this help

${YELLOW}EXAMPLES:${NC}
    # Quick start with Cloudflare tunnel
    $0

    # SSH tunnel to remote server
    $0 -t ssh -h myserver.com --ssh-user ubuntu

    # Local development only
    $0 -t none

    # Custom port with localtunnel
    $0 -t localtunnel -p 8080 -s myapp

${YELLOW}TUNNEL TYPES:${NC}
    cloudflare   - Free, stable, no account needed
    ssh          - Secure, requires remote server
    localtunnel  - Simple, requires npm
    none         - Local only (no external access)

EOF
}

# Parse command line arguments
TUNNEL_TYPE="$DEFAULT_TUNNEL_TYPE"
PORT="$DEFAULT_PORT"
SSH_HOST=""
SSH_PORT="80"
SSH_USER=""
SSH_KEY=""
SUBDOMAIN=""
TUNNEL_NAME=""
SKIP_DOCKER=false
SKIP_DEPS=false
DEV_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tunnel)
            TUNNEL_TYPE="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -h|--ssh-host)
            SSH_HOST="$2"
            shift 2
            ;;
        --ssh-port)
            SSH_PORT="$2"
            shift 2
            ;;
        --ssh-user)
            SSH_USER="$2"
            shift 2
            ;;
        --ssh-key)
            SSH_KEY="$2"
            shift 2
            ;;
        -s|--subdomain)
            SUBDOMAIN="$2"
            shift 2
            ;;
        -n|--name)
            TUNNEL_NAME="$2"
            shift 2
            ;;
        --no-docker)
            SKIP_DOCKER=true
            shift
            ;;
        --no-deps)
            SKIP_DEPS=true
            shift
            ;;
        --dev)
            DEV_MODE=true
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            echo -e "${RED}❌ Unknown option: $1${NC}"
            show_help
            exit 1
            ;;
    esac
done

# Validate tunnel type
case $TUNNEL_TYPE in
    cloudflare|ssh|localtunnel|none)
        ;;
    *)
        echo -e "${RED}❌ Invalid tunnel type: $TUNNEL_TYPE${NC}"
        echo -e "   Valid options: cloudflare, ssh, localtunnel, none"
        exit 1
        ;;
esac

# Validate SSH options
if [ "$TUNNEL_TYPE" = "ssh" ] && [ -z "$SSH_HOST" ]; then
    echo -e "${RED}❌ SSH host required for SSH tunnel${NC}"
    echo -e "   Use: $0 -t ssh -h your-server.com"
    exit 1
fi

# Header
echo -e "${CYAN}🚀 Distributed Data Access Framework${NC}"
echo -e "${CYAN}======================================${NC}"
echo -e "${BLUE}Working directory: ${WORK_DIR}${NC}"
echo -e "${BLUE}Server port: ${PORT}${NC}"
echo -e "${BLUE}Tunnel type: ${TUNNEL_TYPE}${NC}"
echo ""

# Change to script directory
cd "$WORK_DIR"

# Check Python
echo -e "${YELLOW}🐍 Checking Python...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
echo -e "${GREEN}✅ Python ${PYTHON_VERSION}${NC}"

# Install dependencies
if [ "$SKIP_DEPS" = false ]; then
    echo -e "\n${YELLOW}📦 Installing dependencies...${NC}"
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        echo -e "${BLUE}   Creating virtual environment...${NC}"
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Install requirements
    if [ -f "requirements.txt" ]; then
        echo -e "${BLUE}   Installing Python packages...${NC}"
        pip install -q -r requirements.txt
    fi
    
    # Install additional packages for tunnel manager
    pip install -q requests
    
    echo -e "${GREEN}✅ Dependencies installed${NC}"
else
    echo -e "${YELLOW}⏭️  Skipping dependency installation${NC}"
    # Still need to activate venv if it exists
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
fi

# Set up Docker
if [ "$SKIP_DOCKER" = false ]; then
    echo -e "\n${YELLOW}🐳 Setting up Docker...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found. Please install Docker first.${NC}"
        exit 1
    fi
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker daemon not running. Please start Docker.${NC}"
        exit 1
    fi
    
    # Build Docker images if they don't exist
    if ! docker image inspect distributed-python:latest &> /dev/null; then
        echo -e "${BLUE}   Building Python execution environment...${NC}"
        docker build -t distributed-python:latest -f docker/Dockerfile.python . &
        PIDS+=($!)
    fi
    
    if [ -f "docker/Dockerfile.r" ] && ! docker image inspect distributed-r:latest &> /dev/null; then
        echo -e "${BLUE}   Building R execution environment...${NC}"
        docker build -t distributed-r:latest -f docker/Dockerfile.r . &
        PIDS+=($!)
    fi
    
    # Wait for Docker builds
    for pid in "${PIDS[@]}"; do
        wait $pid
    done
    PIDS=()
    
    echo -e "${GREEN}✅ Docker setup complete${NC}"
else
    echo -e "${YELLOW}⏭️  Skipping Docker setup${NC}"
fi

# Set up demo data
echo -e "\n${YELLOW}📊 Setting up demo data...${NC}"
if [ -f "examples/setup_demo_data.py" ]; then
    python examples/setup_demo_data.py
    echo -e "${GREEN}✅ Demo data ready${NC}"
else
    echo -e "${YELLOW}⚠️  Demo data setup script not found${NC}"
fi

# Start the server
echo -e "\n${YELLOW}🖥️  Starting server...${NC}"

# Set environment variables
export NODE_ID="${NODE_ID:-node-1}"
export NODE_NAME="${NODE_NAME:-Default Node}"
export INSTITUTION_NAME="${INSTITUTION_NAME:-Default Institution}"
export PORT="$PORT"
export HOST="${HOST:-0.0.0.0}"

if [ "$DEV_MODE" = true ]; then
    echo -e "${BLUE}   Development mode enabled${NC}"
    python run_server.py &
else
    python run_server.py &
fi

SERVER_PID=$!
PIDS+=($SERVER_PID)

# Wait for server to start
echo -e "${BLUE}   Waiting for server to start...${NC}"
for i in {1..30}; do
    if curl -s "http://localhost:$PORT/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Server started successfully${NC}"
        break
    fi
    if [ $i -eq 30 ]; then
        echo -e "${RED}❌ Server failed to start${NC}"
        cleanup
        exit 1
    fi
    sleep 1
done

# Set up tunnel
if [ "$TUNNEL_TYPE" != "none" ]; then
    echo -e "\n${YELLOW}🌐 Setting up tunnel...${NC}"
    
    # Build tunnel command
    TUNNEL_CMD="python tunnel_manager.py --type $TUNNEL_TYPE --port $PORT"
    
    case $TUNNEL_TYPE in
        ssh)
            TUNNEL_CMD="$TUNNEL_CMD --ssh-host $SSH_HOST --ssh-port $SSH_PORT"
            if [ ! -z "$SSH_USER" ]; then
                TUNNEL_CMD="$TUNNEL_CMD --ssh-user $SSH_USER"
            fi
            if [ ! -z "$SSH_KEY" ]; then
                TUNNEL_CMD="$TUNNEL_CMD --ssh-key $SSH_KEY"
            fi
            ;;
        localtunnel)
            if [ ! -z "$SUBDOMAIN" ]; then
                TUNNEL_CMD="$TUNNEL_CMD --subdomain $SUBDOMAIN"
            fi
            ;;
        cloudflare)
            if [ ! -z "$TUNNEL_NAME" ]; then
                TUNNEL_CMD="$TUNNEL_CMD --name $TUNNEL_NAME"
            fi
            ;;
    esac
    
    echo -e "${BLUE}   Command: $TUNNEL_CMD${NC}"
    
    # Start tunnel in background and capture output
    $TUNNEL_CMD > tunnel.log 2>&1 &
    TUNNEL_PID=$!
    PIDS+=($TUNNEL_PID)
    
    # Wait for tunnel to establish
    echo -e "${BLUE}   Waiting for tunnel to establish...${NC}"
    TUNNEL_URL=""
    for i in {1..60}; do
        if [ ! -z "$(ps -p $TUNNEL_PID -o pid= 2>/dev/null)" ]; then
            # Check log for URL
            if [ -f "tunnel.log" ]; then
                case $TUNNEL_TYPE in
                    cloudflare)
                        TUNNEL_URL=$(grep -o 'https://[a-zA-Z0-9-]*\.trycloudflare\.com' tunnel.log | tail -1)
                        ;;
                    localtunnel)
                        TUNNEL_URL=$(grep -o 'https://[a-zA-Z0-9-]*\.loca\.lt' tunnel.log | tail -1)
                        ;;
                    ssh)
                        TUNNEL_URL="http://$SSH_HOST:$SSH_PORT"
                        ;;
                esac
                
                if [ ! -z "$TUNNEL_URL" ]; then
                    echo -e "${GREEN}✅ Tunnel established!${NC}"
                    echo -e "${GREEN}📡 Public URL: $TUNNEL_URL${NC}"
                    break
                fi
            fi
        else
            echo -e "${RED}❌ Tunnel process died${NC}"
            if [ -f "tunnel.log" ]; then
                echo -e "${RED}   Error log:${NC}"
                tail -5 tunnel.log
            fi
            break
        fi
        
        if [ $i -eq 60 ]; then
            echo -e "${RED}❌ Tunnel failed to establish${NC}"
            if [ -f "tunnel.log" ]; then
                echo -e "${RED}   Log:${NC}"
                tail -10 tunnel.log
            fi
        fi
        sleep 1
    done
else
    echo -e "\n${YELLOW}🏠 Local mode - no tunnel${NC}"
    TUNNEL_URL="http://localhost:$PORT"
fi

# Final status
echo -e "\n${CYAN}🎉 Launch Complete!${NC}"
echo -e "${CYAN}==================${NC}"

if [ ! -z "$TUNNEL_URL" ]; then
    echo -e "${GREEN}📡 Public URL: $TUNNEL_URL${NC}"
    echo -e "${GREEN}🌐 Web Interface: $TUNNEL_URL/docs${NC}"
    echo -e "${GREEN}❤️  Health Check: $TUNNEL_URL/health${NC}"
else
    echo -e "${YELLOW}🏠 Local URL: http://localhost:$PORT${NC}"
    echo -e "${YELLOW}🌐 Web Interface: http://localhost:$PORT/docs${NC}"
    echo -e "${YELLOW}❤️  Health Check: http://localhost:$PORT/health${NC}"
fi

echo -e "\n${YELLOW}🧪 Test Commands:${NC}"
if [ ! -z "$TUNNEL_URL" ]; then
    echo -e "${BLUE}# Basic test:${NC}"
    echo -e "curl $TUNNEL_URL/health"
    echo -e "\n${BLUE}# Python client test:${NC}"
    echo -e "python examples/remote_client_test.py $TUNNEL_URL"
else
    echo -e "${BLUE}# Basic test:${NC}"
    echo -e "curl http://localhost:$PORT/health"
    echo -e "\n${BLUE}# Python client test:${NC}"
    echo -e "python examples/simple_client.py"
fi

echo -e "\n${YELLOW}📊 Monitoring:${NC}"
echo -e "${BLUE}# Server logs: tail -f server.log${NC}"
if [ "$TUNNEL_TYPE" != "none" ]; then
    echo -e "${BLUE}# Tunnel logs: tail -f tunnel.log${NC}"
fi

echo -e "\n${PURPLE}⏳ Services running... Press Ctrl+C to stop all services${NC}"

# Test connection
if [ ! -z "$TUNNEL_URL" ]; then
    echo -e "\n${YELLOW}🔍 Testing connection...${NC}"
    sleep 2
    if curl -s "$TUNNEL_URL/health" > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Connection test successful!${NC}"
    else
        echo -e "${YELLOW}⚠️  Connection test failed - services might still be starting${NC}"
    fi
fi

# Keep script running and monitor processes
while true do
    sleep 5
    
    # Check if server is still running
    if [ ! -z "$(ps -p $SERVER_PID -o pid= 2>/dev/null)" ]; then
        # Server is running
        :
    else
        echo -e "\n${RED}❌ Server process died${NC}"
        cleanup
        exit 1
    fi
    
    # Check tunnel if applicable
    if [ "$TUNNEL_TYPE" != "none" ] && [ ! -z "$TUNNEL_PID" ]; then
        if [ -z "$(ps -p $TUNNEL_PID -o pid= 2>/dev/null)" ]; then
            echo -e "\n${RED}❌ Tunnel process died${NC}"
            cleanup
            exit 1
        fi
    fi
done