import { defineStore } from 'pinia';
import apiClient from '@/services/apiClient';
import { ref, Ref } from 'vue';
import { useMCPWebSocket } from '@/composables/websocket';

export interface ServiceStatus {
  name: string;
  status: 'healthy' | 'unhealthy' | 'degraded';
  details?: Record<string, any> | string;
}

export const useMonitoringStore = defineStore('monitoring', () => {
  const services: Ref<ServiceStatus[]> = ref([]);
  const loading: Ref<boolean> = ref(false);

  // WebSocket integration
  const { isConnected, subscribe, send } = useMCPWebSocket();

  async function fetchSystemStatus() {
    loading.value = true;
    try {
      const response = await apiClient.get('/monitoring/status');
      services.value = response.data;
    } catch (error) {
      console.error('Failed to fetch system status:', error);
      // Create a default error state if the API call fails
      services.value = [
        { name: 'Management Server', status: 'unhealthy', details: 'Failed to fetch status' },
        { name: 'Trading Gateway', status: 'unhealthy', details: 'Failed to fetch status' },
        { name: 'Redis', status: 'unhealthy', details: 'Failed to fetch status' },
      ];
    } finally {
      loading.value = false;
    }
  }

  // Subscribe to real-time monitoring events
  function setupWebSocketListeners() {
    // Subscribe to system status updates
    subscribe('SYSTEM_STATUS_UPDATE', (message) => {
      console.log('Received system status update:', message);
      if (message.payload && Array.isArray(message.payload.services)) {
        services.value = message.payload.services;
      }
    });

    // Subscribe to service health events
    subscribe('SERVICE_HEALTH', (message) => {
      console.log('Received service health update:', message);
      const { service_name, status, details } = message.payload || {};

      if (service_name) {
        const existingService = services.value.find(s => s.name === service_name);
        if (existingService) {
          existingService.status = status || existingService.status;
          existingService.details = details || existingService.details;
        } else {
          services.value.push({
            name: service_name,
            status: status || 'unknown',
            details: details || {}
          });
        }
      }
    });

    // Subscribe to bot events that might affect monitoring
    subscribe('BOT_STARTED', (message) => {
      console.log('Bot started event:', message);
      // Could trigger a status refresh
      fetchSystemStatus();
    });

    subscribe('BOT_STOPPED', (message) => {
      console.log('Bot stopped event:', message);
      fetchSystemStatus();
    });
  }

  // Initialize WebSocket connection and listeners
  function initializeWebSocket() {
    if (isConnected.value) {
      setupWebSocketListeners();
    } else {
      // Wait for connection and then setup listeners
      const checkConnection = setInterval(() => {
        if (isConnected.value) {
          clearInterval(checkConnection);
          setupWebSocketListeners();
        }
      }, 1000);
    }
  }

  // Request subscription to monitoring topics
  function subscribeToMonitoring() {
    send({
      type: 'SUBSCRIBE',
      topics: ['system_status', 'service_health', 'bot_events']
    });
  }

  return {
    services,
    loading,
    isConnected,
    fetchSystemStatus,
    initializeWebSocket,
    subscribeToMonitoring,
  };
});
