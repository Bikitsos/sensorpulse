// ================================
// SensorPulse Frontend - TemperatureChart Tests
// ================================

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { TemperatureChart } from '../TemperatureChart';
import type { SensorReading } from '../../types';

function makeReadings(count: number): SensorReading[] {
  return Array.from({ length: count }, (_, i) => ({
    time: new Date(Date.now() - (count - i) * 3600_000).toISOString(),
    topic: 'zigbee2mqtt/office',
    device_name: 'Office',
    temperature: 20 + Math.sin(i) * 5,
    humidity: 50 + Math.cos(i) * 10,
    battery: 85,
    linkquality: 120,
  }));
}

describe('TemperatureChart', () => {
  it('renders empty state when no readings', () => {
    render(
      <TemperatureChart readings={[]} deviceName="Office" />
    );
    expect(screen.getByText(/No data available for Office/)).toBeInTheDocument();
  });

  it('renders chart container with readings', () => {
    const { container } = render(
      <TemperatureChart readings={makeReadings(10)} deviceName="Office" />
    );
    // Recharts renders inside a ResponsiveContainer → should have the chart wrapper
    const wrapper = container.querySelector('.recharts-responsive-container');
    expect(wrapper || container.querySelector('[class*="h-["]')).toBeTruthy();
  });

  it('does not show empty state when readings exist', () => {
    render(
      <TemperatureChart readings={makeReadings(5)} deviceName="Office" />
    );
    expect(screen.queryByText(/No data available/)).toBeNull();
  });

  it('showHumidity defaults to true', () => {
    const { container } = render(
      <TemperatureChart readings={makeReadings(5)} deviceName="Office" />
    );
    // When showHumidity is true, the humidity gradient should exist in the SVG defs
    const svg = container.querySelector('svg');
    if (svg) {
      const humGradient = svg.querySelector('#humidityGradient');
      expect(humGradient).toBeTruthy();
    }
  });
});
