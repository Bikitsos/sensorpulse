#!/usr/bin/env bash
# ================================
# SensorPulse - Lint Runner Script
# ================================
# Usage: ./scripts/lint.sh [backend|frontend|all]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[lint]${NC} $*"; }
pass()  { echo -e "${GREEN}[pass]${NC} $*"; }
fail()  { echo -e "${RED}[fail]${NC} $*"; }

run_backend_lint() {
  info "Linting backend (ruff)..."
  cd "$ROOT_DIR/api"
  python -m ruff check . --fix
  python -m ruff format --check .
  pass "Backend lint passed"
}

run_frontend_lint() {
  info "Linting frontend (eslint + tsc)..."
  cd "$ROOT_DIR/frontend"
  npx eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0
  npx tsc --noEmit
  pass "Frontend lint passed"
}

run_all() {
  run_backend_lint
  echo ""
  run_frontend_lint
  echo ""
  pass "All lint checks passed"
}

TARGET="${1:-all}"

case "$TARGET" in
  backend)  run_backend_lint  ;;
  frontend) run_frontend_lint ;;
  all)      run_all           ;;
  *)
    echo "Usage: $0 [backend|frontend|all]"
    exit 1
    ;;
esac
