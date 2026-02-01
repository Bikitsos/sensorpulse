// ================================
// SensorPulse Frontend - Connection Status Component
// ================================

import { Wifi, WifiOff, RefreshCw } from 'lucide-react';
import clsx from 'clsx';
import type { ConnectionStatus as ConnectionStatusType } from '../../types';

interface ConnectionStatusProps {
  status: ConnectionStatusType;
  onReconnect?: () => void;
}

export function ConnectionStatus({ status, onReconnect }: ConnectionStatusProps) {
  const statusConfig = {
    connected: {
      icon: Wifi,
      text: 'Live',
      color: 'text-sp-lime',
      bgColor: 'bg-sp-lime/10',
      borderColor: 'border-sp-lime/30',
    },
    connecting: {
      icon: RefreshCw,
      text: 'Connecting',
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-500/10',
      borderColor: 'border-yellow-500/30',
    },
    disconnected: {
      icon: WifiOff,
      text: 'Offline',
      color: 'text-red-500',
      bgColor: 'bg-red-500/10',
      borderColor: 'border-red-500/30',
    },
  };

  const config = statusConfig[status];
  const Icon = config.icon;

  return (
    <button
      onClick={status === 'disconnected' ? onReconnect : undefined}
      disabled={status !== 'disconnected'}
      className={clsx(
        'flex items-center gap-2 px-3 py-1.5 rounded-full border transition-all',
        config.bgColor,
        config.borderColor,
        status === 'disconnected' && 'cursor-pointer hover:scale-105',
        status !== 'disconnected' && 'cursor-default'
      )}
    >
      <Icon
        className={clsx(
          'w-4 h-4',
          config.color,
          status === 'connecting' && 'animate-spin'
        )}
      />
      <span className={clsx('text-sm font-medium', config.color)}>
        {config.text}
      </span>
    </button>
  );
}

export default ConnectionStatus;
