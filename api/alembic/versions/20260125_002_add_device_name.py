"""Add device_name column to sensor_readings

Revision ID: 002_add_device_name
Revises: 001_initial_schema
Create Date: 2026-01-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002_add_device_name'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add device_name column
    op.add_column(
        'sensor_readings',
        sa.Column('device_name', sa.String(length=255), nullable=True)
    )
    
    # Populate device_name from existing topic data
    # Extracts the last part after '/' (e.g., 'zigbee2mqtt/sensor1' -> 'sensor1')
    op.execute("""
        UPDATE sensor_readings 
        SET device_name = CASE 
            WHEN position('/' in topic) > 0 
            THEN substring(topic from '[^/]+$')
            ELSE topic
        END
    """)
    
    # Make column NOT NULL after populating
    op.alter_column('sensor_readings', 'device_name', nullable=False)
    
    # Add index for device_name
    op.create_index('ix_sensor_readings_device_name', 'sensor_readings', ['device_name'], unique=False)
    
    # Update latest_readings view to include device_name
    op.execute("DROP VIEW IF EXISTS latest_readings;")
    op.execute("""
        CREATE OR REPLACE VIEW latest_readings AS
        SELECT DISTINCT ON (topic)
            time,
            topic,
            device_name,
            temperature,
            humidity,
            battery,
            linkquality,
            raw_data
        FROM sensor_readings
        ORDER BY topic, time DESC;
    """)


def downgrade() -> None:
    # Recreate view without device_name
    op.execute("DROP VIEW IF EXISTS latest_readings;")
    op.execute("""
        CREATE OR REPLACE VIEW latest_readings AS
        SELECT DISTINCT ON (topic)
            time,
            topic,
            temperature,
            humidity,
            battery,
            linkquality,
            raw_data
        FROM sensor_readings
        ORDER BY topic, time DESC;
    """)
    
    # Drop index and column
    op.drop_index('ix_sensor_readings_device_name', table_name='sensor_readings')
    op.drop_column('sensor_readings', 'device_name')
