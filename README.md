<p align="center">
  <img src="docs/logo.png" alt="SensorPulse Logo" width="120" />
</p>

<h1 align="center">🌡️ SensorPulse</h1>

<p align="center">
  <strong>A modern, containerized dashboard for home automation sensors</strong>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#api">API</a> •
  <a href="#development">Development</a> •
  <a href="#deployment">Deployment</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python 3.11+" />
  <img src="https://img.shields.io/badge/react-18+-61dafb.svg" alt="React 18+" />
  <img src="https://img.shields.io/badge/fastapi-0.100+-009688.svg" alt="FastAPI" />
  <img src="https://img.shields.io/badge/postgresql-15+-336791.svg" alt="PostgreSQL" />
  <img src="https://img.shields.io/badge/podman-4.0+-892ca0.svg" alt="Podman" />
</p>

---

## ✨ Features

- 📊 **Real-time Dashboard** — Live sensor readings with WebSocket updates
- 🏠 **Zigbee2MQTT Integration** — Auto-discovers your sensors
- 📈 **Historical Charts** — Beautiful temperature & humidity graphs
- 📧 **Daily Reports** — Email summaries via Resend
- 🔐 **Google Auth** — Secure access with OAuth 2.0
- 🌙 **Dark Mode** — Easy on the eyes
- 📱 **Mobile Responsive** — Monitor from anywhere
- 🐳 **Fully Containerized** — Deploy with a single command
- 🔒 **Cloudflare Tunnel** — Secure external access without port forwarding

---

## 🚀 Quick Start

### Prerequisites

- [Podman](https://podman.io/) 4.0+ (or Docker)
- [Podman Compose](https://github.com/containers/podman-compose)
- Access to an MQTT broker (e.g., Zigbee2MQTT)

### 1. Clone & Configure

```bash
git clone https://github.com/yourusername/sensorpulse.git
cd sensorpulse

# Copy example environment file
cp .env.example .env
```

### 2. Edit Environment Variables

```bash
# .env
MQTT_BROKER_IP=192.168.1.100
MQTT_PORT=1883
MQTT_USER=your_user
MQTT_PASS=your_password

POSTGRES_PASSWORD=secure_password
JWT_SECRET=your_jwt_secret

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

RESEND_API_KEY=re_xxxxx
CLOUDFLARE_TUNNEL_TOKEN=your_tunnel_token
```

### 3. Deploy

```bash
./scripts/deploy.sh
```

🎉 **Done!** Open `https://sensors.yourdomain.com` (or `http://localhost:3000` for local dev)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Podman Pod: sensor_stack                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│   │  Ingester   │───▶│ PostgreSQL  │◀───│   FastAPI   │        │
│   │  (Python)   │    │             │    │   Backend   │        │
│   └──────┬──────┘    └─────────────┘    └──────┬──────┘        │
│          │                                      │               │
│          │                              ┌───────┴───────┐       │
│          ▼                              │               │       │
│   ┌─────────────┐                ┌──────┴─────┐  ┌──────┴─────┐ │
│   │ External    │                │   Nginx    │  │ Cloudflared│ │
│   │ MQTT Broker │                │  + React   │  │   Tunnel   │ │
│   └─────────────┘                └────────────┘  └──────┬─────┘ │
│                                                         │       │
└─────────────────────────────────────────────────────────┼───────┘
                                                          │
                                                          ▼
                                                    🌐 Internet
```

---

## 📡 API

Interactive API documentation available at `/docs` (Swagger) or `/redoc`.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/devices` | GET | List all discovered sensors |
| `/api/latest` | GET | Latest reading for each sensor |
| `/api/history/{device}` | GET | Historical data (24h/7d) |
| `/api/version` | GET | API version info |
| `/health` | GET | Health check |
| `/ws/sensors` | WS | Real-time sensor updates |

### Example Response

```json
[
  {
    "device": "Office Sensor",
    "temp": 22.5,
    "humidity": 45.2,
    "battery": 87,
    "last_seen": "2026-01-25T10:30:00Z"
  }
]
```

---

## 🛠️ Development

### Local Development (Hot Reload)

```bash
./scripts/dev.sh
```

This starts all services with:
- **Frontend**: `http://localhost:3000` (Vite dev server)
- **API**: `http://localhost:8000` (FastAPI with reload)
- **Database**: `localhost:5432` (PostgreSQL)

### Project Structure

```
sensorpulse/
├── api/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py
│   │   ├── routers/
│   │   ├── models/
│   │   └── services/
│   ├── alembic/            # Database migrations
│   └── Dockerfile.api
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   └── hooks/
│   └── Dockerfile.web
├── ingester/               # MQTT ingestion service
│   ├── main.py
│   └── Dockerfile.ingester
├── scripts/                # Deployment & utility scripts
├── podman-compose.yml      # Production compose
├── podman-compose.dev.yml  # Development overrides
└── .env.example
```

### Running Tests

```bash
./scripts/test.sh        # Run all tests
./scripts/lint.sh        # Run linters
```

---

## 🚢 Deployment

### Production Deployment

```bash
# Build and deploy
./scripts/deploy.sh --build --migrate

# Or step by step
./scripts/build.sh       # Build images
./scripts/migrate.sh     # Run migrations
./scripts/start.sh       # Start services
```

### Useful Commands

| Command | Description |
|---------|-------------|
| `./scripts/start.sh` | Start all services |
| `./scripts/stop.sh` | Stop all services |
| `./scripts/restart.sh` | Restart services |
| `./scripts/logs.sh` | Tail all logs |
| `./scripts/backup-db.sh` | Backup database |
| `./scripts/tunnel-status.sh` | Check Cloudflare tunnel |

### Version Management

```bash
./scripts/bump-version.sh patch  # 1.0.0 → 1.0.1
./scripts/bump-version.sh minor  # 1.0.0 → 1.1.0
./scripts/bump-version.sh major  # 1.0.0 → 2.0.0
```

---

## 📧 Email Reports

Daily sensor summaries are sent via [Resend](https://resend.com). Configure in the Settings page:

- Toggle daily reports on/off
- Set preferred delivery time
- Send test report

Reports include:
- 24-hour min/max/avg for each sensor
- Battery alerts (< 20%)
- Offline sensor warnings

---

## 🔒 Security

- **Google OAuth 2.0** for authentication
- **JWT tokens** for API access
- **Rate limiting** (100 req/min per user)
- **CORS** configured for your domain only
- **Cloudflare Tunnel** for secure external access

---

## 📖 Documentation

- [ROADMAP.md](ROADMAP.md) — Development roadmap & phases
- [DEPLOYMENT.md](DEPLOYMENT.md) — Detailed deployment guide
- [Production Requirements](docs/REQUIREMENTS-PRODUCTION.md) — System, software & service requirements for production
- [Development Requirements](docs/REQUIREMENTS-DEV.md) — Local development setup & tooling
- [Testing Requirements](docs/REQUIREMENTS-TESTING.md) — Test frameworks, commands & CI integration
- [API Docs](/docs) — Interactive Swagger documentation

---

## 🤝 Contributing

Contributions are welcome! Please read our contributing guidelines before submitting a PR.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

<p align="center">
  Made with ❤️ for home automation enthusiasts
</p>
