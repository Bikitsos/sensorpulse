# ================================
# SensorPulse - Database Migrations
# ================================

## Overview

This project uses **Alembic** for database migrations. All migrations are stored in `api/alembic/versions/`.

## Running Migrations

### Using the migration script (recommended)

```bash
# Upgrade to latest version
./scripts/migrate.sh upgrade

# Upgrade to specific revision
./scripts/migrate.sh upgrade 001_initial_schema

# Downgrade by one revision
./scripts/migrate.sh downgrade

# Downgrade to specific revision
./scripts/migrate.sh downgrade 001_initial_schema

# Show current revision
./scripts/migrate.sh current

# Show migration history
./scripts/migrate.sh history
```

### Using Alembic directly

```bash
cd api

# Upgrade to latest
alembic upgrade head

# Downgrade one revision
alembic downgrade -1

# Show current revision
alembic current

# Generate new migration from model changes
alembic revision --autogenerate -m "description"
```

### In Docker/Podman

Migrations run automatically when the API container starts. To run manually:

```bash
podman-compose exec api alembic upgrade head
```

## Creating New Migrations

1. Modify models in `api/db/models.py`
2. Generate migration:
   ```bash
   ./scripts/migrate.sh generate "add_new_field"
   ```
3. Review the generated migration in `api/alembic/versions/`
4. Apply the migration:
   ```bash
   ./scripts/migrate.sh upgrade
   ```

## Rollback Procedures

### Rollback one migration
```bash
./scripts/migrate.sh downgrade
```

### Rollback to specific version
```bash
./scripts/migrate.sh downgrade 001_initial_schema
```

### Full rollback (dangerous!)
```bash
./scripts/migrate.sh downgrade base
```

## Schema Overview

### Tables

- **sensor_readings** - Time-series sensor data from Zigbee2MQTT
- **users** - User accounts for Google OAuth authentication

### Views

- **latest_readings** - Most recent reading per sensor topic

### Indexes

- `ix_sensor_readings_topic` - Fast topic lookups
- `ix_sensor_readings_time` - Time range queries
- `ix_sensor_readings_topic_time` - Combined topic + time queries
- `ix_users_email` - Unique email lookup
