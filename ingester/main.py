# ================================
# SensorPulse Ingester - Main Entry Point
# ================================

import asyncio
import signal
import sys
from typing import Dict, Any

from config import settings
from logger import logger
from mqtt_client import MQTTClient
from parser import PayloadParser, ParsedReading
from database import DatabaseWriter, BatchWriter
from health import HealthServer


class Ingester:
    """
    Main ingester application.
    
    Coordinates MQTT client, payload parsing, database writing,
    and health monitoring.
    """
    
    def __init__(self):
        self.mqtt_client = MQTTClient()
        self.parser = PayloadParser()
        self.db_writer = DatabaseWriter()
        self.batch_writer: BatchWriter = None
        self.health_server = HealthServer()
        
        self._running = False
        self._shutdown_event = asyncio.Event()
    
    def _on_message(self, topic: str, payload: Dict[str, Any]):
        """Handle incoming MQTT message."""
        # Parse the payload
        reading = self.parser.parse(topic, payload)
        
        if reading:
            # Add to batch (fire and forget for sync callback)
            asyncio.create_task(self.batch_writer.add(reading))
    
    def _get_stats(self) -> Dict[str, Any]:
        """Collect statistics from all components."""
        return {
            "mqtt": self.mqtt_client.get_stats(),
            "parser": self.parser.get_stats(),
            "database": self.db_writer.get_stats(),
            "batch_pending": self.batch_writer.get_pending_count() if self.batch_writer else 0,
        }
    
    async def start(self):
        """Start the ingester service."""
        logger.info("Starting SensorPulse Ingester")
        logger.info(
            "Configuration",
            mqtt_broker=settings.mqtt_broker_ip,
            mqtt_port=settings.mqtt_port,
            mqtt_topic=settings.mqtt_topic,
            log_level=settings.log_level,
        )
        
        # Connect to database
        if not self.db_writer.connect():
            logger.error("Failed to connect to database, exiting")
            sys.exit(1)
        
        # Initialize batch writer
        self.batch_writer = BatchWriter(self.db_writer)
        
        # Set up health server
        self.health_server.set_stats_callback(self._get_stats)
        await self.health_server.start()
        
        # Set up MQTT client
        self.mqtt_client.set_message_callback(self._on_message)
        
        if not self.mqtt_client.connect():
            logger.error("Failed to initialize MQTT client, exiting")
            sys.exit(1)
        
        # Start MQTT loop
        self.mqtt_client.start()
        
        self._running = True
        logger.info("SensorPulse Ingester started successfully")
        
        # Main loop - periodically flush batches and check health
        while self._running:
            try:
                # Wait for shutdown or timeout
                try:
                    await asyncio.wait_for(
                        self._shutdown_event.wait(),
                        timeout=settings.batch_timeout,
                    )
                    # Shutdown requested
                    break
                except asyncio.TimeoutError:
                    pass
                
                # Check batch timeout
                await self.batch_writer.check_timeout()
                
                # Log periodic status
                if self.mqtt_client.is_connected:
                    stats = self._get_stats()
                    logger.debug(
                        "Status update",
                        mqtt_messages=stats["mqtt"]["messages_received"],
                        db_writes=stats["database"]["writes"],
                        batch_pending=stats["batch_pending"],
                    )
                    
            except Exception as e:
                logger.error("Error in main loop", error=str(e))
                await asyncio.sleep(1)
    
    async def stop(self):
        """Stop the ingester service."""
        logger.info("Stopping SensorPulse Ingester")
        
        self._running = False
        self._shutdown_event.set()
        
        # Flush remaining batched readings
        if self.batch_writer:
            await self.batch_writer.flush()
        
        # Stop MQTT client
        self.mqtt_client.stop()
        
        # Stop health server
        await self.health_server.stop()
        
        # Disconnect database
        self.db_writer.disconnect()
        
        logger.info("SensorPulse Ingester stopped")


async def main():
    """Main entry point."""
    ingester = Ingester()
    
    # Set up signal handlers
    loop = asyncio.get_event_loop()
    
    def signal_handler():
        logger.info("Received shutdown signal")
        asyncio.create_task(ingester.stop())
    
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, signal_handler)
    
    try:
        await ingester.start()
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    finally:
        await ingester.stop()


if __name__ == "__main__":
    asyncio.run(main())
