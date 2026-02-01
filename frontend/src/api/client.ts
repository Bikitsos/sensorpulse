// ================================
// SensorPulse Frontend - API Client
// ================================

import axios, { AxiosError, AxiosInstance } from 'axios';
import type {
  DeviceInfo,
  SensorLatest,
  SensorHistory,
  User,
  ReportPreferences,
  DailyReport,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      withCredentials: true,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Redirect to login on 401
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // ================================
  // Sensor Endpoints
  // ================================

  async getDevices(): Promise<DeviceInfo[]> {
    const response = await this.client.get<DeviceInfo[]>('/api/devices');
    return response.data;
  }

  async getLatest(): Promise<SensorLatest[]> {
    const response = await this.client.get<SensorLatest[]>('/api/latest');
    return response.data;
  }

  async getHistory(deviceName: string, hours: number = 24): Promise<SensorHistory> {
    const response = await this.client.get<SensorHistory>(
      `/api/history/${encodeURIComponent(deviceName)}`,
      { params: { hours } }
    );
    return response.data;
  }

  // ================================
  // Auth Endpoints
  // ================================

  async getCurrentUser(): Promise<User> {
    const response = await this.client.get<User>('/auth/me');
    return response.data;
  }

  getLoginUrl(): string {
    return `${API_BASE_URL}/auth/login`;
  }

  async logout(): Promise<void> {
    await this.client.post('/auth/logout');
  }

  async updatePreferences(preferences: ReportPreferences): Promise<User> {
    const response = await this.client.put<User>('/auth/preferences', preferences);
    return response.data;
  }

  // ================================
  // Report Endpoints
  // ================================

  async getReportPreview(): Promise<DailyReport> {
    const response = await this.client.get<DailyReport>('/api/report/preview');
    return response.data;
  }

  async sendReportNow(): Promise<{ message: string }> {
    const response = await this.client.post<{ message: string }>('/api/report/send-now');
    return response.data;
  }
}

export const api = new ApiClient();
export default api;
