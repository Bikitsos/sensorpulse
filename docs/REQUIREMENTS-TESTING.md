# Testing Requirements

Everything needed to run the SensorPulse test suite.

---

## Prerequisites

All [development requirements](REQUIREMENTS-DEV.md) must be met first.

---

## Backend Testing (Python / Pytest)

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | ≥ 7.4 | Test framework |
| `pytest-asyncio` | ≥ 0.23 | Async test support for FastAPI |
| `pytest-cov` | ≥ 4.1 | Coverage reporting |
| `httpx` | ≥ 0.26 | Async HTTP client for `TestClient` |
| `factory-boy` | ≥ 3.3 | Test data factories |
| `faker` | ≥ 22.0 | Fake data generation |

### Install

```bash
cd api
source .venv/bin/activate
pip install pytest pytest-asyncio pytest-cov httpx factory-boy faker
```

### Run

```bash
# All backend tests
pytest

# With coverage
pytest --cov=. --cov-report=html

# Specific module
pytest tests/test_sensors.py -v

# Only unit tests (skip integration)
pytest -m "not integration"
```

### Test Database

Tests use an isolated PostgreSQL database to avoid polluting development data.

| Variable | Value |
|----------|-------|
| `TEST_DATABASE_URL` | `postgresql://sensorpulse:changeme@localhost:5432/sensorpulse_test` |

The test database is created automatically by `podman-compose.test.yml` or can be set up manually:

```sql
CREATE DATABASE sensorpulse_test;
GRANT ALL PRIVILEGES ON DATABASE sensorpulse_test TO sensorpulse;
```

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

| Package | Version | Purpose |
|---------|---------|---------|
| `vitest` | ^1.1 | Unit/component test runner |
| `@testing-library/react` | ^14.1 | React component testing utilities |
| `@testing-library/jest-dom` | ^6.1 | DOM assertion matchers |
| `@testing-library/user-event` | ^14.5 | Simulated user interactions |
| `jsdom` | ^23.0 | Browser DOM simulation (Vitest env) |
| `msw` | ^2.1 | API mocking (Mock Service Worker) |

### Install

```bash
cd frontend
npm install
# Dev dependencies are included in package.json
```

### Run

```bash
# All frontend tests
npm test

# Watch mode (re-runs on save)
npm test -- --watch

# With UI
npm run test:ui

# Coverage
npx vitest --coverage

# Specific file
npx vitest src/components/SensorCard.test.tsx
```

### Test Structure

```
frontend/src/
├── components/
│   ├── SensorCard.tsx
│   ├── SensorCard.test.tsx          ← Unit test
│   ├── TemperatureChart.tsx
│   └── TemperatureChart.test.tsx
├── hooks/
│   ├── useDarkMode.ts
│   └── useDarkMode.test.ts
├── pages/
│   ├── Dashboard.tsx
│   └── Dashboard.test.tsx
└── __mocks__/
    └── handlers.ts                  ← MSW API handlers
```

---

## End-to-End Testing (Playwright)

### Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `@playwright/test` | ^1.41 | E2E browser testing |

### Install

```bash
cd frontend
npm install -D @playwright/test
npx playwright install    # Downloads browser binaries
```

### Run

```bash
# All E2E tests
npx playwright test

# Headed (visible browser)
npx playwright test --headed

# Specific browser
npx playwright test --project=chromium

# Generate report
npx playwright show-report
```

### E2E Test Scenarios

| Scenario | What It Tests |
|----------|---------------|
| Login flow | Google OAuth redirect → callback → dashboard |
| Dashboard | Sensor cards render, data loads, chart opens |
| Dark mode | Toggle cycles light → dark → system |
| Settings | Report preferences save and persist |
| Mobile | Responsive layout on 375px viewport |
| WebSocket | Live updates appear on sensor cards |

---

## Containerized Testing

Run the full test suite inside containers (no local Python/Node needed):

```bash
./scripts/test.sh
```

This uses `podman-compose.test.yml` which spins up:

| Container | Purpose |
|-----------|---------|
| `test-db` | Isolated PostgreSQL for tests |
| `test-api` | Runs `pytest` inside API container |
| `test-frontend` | Runs `vitest` + `playwright` inside Node container |

### Compose File

```yaml
# podman-compose.test.yml (to be created in Phase 7)
services:
  test-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: sensorpulse_test
      POSTGRES_USER: sensorpulse
      POSTGRES_PASSWORD: test_password

  test-api:
    build:
      context: ./api
      dockerfile: Dockerfile.dev
    command: pytest --cov=. --cov-report=term-missing
    depends_on:
      - test-db

  test-frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    command: npm test -- --run
    depends_on:
      - test-api
```

---

## Linting (Pre-test)

Linters run before tests in CI to catch issues early.

| Tool | Language | Command |
|------|----------|---------|
| `ruff` | Python | `ruff check api/` |
| `black` | Python | `black --check api/` |
| `eslint` | TypeScript/React | `cd frontend && npm run lint` |
| `tsc` | TypeScript | `cd frontend && npx tsc --noEmit` |

Run all linters:

```bash
./scripts/lint.sh
```

---

## CI Integration (Phase 8)

Tests will run automatically in GitHub Actions on:

| Trigger | Pipeline |
|---------|----------|
| Push to `main` | Lint → Test → Build → Deploy |
| Pull Request | Lint → Test → Build (no deploy) |
| Tag `v*` | Build → Push images → Create release |

See [ROADMAP.md](../ROADMAP.md) Phase 8 for full CI/CD specification.
