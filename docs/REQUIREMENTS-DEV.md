# Development Requirements

Everything needed to develop and contribute to SensorPulse locally.

---

## System Requirements

| Requirement | Minimum |
|-------------|---------|
| CPU | 2 cores |
| RAM | 4 GB |
| Disk | 5 GB free |
| OS | macOS 13+, Linux, or Windows 11 (WSL2) |

---

## Required Software

| Software | Version | Purpose | Install |
|----------|---------|---------|---------|
| [Podman](https://podman.io/) | 4.0+ | Container runtime | `brew install podman` / `apt install podman` |
| [Podman Compose](https://github.com/containers/podman-compose) | 1.0+ | Orchestration | `pip install podman-compose` |
| [Python](https://www.python.org/) | 3.12+ | API & Ingester development | `brew install python@3.12` |
| [Node.js](https://nodejs.org/) | 20 LTS+ | Frontend development | `brew install node@20` |
| [Git](https://git-scm.com/) | 2.30+ | Version control | Pre-installed on macOS/Linux |

### Optional (recommended)

| Software | Purpose | Install |
|----------|---------|---------|
| [VS Code](https://code.visualstudio.com/) | Editor with great extension support | `brew install --cask visual-studio-code` |
| [DBeaver](https://dbeaver.io/) / pgAdmin | Database GUI | `brew install --cask dbeaver-community` |
| [MQTT Explorer](https://mqtt-explorer.com/) | MQTT debugging | `brew install --cask mqtt-explorer` |

---

## VS Code Extensions (recommended)

| Extension | ID |
|-----------|----|
| Python | `ms-python.python` |
| Pylance | `ms-python.vscode-pylance` |
| ESLint | `dbaeumer.vscode-eslint` |
| Tailwind CSS IntelliSense | `bradlc.vscode-tailwindcss` |
| Prettier | `esbenp.prettier-vscode` |
| REST Client | `humao.rest-client` |

---

## Python Dependencies (API)

All production deps plus dev extras installed by `Dockerfile.dev`:

| Package | Version | Purpose |
|---------|---------|---------|
| *All from [production](REQUIREMENTS-PRODUCTION.md#python-dependencies--api-apirequirementstxt)* | | |
| `pytest` | ≥ 7.4 | Test runner |
| `pytest-asyncio` | ≥ 0.23 | Async test support |
| `httpx` | ≥ 0.26 | Async HTTP test client |
| `ruff` | ≥ 0.2 | Python linter & formatter |
| `black` | ≥ 24.1 | Code formatter |

Install locally (outside containers):

```bash
cd api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install pytest pytest-asyncio ruff black
```

## Node.js Dependencies (Frontend)

All production deps plus:

| Package | Version | Purpose |
|---------|---------|---------|
| *All from [production](REQUIREMENTS-PRODUCTION.md#frontend-dependencies-frontendpackagejson)* | | |
| `typescript` | ^5.3 | Type checking |
| `vite` | ^5.0 | Dev server & bundler |
| `vitest` | ^1.1 | Unit test runner |
| `@testing-library/react` | ^14.1 | React component testing |
| `@testing-library/jest-dom` | ^6.1 | DOM assertion matchers |
| `eslint` | ^8.55 | Linter |
| `eslint-plugin-react-hooks` | ^4.6 | React hooks lint rules |
| `eslint-plugin-react-refresh` | ^0.4.5 | Fast-refresh lint rules |
| `@vitejs/plugin-react` | ^4.2 | React Vite plugin |
| `tailwindcss` | ^3.4 | Utility-first CSS framework |
| `postcss` | ^8.4 | CSS processing |
| `autoprefixer` | ^10.4 | Vendor prefix automation |

Install locally (outside containers):

```bash
cd frontend
npm install
```

---

## Local Development Ports

| Service | URL | Notes |
|---------|-----|-------|
| Frontend (Vite) | `http://localhost:3000` | Hot-reload enabled |
| API (FastAPI) | `http://localhost:8000` | Auto-reload on save |
| API Docs (Swagger) | `http://localhost:8000/docs` | Only in debug mode |
| API Docs (ReDoc) | `http://localhost:8000/redoc` | Only in debug mode |
| PostgreSQL | `localhost:5432` | Direct access for tools |

---

## Environment Setup

1. **Clone the repo:**
   ```bash
   git clone https://github.com/Bikitsos/sensorpulse.git
   cd sensorpulse
   ```

2. **Create `.env`:**
   ```bash
   cp .env.example .env
   # Edit .env with your MQTT broker credentials
   ```

3. **Start dev environment:**
   ```bash
   ./scripts/dev.sh
   # or manually:
   podman-compose -f podman-compose.yml -f podman-compose.dev.yml up
   ```

4. **Run database migrations:**
   ```bash
   ./scripts/migrate.sh
   ```

---

## Development Workflow

```
┌──────────┐    ┌──────────┐    ┌──────────┐
│  Edit    │───▶│  Save    │───▶│  Auto    │
│  Code    │    │  File    │    │  Reload  │
└──────────┘    └──────────┘    └──────────┘
                                     │
                              ┌──────┴───────┐
                              │              │
                        ┌─────┴────┐   ┌─────┴────┐
                        │ Vite HMR │   │ Uvicorn  │
                        │ (React)  │   │ --reload │
                        └──────────┘   └──────────┘
```

- **Frontend:** Vite dev server with HMR — changes reflect instantly
- **API:** Uvicorn `--reload` flag — restarts on Python file changes
- **Ingester:** Volume-mounted — restart container to pick up changes
- **Database:** Persistent volume — data survives container restarts

---

## Code Style

| Language | Tool | Config |
|----------|------|--------|
| Python | `ruff` + `black` | `pyproject.toml` |
| TypeScript/React | `eslint` + `prettier` | `.eslintrc.cjs` |
| CSS | Tailwind utility classes | `tailwind.config.js` |

Run linters:

```bash
# Python
cd api && ruff check . && black --check .

# Frontend
cd frontend && npm run lint
```
