# ================================
# SensorPulse API - Report Routes
# ================================

from datetime import datetime, timedelta, timezone, time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from config import settings
from db import get_db
from db.models import SensorReading, User
from services import SensorService, UserService
from schemas import DailyReport, ReportSummary
from auth import require_user

router = APIRouter(prefix="/api/report", tags=["reports"])


async def generate_report(db: AsyncSession) -> DailyReport:
    """Generate daily report for all sensors."""
    now = datetime.now(timezone.utc)
    period_start = now - timedelta(hours=24)
    
    # Get all readings from last 24 hours grouped by device
    query = select(
        SensorReading.device_name,
        func.min(SensorReading.temperature).label("min_temp"),
        func.max(SensorReading.temperature).label("max_temp"),
        func.avg(SensorReading.temperature).label("avg_temp"),
        func.min(SensorReading.humidity).label("min_humidity"),
        func.max(SensorReading.humidity).label("max_humidity"),
        func.avg(SensorReading.humidity).label("avg_humidity"),
        func.max(SensorReading.battery).label("battery"),
        func.max(SensorReading.time).label("last_seen"),
    ).where(
        SensorReading.time >= period_start,
    ).group_by(
        SensorReading.device_name,
    )
    
    result = await db.execute(query)
    rows = result.all()
    
    sensors = []
    alerts = []
    
    for row in rows:
        last_seen = row.last_seen
        hours_since = (now - last_seen).total_seconds() / 3600 if last_seen else 999
        is_offline = hours_since > 2
        
        sensor = ReportSummary(
            device_name=row.device_name,
            min_temp=round(row.min_temp, 1) if row.min_temp else None,
            max_temp=round(row.max_temp, 1) if row.max_temp else None,
            avg_temp=round(row.avg_temp, 1) if row.avg_temp else None,
            min_humidity=round(row.min_humidity, 1) if row.min_humidity else None,
            max_humidity=round(row.max_humidity, 1) if row.max_humidity else None,
            avg_humidity=round(row.avg_humidity, 1) if row.avg_humidity else None,
            battery=row.battery,
            last_seen=last_seen,
            is_offline=is_offline,
        )
        sensors.append(sensor)
        
        # Generate alerts
        if is_offline:
            alerts.append(f"⚠️ {row.device_name} is offline (last seen {hours_since:.1f}h ago)")
        
        if row.battery and row.battery < 20:
            alerts.append(f"🔋 {row.device_name} has low battery ({row.battery}%)")
    
    return DailyReport(
        generated_at=now,
        period_start=period_start,
        period_end=now,
        sensors=sensors,
        alerts=alerts,
    )


def generate_report_html(report: DailyReport) -> str:
    """Generate HTML version of the daily report."""
    sensors_html = ""
    
    for sensor in report.sensors:
        status_icon = "🔴" if sensor.is_offline else "🟢"
        temp_str = f"{sensor.avg_temp}°C" if sensor.avg_temp else "N/A"
        humidity_str = f"{sensor.avg_humidity}%" if sensor.avg_humidity else "N/A"
        battery_str = f"{sensor.battery}%" if sensor.battery else "N/A"
        
        sensors_html += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #eee;">
                {status_icon} {sensor.device_name}
            </td>
            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">
                {sensor.min_temp or 'N/A'} / {sensor.max_temp or 'N/A'} / {temp_str}
            </td>
            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">
                {humidity_str}
            </td>
            <td style="padding: 8px; border-bottom: 1px solid #eee; text-align: center;">
                {battery_str}
            </td>
        </tr>
        """
    
    alerts_html = ""
    if report.alerts:
        alerts_html = "<h3>⚠️ Alerts</h3><ul>"
        for alert in report.alerts:
            alerts_html += f"<li>{alert}</li>"
        alerts_html += "</ul>"
    
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            h1 {{ color: #3C4650; }}
            h2 {{ color: #00A8E8; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th {{ background: #3C4650; color: white; padding: 12px 8px; text-align: left; }}
            .footer {{ margin-top: 20px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌡️ SensorPulse Daily Report</h1>
            <p>Report for {report.period_start.strftime('%Y-%m-%d %H:%M')} to {report.period_end.strftime('%Y-%m-%d %H:%M')} UTC</p>
            
            {alerts_html}
            
            <h2>Sensor Summary</h2>
            <table>
                <thead>
                    <tr>
                        <th>Sensor</th>
                        <th>Temp (Min/Max/Avg)</th>
                        <th>Humidity</th>
                        <th>Battery</th>
                    </tr>
                </thead>
                <tbody>
                    {sensors_html}
                </tbody>
            </table>
            
            <div class="footer">
                <p>Generated by SensorPulse at {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')} UTC</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html


async def send_report_email(user_email: str, report: DailyReport):
    """Send report email using Resend."""
    if not settings.resend_api_key:
        return
    
    try:
        import resend
        resend.api_key = settings.resend_api_key
        
        html = generate_report_html(report)
        
        resend.Emails.send({
            "from": settings.email_from,
            "to": user_email,
            "subject": f"🌡️ SensorPulse Daily Report - {report.generated_at.strftime('%Y-%m-%d')}",
            "html": html,
        })
    except Exception as e:
        # Log error but don't raise
        print(f"Failed to send report email: {e}")


@router.get("/preview", response_model=DailyReport)
async def preview_report(
    db: AsyncSession = Depends(get_db),
    user = Depends(require_user),
):
    """
    Preview today's daily report.
    
    Returns the report data that would be sent in the daily email.
    """
    report = await generate_report(db)
    return report


@router.get("/preview/html")
async def preview_report_html(
    db: AsyncSession = Depends(get_db),
    user = Depends(require_user),
):
    """
    Preview today's daily report as HTML.
    """
    from fastapi.responses import HTMLResponse
    
    report = await generate_report(db)
    html = generate_report_html(report)
    return HTMLResponse(content=html)


@router.post("/send-now")
async def send_report_now(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    user = Depends(require_user),
):
    """
    Manually trigger a report for the current user.
    """
    if not settings.resend_api_key:
        raise HTTPException(
            status_code=503,
            detail="Email sending not configured (RESEND_API_KEY not set)",
        )
    
    report = await generate_report(db)
    
    # Send in background
    background_tasks.add_task(send_report_email, user.email, report)
    
    return {
        "message": f"Report will be sent to {user.email}",
        "sensors_included": len(report.sensors),
        "alerts": len(report.alerts),
    }
