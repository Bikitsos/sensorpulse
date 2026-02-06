// ================================
// SensorPulse Frontend - Dark Mode Hook
// ================================

import { useState, useEffect, useCallback } from 'react';

type Theme = 'light' | 'dark' | 'system';

const STORAGE_KEY = 'sensorpulse-theme';

function getSystemPreference(): 'light' | 'dark' {
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyTheme(theme: Theme) {
  const resolved = theme === 'system' ? getSystemPreference() : theme;
  if (resolved === 'dark') {
    document.documentElement.classList.add('dark');
  } else {
    document.documentElement.classList.remove('dark');
  }
}

export function useDarkMode() {
  const [theme, setThemeState] = useState<Theme>(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as Theme | null;
    return stored ?? 'system';
  });

  const [resolved, setResolved] = useState<'light' | 'dark'>(() => {
    const stored = localStorage.getItem(STORAGE_KEY) as Theme | null;
    const t = stored ?? 'system';
    return t === 'system' ? getSystemPreference() : t;
  });

  // Apply theme on mount and when it changes
  useEffect(() => {
    applyTheme(theme);
    const r = theme === 'system' ? getSystemPreference() : theme;
    setResolved(r);
    localStorage.setItem(STORAGE_KEY, theme);
  }, [theme]);

  // Listen for system preference changes when in "system" mode
  useEffect(() => {
    if (theme !== 'system') return;

    const mq = window.matchMedia('(prefers-color-scheme: dark)');
    const handler = (e: MediaQueryListEvent) => {
      applyTheme('system');
      setResolved(e.matches ? 'dark' : 'light');
    };
    mq.addEventListener('change', handler);
    return () => mq.removeEventListener('change', handler);
  }, [theme]);

  const setTheme = useCallback((t: Theme) => {
    setThemeState(t);
  }, []);

  const toggle = useCallback(() => {
    setThemeState((prev) => {
      if (prev === 'light') return 'dark';
      if (prev === 'dark') return 'system';
      return 'light';
    });
  }, []);

  const isDark = resolved === 'dark';

  return { theme, resolved, isDark, setTheme, toggle };
}

export default useDarkMode;
