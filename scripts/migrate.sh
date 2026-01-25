#!/bin/bash
# ================================
# SensorPulse - Database Migration Script
# ================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
API_DIR="$PROJECT_ROOT/api"

cd "$API_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}"
echo "╔═══════════════════════════════════════════╗"
echo "║     SensorPulse - Database Migrations     ║"
echo "╚═══════════════════════════════════════════╝"
echo -e "${NC}"

# Check for DATABASE_URL
if [ -z "$DATABASE_URL" ]; then
    if [ -f "$PROJECT_ROOT/.env" ]; then
        export $(grep -v '^#' "$PROJECT_ROOT/.env" | xargs)
    else
        echo -e "${RED}Error: DATABASE_URL not set and .env file not found!${NC}"
        exit 1
    fi
fi

# Parse arguments
ACTION="${1:-upgrade}"

case "$ACTION" in
    upgrade)
        REVISION="${2:-head}"
        echo -e "${GREEN}Upgrading database to: $REVISION${NC}"
        alembic upgrade "$REVISION"
        ;;
    downgrade)
        REVISION="${2:--1}"
        echo -e "${YELLOW}Downgrading database by: $REVISION${NC}"
        echo -e "${RED}WARNING: This may result in data loss!${NC}"
        read -p "Are you sure? (y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            alembic downgrade "$REVISION"
        else
            echo "Aborted."
            exit 0
        fi
        ;;
    current)
        echo -e "${CYAN}Current database revision:${NC}"
        alembic current
        ;;
    history)
        echo -e "${CYAN}Migration history:${NC}"
        alembic history --verbose
        ;;
    generate)
        MESSAGE="${2:-auto_generated}"
        echo -e "${GREEN}Generating new migration: $MESSAGE${NC}"
        alembic revision --autogenerate -m "$MESSAGE"
        ;;
    heads)
        echo -e "${CYAN}Migration heads:${NC}"
        alembic heads
        ;;
    *)
        echo -e "${CYAN}Usage: $0 {upgrade|downgrade|current|history|generate|heads} [revision/message]${NC}"
        echo ""
        echo "Commands:"
        echo "  upgrade [rev]    Upgrade to a revision (default: head)"
        echo "  downgrade [rev]  Downgrade by revision (default: -1)"
        echo "  current          Show current revision"
        echo "  history          Show migration history"
        echo "  generate [msg]   Generate new migration from models"
        echo "  heads            Show current heads"
        exit 1
        ;;
esac

echo -e "${GREEN}Done!${NC}"
