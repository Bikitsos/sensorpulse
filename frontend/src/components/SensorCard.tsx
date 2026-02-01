// ================================
// SensorPulse Frontend - Sensor Card Component
// ================================

import { useMemo } from 'react';
import { 
  Thermometer, 
  Droplets, 
  Battery, 
  BatteryLow, 
  BatteryWarning,
  Wifi,
  WifiOff,
  Clock
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import clsx from 'clsx';
import type { SensorLatest } from '../../types';
import { getTemperatureColor } from '../../types';

interface SensorCardProps {
  sensor: SensorLatest;
  onClick?: () => void;
  isSelected?: boolean;
}

export function SensorCard({ sensor, onClick, isSelected }: SensorCardProps) {
  const lastSeenText = useMemo(() => {
    try {
      return formatDistanceToNow(new Date(sensor.time), { addSuffix: true });
    } catch {
      return 'Unknown';
    }
  }, [sensor.time]);

  const isOnline = (sensor.last_seen_minutes ?? 999) < 10;
  const isStale = (sensor.last_seen_minutes ?? 999) >= 10 && (sensor.last_seen_minutes ?? 999) < 120;
  
  const BatteryIcon = useMemo(() => {
    if (sensor.battery === null) return Battery;
    if (sensor.battery < 10) return BatteryLow;
    if (sensor.battery < 30) return BatteryWarning;
    return Battery;
  }, [sensor.battery]);

  const tempColorClass = getTemperatureColor(sensor.temperature);

  return (
    <div
      onClick={onClick}
      className={clsx(
        'glass-card p-6 cursor-pointer transition-all duration-200',
        'hover:shadow-xl hover:scale-[1.02]',
        isSelected && 'ring-2 ring-sp-cyan ring-offset-2 dark:ring-offset-gray-900'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white truncate">
          {sensor.device_name}
        </h3>
        <div className="flex items-center gap-2">
          {isOnline ? (
            <Wifi className="w-4 h-4 text-sp-lime" />
          ) : (
            <WifiOff className="w-4 h-4 text-red-500" />
          )}
          <span
            className={clsx(
              'status-dot',
              isOnline && 'status-online',
              isStale && 'status-stale',
              !isOnline && !isStale && 'status-offline'
            )}
          />
        </div>
      </div>

      {/* Main Values */}
      <div className="grid grid-cols-2 gap-4 mb-4">
        {/* Temperature */}
        <div className="flex flex-col">
          <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 text-sm mb-1">
            <Thermometer className="w-4 h-4" />
            <span>Temperature</span>
          </div>
          <span className={clsx('sensor-value', tempColorClass)}>
            {sensor.temperature !== null ? `${sensor.temperature.toFixed(1)}°` : '—'}
          </span>
        </div>

        {/* Humidity */}
        <div className="flex flex-col">
          <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 text-sm mb-1">
            <Droplets className="w-4 h-4" />
            <span>Humidity</span>
          </div>
          <span className="sensor-value text-sp-cyan">
            {sensor.humidity !== null ? `${sensor.humidity.toFixed(0)}%` : '—'}
          </span>
        </div>
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 pt-4 border-t border-gray-200 dark:border-gray-700">
        {/* Battery */}
        <div className="flex items-center gap-1.5">
          <BatteryIcon
            className={clsx(
              'w-4 h-4',
              sensor.battery !== null && sensor.battery < 20 && 'text-red-500',
              sensor.battery !== null && sensor.battery >= 20 && sensor.battery < 50 && 'text-yellow-500',
              sensor.battery !== null && sensor.battery >= 50 && 'text-sp-lime'
            )}
          />
          <span>{sensor.battery !== null ? `${sensor.battery}%` : '—'}</span>
        </div>

        {/* Last Seen */}
        <div className="flex items-center gap-1.5">
          <Clock className="w-4 h-4" />
          <span>{lastSeenText}</span>
        </div>
      </div>
    </div>
  );
}

export default SensorCard;
