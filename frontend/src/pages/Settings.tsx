// ================================
// SensorPulse Frontend - Settings Page
// ================================

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Save, Send, Mail, Clock, Bell, AlertCircle, CheckCircle } from 'lucide-react';
import { useAuth } from '../hooks/useAuth';
import { api } from '../api/client';
import type { ReportPreferences } from '../types';

export function Settings() {
  const { user, refreshUser } = useAuth();
  const queryClient = useQueryClient();
  
  const [dailyReport, setDailyReport] = useState(user?.daily_report ?? false);
  const [reportTime, setReportTime] = useState(user?.report_time ?? '08:00');
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [sendStatus, setSendStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');

  // Fetch report preview
  const { data: reportPreview, isLoading: previewLoading } = useQuery({
    queryKey: ['report', 'preview'],
    queryFn: () => api.getReportPreview(),
    enabled: dailyReport,
  });

  // Save preferences mutation
  const saveMutation = useMutation({
    mutationFn: (prefs: ReportPreferences) => api.updatePreferences(prefs),
    onMutate: () => setSaveStatus('saving'),
    onSuccess: () => {
      setSaveStatus('saved');
      refreshUser();
      setTimeout(() => setSaveStatus('idle'), 3000);
    },
    onError: () => {
      setSaveStatus('error');
      setTimeout(() => setSaveStatus('idle'), 3000);
    },
  });

  // Send test report mutation
  const sendMutation = useMutation({
    mutationFn: () => api.sendReportNow(),
    onMutate: () => setSendStatus('sending'),
    onSuccess: () => {
      setSendStatus('sent');
      setTimeout(() => setSendStatus('idle'), 5000);
    },
    onError: () => {
      setSendStatus('error');
      setTimeout(() => setSendStatus('idle'), 3000);
    },
  });

  const handleSave = () => {
    saveMutation.mutate({
      daily_report: dailyReport,
      report_time: reportTime,
    });
  };

  return (
    <div className="max-w-2xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          Settings
        </h1>
        <p className="text-gray-600 dark:text-gray-400 mt-1">
          Configure your notification preferences
        </p>
      </div>

      {/* Account Info */}
      <section className="glass-card p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Account
        </h2>
        <div className="flex items-center gap-4">
          <img
            src={user?.picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(user?.name || user?.email || 'User')}`}
            alt={user?.name || user?.email || 'User'}
            className="w-16 h-16 rounded-full"
          />
          <div>
            <p className="text-lg font-medium text-gray-900 dark:text-white">
              {user?.name || 'User'}
            </p>
            <p className="text-gray-600 dark:text-gray-400">
              {user?.email}
            </p>
          </div>
        </div>
      </section>

      {/* Email Reports */}
      <section className="glass-card p-6">
        <div className="flex items-center gap-3 mb-6">
          <Mail className="w-5 h-5 text-sp-cyan" />
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
            Daily Email Reports
          </h2>
        </div>

        <div className="space-y-6">
          {/* Enable toggle */}
          <div className="flex items-center justify-between">
            <div>
              <label className="text-gray-900 dark:text-white font-medium">
                Enable Daily Reports
              </label>
              <p className="text-sm text-gray-600 dark:text-gray-400">
                Receive a daily summary of all sensor data
              </p>
            </div>
            <button
              onClick={() => setDailyReport(!dailyReport)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                dailyReport ? 'bg-sp-cyan' : 'bg-gray-300 dark:bg-gray-600'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                  dailyReport ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          {/* Time picker */}
          {dailyReport && (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Clock className="w-4 h-4 text-gray-500" />
                <label className="text-gray-900 dark:text-white font-medium">
                  Delivery Time
                </label>
              </div>
              <input
                type="time"
                value={reportTime}
                onChange={(e) => setReportTime(e.target.value)}
                className="px-3 py-1.5 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg"
              />
            </div>
          )}

          {/* Save button */}
          <div className="flex items-center justify-between pt-4 border-t border-gray-200 dark:border-gray-700">
            <button
              onClick={handleSave}
              disabled={saveStatus === 'saving'}
              className="flex items-center gap-2 px-4 py-2 bg-sp-cyan text-white rounded-lg hover:bg-sp-cyan/90 disabled:opacity-50"
            >
              {saveStatus === 'saving' ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
                  Saving...
                </>
              ) : saveStatus === 'saved' ? (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Saved!
                </>
              ) : saveStatus === 'error' ? (
                <>
                  <AlertCircle className="w-4 h-4" />
                  Error
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Save Preferences
                </>
              )}
            </button>

            {dailyReport && (
              <button
                onClick={() => sendMutation.mutate()}
                disabled={sendStatus === 'sending'}
                className="flex items-center gap-2 px-4 py-2 border border-sp-cyan text-sp-cyan rounded-lg hover:bg-sp-cyan/10 disabled:opacity-50"
              >
                {sendStatus === 'sending' ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-sp-cyan" />
                    Sending...
                  </>
                ) : sendStatus === 'sent' ? (
                  <>
                    <CheckCircle className="w-4 h-4" />
                    Sent!
                  </>
                ) : (
                  <>
                    <Send className="w-4 h-4" />
                    Send Test Report
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </section>

      {/* Report Preview */}
      {dailyReport && (
        <section className="glass-card p-6">
          <div className="flex items-center gap-3 mb-4">
            <Bell className="w-5 h-5 text-sp-lime" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
              Report Preview
            </h2>
          </div>

          {previewLoading ? (
            <div className="animate-pulse space-y-4">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
              <div className="h-20 bg-gray-200 dark:bg-gray-700 rounded" />
            </div>
          ) : reportPreview ? (
            <div className="space-y-4">
              {/* Alerts */}
              {reportPreview.alerts.length > 0 && (
                <div className="p-4 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg">
                  <h3 className="font-medium text-yellow-800 dark:text-yellow-200 mb-2">
                    Alerts ({reportPreview.alerts.length})
                  </h3>
                  <ul className="text-sm text-yellow-700 dark:text-yellow-300 space-y-1">
                    {reportPreview.alerts.map((alert, i) => (
                      <li key={i}>{alert}</li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Sensors summary */}
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-gray-200 dark:border-gray-700">
                      <th className="text-left py-2 font-medium text-gray-900 dark:text-white">
                        Sensor
                      </th>
                      <th className="text-center py-2 font-medium text-gray-900 dark:text-white">
                        Temp (Avg)
                      </th>
                      <th className="text-center py-2 font-medium text-gray-900 dark:text-white">
                        Humidity
                      </th>
                      <th className="text-center py-2 font-medium text-gray-900 dark:text-white">
                        Battery
                      </th>
                      <th className="text-center py-2 font-medium text-gray-900 dark:text-white">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {reportPreview.sensors.map((sensor) => (
                      <tr
                        key={sensor.device_name}
                        className="border-b border-gray-100 dark:border-gray-800"
                      >
                        <td className="py-2 text-gray-900 dark:text-white">
                          {sensor.device_name}
                        </td>
                        <td className="py-2 text-center text-gray-600 dark:text-gray-400">
                          {sensor.avg_temp !== null ? `${sensor.avg_temp}°C` : '—'}
                        </td>
                        <td className="py-2 text-center text-gray-600 dark:text-gray-400">
                          {sensor.avg_humidity !== null ? `${sensor.avg_humidity}%` : '—'}
                        </td>
                        <td className="py-2 text-center text-gray-600 dark:text-gray-400">
                          {sensor.battery !== null ? `${sensor.battery}%` : '—'}
                        </td>
                        <td className="py-2 text-center">
                          {sensor.is_offline ? (
                            <span className="text-red-500">Offline</span>
                          ) : (
                            <span className="text-sp-lime">Online</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            <p className="text-gray-500 dark:text-gray-400">
              No preview available
            </p>
          )}
        </section>
      )}
    </div>
  );
}

export default Settings;
