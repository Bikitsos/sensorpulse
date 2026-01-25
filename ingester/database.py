# ================================
# SensorPulse Ingester - Database Writer
# ================================

import asyncio
from datetime import datetime
from typing import List, Dict, Any
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from config import settings
from logger import logger
from parser import ParsedReading


class DatabaseWriter:
    """
    Handles writing sensor readings to PostgreSQL.
    
    Features:
    - Connection pooling
    - Batch inserts for efficiency
    - Automatic reconnection
    - Write statistics
    """
    
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.write_count = 0
        self.error_count = 0
        self.last_write_time = None
        self._connected = False
    
    def connect(self) -> bool:
        """Establish database connection."""
        try:
            self.engine = create_engine(
                settings.database_url,
                pool_size=settings.db_pool_size,
                pool_pre_ping=True,  # Verify connections before use
                echo=settings.log_level.upper() == "DEBUG",
            )
            
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            self._connected = True
            logger.info("Database connection established")
            return True
            
        except Exception as e:
            self._connected = False
            logger.error("Failed to connect to database", error=str(e))
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            self._connected = False
            logger.info("Database connection closed")
    
    @property
    def is_connected(self) -> bool:
        """Check if database is connected."""
        return self._connected
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def write_reading(self, reading: ParsedReading) -> bool:
        """
        Write a single reading to the database.
        
        Args:
            reading: ParsedReading object to persist
            
        Returns:
            True if successful, False otherwise
        """
        return self.write_readings([reading])
    
    def write_readings(self, readings: List[ParsedReading]) -> bool:
        """
        Write multiple readings to the database in a batch.
        
        Args:
            readings: List of ParsedReading objects
            
        Returns:
            True if all writes successful, False otherwise
        """
        if not readings:
            return True
        
        if not self._connected:
            logger.warning("Database not connected, attempting reconnect")
            if not self.connect():
                return False
        
        try:
            with self.get_session() as session:
                # Use raw SQL for efficient batch insert with ON CONFLICT handling
                insert_sql = text("""
                    INSERT INTO sensor_readings 
                        (time, topic, temperature, humidity, battery, linkquality, raw_data)
                    VALUES 
                        (:time, :topic, :temperature, :humidity, :battery, :linkquality, :raw_data)
                    ON CONFLICT (time, topic) DO UPDATE SET
                        temperature = EXCLUDED.temperature,
                        humidity = EXCLUDED.humidity,
                        battery = EXCLUDED.battery,
                        linkquality = EXCLUDED.linkquality,
                        raw_data = EXCLUDED.raw_data
                """)
                
                for reading in readings:
                    session.execute(
                        insert_sql,
                        {
                            "time": reading.time,
                            "topic": reading.topic,
                            "temperature": reading.temperature,
                            "humidity": reading.humidity,
                            "battery": reading.battery,
                            "linkquality": reading.linkquality,
                            "raw_data": reading.raw_data,
                        },
                    )
                
                self.write_count += len(readings)
                self.last_write_time = datetime.utcnow()
                
                logger.debug(
                    "Wrote readings to database",
                    count=len(readings),
                    total=self.write_count,
                )
                
                return True
                
        except SQLAlchemyError as e:
            self.error_count += 1
            self._connected = False
            logger.error(
                "Database write failed",
                error=str(e),
                reading_count=len(readings),
            )
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Return writer statistics."""
        return {
            "connected": self._connected,
            "writes": self.write_count,
            "errors": self.error_count,
            "last_write": self.last_write_time.isoformat() if self.last_write_time else None,
        }


class BatchWriter:
    """
    Batches readings for efficient database writes.
    
    Accumulates readings and flushes either when batch_size is reached
    or batch_timeout expires.
    """
    
    def __init__(self, db_writer: DatabaseWriter):
        self.db_writer = db_writer
        self.batch: List[ParsedReading] = []
        self.last_flush = datetime.utcnow()
        self._lock = asyncio.Lock()
    
    async def add(self, reading: ParsedReading):
        """Add reading to batch, flushing if necessary."""
        async with self._lock:
            self.batch.append(reading)
            
            # Flush if batch is full
            if len(self.batch) >= settings.batch_size:
                await self._flush()
    
    async def check_timeout(self):
        """Check if batch should be flushed due to timeout."""
        async with self._lock:
            if self.batch:
                elapsed = (datetime.utcnow() - self.last_flush).total_seconds()
                if elapsed >= settings.batch_timeout:
                    await self._flush()
    
    async def flush(self):
        """Force flush the current batch."""
        async with self._lock:
            await self._flush()
    
    async def _flush(self):
        """Internal flush implementation (must hold lock)."""
        if not self.batch:
            return
        
        readings = self.batch
        self.batch = []
        self.last_flush = datetime.utcnow()
        
        # Write in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            self.db_writer.write_readings,
            readings,
        )
        
        logger.info("Flushed batch", count=len(readings))
    
    def get_pending_count(self) -> int:
        """Return number of pending readings in batch."""
        return len(self.batch)
