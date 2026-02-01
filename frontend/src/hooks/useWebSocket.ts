// ================================
// SensorPulse Frontend - WebSocket Hook
// ================================

import { useState, useEffect, useCallback, useRef } from 'react';
import type { WebSocketMessage, ConnectionStatus, SensorReading } from '../types';

const WS_URL = import.meta.env.VITE_WS_URL || `ws://${window.location.host}/ws/sensors`;
const RECONNECT_DELAY = 3000;
const MAX_RECONNECT_ATTEMPTS = 10;

interface UseWebSocketOptions {
  onReading?: (reading: SensorReading) => void;
  autoConnect?: boolean;
}

interface UseWebSocketReturn {
  status: ConnectionStatus;
  lastMessage: WebSocketMessage | null;
  subscribe: (devices: string[]) => void;
  unsubscribe: (devices: string[]) => void;
  connect: () => void;
  disconnect: () => void;
}

export function useWebSocket(options: UseWebSocketOptions = {}): UseWebSocketReturn {
  const { onReading, autoConnect = true } = options;
  
  const [status, setStatus] = useState<ConnectionStatus>('disconnected');
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<ReturnType<typeof setTimeout>>();
  const onReadingRef = useRef(onReading);

  // Keep callback ref updated
  useEffect(() => {
    onReadingRef.current = onReading;
  }, [onReading]);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    setStatus('connecting');

    try {
      const ws = new WebSocket(WS_URL);

      ws.onopen = () => {
        console.log('[WebSocket] Connected');
        setStatus('connected');
        reconnectAttempts.current = 0;
      };

      ws.onclose = (event) => {
        console.log('[WebSocket] Disconnected', event.code, event.reason);
        setStatus('disconnected');
        wsRef.current = null;

        // Auto-reconnect unless closed intentionally (code 1000)
        if (event.code !== 1000 && reconnectAttempts.current < MAX_RECONNECT_ATTEMPTS) {
          reconnectAttempts.current++;
          console.log(`[WebSocket] Reconnecting in ${RECONNECT_DELAY}ms (attempt ${reconnectAttempts.current})`);
          reconnectTimeout.current = setTimeout(connect, RECONNECT_DELAY);
        }
      };

      ws.onerror = (error) => {
        console.error('[WebSocket] Error', error);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          setLastMessage(message);

          if (message.type === 'reading' && message.data && onReadingRef.current) {
            onReadingRef.current(message.data);
          }
        } catch (error) {
          console.error('[WebSocket] Failed to parse message', error);
        }
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('[WebSocket] Failed to connect', error);
      setStatus('disconnected');
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
    }
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'User disconnect');
      wsRef.current = null;
    }
    
    setStatus('disconnected');
  }, []);

  const subscribe = useCallback((devices: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'subscribe',
        devices,
      }));
    }
  }, []);

  const unsubscribe = useCallback((devices: string[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'unsubscribe',
        devices,
      }));
    }
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, connect, disconnect]);

  return {
    status,
    lastMessage,
    subscribe,
    unsubscribe,
    connect,
    disconnect,
  };
}

export default useWebSocket;
