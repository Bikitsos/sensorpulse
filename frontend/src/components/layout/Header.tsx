// ================================
// SensorPulse Frontend - Header Component
// ================================

import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Activity, Settings, LogOut, Menu, X, Moon, Sun, Monitor } from 'lucide-react';
import clsx from 'clsx';
import { useAuth } from '../../hooks/useAuth';
import { useDarkMode } from '../../hooks/useDarkMode';
import { ConnectionStatus } from './ConnectionStatus';
import type { ConnectionStatus as ConnectionStatusType } from '../../types';

interface HeaderProps {
  connectionStatus: ConnectionStatusType;
  onReconnect: () => void;
}

export function Header({ connectionStatus, onReconnect }: HeaderProps) {
  const { user, logout } = useAuth();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { theme, isDark, toggle } = useDarkMode();

  const ThemeIcon = theme === 'system' ? Monitor : isDark ? Moon : Sun;
  const themeLabel = theme === 'system' ? 'System' : isDark ? 'Dark' : 'Light';

  const navLinks = [
    { to: '/', label: 'Dashboard', icon: Activity },
    { to: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <header className="sticky top-0 z-50 glass-card border-b border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-2">
            <div className="relative w-8 h-8">
              <div className="absolute inset-0 rounded-full border-2 border-sp-charcoal" />
              <div className="absolute inset-1 rounded-full border-2 border-sp-cyan" />
              <div className="absolute inset-2 rounded-full border-2 border-sp-lime" />
            </div>
            <span className="text-xl font-bold">
              <span className="text-sp-charcoal dark:text-white">Sensor</span>
              <span className="text-sp-cyan">Pulse</span>
            </span>
          </Link>

          {/* Desktop Nav */}
          <nav className="hidden md:flex items-center gap-6">
            {navLinks.map((link) => (
              <Link
                key={link.to}
                to={link.to}
                className={clsx(
                  'flex items-center gap-2 px-3 py-2 rounded-lg transition-colors',
                  location.pathname === link.to
                    ? 'bg-sp-cyan/10 text-sp-cyan'
                    : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                )}
              >
                <link.icon className="w-5 h-5" />
                <span>{link.label}</span>
              </Link>
            ))}
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-4">
            <ConnectionStatus status={connectionStatus} onReconnect={onReconnect} />

            {/* Dark mode toggle */}
            <button
              onClick={toggle}
              className="p-2 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
              title={`Theme: ${themeLabel}`}
            >
              <ThemeIcon className="w-5 h-5" />
            </button>

            {/* User menu */}
            {user && (
              <div className="hidden md:flex items-center gap-3">
                <img
                  src={user.picture || `https://ui-avatars.com/api/?name=${encodeURIComponent(user.name || user.email)}`}
                  alt={user.name || user.email}
                  className="w-8 h-8 rounded-full"
                />
                <button
                  onClick={logout}
                  className="p-2 rounded-lg text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
                  title="Logout"
                >
                  <LogOut className="w-5 h-5" />
                </button>
              </div>
            )}

            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden p-2 rounded-lg text-gray-600 dark:text-gray-300"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {mobileMenuOpen && (
          <div className="md:hidden py-4 border-t border-gray-200 dark:border-gray-700">
            <nav className="flex flex-col gap-2">
              {navLinks.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  onClick={() => setMobileMenuOpen(false)}
                  className={clsx(
                    'flex items-center gap-2 px-3 py-2 rounded-lg transition-colors',
                    location.pathname === link.to
                      ? 'bg-sp-cyan/10 text-sp-cyan'
                      : 'text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
                  )}
                >
                  <link.icon className="w-5 h-5" />
                  <span>{link.label}</span>
                </Link>
              ))}
              {user && (
                <button
                  onClick={() => {
                    setMobileMenuOpen(false);
                    logout();
                  }}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20"
                >
                  <LogOut className="w-5 h-5" />
                  <span>Logout</span>
                </button>
              )}
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}

export default Header;
