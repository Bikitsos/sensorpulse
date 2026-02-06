# Production Requirements

Everything needed to run SensorPulse in production.

---

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 2 GB | 4 GB |
| Disk | 10 GB | 50 GB+ (depends on data retention) |
| OS | Linux (x86_64 / arm64) | Debian 12 / Ubuntu 22.04+ / RHEL 9 |

---

## Software Prerequisites

| Software | Version | Purpose |
|----------|---------|---------|
| [Podman](https://podman.io/) | 4.0+ | Container runtime |
| [Podman Compose](https://github.com/containers/podman-compose) | 1.0+ | Container orchestration |
| Git | 2.30+ | Version control |

> **Note:** Docker / Docker Compose can be used as a drop-in replacement for Podman.

---

## Container Images (built automatically)

| Service | Base Image | Exposed Port |
|---------|-----------|-------------|
| **API** | `python:3.12-slim` | 8000 (internal) |
| **Ingester** | `python:3.12-slim` | — |
| **Frontend** | `node:20-alpine` → `nginx:alpine` (multi-stage) | 80 |
| **Database** | `postgres:16-alpine` | 5432 (internal) |
| **Tunnel** | `cloudflare/cloudflared:latest` | — |

---

## Python Dependencies — API (`api/requirements.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | ≥ 0.109 | Web framework |
| `uvicorn[standard]` | ≥ 0.27 | ASGI server |
| `sqlalchemy` | ≥ 2.0 | ORM / database toolkit |
| `asyncpg` | ≥ 0.29 | Async PostgreSQL driver |
| `alembic` | ≥ 1.13 | Database migrations |
| `psycopg2-binary` | ≥ 2.9.9 | Sync PostgreSQL driver (migrations) |
| `python-jose[cryptography]` | ≥ 3.3 | JWT tokens |
| `passlib[bcrypt]` | ≥ 1.7.4 | Password hashing |
| `authlib` | ≥ 1.3 | Google OAuth 2.0 |
| `httpx` | ≥ 0.26 | Async HTTP client |
| `resend` | ≥ 0.7 | Email delivery (daily reports) |
| `pydantic` | ≥ 2.5 | Data validation |
| `pydantic-settings` | ≥ 2.1 | Settings from env files |
| `python-dotenv` | ≥ 1.0 | `.env` file loading |
| `python-multipart` | ≥ 0.0.6 | Form data parsing |
| `structlog` | ≥ 24.1 | Structured JSON logging |

## Python Dependencies — Ingester (`ingester/requirements.txt`)

| Package | Version | Purpose |
|---------|---------|---------|
| `paho-mqtt` | ≥ 2.0 | MQTT client |
| `sqlalchemy` | ≥ 2.0 | ORM / database toolkit |
| `psycopg2-binary` | ≥ 2.9.9 | PostgreSQL driver |
| `pydantic` | ≥ 2.5 | Data validation |
| `pydantic-settings` | ≥ 2.1 | Settings from env files |
| `python-dotenv` | ≥ 1.0 | `.env` file loading |
| `aiohttp` | ≥ 3.9 | Health-check HTTP server |
| `structlog` | ≥ 24.1 | Structured JSON logging |

## Frontend Dependencies (`frontend/package.json`)

| Package | Version | Purpose |
|---------|---------|---------|
| `react` | ^18.2 | UI library |
| `react-dom` | ^18.2 | DOM renderer |
| `react-router-dom` | ^6.21 | Client-side routing |
| `recharts` | ^2.10 | Data visualization / charts |
| `@tanstack/react-query` | ^5.17 | Server-state management |
| `axios` | ^1.6 | HTTP client |
| `date-fns` | ^3.0 | Date formatting |
| `clsx` | ^2.1 | Conditional class names |
| `lucide-react` | ^0.303 | Icon set |

---

## External Services

| Service | Required? | Purpose | Free Tier |
|---------|-----------|---------|-----------|
| **MQTT Broker** | ✅ Yes | Zigbee2MQTT data source | Self-hosted |
| **Google Cloud Console** | ✅ Yes | OAuth 2.0 credentials | Free |
| [Resend](https://resend.com) | Optional | Email reports | 100 emails/day |
| [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/) | Optional | Secure remote access | Free |

---

## Environment Variables

All configuration is via a single `.env` file. See [`.env.example`](../.env.example) for the template.

| Variable | Required | Description |
|----------|----------|-------------|
| `POSTGRES_USER` | ✅ | Database user |
| `POSTGRES_PASSWORD` | ✅ | Database password |
| `POSTGRES_DB` | ✅ | Database name |
| `DATABASE_URL` | ✅ | Full connection string |
| `MQTT_BROKER_IP` | ✅ | MQTT broker address |
| `MQTT_PORT` | ✅ | MQTT broker port (default: 1883) |
| `MQTT_USER` | ✅ | MQTT username |
| `MQTT_PASS` | ✅ | MQTT password |
| `MQTT_TOPIC` | ✅ | MQTT topic pattern (default: `zigbee2mqtt/+`) |
| `SECRET_KEY` | ✅ | JWT signing key |
| `GOOGLE_CLIENT_ID` | ✅ | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | ✅ | Google OAuth client secret |
| `OAUTH_REDIRECT_URI` | ✅ | OAuth callback URL |
| `RESEND_API_KEY` | Optional | Resend API key for email reports |
| `EMAIL_FROM` | Optional | Sender email address |
| `CLOUDFLARE_TUNNEL_TOKEN` | Optional | Cloudflare tunnel token |
| `APP_VERSION` | Optional | Displayed in UI / API |

---

## Network / Firewall

| Direction | Port | Protocol | Purpose |
|-----------|------|----------|---------|
| **Outbound** | 1883 | TCP | Connect to MQTT broker |
| **Outbound** | 443 | TCP | Google OAuth, Resend API, Cloudflare Tunnel |
| **Inbound** | 80/443 | TCP | Web UI (only if **not** using Cloudflare Tunnel) |
| **Internal** | 5432 | TCP | PostgreSQL (pod-internal only) |
| **Internal** | 8000 | TCP | FastAPI (pod-internal only) |

> With Cloudflare Tunnel, **no inbound ports** need to be opened.

---

## Data Storage

| Volume | Mount Path | Purpose |
|--------|-----------|---------|
| `pg_data` | `/var/lib/postgresql/data` | PostgreSQL persistent data |

Sensor data is retained indefinitely. Estimate ~1 KB per reading; at 6 sensors reporting every 5 minutes ≈ **2.5 GB per year**.
