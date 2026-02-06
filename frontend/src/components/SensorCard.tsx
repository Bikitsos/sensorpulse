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
  Clock,
  Signal
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import clsx from 'clsx';
import type { SensorLatest } from '../../types';
import { getTemperatureColor, getTemperatureBadgeClass, getHumidityColor, getBatteryColor } from '../../types';

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
  const humidityColorClass = getHumidityColor(sensor.humidity);
  const batteryColorClass = getBatteryColor(sensor.battery);

  return (
    <div
      onClick={onClick}
      className={clsx(
        'glass-card p-5 sm:p-6 cursor-pointer transition-all duration-200',
        'hover:shadow-xl hover:scale-[1.02] active:scale-[0.98]',
        isSelected && 'ring-2 ring-sp-cyan ring-offset-2 dark:ring-offset-gray-900'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white truncate mr-2">
          {sensor.device_name}
        </h3>
        <div className="flex items-center gap-2 flex-shrink-0">
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
      <div className="grid grid-cols-2 gap-3 sm:gap-4 mb-4">
        {/* Temperature */}
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5 text-gray-500 dark:text-gray-400 text-xs sm:text-sm mb-1">
            <Thermometer className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
            <span>Temperature</span>
          </div>
          <span className={clsx('sensor-value', tempColorClass)}>
            {sensor.temperature !== null ? `${sensor.temperature.toFixed(1)}°` : '—'}
          </span>
          {sensor.temperature !== null && (
            <span className={clsx('mt-1', getTemperatureBadgeClass(sensor.temperature))}>
              {sensor.temperature < 10 ? '❄️ Cold' : sensor.temperature < 22 ? '🌤️ Normal' : sensor.temperature < 28 ? '🌡️ Warm' : '🔥 Hot'}
            </span>
          )}
        </div>

        {/* Humidity */}
        <div className="flex flex-col">
          <div className="flex items-center gap-1.5 text-gray-500 dark:text-gray-400 text-xs sm:text-sm mb-1">
            <Droplets className="w-3.5 h-3.5 sm:w-4 sm:h-4" />
            <span>Humidity</span>
          </div>
          <span className={clsx('sensor-value', humidityColorClass)}>
            {sensor.humidity !== null ? `${sensor.humidity.toFixed(0)}%` : '—'}
          </span>
        </div>
      </div>

      {/* Battery Bar */}
      {sensor.battery !== null && (
        <div className="mb-4">
          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mb-1">
            <span className="flex items-center gap-1">
              <BatteryIcon className={clsx('w-3.5 h-3.5', batteryColorClass)} />
              Battery
            </span>
            <span className={batteryColorClass}>{sensor.battery}%</span>
          </div>
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
            <div
              className={clsx(
                'battery-bar',
                sensor.battery < 20 && 'bg-red-500',
                sensor.battery >= 20 && sensor.battery < 50 && 'bg-yellow-500',
                sensor.battery >= 50 && 'bg-sp-lime'
              )}
              style={{ width: `${Math.min(sensor.battery, 100)}%` }}
            />
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between text-xs sm:text-sm text-gray-500 dark:text-gray-400 pt-3 border-t border-gray-200 dark:border-gray-700">
        {/* Link Quality */}
        {sensor.linkquality !== null && (
          <div className="flex items-center gap-1">
            <Signal className="w-3.5 h-3.5" />
            <span>{sensor.linkquality}</span>
          </div>
        )}

        {/* Last Seen */}
        <div className="flex items-center gap-1 ml-auto">
          <Clock className="w-3.5 h-3.5" />
          <span>{lastSeenText}</span>
        </div>
      </div>
    </div>
  );
}

export default SensorCard;
