"""Initial schema: sensor_readings and users tables

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-01-25

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ===========================================
    # Create sensor_readings table
    # ===========================================
    op.create_table(
        'sensor_readings',
        sa.Column('time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('topic', sa.Text(), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=True),
        sa.Column('humidity', sa.Float(), nullable=True),
        sa.Column('battery', sa.Integer(), nullable=True),
        sa.Column('linkquality', sa.Integer(), nullable=True),
        sa.Column('raw_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint('time', 'topic'),
    )
    
    # Indexes for sensor_readings
    op.create_index('ix_sensor_readings_topic', 'sensor_readings', ['topic'], unique=False)
    op.create_index('ix_sensor_readings_time', 'sensor_readings', ['time'], unique=False)
    op.create_index('ix_sensor_readings_topic_time', 'sensor_readings', ['topic', 'time'], unique=False)
    
    # ===========================================
    # Create users table
    # ===========================================
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('picture', sa.Text(), nullable=True),
        sa.Column('is_allowed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('daily_report', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('report_time', sa.Time(), nullable=True, server_default='08:00:00'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Indexes for users
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    
    # ===========================================
    # Create latest_readings view
    # ===========================================
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
    
    # Add comment to the view
    op.execute("""
        COMMENT ON VIEW latest_readings IS 
        'Returns the most recent reading for each sensor topic';
    """)


def downgrade() -> None:
    # Drop view first
    op.execute("DROP VIEW IF EXISTS latest_readings;")
    
    # Drop indexes
    op.drop_index('ix_users_email', table_name='users')
    op.drop_index('ix_sensor_readings_topic_time', table_name='sensor_readings')
    op.drop_index('ix_sensor_readings_time', table_name='sensor_readings')
    op.drop_index('ix_sensor_readings_topic', table_name='sensor_readings')
    
    # Drop tables
    op.drop_table('users')
    op.drop_table('sensor_readings')
