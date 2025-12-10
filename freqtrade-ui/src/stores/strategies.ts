import { defineStore } from 'pinia';
import apiClient, { backtestingApi } from '@/services/apiClient';

interface Strategy {
  name: string;
}

interface BacktestResult {
  id: number;
  strategy_name: string;
  status: string;
  results?: any;
  created_at: string;
}

interface AnalysisResult {
  valid: boolean;
  errors: string[];
  parameters: Record<string, any>;
}

export const useStrategiesStore = defineStore('strategies', {
  state: () => ({
    strategies: [] as Strategy[],
    backtestResults: [] as BacktestResult[],
    loadingStrategies: false,
    loadingResults: false,
  }),
  actions: {
    async fetchStrategies() {
      this.loadingStrategies = true;
      try {
        const response = await apiClient.get('/strategies');
        this.strategies = response.data.map((name: string) => ({ name }));
      } catch (error) {
        console.error('Failed to fetch strategies:', error);
        throw error;
      } finally {
        this.loadingStrategies = false;
      }
    },

    async fetchBacktestResults() {
      this.loadingResults = true;
      try {
        const response = await apiClient.get('/strategies/backtest/results');
        this.backtestResults = response.data;
      } catch (error) {
        console.error('Failed to fetch backtest results:', error);
        throw error;
      } finally {
        this.loadingResults = false;
      }
    },

    async getStrategyCode(strategyName: string): Promise<string> {
      try {
        const response = await apiClient.get(`/strategies/${strategyName}`);
        return response.data.code;
      } catch (error) {
        console.error(`Failed to get strategy ${strategyName}:`, error);
        throw error;
      }
    },

    async createStrategy(strategyName: string, code: string) {
      try {
        await apiClient.post(`/strategies/?strategy_name=${strategyName}`, { code });
        await this.fetchStrategies();
      } catch (error) {
        console.error('Failed to create strategy:', error);
        throw error;
      }
    },

    async updateStrategy(strategyName: string, code: string) {
      try {
        await apiClient.put(`/strategies/${strategyName}`, { code });
        await this.fetchStrategies();
      } catch (error) {
        console.error('Failed to update strategy:', error);
        throw error;
      }
    },

    async deleteStrategy(strategyName: string) {
      try {
        await apiClient.delete(`/strategies/${strategyName}`);
        await this.fetchStrategies();
      } catch (error) {
        console.error('Failed to delete strategy:', error);
        throw error;
      }
    },

    async analyzeStrategy(code: string): Promise<AnalysisResult> {
      try {
        const response = await apiClient.post('/strategies/analyze', { code });
        return response.data;
      } catch (error) {
        console.error('Failed to analyze strategy:', error);
        throw error;
      }
    },

    async uploadMarkdownStrategy(file: File): Promise<string> {
      try {
        const formData = new FormData();
        formData.append('file', file);
        const response = await apiClient.post('/strategies/upload_md', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        });
        return response.data.code;
      } catch (error) {
        console.error('Failed to upload markdown strategy:', error);
        throw error;
      }
    },

    async startBacktest(strategyName: string, botId: number) {
      try {
        const response = await backtestingApi.post('/test-backtest', {
          strategy_name: strategyName,
          bot_id: botId,
        });
        await this.fetchBacktestResults();
        return response.data;
      } catch (error) {
        console.error('Failed to start backtest:', error);
        throw error;
      }
    },
  },
});