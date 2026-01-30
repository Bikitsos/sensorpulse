# ================================
# SensorPulse API - Sensor Routes
# ================================

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from db import get_db
from services import SensorService
from schemas import DeviceInfo, SensorLatest, SensorHistory, SensorReading
from auth import get_current_user, require_user

router = APIRouter(prefix="/api", tags=["sensors"])


@router.get("/devices", response_model=List[DeviceInfo])
async def get_devices(
    db: AsyncSession = Depends(get_db),
    user = Depends(require_user),
):
    """
    Get list of all discovered sensors/devices.
    
    Returns distinct list of topics with their device names and last seen time.
    """
    service = SensorService(db)
    devices = await service.get_devices()
    return devices


@router.get("/latest", response_model=List[SensorLatest])
async def get_latest_readings(
    db: AsyncSession = Depends(get_db),
    user = Depends(require_user),
):
    """
    Get the most recent reading for all devices.
    
    Ideal for populating dashboard cards showing current sensor values.
    Includes minutes since last reading for freshness indication.
    """
    service = SensorService(db)
    readings = await service.get_latest_readings()
    return readings


@router.get("/history/{device_name}", response_model=SensorHistory)
async def get_device_history(
    device_name: str,
    hours: int = Query(default=24, ge=1, le=168, description="Hours of history (max 168/7 days)"),
    resolution: Optional[str] = Query(default=None, pattern="^(1m|5m|15m|1h)$"),
    db: AsyncSession = Depends(get_db),
    user = Depends(require_user),
):
    """
    Get historical readings for a specific device.
    
    Returns all readings within the specified time range along with
    summary statistics (min, max, avg for temperature and humidity).
    
    - **device_name**: The device name (e.g., 'living_room_sensor')
    - **hours**: How many hours of history to fetch (default: 24, max: 168)
    - **resolution**: Optional downsampling (1m, 5m, 15m, 1h)
    """
    service = SensorService(db)
    history = await service.get_device_history(device_name, hours, resolution)
    
    if not history["readings"]:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for device: {device_name}",
        )
    
    return history


@router.get("/devices/{device_name}/latest", response_model=SensorReading)
async def get_device_latest(
    device_name: str,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_user),
):
    """
    Get the most recent reading for a specific device.
    """
    service = SensorService(db)
    readings = await service.get_latest_readings()
    
    for reading in readings:
        if reading["device_name"] == device_name:
            return reading
    
    raise HTTPException(
        status_code=404,
        detail=f"Device not found: {device_name}",
    )
