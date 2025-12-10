import { ref, reactive, onMounted, onUnmounted } from 'vue';

export interface WebSocketMessage {
  type: string;
  payload?: any;
  timestamp?: string;
  [key: string]: any;
}

export interface WebSocketConfig {
  url: string;
  protocols?: string | string[];
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

class WebSocketManager {
  private ws: WebSocket | null = null;
  private config: WebSocketConfig;
  private reconnectAttempts = 0;
  private reconnectTimer: number | null = null;
  private messageHandlers: Map<string, (message: WebSocketMessage) => void> = new Map();
  private eventHandlers: Map<string, (event: any) => void> = new Map();

  public isConnected = ref(false);
  public isConnecting = ref(false);
  public lastMessage = ref<WebSocketMessage | null>(null);
  public error = ref<string | null>(null);

  constructor(config: WebSocketConfig) {
    this.config = {
      reconnectInterval: 5000,
      maxReconnectAttempts: 10,
      ...config,
    };
  }

  connect(): void {
    if (this.isConnecting.value || this.isConnected.value) {
      console.log('WebSocket connection already in progress or established');
      return;
    }

    this.isConnecting.value = true;
    this.error.value = null;

    try {
      this.ws = new WebSocket(this.config.url, this.config.protocols);

      this.ws.onopen = () => {
        console.log('WebSocket connected');
        this.isConnected.value = true;
        this.isConnecting.value = false;
        this.reconnectAttempts = 0; // Reset on successful connection
        this.error.value = null; // Clear any previous errors
      };

      this.ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          this.lastMessage.value = message;

          // Handle message by type
          const handler = this.messageHandlers.get(message.type);
          if (handler) {
            handler(message);
          }

          // Emit general message event
          const eventHandler = this.eventHandlers.get('message');
          if (eventHandler) {
            eventHandler(message);
          }
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      };

      this.ws.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        this.isConnected.value = false;
        this.isConnecting.value = false;

        // Determine if we should attempt reconnection
        const shouldReconnect = this.shouldAttemptReconnect(event);

        if (shouldReconnect && this.reconnectAttempts < (this.config.maxReconnectAttempts || 10)) {
          this.scheduleReconnect();
        } else if (!shouldReconnect) {
          console.log('WebSocket closed cleanly or intentionally, not reconnecting');
        } else {
          console.log('Max reconnection attempts reached, giving up');
        }
      };

      this.ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.error.value = 'WebSocket connection error';
        this.isConnecting.value = false;

        // Schedule reconnection on error (will be handled by onclose if connection closes)
        // We don't schedule here to avoid double scheduling
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.error.value = 'Failed to create WebSocket connection';
      this.isConnecting.value = false;
    }
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close(1000, 'Client disconnect'); // Clean close
      this.ws = null;
    }

    this.isConnected.value = false;
    this.isConnecting.value = false;
    this.reconnectAttempts = 0; // Reset attempts on intentional disconnect
  }

  reconnect(): void {
    console.log('Manual reconnect requested');
    this.disconnect(); // Clean disconnect first
    setTimeout(() => this.connect(), 100); // Small delay before reconnect
  }

  private shouldAttemptReconnect(event: CloseEvent): boolean {
    // Don't reconnect if the connection was closed cleanly
    if (event.wasClean) {
      return false;
    }

    // Don't reconnect for certain error codes
    const noReconnectCodes = [1000, 1001, 1005]; // Normal closure, going away, no status
    if (noReconnectCodes.includes(event.code)) {
      return false;
    }

    // Reconnect for network errors, server errors, etc.
    return true;
  }

  send(message: WebSocketMessage): void {
    if (this.ws && this.isConnected.value) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected, cannot send message');
    }
  }

  subscribe(messageType: string, handler: (message: WebSocketMessage) => void): void {
    this.messageHandlers.set(messageType, handler);
  }

  unsubscribe(messageType: string): void {
    this.messageHandlers.delete(messageType);
  }

  on(event: string, handler: (data: any) => void): void {
    this.eventHandlers.set(event, handler);
  }

  off(event: string): void {
    this.eventHandlers.delete(event);
  }

  private scheduleReconnect(): void {
    // Clear any existing timer
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
    }

    this.reconnectAttempts++;
    const delay = Math.min(
      (this.config.reconnectInterval || 5000) * Math.pow(1.5, this.reconnectAttempts - 1),
      30000 // Max 30 seconds
    );

    console.log(`Scheduling reconnect attempt ${this.reconnectAttempts}/${this.config.maxReconnectAttempts || 10} in ${delay}ms`);

    this.reconnectTimer = window.setTimeout(() => {
      // Double-check we're not already connecting/connected
      if (!this.isConnecting.value && !this.isConnected.value) {
        console.log(`Attempting reconnect ${this.reconnectAttempts}`);
        this.connect();
      } else {
        console.log('Skipping reconnect - already connecting or connected');
      }
    }, delay);
  }
}

// Global WebSocket instances
const websocketInstances = new Map<string, WebSocketManager>();

export function useWebSocket(config: WebSocketConfig) {
  const key = config.url;

  if (!websocketInstances.has(key)) {
    websocketInstances.set(key, new WebSocketManager(config));
  }

  const ws = websocketInstances.get(key)!;

  // Auto-connect on component mount
  onMounted(() => {
    if (!ws.isConnected.value && !ws.isConnecting.value) {
      ws.connect();
    }
  });

  // Auto-disconnect on component unmount (optional - keep connection alive)
  // onUnmounted(() => {
  //   // Only disconnect if no other components are using it
  //   // For now, keep connections alive
  // });

  return {
    isConnected: ws.isConnected,
    isConnecting: ws.isConnecting,
    lastMessage: ws.lastMessage,
    error: ws.error,
    connect: () => ws.connect(),
    disconnect: () => ws.disconnect(),
    reconnect: () => ws.reconnect(),
    send: (message: WebSocketMessage) => ws.send(message),
    subscribe: (type: string, handler: (message: WebSocketMessage) => void) => ws.subscribe(type, handler),
    unsubscribe: (type: string) => ws.unsubscribe(type),
    on: (event: string, handler: (data: any) => void) => ws.on(event, handler),
    off: (event: string) => ws.off(event),
  };
}

// Specific composable for Freqtrade WebSocket
export function useFreqtradeWebSocket() {
  const config: WebSocketConfig = {
    url: `ws://localhost:8001/ws`,
    reconnectInterval: 5000,
    maxReconnectAttempts: 10,
  };

  return useWebSocket(config);
}

// Specific composable for MCP WebSocket
export function useMCPWebSocket() {
  const config: WebSocketConfig = {
    url: `ws://localhost:8001/ws/mcp`,
    reconnectInterval: 5000,
    maxReconnectAttempts: 10,
  };

  return useWebSocket(config);
}