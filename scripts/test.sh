#!/usr/bin/env bash
# ================================
# SensorPulse - Test Runner Script
# ================================
# Usage: ./scripts/test.sh [backend|frontend|e2e|container|all]
#
# Modes:
#   backend   – Run pytest locally (SQLite, no Postgres needed)
#   frontend  – Run vitest locally
#   e2e       – Run Playwright E2E locally
#   container – Run backend + frontend tests inside Podman containers
#              (real Postgres, isolated environment)
#   all       – Run backend + frontend locally (default)

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
  info "Running backend tests (local / SQLite)..."
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
  info "Running frontend unit tests (local)..."
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

run_container() {
  info "Running tests inside Podman containers (Postgres + Node)..."
  cd "$ROOT_DIR"

  # Detect compose command (podman-compose or docker compose)
  if command -v podman-compose &>/dev/null; then
    COMPOSE="podman-compose"
  elif command -v docker &>/dev/null && docker compose version &>/dev/null 2>&1; then
    COMPOSE="docker compose"
  else
    fail "Neither podman-compose nor docker compose found"
    exit 1
  fi

  info "Using: $COMPOSE"

  # Build and run — exit when any container stops
  $COMPOSE -f podman-compose.test.yml up \
    --build \
    --abort-on-container-exit \
    --exit-code-from test-api

  EXIT_CODE=$?

  # Clean up containers
  $COMPOSE -f podman-compose.test.yml down -v --remove-orphans 2>/dev/null || true

  if [ "$EXIT_CODE" -eq 0 ]; then
    pass "Container tests passed"
  else
    fail "Container tests failed (exit code: $EXIT_CODE)"
    exit "$EXIT_CODE"
  fi
}

run_all() {
  run_backend
  echo ""
  run_frontend
  echo ""
  info "Skipping E2E tests (run with: ./scripts/test.sh e2e)"
  info "Skipping container tests (run with: ./scripts/test.sh container)"
  echo ""
  pass "All local tests completed"
}

TARGET="${1:-all}"

case "$TARGET" in
  backend)   run_backend   ;;
  frontend)  run_frontend  ;;
  e2e)       run_e2e       ;;
  container) run_container ;;
  all)       run_all       ;;
  *)
    echo "Usage: $0 [backend|frontend|e2e|container|all]"
    exit 1
    ;;
esac
