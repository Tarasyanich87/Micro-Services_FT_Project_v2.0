<template>
  <div class="strategies-dashboard">
    <div class="dashboard-header">
      <h1>📈 Управление стратегиями</h1>
      <p>Создание, загрузка и тестирование торговых стратегий</p>
    </div>

    <div class="dashboard-actions">
      <button class="btn btn-primary" @click="showCreateDialog = true">
        ➕ Создать стратегию
      </button>
      <label class="btn btn-secondary">
        📤 Загрузить .md файл
        <input
          type="file"
          accept=".md"
          @change="handleFileUpload"
          style="display: none"
        />
      </label>
    </div>

    <div class="strategies-section">
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Загрузка стратегий...</p>
      </div>

      <div v-else-if="strategies.length === 0" class="empty-state">
        <h3>Нет доступных стратегий</h3>
        <p>Создайте свою первую стратегию или загрузите существующую</p>
        <div class="empty-actions">
          <button class="btn btn-primary" @click="showCreateDialog = true">
            🚀 Создать стратегию
          </button>
          <label class="btn btn-secondary">
            📤 Загрузить файл
            <input
              type="file"
              accept=".md"
              @change="handleFileUpload"
              style="display: none"
            />
          </label>
        </div>
      </div>

      <div v-else class="strategies-grid">
        <div v-for="strategy in strategies" :key="strategy" class="strategy-card">
          <div class="strategy-header">
            <h3>{{ strategy }}</h3>
            <div class="strategy-actions">
              <button class="btn btn-info btn-sm" @click="runBacktest(strategy)">
                🧪 Бектест
              </button>
              <button class="btn btn-secondary btn-sm" @click="editStrategy(strategy)">
                ✏️ Edit
              </button>
              <button class="btn btn-danger btn-sm" @click="deleteStrategy(strategy)">
                🗑️ Delete
              </button>
            </div>
          </div>

          <div class="strategy-details">
            <div class="detail-item">
              <span class="label">Тип:</span>
              <span class="value">Momentum Strategy</span>
            </div>
            <div class="detail-item">
              <span class="label">Время создания:</span>
              <span class="value">{{ formatDate(new Date()) }}</span>
            </div>
            <div class="detail-item">
              <span class="label">Статус:</span>
              <span class="value status-active">Активна</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Backtest Results Section -->
    <div v-if="backtestResults.length > 0" class="backtest-section">
      <h2>📊 Результаты бектестинга</h2>
      <div class="backtest-results">
        <div v-for="result in backtestResults" :key="result.id" class="backtest-card">
          <div class="backtest-header">
            <h4>{{ result.strategy }}</h4>
            <span :class="['status-badge', result.status]">
              {{ result.status === 'completed' ? '✅' : '⏳' }} {{ result.status }}
            </span>
          </div>

          <div v-if="result.status === 'completed'" class="backtest-metrics">
            <div class="metric">
              <span class="label">Total Trades:</span>
              <span class="value">{{ result.total_trades || 0 }}</span>
            </div>
            <div class="metric">
              <span class="label">Win Rate:</span>
              <span class="value">{{ result.win_rate || 0 }}%</span>
            </div>
            <div class="metric">
              <span class="label">Profit:</span>
              <span class="value">{{ result.profit || 0 }}%</span>
            </div>
            <div class="metric">
              <span class="label">Max Drawdown:</span>
              <span class="value">{{ result.max_drawdown || 0 }}%</span>
            </div>
          </div>

          <div v-else class="backtest-loading">
            <div class="spinner"></div>
            <p>Выполняется бектестирование...</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Strategy Dialog -->
    <div v-if="showCreateDialog" class="modal-overlay" @click="closeDialog">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>🚀 Создать стратегию</h2>
          <button class="close-btn" @click="closeDialog">✕</button>
        </div>

        <form @submit.prevent="createStrategy" class="strategy-form">
          <div class="form-group">
            <label for="strategy-name">Имя стратегии *</label>
            <input
              id="strategy-name"
              v-model="newStrategyName"
              type="text"
              required
              placeholder="Например: MyAwesomeStrategy"
            />
          </div>

           <div class="form-group">
             <label for="strategyCode">Код стратегии:</label>
             <CodeEditor
               v-model="strategyCode"
               placeholder="Введите код стратегии..."
             />
           </div>

          <div class="form-actions">
            <button type="button" class="btn btn-secondary" @click="closeDialog">
              Отмена
            </button>
            <button type="submit" class="btn btn-primary" :disabled="createLoading">
              <span v-if="createLoading" class="spinner"></span>
              {{ createLoading ? 'Создание...' : '🚀 Создать' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import CodeEditor from '@/components/CodeEditor.vue'

// Reactive data
const strategies = ref([])
const backtestResults = ref([])
const loading = ref(true)
const createLoading = ref(false)

// Dialog states
const showCreateDialog = ref(false)

// Form data
const newStrategyName = ref('')
const strategyCode = ref(`from freqtrade.strategy import IStrategy
from typing import Dict, List
import numpy as np
import pandas as pd
from freqtrade.strategy import DecimalParameter, IntParameter

class ${newStrategyName.value || 'MyStrategy'}(IStrategy):
    """
    Custom strategy implementation
    """

    # Strategy metadata
    INTERFACE_VERSION = 3
    minimal_roi = {"0": 0.10, "15": 0.05, "240": 0, "1440": -0.05}
    stoploss = -0.10
    timeframe = '5m'

    # Strategy parameters
    buy_rsi = IntParameter(10, 40, default=30, space='buy')
    sell_rsi = IntParameter(60, 90, default=70, space='sell')

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        # Add RSI indicator
        dataframe['rsi'] = ta.RSI(dataframe)
        return dataframe

    def populate_buy_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[
            (
                (dataframe['rsi'] < self.buy_rsi.value) &
                (dataframe['volume'] > 0)
            ),
            'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[
            (
                (dataframe['rsi'] > self.sell_rsi.value)
            ),
            'sell'] = 1
        return dataframe`)

// Components
// CodeEditor is imported above

// Methods
const loadData = async () => {
  try {
    loading.value = true

    // Load strategies
    const strategiesResponse = await fetch('/api/v1/strategies/')
    if (strategiesResponse.ok) {
      strategies.value = await strategiesResponse.json()
    }

    // Load backtest results
    const backtestResponse = await fetch('/api/v1/hyperopt/results')
    if (backtestResponse.ok) {
      backtestResults.value = await backtestResponse.json()
    }

  } catch (error) {
    console.error('Error loading strategies data:', error)
  } finally {
    loading.value = false
  }
}

const handleFileUpload = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return

  const formData = new FormData()
  formData.append('file', file)

  try {
    const response = await fetch('/api/v1/strategies/upload_md', {
      method: 'POST',
      body: formData
    })

    if (response.ok) {
      await loadData() // Reload strategies
      alert('Стратегия успешно загружена!')
    } else {
      alert('Ошибка загрузки стратегии')
    }
  } catch (error) {
    console.error('Error uploading strategy:', error)
    alert('Ошибка загрузки файла')
  }

  // Reset input
  ;(event.target as HTMLInputElement).value = ''
}

const runBacktest = async (strategyName: string) => {
  try {
    const response = await fetch('/api/v1/strategies/backtest', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        strategy_name: strategyName,
        timeframe: '5m',
        timerange: '20240101-20241201'
      })
    })

    if (response.ok) {
      const result = await response.json()
      backtestResults.value.unshift({
        id: Date.now(),
        strategy: strategyName,
        status: 'running',
        ...result
      })

      // Simulate completion after 3 seconds
      setTimeout(() => {
        const index = backtestResults.value.findIndex(r => r.strategy === strategyName && r.status === 'running')
        if (index !== -1) {
          backtestResults.value[index] = {
            ...backtestResults.value[index],
            status: 'completed',
            total_trades: Math.floor(Math.random() * 100) + 50,
            win_rate: Math.floor(Math.random() * 30) + 50,
            profit: (Math.random() * 20 - 5).toFixed(2),
            max_drawdown: (Math.random() * 15).toFixed(2)
          }
        }
      }, 3000)
    } else {
      alert('Ошибка запуска бектеста')
    }
  } catch (error) {
    console.error('Error running backtest:', error)
    alert('Ошибка запуска бектестинга')
  }
}

const editStrategy = (strategyName: string) => {
  // For now, just show alert
  alert(`Редактирование стратегии ${strategyName} (функционал в разработке)`)
}

const deleteStrategy = async (strategyName: string) => {
  if (!confirm(`Удалить стратегию "${strategyName}"?`)) return

  try {
    const response = await fetch(`/api/v1/strategies/${strategyName}`, {
      method: 'DELETE'
    })

    if (response.ok) {
      await loadData() // Reload strategies
    } else {
      alert('Ошибка удаления стратегии')
    }
  } catch (error) {
    console.error('Error deleting strategy:', error)
    alert('Ошибка удаления стратегии')
  }
}

const createStrategy = async () => {
  if (!newStrategyName.value.trim()) {
    alert('Введите имя стратегии')
    return
  }

  createLoading.value = true
  try {
    const response = await fetch('/api/v1/strategies/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        name: newStrategyName.value,
        code: strategyCode.value
      })
    })

    if (response.ok) {
      closeDialog()
      await loadData() // Reload strategies
    } else {
      alert('Ошибка создания стратегии')
    }
  } catch (error) {
    console.error('Error creating strategy:', error)
    alert('Ошибка создания стратегии')
  } finally {
    createLoading.value = false
  }
}

const closeDialog = () => {
  showCreateDialog.value = false
  newStrategyName.value = ''
  strategyCode.value = `from freqtrade.strategy import IStrategy
from typing import Dict, List
import numpy as np
import pandas as pd
from freqtrade.strategy import DecimalParameter, IntParameter

class \${newStrategyName.value || 'MyStrategy'}(IStrategy):
    """
    Custom strategy implementation
    """

    # Strategy metadata
    INTERFACE_VERSION = 3
    minimal_roi = {"0": 0.10, "15": 0.05, "240": 0, "1440": -0.05}
    stoploss = -0.10
    timeframe = '5m'

    # Strategy parameters
    buy_rsi = IntParameter(10, 40, default=30, space='buy')
    sell_rsi = IntParameter(60, 90, default=70, space='sell')

    def populate_indicators(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        # Add RSI indicator
        dataframe['rsi'] = ta.RSI(dataframe)
        return dataframe

    def populate_buy_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[
            (
                (dataframe['rsi'] < self.buy_rsi.value) &
                (dataframe['volume'] > 0)
            ),
            'buy'] = 1
        return dataframe

    def populate_sell_trend(self, dataframe: pd.DataFrame, metadata: dict) -> pd.DataFrame:
        dataframe.loc[
            (
                (dataframe['rsi'] > self.sell_rsi.value)
            ),
            'sell'] = 1
        return dataframe`
}

const formatDate = (date: Date) => {
  return date.toLocaleString('ru-RU')
}

// Lifecycle
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.strategies-dashboard {
  min-height: 100vh;
  background: #f8f9fa;
  padding: 2rem;
}

.dashboard-header {
  text-align: center;
  margin-bottom: 2rem;
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
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

.dashboard-actions {
  display: flex;
  gap: 1rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.strategies-section, .backtest-section {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  margin-bottom: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.strategies-section h2, .backtest-section h2 {
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
  border-top: 4px solid #28a745;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.empty-state h3 {
  margin: 0 0 1rem 0;
  color: #333;
}

.empty-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  margin-top: 2rem;
  flex-wrap: wrap;
}

.strategies-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.strategy-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 0.75rem;
  padding: 1.5rem;
  transition: all 0.3s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.strategy-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
  gap: 1rem;
}

.strategy-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.25rem;
  flex: 1;
}

.strategy-actions {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;
}

.strategy-details {
  margin-bottom: 1rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #f0f0f0;
}

.detail-item:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.label {
  font-weight: 500;
  color: #666;
}

.value {
  color: #333;
}

.status-active {
  color: #28a745;
  font-weight: 500;
}

.backtest-results {
  display: grid;
  gap: 1rem;
}

.backtest-card {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  padding: 1.5rem;
}

.backtest-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.backtest-header h4 {
  margin: 0;
  color: #333;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.8rem;
  font-weight: bold;
}

.status-badge.completed {
  background: #d4edda;
  color: #155724;
}

.status-badge.running {
  background: #fff3cd;
  color: #856404;
}

.backtest-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.metric {
  text-align: center;
}

.metric .label {
  display: block;
  font-size: 0.9rem;
  color: #666;
  margin-bottom: 0.25rem;
}

.metric .value {
  font-size: 1.2rem;
  font-weight: bold;
  color: #333;
}

.backtest-loading {
  text-align: center;
  padding: 2rem;
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

.strategy-form {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
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
.form-group textarea {
  padding: 0.75rem;
  border: 2px solid #e0e0e0;
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.form-group input:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #28a745;
}

.form-group textarea {
  resize: vertical;
  min-height: 300px;
  font-family: 'Courier New', monospace;
  font-size: 0.9rem;
}

.form-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
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

.btn-info {
  background: #17a2b8;
  color: white;
}

.btn-danger {
  background: #dc3545;
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

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

@media (max-width: 768px) {
  .dashboard-actions {
    flex-direction: column;
  }

  .strategies-grid {
    grid-template-columns: 1fr;
  }

  .strategy-header {
    flex-direction: column;
    align-items: stretch;
  }

  .strategy-actions {
    justify-content: center;
  }

  .modal-overlay {
    padding: 1rem;
  }

  .modal-content {
    max-height: 95vh;
  }

  .backtest-metrics {
    grid-template-columns: 1fr;
  }
}
</style>