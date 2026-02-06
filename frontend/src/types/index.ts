// ================================
// SensorPulse Frontend - TypeScript Types
// ================================

export interface SensorReading {
  time: string;
  topic: string;
  device_name: string;
  temperature: number | null;
  humidity: number | null;
  battery: number | null;
  linkquality: number | null;
  raw_data?: Record<string, unknown>;
}

export interface DeviceInfo {
  topic: string;
  device_name: string;
  last_seen: string;
  reading_count: number;
}

export interface SensorLatest extends SensorReading {
  last_seen_minutes?: number;
}

export interface HistorySummary {
  min_temp: number | null;
  max_temp: number | null;
  avg_temp: number | null;
  min_humidity: number | null;
  max_humidity: number | null;
  avg_humidity: number | null;
  reading_count: number;
}

export interface SensorHistory {
  device_name: string;
  topic: string;
  readings: SensorReading[];
  summary?: HistorySummary;
}

export interface User {
  id: string;
  email: string;
  name: string | null;
  picture: string | null;
  is_allowed: boolean;
  daily_report: boolean;
  report_time: string | null;
}

export interface ReportPreferences {
  daily_report: boolean;
  report_time: string;
}

export interface ReportSummary {
  device_name: string;
  min_temp: number | null;
  max_temp: number | null;
  avg_temp: number | null;
  min_humidity: number | null;
  max_humidity: number | null;
  avg_humidity: number | null;
  battery: number | null;
  last_seen: string | null;
  is_offline: boolean;
}

export interface DailyReport {
  generated_at: string;
  period_start: string;
  period_end: string;
  sensors: ReportSummary[];
  alerts: string[];
}

export interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
}

export interface WebSocketMessage {
  type: 'connected' | 'reading' | 'error' | 'subscribed' | 'unsubscribed';
  data?: SensorReading;
  client_id?: string;
  timestamp?: string;
  message?: string;
}

export type ConnectionStatus = 'connected' | 'connecting' | 'disconnected';

export type TemperatureRange = 'cold' | 'normal' | 'warm' | 'hot';

export function getTemperatureRange(temp: number | null): TemperatureRange {
  if (temp === null) return 'normal';
  if (temp < 10) return 'cold';
  if (temp < 22) return 'normal';
  if (temp < 28) return 'warm';
  return 'hot';
}

export function getTemperatureColor(temp: number | null): string {
  const range = getTemperatureRange(temp);
  switch (range) {
    case 'cold': return 'text-blue-500 dark:text-blue-400';
    case 'normal': return 'text-sp-cyan';
    case 'warm': return 'text-orange-500 dark:text-orange-400';
    case 'hot': return 'text-red-500 dark:text-red-400';
  }
}

export function getTemperatureBadgeClass(temp: number | null): string {
  const range = getTemperatureRange(temp);
  return `temp-badge temp-badge-${range}`;
}

export type HumidityRange = 'low' | 'normal' | 'high';

export function getHumidityRange(humidity: number | null): HumidityRange {
  if (humidity === null) return 'normal';
  if (humidity < 30) return 'low';
  if (humidity < 65) return 'normal';
  return 'high';
}

export function getHumidityColor(humidity: number | null): string {
  const range = getHumidityRange(humidity);
  switch (range) {
    case 'low': return 'text-yellow-500 dark:text-yellow-400';
    case 'normal': return 'text-sp-cyan';
    case 'high': return 'text-blue-600 dark:text-blue-400';
  }
}

export function getBatteryColor(battery: number | null): string {
  if (battery === null) return 'text-gray-400';
  if (battery < 20) return 'text-red-500';
  if (battery < 50) return 'text-yellow-500';
  return 'text-sp-lime';
}
