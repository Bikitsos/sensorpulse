# ================================
# SensorPulse API - Database Service
# ================================

from datetime import datetime, timedelta, timezone
from typing import List, Optional, Dict, Any
from sqlalchemy import select, func, text, distinct
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import SensorReading, User


class SensorService:
    """Service for sensor data operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_devices(self) -> List[Dict[str, Any]]:
        """Get list of all discovered devices with their last reading time."""
        query = select(
            SensorReading.topic,
            SensorReading.device_name,
            func.max(SensorReading.time).label("last_seen"),
            func.count().label("reading_count"),
        ).group_by(
            SensorReading.topic,
            SensorReading.device_name,
        ).order_by(
            SensorReading.device_name,
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        return [
            {
                "topic": row.topic,
                "device_name": row.device_name,
                "last_seen": row.last_seen,
                "reading_count": row.reading_count,
            }
            for row in rows
        ]
    
    async def get_latest_readings(self) -> List[Dict[str, Any]]:
        """Get the most recent reading for each device."""
        # Use the latest_readings view
        query = text("""
            SELECT 
                time,
                topic,
                device_name,
                temperature,
                humidity,
                battery,
                linkquality,
                raw_data,
                EXTRACT(EPOCH FROM (NOW() - time)) / 60 AS last_seen_minutes
            FROM latest_readings
            ORDER BY device_name
        """)
        
        result = await self.db.execute(query)
        rows = result.mappings().all()
        
        return [dict(row) for row in rows]
    
    async def get_device_history(
        self,
        device_name: str,
        hours: int = 24,
        resolution: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Get historical readings for a device."""
        since = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        # Base query
        query = select(SensorReading).where(
            SensorReading.device_name == device_name,
            SensorReading.time >= since,
        ).order_by(SensorReading.time.asc())
        
        result = await self.db.execute(query)
        readings = result.scalars().all()
        
        # Calculate summary
        temps = [r.temperature for r in readings if r.temperature is not None]
        humids = [r.humidity for r in readings if r.humidity is not None]
        
        summary = {
            "min_temp": min(temps) if temps else None,
            "max_temp": max(temps) if temps else None,
            "avg_temp": sum(temps) / len(temps) if temps else None,
            "min_humidity": min(humids) if humids else None,
            "max_humidity": max(humids) if humids else None,
            "avg_humidity": sum(humids) / len(humids) if humids else None,
            "reading_count": len(readings),
        }
        
        # Get topic for the device
        topic = readings[0].topic if readings else f"zigbee2mqtt/{device_name}"
        
        return {
            "device_name": device_name,
            "topic": topic,
            "readings": [
                {
                    "time": r.time,
                    "topic": r.topic,
                    "device_name": r.device_name,
                    "temperature": r.temperature,
                    "humidity": r.humidity,
                    "battery": r.battery,
                    "linkquality": r.linkquality,
                    "raw_data": r.raw_data,
                }
                for r in readings
            ],
            "summary": summary,
        }
    
    async def get_reading_by_time(
        self,
        device_name: str,
        timestamp: datetime,
    ) -> Optional[SensorReading]:
        """Get a specific reading by device and timestamp."""
        query = select(SensorReading).where(
            SensorReading.device_name == device_name,
            SensorReading.time == timestamp,
        )
        
        result = await self.db.execute(query)
        return result.scalar_one_or_none()


class UserService:
    """Service for user operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def create_or_update(
        self,
        email: str,
        name: Optional[str] = None,
        picture: Optional[str] = None,
    ) -> User:
        """Create new user or update existing."""
        user = await self.get_by_email(email)
        
        if user:
            # Update existing user
            if name:
                user.name = name
            if picture:
                user.picture = picture
            await self.db.commit()
            await self.db.refresh(user)
        else:
            # Create new user
            user = User(
                email=email,
                name=name,
                picture=picture,
                is_allowed=False,  # Must be manually approved
            )
            self.db.add(user)
            await self.db.commit()
            await self.db.refresh(user)
        
        return user
    
    async def update_preferences(
        self,
        user_id: str,
        daily_report: Optional[bool] = None,
        report_time: Optional[Any] = None,
    ) -> Optional[User]:
        """Update user preferences."""
        user = await self.get_by_id(user_id)
        
        if not user:
            return None
        
        if daily_report is not None:
            user.daily_report = daily_report
        if report_time is not None:
            user.report_time = report_time
        
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def get_users_for_report(self, target_time: Any) -> List[User]:
        """Get users who should receive reports at the given time."""
        query = select(User).where(
            User.is_allowed == True,
            User.daily_report == True,
            User.report_time == target_time,
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()
