// src/types/api.ts
export interface Bot {
  id: number;
  name: string;
  status: 'running' | 'stopped' | 'starting' | 'stopping' | 'error';
  strategy_name: string;
  exchange: string;
  stake_amount: number;
  max_open_trades: number;
  config: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface Strategy {
  id?: number;
  name: string;
  code: string;
  created_at?: string;
  updated_at?: string;
}

export interface AnalyticsData {
  total_trades: number;
  profitable_trades: number;
  win_rate: number;
  avg_profit: number;
  portfolio_value: number;
  assets: Array<{
    symbol: string;
    amount: number;
    value: number;
  }>;
  pnl: {
    total: number;
    daily: number;
    weekly: number;
  };
  max_drawdown: number;
  sharpe_ratio: number;
  volatility: number;
}

export interface MarketData {
  symbol: string;
  current_price_usd: number;
  price_change_percentage_24h: number;
  market_sentiment: 'bullish' | 'bearish' | 'neutral';
}

export interface Trade {
  id: number;
  pair: string;
  type: 'buy' | 'sell';
  amount: number;
  currency: string;
  profit: number;
  timestamp: Date;
}

export interface AuditLog {
  id: number;
  timestamp: string;
  user: string;
  action: string;
  method: string;
  url: string;
  status: number;
  ip: string;
  user_agent: string;
}

export interface SystemService {
  id: number;
  name: string;
  status: 'healthy' | 'unhealthy' | 'unknown';
  response_time: number;
  uptime: number;
  last_check: string;
}

export interface ProcessInfo {
  id: number;
  name: string;
  pid: number;
  status: 'running' | 'stopped' | 'error';
  cpu: number;
  memory: number;
}

export interface Alert {
  id: number;
  title: string;
  message: string;
  severity: 'low' | 'medium' | 'high' | 'critical';
  timestamp: string;
}

export interface LogEntry {
  timestamp: Date;
  level: 'info' | 'warning' | 'error' | 'debug';
  message: string;
}

export interface AIModel {
  id: number;
  name: string;
  description: string;
  status: string;
  accuracy: number | null;
  features: number;
}

export interface TrainingJob {
  id: number;
  modelName: string;
  progress: number;
  status: string;
}

export interface BacktestResult {
  id: number;
  model: string;
  strategy: string;
  sharpe: number;
  maxDrawdown: number;
  winRate: number;
}

export interface FeatureImportance {
  name: string;
  importance: number;
}

export interface DataDownload {
  id: number;
  pairs: string[];
  exchange: string;
  timeframe: string;
  days: number;
  status: string;
  timestamp: Date;
}

export interface HyperoptJob {
  id: number;
  strategy: string;
  progress: number;
  currentEpoch: number;
  totalEpochs: number;
  bestLoss: number;
}

export interface HyperoptResult {
  id: number;
  strategy: string;
  loss: number;
  totalProfit: number;
  maxDrawdown: number;
  winRate: number;
  totalTrades: number;
  parameters: {
    buy_rsi: number;
    sell_rsi: number;
    stoploss: number;
    roi_t1: number;
    roi_t2: number;
    roi_t3: number;
  };
}