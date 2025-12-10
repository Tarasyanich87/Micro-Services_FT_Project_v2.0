<template>
  <div class="analytics-dashboard">
    <div class="dashboard-header">
      <h1>📊 Аналитика и метрики</h1>
      <p>Подробный анализ производительности торговых ботов</p>
    </div>

    <div class="analytics-grid">
      <!-- Performance Metrics -->
      <div class="metrics-section">
        <h2>📈 Производительность</h2>
        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <p>Загрузка метрик...</p>
        </div>
        <div v-else class="metrics-cards">
          <div class="metric-card">
            <div class="metric-icon">📊</div>
            <div class="metric-content">
              <h3>{{ performance.total_trades || 0 }}</h3>
              <p>Всего сделок</p>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-icon">✅</div>
            <div class="metric-content">
              <h3>{{ performance.profitable_trades || 0 }}</h3>
              <p>Прибыльных сделок</p>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-icon">📈</div>
            <div class="metric-content">
              <h3>{{ performance.win_rate || 0 }}%</h3>
              <p>Win Rate</p>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-icon">💰</div>
            <div class="metric-content">
              <h3>${{ performance.avg_profit || 0 }}</h3>
              <p>Средняя прибыль</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Portfolio Overview -->
      <div class="portfolio-section">
        <h2>💼 Портфель</h2>
        <div class="portfolio-card">
          <div class="portfolio-value">
            <h3>${{ portfolio.portfolio_value?.toLocaleString() || '0.00' }}</h3>
            <p>Общая стоимость портфеля</p>
          </div>
          <div class="portfolio-details">
            <div class="detail-item">
              <span class="label">Активы:</span>
              <span class="value">{{ portfolio.assets || 0 }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Прибыль/Убыток:</span>
              <span :class="['value', (portfolio.pnl || 0) >= 0 ? 'positive' : 'negative']">
                {{ (portfolio.pnl || 0) >= 0 ? '+' : '' }}{{ portfolio.pnl || 0 }}%
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Risk Analysis -->
      <div class="risk-section">
        <h2>⚠️ Анализ рисков</h2>
        <div class="risk-card">
          <div class="risk-metrics">
            <div class="risk-item">
              <h4>Max Drawdown</h4>
              <p class="risk-value">{{ risk.max_drawdown || 0 }}%</p>
              <div class="risk-bar">
                <div class="risk-fill" :style="{ width: Math.min((risk.max_drawdown || 0), 100) + '%' }"></div>
              </div>
            </div>
            <div class="risk-item">
              <h4>Sharpe Ratio</h4>
              <p class="risk-value">{{ risk.sharpe_ratio || 0 }}</p>
            </div>
            <div class="risk-item">
              <h4>Volatility</h4>
              <p class="risk-value">{{ risk.volatility || 0 }}%</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Market Data -->
      <div class="market-section">
        <h2>🌍 Рыночные данные</h2>
        <div class="market-card">
          <div class="market-item">
            <h4>{{ market.symbol || 'BTC' }}</h4>
            <p class="price">${{ market.current_price_usd || 0 }}</p>
            <p :class="['change', (market.price_change_percentage_24h || 0) >= 0 ? 'positive' : 'negative']">
              {{ (market.price_change_percentage_24h || 0) >= 0 ? '+' : '' }}{{ market.price_change_percentage_24h || 0 }}%
            </p>
            <p class="sentiment">Sentiment: {{ market.market_sentiment || 'neutral' }}</p>
          </div>
        </div>
      </div>

      <!-- Charts Placeholder -->
      <div class="charts-section">
        <h2>📉 Графики и визуализация</h2>
        <div class="chart-placeholder">
          <div class="chart-icon">📊</div>
          <h3>Графики производительности</h3>
          <p>Визуализация прибыли, убытков и других метрик</p>
          <p class="note">Интеграция с Chart.js или D3.js</p>
        </div>
      </div>

      <!-- Recent Trades -->
      <div class="trades-section">
        <h2>🔄 Недавние сделки</h2>
        <div class="trades-list">
          <div v-for="trade in recentTrades" :key="trade.id" class="trade-item">
            <div class="trade-info">
              <span class="pair">{{ trade.pair }}</span>
              <span :class="['type', trade.type]">{{ trade.type }}</span>
            </div>
            <div class="trade-details">
              <span class="amount">{{ trade.amount }} {{ trade.currency }}</span>
              <span class="profit" :class="trade.profit >= 0 ? 'positive' : 'negative'">
                {{ trade.profit >= 0 ? '+' : '' }}{{ trade.profit }}%
              </span>
            </div>
            <div class="trade-time">
              {{ formatDate(trade.timestamp) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { AnalyticsData, MarketData, Trade } from '@/types/api'

// Reactive data
const performance = ref<Partial<AnalyticsData>>({})
const portfolio = ref<Partial<AnalyticsData>>({})
const risk = ref<Partial<AnalyticsData>>({})
const market = ref<MarketData[]>([])
const recentTrades = ref<Trade[]>([])
const loading = ref(true)

// Methods
const loadData = async () => {
  try {
    loading.value = true

    // Load performance data
    const perfResponse = await fetch('/api/v1/analytics/performance')
    if (perfResponse.ok) {
      const perfData = await perfResponse.json()
      performance.value = perfData.data || {}
    }

    // Load portfolio data
    const portResponse = await fetch('/api/v1/analytics/portfolio')
    if (portResponse.ok) {
      portfolio.value = await portResponse.json()
    }

    // Load risk data
    const riskResponse = await fetch('/api/v1/analytics/risk')
    if (riskResponse.ok) {
      risk.value = await riskResponse.json()
    }

    // Load market data
    const marketResponse = await fetch('/api/v1/analytics/market')
    if (marketResponse.ok) {
      market.value = await marketResponse.json()
    }

    // Mock recent trades
    recentTrades.value = [
      { id: 1, pair: 'BTC/USDT', type: 'buy', amount: 0.001, currency: 'BTC', profit: 2.5, timestamp: new Date() },
      { id: 2, pair: 'ETH/USDT', type: 'sell', amount: 0.5, currency: 'ETH', profit: -1.2, timestamp: new Date(Date.now() - 3600000) },
      { id: 3, pair: 'ADA/USDT', type: 'buy', amount: 100, currency: 'ADA', profit: 5.8, timestamp: new Date(Date.now() - 7200000) }
    ]

  } catch (error) {
    console.error('Error loading analytics data:', error)
  } finally {
    loading.value = false
  }
}

const formatDate = (date: Date) => {
  return date.toLocaleString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
    day: '2-digit',
    month: '2-digit'
  })
}

// Lifecycle
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.analytics-dashboard {
  min-height: 100vh;
  background: #f8f9fa;
  padding: 2rem;
}

.dashboard-header {
  text-align: center;
  margin-bottom: 2rem;
  background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
  color: white;
  padding: 2rem;
  border-radius: 1rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.dashboard-header h1 {
  margin: 0 0 0.5rem 0;
  font-size: 2.5rem;
}

.dashboard-header p {
  margin: 0;
  opacity: 0.9;
  font-size: 1.1rem;
}

.analytics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.metrics-section, .portfolio-section, .risk-section, .market-section, .charts-section, .trades-section {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.metrics-section h2, .portfolio-section h2, .risk-section h2, .market-section h2, .charts-section h2, .trades-section h2 {
  margin: 0 0 1.5rem 0;
  color: #333;
  font-size: 1.5rem;
}

.loading {
  text-align: center;
  padding: 3rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #17a2b8;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.metrics-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.metric-card {
  background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: transform 0.3s;
}

.metric-card:hover {
  transform: translateY(-5px);
}

.metric-icon {
  font-size: 2rem;
  opacity: 0.9;
}

.metric-content h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.8rem;
  font-weight: bold;
}

.metric-content p {
  margin: 0;
  opacity: 0.9;
  font-size: 0.9rem;
}

.portfolio-card {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  padding: 2rem;
  border-radius: 0.75rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 2rem;
}

.portfolio-value h3 {
  margin: 0 0 0.5rem 0;
  font-size: 2.5rem;
  font-weight: bold;
}

.portfolio-value p {
  margin: 0;
  opacity: 0.9;
}

.portfolio-details {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.label {
  font-weight: 500;
  opacity: 0.9;
}

.value {
  font-weight: bold;
}

.value.positive {
  color: #d4edda;
}

.value.negative {
  color: #f8d7da;
}

.risk-card {
  background: linear-gradient(135deg, #ffc107 0%, #e0a800 100%);
  color: #333;
  padding: 2rem;
  border-radius: 0.75rem;
}

.risk-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1.5rem;
}

.risk-item {
  text-align: center;
}

.risk-item h4 {
  margin: 0 0 1rem 0;
  font-size: 1.1rem;
}

.risk-value {
  font-size: 1.8rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.risk-bar {
  width: 100%;
  height: 8px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  overflow: hidden;
}

.risk-fill {
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  transition: width 0.3s;
}

.market-card {
  background: linear-gradient(135deg, #6f42c1 0%, #5a359a 100%);
  color: white;
  padding: 2rem;
  border-radius: 0.75rem;
}

.market-item {
  text-align: center;
}

.market-item h4 {
  margin: 0 0 1rem 0;
  font-size: 1.5rem;
}

.price {
  font-size: 2rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.change {
  font-size: 1.2rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.change.positive {
  color: #d4edda;
}

.change.negative {
  color: #f8d7da;
}

.sentiment {
  font-size: 0.9rem;
  opacity: 0.9;
  margin: 0;
}

.charts-section {
  grid-column: span 2;
}

.chart-placeholder {
  background: #f8f9fa;
  border: 2px dashed #dee2e6;
  border-radius: 0.75rem;
  padding: 3rem;
  text-align: center;
}

.chart-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.chart-placeholder h3 {
  margin: 0 0 1rem 0;
  color: #666;
}

.chart-placeholder p {
  margin: 0.5rem 0;
  color: #999;
}

.note {
  font-style: italic;
  color: #777;
}

.trades-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.trade-item {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  padding: 1rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  transition: box-shadow 0.3s;
}

.trade-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.trade-info {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.pair {
  font-weight: bold;
  color: #333;
}

.type {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.8rem;
  font-weight: bold;
  width: fit-content;
}

.type.buy {
  background: #d4edda;
  color: #155724;
}

.type.sell {
  background: #f8d7da;
  color: #721c24;
}

.trade-details {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  text-align: right;
}

.amount {
  font-weight: 500;
  color: #666;
}

.profit {
  font-weight: bold;
}

.profit.positive {
  color: #28a745;
}

.profit.negative {
  color: #dc3545;
}

.trade-time {
  color: #999;
  font-size: 0.9rem;
}

@media (max-width: 768px) {
  .analytics-grid {
    grid-template-columns: 1fr;
  }

  .charts-section {
    grid-column: span 1;
  }

  .portfolio-card {
    flex-direction: column;
    text-align: center;
    gap: 1rem;
  }

  .portfolio-details {
    align-items: center;
  }

  .risk-metrics {
    grid-template-columns: 1fr;
  }

  .trade-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .trade-details {
    text-align: left;
    flex-direction: row;
    justify-content: space-between;
  }
}
</style>