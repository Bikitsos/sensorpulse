#!/usr/bin/env bash
# ================================
# SensorPulse - Lint Runner Script
# ================================
# Runs linters inside Podman/Docker containers.
# Shortcut for: ./scripts/test.sh lint
#
# Usage: ./scripts/lint.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec "$SCRIPT_DIR/test.sh" lint
