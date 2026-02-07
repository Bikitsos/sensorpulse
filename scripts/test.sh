#!/usr/bin/env bash
# ================================
# SensorPulse - Test Runner Script
# ================================
# All tests run inside Podman/Docker containers.
# No local Python, Node.js, or database required.
#
# Usage: ./scripts/test.sh [backend|frontend|e2e|lint|all]
#
# Modes:
#   backend  - Pytest against real Postgres (test-db + test-api)
#   frontend - Vitest unit tests (test-frontend)
#   e2e      - Playwright E2E (test-db + api-serve + frontend-serve + Playwright)
#   lint     - Ruff + ESLint + tsc (lint-api + lint-frontend)
#   all      - backend + frontend (default)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$ROOT_DIR/podman-compose.test.yml"

RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[test]${NC} $*"; }
pass()  { echo -e "${GREEN}[pass]${NC} $*"; }
fail()  { echo -e "${RED}[fail]${NC} $*"; }

# ---------- Detect compose command ----------
detect_compose() {
  if command -v podman-compose &>/dev/null; then
    COMPOSE="podman-compose"
  elif command -v docker &>/dev/null && docker compose version &>/dev/null 2>&1; then
    COMPOSE="docker compose"
  else
    fail "Neither podman-compose nor docker compose found"
    exit 1
  fi
  info "Using: $COMPOSE"
}

# ---------- Cleanup (runs on exit) ----------
cleanup() {
  info "Cleaning up containers..."
  $COMPOSE -f "$COMPOSE_FILE" --profile e2e --profile lint down -v --remove-orphans 2>/dev/null || true
}
trap cleanup EXIT

# ---------- Modes ----------

run_backend() {
  info "Running backend tests (Postgres container)..."
  cd "$ROOT_DIR"
  $COMPOSE -f "$COMPOSE_FILE" up \
    --build \
    --abort-on-container-exit \
    --exit-code-from test-api \
    test-db test-api
}

run_frontend() {
  info "Running frontend unit tests (container)..."
  cd "$ROOT_DIR"
  $COMPOSE -f "$COMPOSE_FILE" up \
    --build \
    --abort-on-container-exit \
    --exit-code-from test-frontend \
    test-frontend
}

run_e2e() {
  info "Running Playwright E2E tests (containers)..."
  cd "$ROOT_DIR"
  $COMPOSE -f "$COMPOSE_FILE" --profile e2e up \
    --build \
    --abort-on-container-exit \
    --exit-code-from test-e2e
}

run_lint() {
  info "Running linters (containers)..."
  cd "$ROOT_DIR"
  $COMPOSE -f "$COMPOSE_FILE" --profile lint up \
    --build \
    --abort-on-container-exit \
    lint-api lint-frontend
}

run_all() {
  info "Running all tests (backend + frontend) in containers..."
  cd "$ROOT_DIR"
  $COMPOSE -f "$COMPOSE_FILE" up \
    --build \
    --abort-on-container-exit \
    --exit-code-from test-api \
    test-db test-api test-frontend
}

# ---------- Main ----------

detect_compose

TARGET="${1:-all}"

case "$TARGET" in
  backend)  run_backend  ;;
  frontend) run_frontend ;;
  e2e)      run_e2e      ;;
  lint)     run_lint     ;;
  all)      run_all      ;;
  *)
    echo "Usage: $0 [backend|frontend|e2e|lint|all]"
    exit 1
    ;;
esac

pass "Tests passed ($TARGET)"
