# SensorPulse Ingester

MQTT ingestion service that connects to an external broker and stores sensor data in PostgreSQL.

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run the ingester
python main.py
```

## Environment Variables

- `MQTT_BROKER_IP` - External MQTT broker IP address
- `MQTT_PORT` - MQTT broker port (default: 1883)
- `MQTT_USER` - MQTT username
- `MQTT_PASS` - MQTT password
- `MQTT_TOPIC` - Topic to subscribe to (default: zigbee2mqtt/+)
- `DATABASE_URL` - PostgreSQL connection string
