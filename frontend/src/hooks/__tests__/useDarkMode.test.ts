// ================================
// SensorPulse Frontend - useDarkMode Hook Tests
// ================================

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useDarkMode } from '../useDarkMode';

describe('useDarkMode', () => {
  beforeEach(() => {
    localStorage.clear();
    document.documentElement.classList.remove('dark');
  });

  it('defaults to system theme when no stored value', () => {
    const { result } = renderHook(() => useDarkMode());
    expect(result.current.theme).toBe('system');
  });

  it('reads stored theme from localStorage', () => {
    localStorage.setItem('sensorpulse-theme', 'dark');
    const { result } = renderHook(() => useDarkMode());
    expect(result.current.theme).toBe('dark');
    expect(result.current.isDark).toBe(true);
  });

  it('setTheme changes theme to dark', () => {
    const { result } = renderHook(() => useDarkMode());
    act(() => result.current.setTheme('dark'));
    expect(result.current.theme).toBe('dark');
    expect(result.current.isDark).toBe(true);
    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });

  it('setTheme changes theme to light', () => {
    const { result } = renderHook(() => useDarkMode());
    act(() => result.current.setTheme('light'));
    expect(result.current.theme).toBe('light');
    expect(result.current.isDark).toBe(false);
    expect(document.documentElement.classList.contains('dark')).toBe(false);
  });

  it('persists theme choice to localStorage', () => {
    const { result } = renderHook(() => useDarkMode());
    act(() => result.current.setTheme('dark'));
    expect(localStorage.getItem('sensorpulse-theme')).toBe('dark');
  });

  it('toggle cycles light → dark → system → light', () => {
    const { result } = renderHook(() => useDarkMode());
    
    // Start at system, set to light first
    act(() => result.current.setTheme('light'));
    expect(result.current.theme).toBe('light');
    
    act(() => result.current.toggle());
    expect(result.current.theme).toBe('dark');
    
    act(() => result.current.toggle());
    expect(result.current.theme).toBe('system');
    
    act(() => result.current.toggle());
    expect(result.current.theme).toBe('light');
  });

  it('resolved is "light" when system prefers light and theme is "system"', () => {
    // Our matchMedia mock returns false for prefers-color-scheme: dark
    const { result } = renderHook(() => useDarkMode());
    act(() => result.current.setTheme('system'));
    expect(result.current.resolved).toBe('light');
  });

  it('isDark reflects the resolved theme', () => {
    const { result } = renderHook(() => useDarkMode());
    
    act(() => result.current.setTheme('dark'));
    expect(result.current.isDark).toBe(true);
    
    act(() => result.current.setTheme('light'));
    expect(result.current.isDark).toBe(false);
  });
});
