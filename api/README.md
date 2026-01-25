# SensorPulse API

FastAPI backend for the SensorPulse MQTT sensor dashboard.

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn main:app --reload --port 8000
```

## Endpoints

- `GET /health` - Health check
- `GET /api/version` - API version
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation
