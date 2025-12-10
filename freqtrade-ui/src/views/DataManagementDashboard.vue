<template>
  <div class="data-management-dashboard">
    <div class="dashboard-header">
      <h1>💾 Управление данными</h1>
      <p>Загрузка и управление историческими данными для бектестинга</p>
    </div>

    <div class="data-grid">
      <!-- Available Data -->
      <div class="available-data-section">
        <h2>📊 Доступные данные</h2>
        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <p>Загрузка списка данных...</p>
        </div>
        <div v-else class="data-table">
          <div class="table-header">
            <div class="col-exchange">Биржа</div>
            <div class="col-pair">Пара</div>
            <div class="col-timeframe">Таймфрейм</div>
            <div class="col-status">Статус</div>
            <div class="col-actions">Действия</div>
          </div>
          <div v-for="data in availableData" :key="`${data.exchange}-${data.pair}-${data.timeframe}`" class="table-row">
            <div class="col-exchange">{{ data.exchange.toUpperCase() }}</div>
            <div class="col-pair">{{ data.pair }}</div>
            <div class="col-timeframe">{{ data.timeframe }}</div>
            <div class="col-status">
              <span :class="['status-badge', data.available ? 'available' : 'unavailable']">
                {{ data.available ? '✅ Доступно' : '❌ Недоступно' }}
              </span>
            </div>
            <div class="col-actions">
              <button
                v-if="data.available"
                class="btn btn-secondary btn-sm"
                @click="downloadData(data)"
                :disabled="downloadLoading[data.pair]"
              >
                {{ downloadLoading[data.pair] ? '⏳' : '📥' }} Скачать
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Download Form -->
      <div class="download-section">
        <h2>⬇️ Загрузка данных</h2>
        <form @submit.prevent="startDownload" class="download-form">
          <div class="form-row">
            <div class="form-group">
              <label for="exchange">Биржа</label>
              <select id="exchange" v-model="downloadForm.exchange" required>
                <option value="">Выберите биржу</option>
                <option value="binance">Binance</option>
                <option value="coinbase">Coinbase</option>
                <option value="kraken">Kraken</option>
                <option value="bybit">Bybit</option>
              </select>
            </div>

            <div class="form-group">
              <label for="pairs">Пары (через запятую)</label>
              <input
                id="pairs"
                v-model="downloadForm.pairs"
                type="text"
                placeholder="BTC/USDT, ETH/USDT"
                required
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="timeframe">Таймфрейм</label>
              <select id="timeframe" v-model="downloadForm.timeframe" required>
                <option value="1m">1 минута</option>
                <option value="5m">5 минут</option>
                <option value="15m">15 минут</option>
                <option value="30m">30 минут</option>
                <option value="1h">1 час</option>
                <option value="2h">2 часа</option>
                <option value="4h">4 часа</option>
                <option value="6h">6 часов</option>
                <option value="8h">8 часов</option>
                <option value="12h">12 часов</option>
                <option value="1d">1 день</option>
                <option value="3d">3 дня</option>
                <option value="1w">1 неделя</option>
              </select>
            </div>

            <div class="form-group">
              <label for="days">Количество дней</label>
              <input
                id="days"
                v-model.number="downloadForm.days"
                type="number"
                min="1"
                max="365"
                placeholder="30"
                required
              />
            </div>
          </div>

          <button type="submit" class="btn btn-primary" :disabled="downloadInProgress">
            <span v-if="downloadInProgress" class="spinner"></span>
            {{ downloadInProgress ? 'Загрузка...' : '🚀 Начать загрузку' }}
          </button>
        </form>
      </div>

      <!-- Download History -->
      <div class="history-section">
        <h2>📋 История загрузок</h2>
        <div v-if="downloadHistory.length === 0" class="empty-state">
          <p>История загрузок пуста</p>
        </div>
        <div v-else class="history-list">
          <div v-for="item in downloadHistory" :key="item.id" class="history-item">
            <div class="history-info">
              <h4>{{ item.pairs.join(', ') }}</h4>
              <p>{{ item.exchange }} • {{ item.timeframe }} • {{ item.days }} дней</p>
            </div>
            <div class="history-status">
              <span :class="['status-badge', item.status]">
                {{ item.status === 'completed' ? '✅' : item.status === 'failed' ? '❌' : '⏳' }} {{ item.status }}
              </span>
            </div>
            <div class="history-time">
              {{ formatDate(item.timestamp) }}
            </div>
          </div>
        </div>
      </div>

      <!-- Storage Info -->
      <div class="storage-section">
        <h2>💽 Хранилище данных</h2>
        <div class="storage-info">
          <div class="storage-metric">
            <h3>{{ storageInfo.used }} GB</h3>
            <p>Использовано</p>
          </div>
          <div class="storage-metric">
            <h3>{{ storageInfo.total }} GB</h3>
            <p>Всего</p>
          </div>
          <div class="storage-metric">
            <h3>{{ storageInfo.free }} GB</h3>
            <p>Свободно</p>
          </div>
        </div>
        <div class="storage-bar">
          <div class="storage-fill" :style="{ width: storageInfo.percentage + '%' }"></div>
        </div>
        <p class="storage-note">Используется {{ storageInfo.percentage }}% дискового пространства</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// Reactive data
const availableData = ref([])
const downloadHistory = ref([])
const downloadLoading = ref({})
const downloadInProgress = ref(false)
const loading = ref(true)

const downloadForm = ref({
  exchange: '',
  pairs: '',
  timeframe: '1h',
  days: 30
})

const storageInfo = ref({
  used: 25,
  total: 100,
  free: 75,
  percentage: 25
})

// Methods
const loadData = async () => {
  try {
    loading.value = true

    // Load available data
    const dataResponse = await fetch('/api/v1/data/')
    if (dataResponse.ok) {
      availableData.value = await dataResponse.json()
    }

    // Mock download history
    downloadHistory.value = [
      {
        id: 1,
        pairs: ['BTC/USDT'],
        exchange: 'binance',
        timeframe: '1h',
        days: 30,
        status: 'completed',
        timestamp: new Date(Date.now() - 3600000)
      },
      {
        id: 2,
        pairs: ['ETH/USDT', 'ADA/USDT'],
        exchange: 'binance',
        timeframe: '5m',
        days: 7,
        status: 'completed',
        timestamp: new Date(Date.now() - 7200000)
      }
    ]

  } catch (error) {
    console.error('Error loading data management info:', error)
  } finally {
    loading.value = false
  }
}

const downloadData = async (data: any) => {
  if (downloadLoading.value[data.pair]) return

  downloadLoading.value[data.pair] = true
  try {
    const response = await fetch('/api/v1/data/download', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        exchange: data.exchange,
        pairs: [data.pair],
        timeframe: data.timeframe,
        days: 30
      })
    })

    if (response.ok) {
      alert(`Загрузка данных для ${data.pair} начата`)
    } else {
      alert('Ошибка запуска загрузки')
    }
  } catch (error) {
    console.error('Error downloading data:', error)
    alert('Ошибка загрузки данных')
  } finally {
    downloadLoading.value[data.pair] = false
  }
}

const startDownload = async () => {
  if (!downloadForm.value.exchange || !downloadForm.value.pairs) {
    alert('Заполните все поля')
    return
  }

  downloadInProgress.value = true
  try {
    const pairs = downloadForm.value.pairs.split(',').map(p => p.trim()).filter(p => p)

    const response = await fetch('/api/v1/data/download', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        exchange: downloadForm.value.exchange,
        pairs: pairs,
        timeframe: downloadForm.value.timeframe,
        days: downloadForm.value.days
      })
    })

    if (response.ok) {
      // Add to history
      downloadHistory.value.unshift({
        id: Date.now(),
        pairs: pairs,
        exchange: downloadForm.value.exchange,
        timeframe: downloadForm.value.timeframe,
        days: downloadForm.value.days,
        status: 'in_progress',
        timestamp: new Date()
      })

      // Simulate completion
      setTimeout(() => {
        const item = downloadHistory.value.find(h => h.pairs.includes(pairs[0]))
        if (item) {
          item.status = 'completed'
        }
      }, 5000)

      alert('Загрузка данных начата')
      downloadForm.value = {
        exchange: '',
        pairs: '',
        timeframe: '1h',
        days: 30
      }
    } else {
      alert('Ошибка запуска загрузки')
    }
  } catch (error) {
    console.error('Error starting download:', error)
    alert('Ошибка запуска загрузки')
  } finally {
    downloadInProgress.value = false
  }
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
.data-management-dashboard {
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

.data-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.available-data-section, .download-section, .history-section, .storage-section {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.available-data-section h2, .download-section h2, .history-section h2, .storage-section h2 {
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
  border-top: 4px solid #9c27b0;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.data-table {
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 1fr 1fr 100px 120px 100px;
  gap: 1rem;
  background: #f8f9fa;
  padding: 1rem;
  font-weight: bold;
  color: #333;
  border-bottom: 1px solid #e0e0e0;
}

.table-row {
  display: grid;
  grid-template-columns: 1fr 1fr 100px 120px 100px;
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

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.8rem;
  font-weight: bold;
  text-align: center;
}

.status-badge.available {
  background: #d4edda;
  color: #155724;
}

.status-badge.unavailable {
  background: #f8d7da;
  color: #721c24;
}

.download-form {
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

.history-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  padding: 1rem;
  transition: box-shadow 0.3s;
}

.history-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.history-info h4 {
  margin: 0 0 0.25rem 0;
  color: #333;
}

.history-info p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.history-status {
  flex-shrink: 0;
}

.history-time {
  color: #999;
  font-size: 0.9rem;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.storage-info {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
}

.storage-metric {
  text-align: center;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 0.5rem;
}

.storage-metric h3 {
  margin: 0 0 0.5rem 0;
  color: #333;
  font-size: 1.5rem;
}

.storage-metric p {
  margin: 0;
  color: #666;
}

.storage-bar {
  width: 100%;
  height: 20px;
  background: #e0e0e0;
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.storage-fill {
  height: 100%;
  background: linear-gradient(90deg, #28a745 0%, #ffc107 50%, #dc3545 100%);
  transition: width 0.3s;
}

.storage-note {
  text-align: center;
  color: #666;
  font-size: 0.9rem;
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

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

@media (max-width: 768px) {
  .data-grid {
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

  .storage-info {
    grid-template-columns: 1fr;
  }

  .history-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }
}
</style>