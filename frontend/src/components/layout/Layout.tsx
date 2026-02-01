// ================================
// SensorPulse Frontend - Layout Component
// ================================

import { ReactNode } from 'react';
import { Header } from './Header';
import type { ConnectionStatus } from '../../types';

interface LayoutProps {
  children: ReactNode;
  connectionStatus: ConnectionStatus;
  onReconnect: () => void;
}

export function Layout({ children, connectionStatus, onReconnect }: LayoutProps) {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800">
      <Header connectionStatus={connectionStatus} onReconnect={onReconnect} />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
      <footer className="text-center py-6 text-sm text-gray-500 dark:text-gray-400">
        <p>
          SensorPulse v{import.meta.env.VITE_APP_VERSION || '0.1.0'} • 
          Built with ❤️ using React + Tailwind
        </p>
      </footer>
    </div>
  );
}

export default Layout;
