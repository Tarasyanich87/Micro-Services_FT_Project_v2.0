<template>
  <div class="hyperopt-dashboard">
    <div class="dashboard-header">
      <h1>⚙️ Hyperopt</h1>
      <p>Оптимизация параметров торговых стратегий</p>
    </div>

    <div class="hyperopt-grid">
      <!-- Available Strategies -->
      <div class="strategies-section">
        <h2>📋 Доступные стратегии</h2>
        <div class="strategies-list">
          <div v-for="strategy in strategies" :key="strategy" class="strategy-item">
            <div class="strategy-info">
              <h3>{{ strategy }}</h3>
              <p>Готова к оптимизации</p>
            </div>
            <button class="btn btn-primary" @click="startHyperopt(strategy)">
              🚀 Оптимизировать
            </button>
          </div>
        </div>
      </div>

      <!-- Running Optimizations -->
      <div class="running-section">
        <h2>🔄 Активные оптимизации</h2>
        <div v-if="runningOptimizations.length === 0" class="empty-state">
          <p>Нет запущенных оптимизаций</p>
        </div>
        <div v-else class="optimizations-list">
          <div v-for="opt in runningOptimizations" :key="opt.id" class="optimization-card">
            <div class="opt-header">
              <h4>{{ opt.strategy }}</h4>
              <span class="progress-text">{{ opt.progress }}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: opt.progress + '%' }"></div>
            </div>
            <div class="opt-details">
              <span>Эпохи: {{ opt.currentEpoch }}/{{ opt.totalEpochs }}</span>
              <span>Лучший результат: {{ opt.bestLoss }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Optimization Results -->
      <div class="results-section">
        <h2>📊 Результаты оптимизации</h2>
        <div v-if="optimizationResults.length === 0" class="empty-state">
          <p>Нет завершенных оптимизаций</p>
        </div>
        <div v-else class="results-table">
          <div class="table-header">
            <div class="col-strategy">Стратегия</div>
            <div class="col-loss">Loss</div>
            <div class="col-profit">Прибыль</div>
            <div class="col-drawdown">Drawdown</div>
            <div class="col-trades">Сделки</div>
            <div class="col-actions">Действия</div>
          </div>
          <div v-for="result in optimizationResults" :key="result.id" class="table-row">
            <div class="col-strategy">{{ result.strategy }}</div>
            <div class="col-loss">{{ result.loss }}</div>
            <div class="col-profit">{{ result.totalProfit }}%</div>
            <div class="col-drawdown">{{ result.maxDrawdown }}%</div>
            <div class="col-trades">{{ result.totalTrades }}</div>
            <div class="col-actions">
              <button class="btn btn-secondary btn-sm" @click="viewDetails(result)">
                👁️ Детали
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Optimization Config -->
      <div class="config-section">
        <h2>⚙️ Настройки оптимизации</h2>
        <form @submit.prevent="updateConfig" class="config-form">
          <div class="form-row">
            <div class="form-group">
              <label for="epochs">Количество эпох</label>
              <input
                id="epochs"
                v-model.number="config.epochs"
                type="number"
                min="10"
                max="1000"
                step="10"
              />
            </div>

            <div class="form-group">
              <label for="spaces">Пространства оптимизации</label>
              <select id="spaces" v-model="config.spaces" multiple>
                <option value="buy">Buy space</option>
                <option value="sell">Sell space</option>
                <option value="roi">ROI space</option>
                <option value="stoploss">Stoploss space</option>
              </select>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="method">Метод оптимизации</label>
              <select id="method" v-model="config.method">
                <option value="tpe">TPE (Tree-structured Parzen Estimator)</option>
                <option value="random">Random Search</option>
                <option value="grid">Grid Search</option>
              </select>
            </div>

            <div class="form-group">
              <label for="parallel">Параллельные процессы</label>
              <input
                id="parallel"
                v-model.number="config.parallel"
                type="number"
                min="1"
                max="8"
              />
            </div>
          </div>

          <button type="submit" class="btn btn-primary">
            💾 Сохранить настройки
          </button>
        </form>
      </div>
    </div>

    <!-- Optimization Details Modal -->
    <div v-if="selectedResult" class="modal-overlay" @click="closeDetails">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>Детали оптимизации: {{ selectedResult.strategy }}</h2>
          <button class="close-btn" @click="closeDetails">✕</button>
        </div>

        <div class="optimization-details">
          <div class="detail-section">
            <h3>📈 Метрики производительности</h3>
            <div class="metrics-grid">
              <div class="metric-card">
                <h4>Total Profit</h4>
                <p class="metric-value">{{ selectedResult.totalProfit }}%</p>
              </div>
              <div class="metric-card">
                <h4>Max Drawdown</h4>
                <p class="metric-value">{{ selectedResult.maxDrawdown }}%</p>
              </div>
              <div class="metric-card">
                <h4>Win Rate</h4>
                <p class="metric-value">{{ selectedResult.winRate }}%</p>
              </div>
              <div class="metric-card">
                <h4>Total Trades</h4>
                <p class="metric-value">{{ selectedResult.totalTrades }}</p>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <h3>⚙️ Оптимальные параметры</h3>
            <div class="parameters-list">
              <div v-for="(value, param) in selectedResult.parameters" :key="param" class="parameter-item">
                <span class="param-name">{{ param }}:</span>
                <span class="param-value">{{ value }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// Reactive data
const strategies = ref([])
const runningOptimizations = ref([])
const optimizationResults = ref([])
const selectedResult = ref(null)

const config = ref({
  epochs: 100,
  spaces: ['buy', 'sell'],
  method: 'tpe',
  parallel: 1
})

// Methods
const loadData = async () => {
  // Load strategies
  const strategiesResponse = await fetch('/api/v1/strategies/')
  if (strategiesResponse.ok) {
    strategies.value = await strategiesResponse.json()
  }

  // Load hyperopt results
  const resultsResponse = await fetch('/api/v1/hyperopt/results')
  if (resultsResponse.ok) {
    optimizationResults.value = await resultsResponse.json()
  }

  // Mock running optimizations
  runningOptimizations.value = [
    {
      id: 1,
      strategy: 'SampleStrategy',
      progress: 45,
      currentEpoch: 45,
      totalEpochs: 100,
      bestLoss: -0.123
    }
  ]

  // Mock results if empty
  if (optimizationResults.value.length === 0) {
    optimizationResults.value = [
      {
        id: 1,
        strategy: 'SampleStrategy',
        loss: -0.123,
        totalProfit: 15.7,
        maxDrawdown: 8.2,
        winRate: 62,
        totalTrades: 245,
        parameters: {
          'buy_rsi': 32,
          'sell_rsi': 68,
          'stoploss': -0.08,
          'roi_t1': 0.05,
          'roi_t2': 0.02,
          'roi_t3': 0.01
        }
      },
      {
        id: 2,
        strategy: 'AnotherStrategy',
        loss: -0.089,
        totalProfit: 22.3,
        maxDrawdown: 12.1,
        winRate: 58,
        totalTrades: 189,
        parameters: {
          'buy_rsi': 28,
          'sell_rsi': 72,
          'stoploss': -0.12,
          'roi_t1': 0.08,
          'roi_t2': 0.03,
          'roi_t3': 0.015
        }
      }
    ]
  }
}

const startHyperopt = async (strategyName: string) => {
  try {
    const response = await fetch('/api/v1/hyperopt/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        strategy_name: strategyName,
        epochs: config.value.epochs,
        spaces: config.value.spaces,
        method: config.value.method
      })
    })

    if (response.ok) {
      const result = await response.json()
      runningOptimizations.value.push({
        id: Date.now(),
        strategy: strategyName,
        progress: 0,
        currentEpoch: 0,
        totalEpochs: config.value.epochs,
        bestLoss: 0
      })

      // Simulate progress
      simulateProgress(result.id)
    } else {
      alert('Ошибка запуска оптимизации')
    }
  } catch (error) {
    console.error('Error starting hyperopt:', error)
    alert('Ошибка запуска оптимизации')
  }
}

const simulateProgress = (optId: number) => {
  const interval = setInterval(() => {
    const opt = runningOptimizations.value.find(o => o.id === optId)
    if (opt) {
      opt.progress += Math.random() * 5
      opt.currentEpoch = Math.floor((opt.progress / 100) * opt.totalEpochs)
      opt.bestLoss = -(Math.random() * 0.2)

      if (opt.progress >= 100) {
        clearInterval(interval)
        // Move to results
        optimizationResults.value.unshift({
          id: Date.now(),
          strategy: opt.strategy,
          loss: opt.bestLoss,
          totalProfit: Math.random() * 30,
          maxDrawdown: Math.random() * 15,
          winRate: 50 + Math.random() * 20,
          totalTrades: Math.floor(Math.random() * 200) + 100,
          parameters: {
            'buy_rsi': Math.floor(Math.random() * 20) + 25,
            'sell_rsi': Math.floor(Math.random() * 20) + 65,
            'stoploss': -(Math.random() * 0.1 + 0.05)
          }
        })
        runningOptimizations.value = runningOptimizations.value.filter(o => o.id !== optId)
      }
    } else {
      clearInterval(interval)
    }
  }, 1000)
}

const viewDetails = (result: any) => {
  selectedResult.value = result
}

const closeDetails = () => {
  selectedResult.value = null
}

const updateConfig = () => {
  alert('Настройки сохранены!')
}

// Lifecycle
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.hyperopt-dashboard {
  min-height: 100vh;
  background: #f8f9fa;
  padding: 2rem;
}

.dashboard-header {
  text-align: center;
  margin-bottom: 2rem;
  background: linear-gradient(135deg, #9c27b0 0%, #ba68c8 100%);
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

.hyperopt-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.strategies-section, .running-section, .results-section, .config-section {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.strategies-section h2, .running-section h2, .results-section h2, .config-section h2 {
  margin: 0 0 1.5rem 0;
  color: #333;
  font-size: 1.5rem;
}

.strategies-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.strategy-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  padding: 1rem;
  transition: box-shadow 0.3s;
}

.strategy-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.strategy-info h3 {
  margin: 0 0 0.25rem 0;
  color: #333;
}

.strategy-info p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.optimizations-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.optimization-card {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  padding: 1rem;
}

.opt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.opt-header h4 {
  margin: 0;
  color: #333;
}

.progress-text {
  font-weight: bold;
  color: #007bff;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #28a745 0%, #007bff 100%);
  transition: width 0.3s;
}

.opt-details {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  color: #666;
}

.results-table {
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr;
  gap: 1rem;
  background: #f8f9fa;
  padding: 1rem;
  font-weight: bold;
  color: #333;
  border-bottom: 1px solid #e0e0e0;
}

.table-row {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr 1fr 1fr 1fr;
  gap: 1rem;
  padding: 1rem;
  border-bottom: 1px solid #f0f0f0;
  align-items: center;
  transition: background-color 0.3s;
}

.table-row:hover {
  background: #f8f9fa;
}

.table-row:last-child {
  border-bottom: none;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group select {
  padding: 0.75rem;
  border: 2px solid #e0e0e0;
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #9c27b0;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 2rem;
}

.modal-content {
  background: white;
  border-radius: 1rem;
  width: 100%;
  max-width: 800px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.2);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid #e0e0e0;
}

.modal-header h2 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #666;
  padding: 0.25rem;
  border-radius: 0.25rem;
  transition: all 0.3s;
}

.close-btn:hover {
  background: #f0f0f0;
  color: #333;
}

.optimization-details {
  padding: 1.5rem;
}

.detail-section {
  margin-bottom: 2rem;
}

.detail-section h3 {
  margin: 0 0 1rem 0;
  color: #333;
  font-size: 1.25rem;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.metric-card {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  padding: 1rem;
  text-align: center;
}

.metric-card h4 {
  margin: 0 0 0.5rem 0;
  color: #666;
  font-size: 0.9rem;
}

.metric-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #333;
  margin: 0;
}

.parameters-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.parameter-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 0.25rem;
  padding: 0.75rem;
}

.param-name {
  font-weight: 500;
  color: #333;
}

.param-value {
  font-weight: bold;
  color: #007bff;
}

.btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.9rem;
}

.btn:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .hyperopt-grid {
    grid-template-columns: 1fr;
  }

  .table-header,
  .table-row {
    grid-template-columns: 1fr;
    gap: 0.5rem;
  }

  .table-header {
    display: none;
  }

  .table-row {
    border: 1px solid #e0e0e0;
    border-radius: 0.5rem;
    margin-bottom: 1rem;
    padding: 1rem;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .metrics-grid {
    grid-template-columns: 1fr;
  }

  .parameters-list {
    grid-template-columns: 1fr;
  }

  .strategy-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .opt-details {
    flex-direction: column;
    gap: 0.5rem;
  }

  .modal-overlay {
    padding: 1rem;
  }

  .modal-content {
    max-height: 95vh;
  }
}
</style>