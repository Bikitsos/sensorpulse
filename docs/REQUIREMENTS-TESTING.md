# Testing Requirements

Everything needed to run the SensorPulse test suite.

---

## Quick Start

All tests run inside **Podman/Docker containers**. No local Python, Node.js, or database required.

```bash
./scripts/test.sh            # backend + frontend (default)
./scripts/test.sh backend    # backend only (Postgres container)
./scripts/test.sh frontend   # frontend unit tests only
./scripts/test.sh e2e        # Playwright E2E (full stack in containers)
./scripts/test.sh lint       # ruff + eslint + tsc
```

The script auto-detects `podman-compose` or `docker compose` and cleans up containers on exit.

---

## Prerequisites

- **Podman** (with `podman-compose`) or **Docker** (with `docker compose`)
- No local Python, Node.js, or PostgreSQL installation required
- All dependencies are installed inside the container images

---

## Backend Testing (Python / Pytest)

### Dependencies

Installed inside the container via `api/requirements.txt`:

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | ≥ 7.4 | Test framework |
| `pytest-asyncio` | ≥ 0.23 | Async test support for FastAPI |
| `pytest-cov` | ≥ 4.1 | Coverage reporting |
| `httpx` | ≥ 0.26 | Async HTTP test client (`ASGITransport`) |
| `ruff` | ≥ 0.2 | Linter / formatter |

### Run

```bash
./scripts/test.sh backend
```

The container runs `alembic upgrade head` then `pytest tests/ -v --tb=short --cov`.

### Configuration

Pytest config is in `api/pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

### Test Database

Tests run against a **real PostgreSQL 16** container (ephemeral, tmpfs-backed). Alembic migrations create all tables and the `latest_readings` view, so tests exercise the same schema as production.

`podman-compose.test.yml` sets these environment variables for the test-api container:

| Variable | Test Value | Purpose |
|----------|-----------|--------|
| `TEST_DATABASE_URL` | `postgresql+asyncpg://sp_test:sp_test_pass@test-db:5432/sensorpulse_test` | Tells conftest to use Postgres |
| `DATABASE_URL` | (same as above) | App-level DB connection |
| `SECRET_KEY` | `test-secret-key-not-for-production` | JWT signing |
| `GOOGLE_CLIENT_ID` | `""` (empty) | Disables OAuth |
| `GOOGLE_CLIENT_SECRET` | `""` (empty) | Disables OAuth |
| `RESEND_API_KEY` | `""` (empty) | Disables email sending |

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

Installed inside the container via `frontend/package.json` devDependencies:

| Package | Version | Purpose |
|---------|---------|---------|
| `vitest` | ^1.1 | Unit/component test runner |
| `@vitest/coverage-v8` | ^1.1 | Code coverage via V8 |
| `jsdom` | ^23.0 | Browser DOM simulation |
| `@testing-library/react` | ^14.1 | React component testing utilities |
| `@testing-library/jest-dom` | ^6.1 | DOM assertion matchers |
| `@testing-library/user-event` | ^14.5 | Simulated user interactions |

### Run

```bash
./scripts/test.sh frontend
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

### Run (inside container)

```bash
./scripts/test.sh e2e
```

The `test-e2e` container uses `frontend/Dockerfile.e2e` (based on `mcr.microsoft.com/playwright`) with Chromium pre-installed.

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

All tests run inside containers via `podman-compose.test.yml`.

### Services

| Container | Image | Profile | What It Does |
|-----------|-------|---------|-------------|
| `test-db` | postgres:16-alpine | default | Ephemeral Postgres on tmpfs (port 5433) |
| `test-api` | `./api/Dockerfile.dev` | default | `alembic upgrade head` → `pytest` (84 tests) |
| `test-frontend` | `./frontend/Dockerfile.dev` | default | `vitest run` (48 unit tests) |
| `lint-api` | `./api/Dockerfile.dev` | lint | `ruff check` + `ruff format --check` |
| `lint-frontend` | `./frontend/Dockerfile.dev` | lint | `eslint` + `tsc --noEmit` |
| `test-api-serve` | `./api/Dockerfile.dev` | e2e | FastAPI server for E2E |
| `test-frontend-serve` | `./frontend/Dockerfile.dev` | e2e | Vite dev server for E2E |
| `test-e2e` | `./frontend/Dockerfile.e2e` | e2e | Playwright (Chromium) E2E tests |

### Running

```bash
./scripts/test.sh            # backend + frontend (default)
./scripts/test.sh backend    # test-db + test-api
./scripts/test.sh frontend   # test-frontend
./scripts/test.sh e2e        # full stack + Playwright
./scripts/test.sh lint       # lint-api + lint-frontend
```

Or directly with compose:

```bash
podman-compose -f podman-compose.test.yml up --build --abort-on-container-exit
```

### Why Containers

- **Real Postgres**: The `latest_readings` SQL view and all indexes exist
- **Isolated**: Ephemeral tmpfs DB, containers destroyed on exit
- **Reproducible**: Same images and dependencies every run
- **No setup**: No local Python, Node, or Postgres needed

---

## Linting

Run all linters inside containers:

```bash
./scripts/lint.sh        # shortcut for ./scripts/test.sh lint
./scripts/test.sh lint   # same thing
```

| Tool | Language | Container | What It Checks |
|------|----------|-----------|----------------|
| `ruff check` | Python | lint-api | Lint rules |
| `ruff format --check` | Python | lint-api | Formatting |
| `eslint` | TypeScript/React | lint-frontend | Lint with `--max-warnings 0` |
| `tsc --noEmit` | TypeScript | lint-frontend | Type checking |

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
