// ================================
// SensorPulse Frontend - SensorCard Tests
// ================================

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { SensorCard } from '../SensorCard';
import type { SensorLatest } from '../../types';

function makeSensor(overrides: Partial<SensorLatest> = {}): SensorLatest {
  return {
    time: new Date().toISOString(),
    topic: 'zigbee2mqtt/office_sensor',
    device_name: 'Office Sensor',
    temperature: 22.5,
    humidity: 55,
    battery: 85,
    linkquality: 120,
    last_seen_minutes: 2,
    ...overrides,
  };
}

describe('SensorCard', () => {
  it('renders device name', () => {
    render(<SensorCard sensor={makeSensor()} />);
    expect(screen.getByText('Office Sensor')).toBeInTheDocument();
  });

  it('renders temperature value', () => {
    render(<SensorCard sensor={makeSensor({ temperature: 18.3 })} />);
    expect(screen.getByText('18.3°')).toBeInTheDocument();
  });

  it('renders — when temperature is null', () => {
    render(<SensorCard sensor={makeSensor({ temperature: null })} />);
    const dashes = screen.getAllByText('—');
    expect(dashes.length).toBeGreaterThanOrEqual(1);
  });

  it('renders humidity value', () => {
    render(<SensorCard sensor={makeSensor({ humidity: 60 })} />);
    expect(screen.getByText('60%')).toBeInTheDocument();
  });

  it('renders battery percentage', () => {
    render(<SensorCard sensor={makeSensor({ battery: 85 })} />);
    expect(screen.getByText('85%')).toBeInTheDocument();
  });

  it('hides battery bar when battery is null', () => {
    const { container } = render(
      <SensorCard sensor={makeSensor({ battery: null })} />
    );
    expect(container.querySelector('.battery-bar')).toBeNull();
  });

  it('renders battery bar with correct width', () => {
    const { container } = render(
      <SensorCard sensor={makeSensor({ battery: 42 })} />
    );
    const bar = container.querySelector('.battery-bar') as HTMLElement;
    expect(bar).toBeTruthy();
    expect(bar.style.width).toBe('42%');
  });

  it('shows link quality when present', () => {
    render(<SensorCard sensor={makeSensor({ linkquality: 120 })} />);
    expect(screen.getByText('120')).toBeInTheDocument();
  });

  it('shows online status when last_seen_minutes < 10', () => {
    const { container } = render(
      <SensorCard sensor={makeSensor({ last_seen_minutes: 2 })} />
    );
    expect(container.querySelector('.status-online')).toBeTruthy();
  });

  it('shows stale status when last_seen_minutes between 10 and 120', () => {
    const { container } = render(
      <SensorCard sensor={makeSensor({ last_seen_minutes: 60 })} />
    );
    expect(container.querySelector('.status-stale')).toBeTruthy();
  });

  it('shows offline status when last_seen_minutes >= 120', () => {
    const { container } = render(
      <SensorCard sensor={makeSensor({ last_seen_minutes: 200 })} />
    );
    expect(container.querySelector('.status-offline')).toBeTruthy();
  });

  it('applies selected ring when isSelected', () => {
    const { container } = render(
      <SensorCard sensor={makeSensor()} isSelected />
    );
    const card = container.firstChild as HTMLElement;
    expect(card.className).toContain('ring-sp-cyan');
  });

  it('calls onClick when clicked', async () => {
    const user = userEvent.setup();
    const onClick = vi.fn();
    render(<SensorCard sensor={makeSensor()} onClick={onClick} />);
    
    const card = screen.getByText('Office Sensor').closest('div[class*="glass-card"]');
    if (card) await user.click(card);
    
    expect(onClick).toHaveBeenCalledOnce();
  });

  it('shows cold badge for low temperature', () => {
    render(<SensorCard sensor={makeSensor({ temperature: 5 })} />);
    expect(screen.getByText(/Cold/)).toBeInTheDocument();
  });

  it('shows hot badge for high temperature', () => {
    render(<SensorCard sensor={makeSensor({ temperature: 35 })} />);
    expect(screen.getByText(/Hot/)).toBeInTheDocument();
  });
});
