# Testing Requirements

Everything needed to run the SensorPulse test suite.

---

## Quick Start

```bash
# Backend — no Postgres needed (uses SQLite)
cd api && pip install -r requirements.txt && python -m pytest tests/ -v

# Frontend unit tests
cd frontend && npm install && npx vitest run

# E2E (requires dev server running)
cd frontend && npx playwright install chromium && npx playwright test
```

Or use the test script:

```bash
./scripts/test.sh            # backend + frontend (local)
./scripts/test.sh backend    # backend only (local, SQLite)
./scripts/test.sh frontend   # frontend only (local)
./scripts/test.sh e2e        # Playwright E2E (local)
./scripts/test.sh container  # backend + frontend inside Podman containers (real Postgres)
```

---

## Prerequisites

All [development requirements](REQUIREMENTS-DEV.md) must be met first.

No external services, API keys, or running databases are required for unit and integration tests. The test suite uses **SQLite via aiosqlite** for the backend and **jsdom** for the frontend.

---

## Backend Testing (Python / Pytest)

### Dependencies

Included in `api/requirements.txt`:

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | ≥ 7.4 | Test framework |
| `pytest-asyncio` | ≥ 0.23 | Async test support for FastAPI |
| `pytest-cov` | ≥ 4.1 | Coverage reporting |
| `httpx` | ≥ 0.26 | Async HTTP test client (`ASGITransport`) |
| `aiosqlite` | ≥ 0.19 | SQLite async driver (test DB) |
| `ruff` | ≥ 0.2 | Linter / formatter |

### Install

```bash
cd api
pip install -r requirements.txt
```

### Run

```bash
# All backend tests
python -m pytest tests/ -v

# With coverage report
python -m pytest tests/ --cov=. --cov-report=term-missing --cov-report=html:htmlcov

# Specific test file
python -m pytest tests/test_auth.py -v

# Specific test class
python -m pytest tests/test_routes.py::TestSensorRoutes -v
```

### Configuration

Pytest config is in `api/pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

### Test Database (Dual Mode)

The test suite supports two database modes, selected automatically:

| Mode | When | Database | `latest_readings` View |
|------|------|----------|------------------------|
| **Local** (default) | `TEST_DATABASE_URL` not set | SQLite via aiosqlite | Not available — affected tests accept 500 |
| **Container** | `TEST_DATABASE_URL` is set | PostgreSQL via asyncpg | Created by Alembic migrations |

**Local mode** — `conftest.py` sets these env vars automatically:

| Variable | Test Value | Purpose |
|----------|-----------|--------|
| `DATABASE_URL` | `sqlite:///./test.db` | SQLite instead of Postgres |
| `SECRET_KEY` | `test-secret-key-for-jwt-signing` | JWT signing |
| `GOOGLE_CLIENT_ID` | `""` (empty) | Disables OAuth |
| `GOOGLE_CLIENT_SECRET` | `""` (empty) | Disables OAuth |
| `RESEND_API_KEY` | `""` (empty) | Disables email sending |

**Container mode** — `podman-compose.test.yml` sets `TEST_DATABASE_URL` pointing to a real Postgres container. Alembic migrations run first, so the `latest_readings` view and all indexes exist.

### Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `setup_database` | session | Creates/drops all tables via `Base.metadata` |
| `db_session` | function | Transactional session, rolls back after each test |
| `client` | function | `httpx.AsyncClient` with ASGI transport |
| `test_user_data` | function | Dict with standard test user fields |
| `test_user` | function | User row created in test DB |
| `auth_headers` | function | `{"Authorization": "Bearer <jwt>"}` |
| `auth_client` | function | `client` with auth headers pre-applied |
| `seed_readings` | function | 3 devices × 5 readings (office, bedroom, fridge) |

### Test Files (84 tests)

| File | Tests | What It Covers |
|------|-------|----------------|
| `test_auth.py` | 6 | JWT creation, decode, expiry, invalid/tampered tokens |
| `test_schemas.py` | 14 | All Pydantic models: SensorReading, User, HistoryQuery, Report, Token |
| `test_middleware.py` | 6 | Rate limiter: allow, block, per-IP limits, X-Forwarded-For |
| `test_websocket.py` | 10 | WebSocketManager: connect, subscribe, broadcast, cleanup |
| `test_routes.py` | 18 | All HTTP routes: health, sensors, auth, reports |
| `test_services.py` | 13 | SensorService + UserService: queries, CRUD, preferences |
| `test_parser.py` | 17 | Ingester payload parsing: Type A/B, filtering, stats |

### Coverage Target

| Scope | Target |
|-------|--------|
| Overall | **80%+** |
| API routes | 90%+ |
| Models / schemas | 95%+ |
| Auth flow | 85%+ |

---

## Frontend Testing (TypeScript / Vitest)

### Dependencies

Included in `frontend/package.json` devDependencies:

| Package | Version | Purpose |
|---------|---------|---------|
| `vitest` | ^1.1 | Unit/component test runner |
| `@vitest/coverage-v8` | ^1.1 | Code coverage via V8 |
| `jsdom` | ^23.0 | Browser DOM simulation |
| `@testing-library/react` | ^14.1 | React component testing utilities |
| `@testing-library/jest-dom` | ^6.1 | DOM assertion matchers |
| `@testing-library/user-event` | ^14.5 | Simulated user interactions |

### Install

```bash
cd frontend
npm install
```

### Run

```bash
# All frontend tests
npm test

# Single run (no watch)
npx vitest run

# Watch mode (re-runs on save)
npm test -- --watch

# With UI dashboard
npm run test:ui

# With coverage
npx vitest run --coverage

# Specific file
npx vitest src/types/index.test.ts
```

### Configuration

Test config is in `frontend/vite.config.ts` under the `test` block:

- **Environment:** jsdom
- **Globals:** enabled (no need to import `describe`, `it`, `expect`)
- **Setup file:** `src/test/setup.ts` (mocks `matchMedia`, `localStorage`, `ResizeObserver`)
- **Coverage:** V8 provider

### Test Structure

```
frontend/src/
├── types/
│   └── index.test.ts                      ← Type helper tests (22)
├── components/
│   └── __tests__/
│       ├── SensorCard.test.tsx             ← Component tests (14)
│       └── TemperatureChart.test.tsx       ← Chart tests (4)
├── hooks/
│   └── __tests__/
│       └── useDarkMode.test.ts            ← Hook tests (8)
└── test/
    └── setup.ts                           ← Global test setup
```

### Test Files (48 tests)

| File | Tests | What It Covers |
|------|-------|----------------|
| `types/index.test.ts` | 22 | `getTemperatureRange/Color`, `getHumidityRange/Color`, `getBatteryColor`, badge classes |
| `SensorCard.test.tsx` | 14 | Rendering, temp/humidity display, battery bar, online/stale/offline status, click handler |
| `TemperatureChart.test.tsx` | 4 | Chart container, empty state message, humidity gradient |
| `useDarkMode.test.ts` | 8 | Theme toggle cycle, localStorage persistence, resolved value, `isDark` flag |

---

## End-to-End Testing (Playwright)

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `@playwright/test` | ^1.40 | E2E browser testing |

### Install

```bash
cd frontend
npx playwright install chromium
```

### Run

```bash
# All E2E tests
npx playwright test

# Headed (visible browser)
npx playwright test --headed

# Specific project
npx playwright test --project=chromium

# Generate HTML report
npx playwright show-report
```

### Configuration

`frontend/playwright.config.ts` defines:

| Setting | Value |
|---------|-------|
| Test dir | `e2e/` |
| Base URL | `http://localhost:5173` (or `$E2E_BASE_URL`) |
| Projects | `chromium`, `mobile-chrome` (Pixel 5) |
| Web server | Auto-starts `npm run dev` (local) |
| Retries | 2 in CI, 0 locally |

### E2E Specs

| File | What It Tests |
|------|---------------|
| `e2e/dashboard.spec.ts` | Page load, SensorPulse branding, sensor cards, dark mode toggle |
| `e2e/auth.spec.ts` | Login UI visibility, auth-protected routes (settings, reports) |

---

## Containerized Testing

Run the full suite inside Podman/Docker containers — no local Python or Node.js required:

```bash
# Via the test script (recommended)
./scripts/test.sh container

# Or directly with podman-compose
podman-compose -f podman-compose.test.yml up --build --abort-on-container-exit
```

The script auto-detects `podman-compose` or `docker compose` and cleans up containers after the run.

### What Runs

`podman-compose.test.yml` spins up three containers:

| Container | Image | What It Does |
|-----------|-------|--------------|
| `test-db` | postgres:16-alpine | Ephemeral Postgres on tmpfs (port 5433) |
| `test-api` | `./api/Dockerfile.dev` | `alembic upgrade head` → `pytest` (84 tests against real Postgres) |
| `test-frontend` | `./frontend/Dockerfile.dev` | `vitest run` (48 unit tests) |

### Advantages Over Local Tests

- **Real Postgres**: The `latest_readings` SQL view exists, so all route tests assert `200`
- **Isolated**: Containers are destroyed after the run — no leftover state
- **Reproducible**: Same environment as CI/production
- **No setup**: No need to install Python, Node, or any dependencies locally

---

## Linting

Run all linters before tests:

```bash
./scripts/lint.sh          # both backend + frontend
./scripts/lint.sh backend  # ruff only
./scripts/lint.sh frontend # eslint + tsc only
```

| Tool | Language | Command |
|------|----------|---------|
| `ruff check` | Python | Lint + auto-fix |
| `ruff format` | Python | Formatter check |
| `eslint` | TypeScript/React | Lint with `--max-warnings 0` |
| `tsc --noEmit` | TypeScript | Type checking |

---

## API Keys for Production Testing

Unit and integration tests **do not require any API keys**. These are only needed when testing against real external services:

| Credential | Env Variable | Where to Get It | Needed For |
|---|---|---|---|
| Google OAuth Client ID | `GOOGLE_CLIENT_ID` | [Google Cloud Console](https://console.cloud.google.com/apis/credentials) | Login flow |
| Google OAuth Client Secret | `GOOGLE_CLIENT_SECRET` | Same as above | Login flow |
| JWT Secret | `SECRET_KEY` | `openssl rand -hex 32` | Token signing (tests use `test-secret`) |
| Resend API Key | `RESEND_API_KEY` | [resend.com/api-keys](https://resend.com/api-keys) | Email report sending |
| Resend From Email | `EMAIL_FROM` | Verified domain in Resend | Email sender address |
| MQTT Broker | `MQTT_BROKER_IP`, `MQTT_USER`, `MQTT_PASS` | Your Zigbee2MQTT broker | Ingester only |
| Cloudflare Tunnel | `CLOUDFLARE_TUNNEL_TOKEN` | [Cloudflare Zero Trust](https://one.dash.cloudflare.com/) | Production tunnel only |

---

## CI Integration (Phase 8)

Tests will run automatically in GitHub Actions. See [ROADMAP.md](../ROADMAP.md) Phase 8 for the full CI/CD specification.
