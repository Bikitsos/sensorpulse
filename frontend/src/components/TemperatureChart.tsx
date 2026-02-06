// ================================
// SensorPulse Frontend - Temperature Chart Component
// ================================

import { useMemo, useState, useEffect } from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from 'recharts';
import { format } from 'date-fns';
import type { SensorReading } from '../../types';

interface TemperatureChartProps {
  readings: SensorReading[];
  deviceName: string;
  showHumidity?: boolean;
}

interface ChartDataPoint {
  time: string;
  timestamp: number;
  temperature: number | null;
  humidity: number | null;
}

export function TemperatureChart({ 
  readings, 
  deviceName,
  showHumidity = true 
}: TemperatureChartProps) {
  const isDark = document.documentElement.classList.contains('dark');
  const [isMobile, setIsMobile] = useState(window.innerWidth < 640);

  useEffect(() => {
    const handler = () => setIsMobile(window.innerWidth < 640);
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, []);

  const chartData = useMemo<ChartDataPoint[]>(() => {
    return readings
      .map((r) => ({
        time: format(new Date(r.time), 'HH:mm'),
        timestamp: new Date(r.time).getTime(),
        temperature: r.temperature,
        humidity: r.humidity,
      }))
      .sort((a, b) => a.timestamp - b.timestamp);
  }, [readings]);

  const [minTemp, maxTemp] = useMemo(() => {
    const temps = readings
      .map((r) => r.temperature)
      .filter((t): t is number => t !== null);
    
    if (temps.length === 0) return [0, 30];
    
    const min = Math.floor(Math.min(...temps) - 2);
    const max = Math.ceil(Math.max(...temps) + 2);
    return [min, max];
  }, [readings]);

  if (readings.length === 0) {
    return (
      <div className="h-[300px] flex items-center justify-center text-gray-500 dark:text-gray-400">
        No data available for {deviceName}
      </div>
    );
  }

  return (
    <div className="h-[250px] sm:h-[300px] w-full">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={chartData}
          margin={{ top: 10, right: isMobile ? 10 : 30, left: isMobile ? -10 : 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="tempGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#00A8E8" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#00A8E8" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="humidityGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#92D13F" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#92D13F" stopOpacity={0} />
            </linearGradient>
          </defs>
          
          <CartesianGrid 
            strokeDasharray="3 3" 
            stroke={isDark ? '#374151' : '#e5e7eb'}
          />
          
          <XAxis
            dataKey="time"
            tick={{ fill: isDark ? '#9ca3af' : '#6b7280', fontSize: isMobile ? 10 : 12 }}
            tickLine={{ stroke: isDark ? '#4b5563' : '#6b7280' }}
            axisLine={{ stroke: isDark ? '#374151' : '#e5e7eb' }}
            interval={isMobile ? 'preserveStartEnd' : 'equidistantPreserveStart'}
          />
          
          <YAxis
            yAxisId="temp"
            domain={[minTemp, maxTemp]}
            tick={{ fill: isDark ? '#9ca3af' : '#6b7280', fontSize: isMobile ? 10 : 12 }}
            tickLine={{ stroke: isDark ? '#4b5563' : '#6b7280' }}
            axisLine={{ stroke: isDark ? '#374151' : '#e5e7eb' }}
            tickFormatter={(value) => `${value}°`}
            width={isMobile ? 35 : 45}
          />
          
          {showHumidity && (
            <YAxis
              yAxisId="humidity"
              orientation="right"
              domain={[0, 100]}
              tick={{ fill: isDark ? '#9ca3af' : '#6b7280', fontSize: isMobile ? 10 : 12 }}
              tickLine={{ stroke: isDark ? '#4b5563' : '#6b7280' }}
              axisLine={{ stroke: isDark ? '#374151' : '#e5e7eb' }}
              tickFormatter={(value) => `${value}%`}
              width={isMobile ? 35 : 45}
            />
          )}
          
          <Tooltip
            contentStyle={{
              backgroundColor: isDark ? 'rgba(31, 41, 55, 0.95)' : 'rgba(255, 255, 255, 0.95)',
              borderRadius: '8px',
              border: isDark ? '1px solid #374151' : '1px solid #e5e7eb',
              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
              color: isDark ? '#f3f4f6' : '#111827',
            }}
            labelFormatter={(label) => `Time: ${label}`}
            formatter={(value: number, name: string) => {
              if (name === 'temperature') return [`${value?.toFixed(1)}°C`, 'Temperature'];
              if (name === 'humidity') return [`${value?.toFixed(0)}%`, 'Humidity'];
              return [value, name];
            }}
          />
          
          <Legend />
          
          <Area
            yAxisId="temp"
            type="monotone"
            dataKey="temperature"
            name="Temperature"
            stroke="#00A8E8"
            strokeWidth={2}
            fill="url(#tempGradient)"
            dot={false}
            activeDot={{ r: 6, fill: '#00A8E8' }}
          />
          
          {showHumidity && (
            <Area
              yAxisId="humidity"
              type="monotone"
              dataKey="humidity"
              name="Humidity"
              stroke="#92D13F"
              strokeWidth={2}
              fill="url(#humidityGradient)"
              dot={false}
              activeDot={{ r: 6, fill: '#92D13F' }}
            />
          )}
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export default TemperatureChart;
