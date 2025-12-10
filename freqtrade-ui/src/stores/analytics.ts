import { defineStore } from 'pinia';
import apiClient from '@/services/apiClient';
import { ref } from 'vue';
import type { Ref } from 'vue';
import { z } from 'zod';

const PerformanceDataSchema = z.object({
  total_trades: z.number(),
  profitable_trades: z.number(),
  avg_profit: z.number(),
  win_rate: z.number(),
});

const RiskDataSchema = z.object({
  max_drawdown: z.number(),
});

const PortfolioDataSchema = z.object({
  portfolio_value: z.number(),
});

const MarketDataSchema = z.object({
  symbol: z.string(),
  current_price_usd: z.number(),
  price_change_percentage_24h: z.number(),
  market_sentiment: z.enum(['positive', 'negative', 'neutral']),
});

export type PerformanceData = z.infer<typeof PerformanceDataSchema>;
export type RiskData = z.infer<typeof RiskDataSchema>;
export type PortfolioData = z.infer<typeof PortfolioDataSchema>;
export type MarketData = z.infer<typeof MarketDataSchema>;

export const useAnalyticsStore = defineStore('analytics', () => {
  const performanceData: Ref<PerformanceData | null> = ref(null);
  const riskData: Ref<RiskData | null> = ref(null);
  const portfolioData: Ref<PortfolioData | null> = ref(null);
  const marketData: Ref<MarketData | null> = ref(null);
  const loading: Ref<boolean> = ref(false);
  const error: Ref<string | null> = ref(null);

  async function fetchAnalytics(botId: number | null = null, marketSymbol: string = 'bitcoin') {
    loading.value = true;
    error.value = null;
    try {
      const botParams = botId ? { bot_id: botId } : {};
      const marketParams = { symbol: marketSymbol };

      const [perfRes, riskRes, portfolioRes, marketRes] = await Promise.all([
        apiClient.get('/analytics/performance', { params: botParams }),
        apiClient.get('/analytics/risk', { params: botParams }),
        apiClient.get('/analytics/portfolio'),
        apiClient.get('/analytics/market', { params: marketParams }),
      ]);

      performanceData.value = PerformanceDataSchema.parse(perfRes.data.data);
      riskData.value = RiskDataSchema.parse(riskRes.data.data);
      portfolioData.value = PortfolioDataSchema.parse(portfolioRes.data.data);
      marketData.value = MarketDataSchema.parse(marketRes.data.data);

    } catch (e: any) {
      if (e instanceof z.ZodError) {
        error.value = "Received invalid data from the server.";
        console.error("Zod validation error:", e.errors);
      } else {
        error.value = e.response?.data?.detail || 'Failed to fetch analytics data.';
        console.error(error.value);
      }
    } finally {
      loading.value = false;
    }
  }

  return {
    performanceData,
    riskData,
    portfolioData,
    marketData,
    loading,
    error,
    fetchAnalytics,
  };
});
