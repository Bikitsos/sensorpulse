#!/usr/bin/env bash
# ================================
# SensorPulse - Test Runner Script
# ================================
# Usage: ./scripts/test.sh [backend|frontend|e2e|all]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[test]${NC} $*"; }
pass()  { echo -e "${GREEN}[pass]${NC} $*"; }
fail()  { echo -e "${RED}[fail]${NC} $*"; }

run_backend() {
  info "Running backend tests..."
  cd "$ROOT_DIR/api"
  python -m pytest tests/ \
    -v \
    --tb=short \
    --cov=. \
    --cov-report=term-missing \
    --cov-report=html:htmlcov \
    --cov-fail-under=70
  pass "Backend tests passed"
}

run_frontend() {
  info "Running frontend unit tests..."
  cd "$ROOT_DIR/frontend"
  npx vitest run --reporter=verbose --coverage
  pass "Frontend unit tests passed"
}

run_e2e() {
  info "Running E2E tests..."
  cd "$ROOT_DIR/frontend"
  npx playwright test --reporter=list
  pass "E2E tests passed"
}

run_all() {
  run_backend
  echo ""
  run_frontend
  echo ""
  info "Skipping E2E tests (run with: ./scripts/test.sh e2e)"
  echo ""
  pass "All tests completed"
}

TARGET="${1:-all}"

case "$TARGET" in
  backend)  run_backend  ;;
  frontend) run_frontend ;;
  e2e)      run_e2e      ;;
  all)      run_all      ;;
  *)
    echo "Usage: $0 [backend|frontend|e2e|all]"
    exit 1
    ;;
esac
