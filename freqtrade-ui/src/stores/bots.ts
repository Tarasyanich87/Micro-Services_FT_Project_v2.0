import { defineStore } from 'pinia';
import apiClient, { freqaiApi } from '@/services/apiClient';
import { useMCPWebSocket } from '@/composables/websocket';

// Define the structure of a single prediction entry
interface Prediction {
  // Assuming the prediction data is a key-value pair of string to any type.
  // You might want to define a more specific type based on your API response.
  [key: string]: any;
}

export const useBotsStore = defineStore('bots', {
  state: () => ({
    bots: [] as any[], // Using any[] for now, but a specific type is better
    activeBotId: null as number | null,
    activeBotPredictions: [] as Prediction[], // To store predictions for the active bot
    isPredictionLoading: false, // To track loading state
  }),

  getters: {
    activeBot: (state) => state.bots.find(bot => bot.id === state.activeBotId),
  },
  actions: {
    // WebSocket setup
    setupWebSocketListeners() {
      const { subscribe } = useMCPWebSocket();

      // Subscribe to bot status updates
      subscribe('BOT_STATUS_UPDATE', (message) => {
        console.log('Bot status update:', message);
        const { bot_id, status, details } = message.payload || {};
        this.updateBotStatus(bot_id, status, details);
      });

      // Subscribe to bot events
      subscribe('BOT_STARTED', (message) => {
        console.log('Bot started:', message);
        const { bot_id } = message.payload || {};
        this.updateBotStatus(bot_id, 'running');
        this.fetchBots(); // Refresh full list
      });

      subscribe('BOT_STOPPED', (message) => {
        console.log('Bot stopped:', message);
        const { bot_id } = message.payload || {};
        this.updateBotStatus(bot_id, 'stopped');
        this.fetchBots(); // Refresh full list
      });

      subscribe('BOT_ERROR', (message) => {
        console.log('Bot error:', message);
        const { bot_id, error } = message.payload || {};
        this.updateBotStatus(bot_id, 'error', { error });
      });

      // Subscribe to trading events
      subscribe('TRADE_EXECUTED', (message) => {
        console.log('Trade executed:', message);
        // Could update bot's trade statistics
        this.fetchBots();
      });
    },

    updateBotStatus(botId: number, status: string, details?: any) {
      const bot = this.bots.find(b => b.id === botId);
      if (bot) {
        bot.status = status;
        if (details) {
          bot.details = { ...bot.details, ...details };
        }
      }
    },

    async fetchBots() {
      try {
        const response = await apiClient.get('/bots');
        this.bots = response.data;
      } catch (error) {
        console.error('Failed to fetch bots:', error);
      }
    },
    async startBot(botId: number) {
      try {
        await apiClient.post(`/bots/${botId}/start`);
        await this.fetchBots();
      } catch (error) {
        console.error(`Failed to start bot ${botId}:`, error);
      }
    },
    async stopBot(botId: number) {
      try {
        await apiClient.post(`/bots/${botId}/stop`);
        await this.fetchBots();
      } catch (error) {
        console.error(`Failed to stop bot ${botId}:`, error);
      }
    },
    async createBot(botData: any) {
      try {
        await apiClient.post('/bots', botData);
        await this.fetchBots();
      } catch (error) {
        console.error('Failed to create bot:', error);
        throw error;
      }
    },
    async updateBot(botId: number, botData: any) {
      try {
        await apiClient.put(`/bots/${botId}`, botData);
        await this.fetchBots();
      } catch (error) {
        console.error(`Failed to update bot ${botId}:`, error);
        throw error;
      }
    },
    async deleteBot(botId: number) {
      try {
        await apiClient.delete(`/bots/${botId}`);
        await this.fetchBots();
      } catch (error) {
        console.error(`Failed to delete bot ${botId}:`, error);
      }
    },
    async restartBot(botId: number) {
      try {
        await apiClient.post(`/bots/${botId}/restart`);
        await this.fetchBots();
      } catch (error) {
        console.error(`Failed to restart bot ${botId}:`, error);
      }
    },

    async startAllBots() {
      try {
        await apiClient.post('/bots/start-all');
        await this.fetchBots();
      } catch (error) {
        console.error('Failed to start all bots:', error);
      }
    },
    async stopAllBots() {
      try {
        await apiClient.post('/bots/stop-all');
        await this.fetchBots();
      } catch (error) {
        console.error('Failed to stop all bots:', error);
      }
    },
    async emergencyStopAllBots() {
      try {
        await apiClient.post('/emergency/stop-all');
        setTimeout(() => {
          this.fetchBots();
        }, 1000);
      } catch (error) {
        console.error('Failed to send emergency stop command:', error);
      }
    },

    // Initialize WebSocket connection
    initializeWebSocket() {
      this.setupWebSocketListeners();
    },
    // Action to fetch predictions for a specific bot
    async fetchPredictions(botId: number) {
      this.isPredictionLoading = true;
      this.activeBotId = botId;
      try {
        // For now, use mock predictions since FreqAI Server may not have this endpoint yet
        // TODO: Update when FreqAI Server has prediction endpoint for bots
        const mockPredictions = [
          { pair: 'BTC/USDT', prediction: 0.85, confidence: 0.72 },
          { pair: 'ETH/USDT', prediction: 0.62, confidence: 0.68 },
          { pair: 'ADA/USDT', prediction: 0.91, confidence: 0.75 }
        ];
        this.activeBotPredictions = mockPredictions;
        console.log(`Mock predictions loaded for bot ${botId}`);
      } catch (error) {
        console.error(`Failed to fetch predictions for bot ${botId}:`, error);
        this.activeBotPredictions = []; // Clear previous data on error
      } finally {
        this.isPredictionLoading = false;
      }
    },
  },
});
