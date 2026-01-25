#!/bin/bash
# ================================
# SensorPulse - Development Startup Script
# ================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════╗"
echo "║     SensorPulse - Development Mode        ║"
echo "╚═══════════════════════════════════════════╝"
echo -e "${NC}"

# Check for .env file
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}Warning: .env file not found!${NC}"
    echo -e "Creating from .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}Created .env file. Please update it with your credentials.${NC}"
    else
        echo -e "${RED}Error: .env.example not found!${NC}"
        exit 1
    fi
fi

# Check if podman is available
if ! command -v podman &> /dev/null; then
    echo -e "${RED}Error: podman is not installed!${NC}"
    exit 1
fi

# Check if podman-compose is available
if ! command -v podman-compose &> /dev/null; then
    echo -e "${YELLOW}Warning: podman-compose not found, trying docker-compose...${NC}"
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="podman-compose"
fi

# Parse arguments
ACTION="${1:-up}"

case "$ACTION" in
    up)
        echo -e "${GREEN}Starting development environment...${NC}"
        $COMPOSE_CMD -f podman-compose.yml -f podman-compose.dev.yml up --build
        ;;
    down)
        echo -e "${YELLOW}Stopping development environment...${NC}"
        $COMPOSE_CMD -f podman-compose.yml -f podman-compose.dev.yml down
        ;;
    logs)
        SERVICE="${2:-}"
        if [ -n "$SERVICE" ]; then
            $COMPOSE_CMD -f podman-compose.yml -f podman-compose.dev.yml logs -f "$SERVICE"
        else
            $COMPOSE_CMD -f podman-compose.yml -f podman-compose.dev.yml logs -f
        fi
        ;;
    restart)
        SERVICE="${2:-}"
        if [ -n "$SERVICE" ]; then
            echo -e "${YELLOW}Restarting $SERVICE...${NC}"
            $COMPOSE_CMD -f podman-compose.yml -f podman-compose.dev.yml restart "$SERVICE"
        else
            echo -e "${YELLOW}Restarting all services...${NC}"
            $COMPOSE_CMD -f podman-compose.yml -f podman-compose.dev.yml restart
        fi
        ;;
    ps)
        $COMPOSE_CMD -f podman-compose.yml -f podman-compose.dev.yml ps
        ;;
    shell)
        SERVICE="${2:-api}"
        echo -e "${CYAN}Opening shell in $SERVICE...${NC}"
        $COMPOSE_CMD -f podman-compose.yml -f podman-compose.dev.yml exec "$SERVICE" /bin/sh
        ;;
    *)
        echo -e "${CYAN}Usage: $0 {up|down|logs|restart|ps|shell} [service]${NC}"
        echo ""
        echo "Commands:"
        echo "  up        Start all services (default)"
        echo "  down      Stop all services"
        echo "  logs      View logs (optionally specify service)"
        echo "  restart   Restart services (optionally specify service)"
        echo "  ps        List running containers"
        echo "  shell     Open shell in container (default: api)"
        exit 1
        ;;
esac

echo -e "${GREEN}Done!${NC}"
