import { defineStore } from 'pinia';
import apiClient from '@/services/apiClient';

export const useExchangesStore = defineStore('exchanges', {
  state: () => ({
    exchanges: [] as string[],
    pairs: [] as string[],
    loading: false,
    error: null,
  }),
  actions: {
    async fetchExchanges() {
      this.loading = true;
      try {
        const response = await apiClient.get('/exchanges');
        this.exchanges = response.data;
        this.error = null;
      } catch (error) {
        this.error = error;
        console.error('Failed to fetch exchanges:', error);
      } finally {
        this.loading = false;
      }
    },
    async fetchPairs(exchangeId: string) {
      if (!exchangeId) return;
      this.loading = true;
      try {
        const response = await apiClient.get(`/exchanges/${exchangeId}/pairs`);
        this.pairs = response.data;
        this.error = null;
      } catch (error) {
        this.error = error;
        this.pairs = []; // Reset pairs on error
        console.error(`Failed to fetch pairs for ${exchangeId}:`, error);
      } finally {
        this.loading = false;
      }
    },
  },
});
