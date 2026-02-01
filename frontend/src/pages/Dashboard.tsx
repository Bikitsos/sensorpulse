// ================================
// SensorPulse Frontend - Dashboard Page
// ================================

import { useState, useCallback, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { RefreshCw, Thermometer, Droplets } from 'lucide-react';
import { SensorCard } from '../components/SensorCard';
import { TemperatureChart } from '../components/TemperatureChart';
import { api } from '../api/client';
import type { SensorLatest, SensorReading } from '../types';

interface DashboardProps {
  onSensorUpdate?: (reading: SensorReading) => void;
}

export function Dashboard({ onSensorUpdate }: DashboardProps) {
  const queryClient = useQueryClient();
  const [selectedSensor, setSelectedSensor] = useState<string | null>(null);
  const [historyHours, setHistoryHours] = useState(24);

  // Fetch latest sensor readings
  const {
    data: sensors,
    isLoading: sensorsLoading,
    error: sensorsError,
    refetch: refetchSensors,
  } = useQuery({
    queryKey: ['sensors', 'latest'],
    queryFn: () => api.getLatest(),
    refetchInterval: 30000, // Refetch every 30 seconds
    staleTime: 10000,
  });

  // Fetch history for selected sensor
  const {
    data: history,
    isLoading: historyLoading,
  } = useQuery({
    queryKey: ['sensors', 'history', selectedSensor, historyHours],
    queryFn: () => api.getHistory(selectedSensor!, historyHours),
    enabled: !!selectedSensor,
    staleTime: 60000,
  });

  // Handle real-time updates from WebSocket
  const handleSensorUpdate = useCallback(
    (reading: SensorReading) => {
      // Update the cache with new reading
      queryClient.setQueryData<SensorLatest[]>(['sensors', 'latest'], (old) => {
        if (!old) return old;
        return old.map((sensor) =>
          sensor.device_name === reading.device_name
            ? { ...sensor, ...reading, last_seen_minutes: 0 }
            : sensor
        );
      });
      
      onSensorUpdate?.(reading);
    },
    [queryClient, onSensorUpdate]
  );

  // Calculate summary stats
  const stats = useMemo(() => {
    if (!sensors || sensors.length === 0) {
      return { avgTemp: null, avgHumidity: null, onlineCount: 0, totalCount: 0 };
    }

    const temps = sensors.map((s) => s.temperature).filter((t): t is number => t !== null);
    const humidities = sensors.map((s) => s.humidity).filter((h): h is number => h !== null);
    const online = sensors.filter((s) => (s.last_seen_minutes ?? 999) < 10);

    return {
      avgTemp: temps.length > 0 ? temps.reduce((a, b) => a + b, 0) / temps.length : null,
      avgHumidity: humidities.length > 0 ? humidities.reduce((a, b) => a + b, 0) / humidities.length : null,
      onlineCount: online.length,
      totalCount: sensors.length,
    };
  }, [sensors]);

  if (sensorsError) {
    return (
      <div className="text-center py-12">
        <p className="text-red-500 mb-4">Failed to load sensors</p>
        <button
          onClick={() => refetchSensors()}
          className="px-4 py-2 bg-sp-cyan text-white rounded-lg hover:bg-sp-cyan/90"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
            Dashboard
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Monitor your sensors in real-time
          </p>
        </div>
        <button
          onClick={() => refetchSensors()}
          disabled={sensorsLoading}
          className="flex items-center gap-2 px-4 py-2 bg-sp-cyan text-white rounded-lg hover:bg-sp-cyan/90 disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 ${sensorsLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass-card p-4">
          <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 text-sm mb-1">
            <Thermometer className="w-4 h-4" />
            <span>Avg Temperature</span>
          </div>
          <p className="text-2xl font-bold text-sp-cyan">
            {stats.avgTemp !== null ? `${stats.avgTemp.toFixed(1)}°C` : '—'}
          </p>
        </div>
        <div className="glass-card p-4">
          <div className="flex items-center gap-2 text-gray-500 dark:text-gray-400 text-sm mb-1">
            <Droplets className="w-4 h-4" />
            <span>Avg Humidity</span>
          </div>
          <p className="text-2xl font-bold text-sp-cyan">
            {stats.avgHumidity !== null ? `${stats.avgHumidity.toFixed(0)}%` : '—'}
          </p>
        </div>
        <div className="glass-card p-4">
          <div className="text-gray-500 dark:text-gray-400 text-sm mb-1">
            Online Sensors
          </div>
          <p className="text-2xl font-bold text-sp-lime">
            {stats.onlineCount} / {stats.totalCount}
          </p>
        </div>
        <div className="glass-card p-4">
          <div className="text-gray-500 dark:text-gray-400 text-sm mb-1">
            Status
          </div>
          <p className="text-2xl font-bold text-sp-lime">
            {stats.onlineCount === stats.totalCount ? '✓ All Online' : '⚠️ Some Offline'}
          </p>
        </div>
      </div>

      {/* Sensor Grid */}
      <section>
        <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
          Sensors
        </h2>
        
        {sensorsLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {[1, 2, 3].map((i) => (
              <div key={i} className="glass-card p-6 animate-pulse">
                <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4" />
                <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-3/4 mb-2" />
                <div className="h-10 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
              </div>
            ))}
          </div>
        ) : sensors && sensors.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {sensors.map((sensor) => (
              <SensorCard
                key={sensor.device_name}
                sensor={sensor}
                isSelected={selectedSensor === sensor.device_name}
                onClick={() => setSelectedSensor(
                  selectedSensor === sensor.device_name ? null : sensor.device_name
                )}
              />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 text-gray-500 dark:text-gray-400">
            No sensors found. Make sure your MQTT ingester is running.
          </div>
        )}
      </section>

      {/* Chart Section */}
      {selectedSensor && (
        <section className="glass-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              {selectedSensor} History
            </h2>
            <div className="flex items-center gap-2">
              <select
                value={historyHours}
                onChange={(e) => setHistoryHours(Number(e.target.value))}
                className="px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-sm"
              >
                <option value={6}>Last 6 hours</option>
                <option value={12}>Last 12 hours</option>
                <option value={24}>Last 24 hours</option>
                <option value={48}>Last 2 days</option>
                <option value={168}>Last 7 days</option>
              </select>
            </div>
          </div>
          
          {historyLoading ? (
            <div className="h-[300px] flex items-center justify-center">
              <RefreshCw className="w-8 h-8 text-sp-cyan animate-spin" />
            </div>
          ) : history ? (
            <TemperatureChart
              readings={history.readings}
              deviceName={selectedSensor}
              showHumidity={true}
            />
          ) : (
            <div className="h-[300px] flex items-center justify-center text-gray-500">
              No history data available
            </div>
          )}
        </section>
      )}
    </div>
  );
}

export default Dashboard;
