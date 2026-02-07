// ================================
// SensorPulse Frontend - Type Helper Tests
// ================================

import { describe, it, expect } from 'vitest';
import {
  getTemperatureRange,
  getTemperatureColor,
  getTemperatureBadgeClass,
  getHumidityRange,
  getHumidityColor,
  getBatteryColor,
} from '../types';

describe('getTemperatureRange', () => {
  it('returns "cold" for < 10', () => {
    expect(getTemperatureRange(5)).toBe('cold');
  });

  it('returns "normal" for 10–21', () => {
    expect(getTemperatureRange(15)).toBe('normal');
  });

  it('returns "warm" for 22–27', () => {
    expect(getTemperatureRange(25)).toBe('warm');
  });

  it('returns "hot" for >= 28', () => {
    expect(getTemperatureRange(35)).toBe('hot');
  });

  it('returns "normal" for null', () => {
    expect(getTemperatureRange(null)).toBe('normal');
  });
});

describe('getTemperatureColor', () => {
  it('returns blue classes for cold', () => {
    expect(getTemperatureColor(3)).toContain('blue');
  });

  it('returns cyan for normal', () => {
    expect(getTemperatureColor(18)).toContain('sp-cyan');
  });

  it('returns orange for warm', () => {
    expect(getTemperatureColor(25)).toContain('orange');
  });

  it('returns red for hot', () => {
    expect(getTemperatureColor(35)).toContain('red');
  });
});

describe('getTemperatureBadgeClass', () => {
  it('includes range name in badge class', () => {
    expect(getTemperatureBadgeClass(5)).toContain('temp-badge-cold');
    expect(getTemperatureBadgeClass(20)).toContain('temp-badge-normal');
    expect(getTemperatureBadgeClass(25)).toContain('temp-badge-warm');
    expect(getTemperatureBadgeClass(35)).toContain('temp-badge-hot');
  });
});

describe('getHumidityRange', () => {
  it('returns "low" for < 30', () => {
    expect(getHumidityRange(20)).toBe('low');
  });

  it('returns "normal" for 30–64', () => {
    expect(getHumidityRange(50)).toBe('normal');
  });

  it('returns "high" for >= 65', () => {
    expect(getHumidityRange(80)).toBe('high');
  });

  it('returns "normal" for null', () => {
    expect(getHumidityRange(null)).toBe('normal');
  });
});

describe('getHumidityColor', () => {
  it('returns yellow for low', () => {
    expect(getHumidityColor(20)).toContain('yellow');
  });

  it('returns cyan for normal', () => {
    expect(getHumidityColor(50)).toContain('sp-cyan');
  });

  it('returns blue for high', () => {
    expect(getHumidityColor(80)).toContain('blue');
  });
});

describe('getBatteryColor', () => {
  it('returns red for < 20', () => {
    expect(getBatteryColor(10)).toContain('red');
  });

  it('returns yellow for 20–49', () => {
    expect(getBatteryColor(30)).toContain('yellow');
  });

  it('returns lime for >= 50', () => {
    expect(getBatteryColor(80)).toContain('sp-lime');
  });

  it('returns gray for null', () => {
    expect(getBatteryColor(null)).toContain('gray');
  });
});
