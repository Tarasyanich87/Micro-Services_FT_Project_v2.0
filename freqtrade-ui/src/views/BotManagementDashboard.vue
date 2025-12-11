<template>
  <div class="bot-management-dashboard">
    <div class="dashboard-header">
      <h1>🤖 Управление ботами</h1>
      <p>Создание, настройка и мониторинг торговых ботов</p>
    </div>

    <div class="dashboard-actions">
      <button class="btn btn-primary" @click="showCreateDialog = true">
        ➕ Создать бота
      </button>
      <button class="btn btn-success" @click="startAllBots" :disabled="bulkActionLoading">
        ▶️ Запустить все
      </button>
      <button class="btn btn-danger" @click="stopAllBots" :disabled="bulkActionLoading">
        ⏹️ Остановить все
      </button>
    </div>

    <div class="bots-section">
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Загрузка ботов...</p>
      </div>

      <div v-else-if="bots.length === 0" class="empty-state">
        <h3>Нет созданных ботов</h3>
        <p>Создайте своего первого торгового бота</p>
        <button class="btn btn-primary" @click="showCreateDialog = true">
          🚀 Создать бота
        </button>
      </div>

      <div v-else class="bots-grid">
        <div v-for="bot in bots" :key="bot.id" class="bot-card">
          <div class="bot-header">
            <h3>{{ bot.name }}</h3>
            <span :class="['status-badge', bot.status]">
              {{ bot.status === 'running' ? '🟢' : '🔴' }} {{ bot.status }}
            </span>
          </div>

          <div class="bot-details">
            <div class="detail-row">
              <span class="label">Стратегия:</span>
              <span class="value">{{ bot.strategy_name }}</span>
            </div>
            <div class="detail-row">
              <span class="label">Биржа:</span>
              <span class="value">{{ bot.exchange || 'Не указана' }}</span>
            </div>
            <div class="detail-row">
              <span class="label">Stake Amount:</span>
              <span class="value">{{ bot.stake_amount || 0 }} USDT</span>
            </div>
            <div class="detail-row">
              <span class="label">Max Open Trades:</span>
              <span class="value">{{ bot.max_open_trades || 0 }}</span>
            </div>
          </div>

          <div class="bot-actions">
            <button
              class="btn btn-sm"
              :class="bot.status === 'running' ? 'btn-warning' : 'btn-success'"
              @click="toggleBot(bot)"
              :disabled="actionLoading[bot.id]"
            >
              {{ actionLoading[bot.id] ? '...' : (bot.status === 'running' ? '⏹️ Stop' : '▶️ Start') }}
            </button>
            <button class="btn btn-secondary btn-sm" @click="editBot(bot)">
              ✏️ Edit
            </button>
            <button class="btn btn-danger btn-sm" @click="deleteBot(bot)">
              🗑️ Delete
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Bot Dialog -->
    <div v-if="showCreateDialog || showEditDialog" class="modal-overlay" @click="closeDialog">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>{{ showEditDialog ? '✏️ Редактировать бота' : '➕ Создать бота' }}</h2>
          <button class="close-btn" @click="closeDialog">✕</button>
        </div>

        <form @submit.prevent="saveBot" class="bot-form">
          <div class="form-row">
            <div class="form-group">
              <label for="bot-name">Имя бота *</label>
              <input
                id="bot-name"
                v-model="botForm.name"
                type="text"
                required
                placeholder="Например: BTC_Bot_1"
              />
            </div>

            <div class="form-group">
              <label for="bot-strategy">Стратегия *</label>
              <select id="bot-strategy" v-model="botForm.strategy_name" required>
                <option value="">Выберите стратегию</option>
                <option v-for="strategy in strategies" :key="strategy" :value="strategy">
                  {{ strategy }}
                </option>
              </select>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="bot-exchange">Биржа</label>
              <select id="bot-exchange" v-model="botForm.exchange">
                <option value="">Выберите биржу</option>
                <option value="binance">Binance</option>
                <option value="coinbase">Coinbase</option>
                <option value="kraken">Kraken</option>
              </select>
            </div>

            <div class="form-group">
              <label for="bot-stake-amount">Stake Amount (USDT)</label>
              <input
                id="bot-stake-amount"
                v-model.number="botForm.stake_amount"
                type="number"
                min="1"
                step="0.01"
                placeholder="100"
              />
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="bot-max-trades">Max Open Trades</label>
              <input
                id="bot-max-trades"
                v-model.number="botForm.max_open_trades"
                type="number"
                min="1"
                max="10"
                placeholder="5"
              />
            </div>

            <div class="form-group">
              <label for="bot-freqai-model">FreqAI Model</label>
              <select id="bot-freqai-model" v-model="botForm.freqai_model_id">
                <option value="">Без FreqAI</option>
                <option v-for="model in freqaiModels" :key="model.id" :value="model.id">
                  {{ model.name }}
                </option>
              </select>
            </div>
          </div>

          <div class="form-group">
            <label for="bot-config">JSON Конфигурация</label>
            <textarea
              id="bot-config"
              v-model="botForm.config"
              rows="6"
              placeholder='{"timeframe": "5m", "pair_whitelist": ["BTC/USDT"]}'
            ></textarea>
          </div>

          <div class="form-actions">
            <button type="button" class="btn btn-secondary" @click="closeDialog">
              Отмена
            </button>
            <button type="submit" class="btn btn-primary" :disabled="saveLoading">
              <span v-if="saveLoading" class="spinner"></span>
              {{ saveLoading ? 'Сохранение...' : (showEditDialog ? '💾 Сохранить' : '🚀 Создать') }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// Reactive data
const bots = ref<any[]>([])
const strategies = ref<string[]>([])
const freqaiModels = ref<any[]>([])
const loading = ref(true)
const bulkActionLoading = ref(false)
const saveLoading = ref(false)

// Dialog states
const showCreateDialog = ref(false)
const showEditDialog = ref(false)

// Form data
const botForm = ref({
  id: null as number | null,
  name: '',
  strategy_name: '',
  exchange: '',
  stake_amount: 100,
  max_open_trades: 5,
  config: '{"timeframe": "5m", "pair_whitelist": ["BTC/USDT"]}',
  freqai_model_id: null as number | null
})

// Methods
const loadData = async () => {
  try {
    loading.value = true

    // Load bots
    const botsResponse = await fetch('/api/v1/bots/')
    if (botsResponse.ok) {
      bots.value = await botsResponse.json()
    }

    // Load strategies
    const strategiesResponse = await fetch('/api/v1/strategies/')
    if (strategiesResponse.ok) {
      const strategiesData = await strategiesResponse.json()
      strategies.value = strategiesData.map((s: any) => s.name)
    }

    // Load FreqAI models
    const modelsResponse = await fetch('/api/v1/freqai/models')
    if (modelsResponse.ok) {
      freqaiModels.value = await modelsResponse.json()
    }

  } catch (error) {
    console.error('Error loading bot management data:', error)
  } finally {
    loading.value = false
  }
}

const toggleBot = async (bot: any) => {
  const actionLoading = ref<Record<number, boolean>>({})
  if (actionLoading.value[bot.id]) return

  actionLoading.value[bot.id] = true
  try {
    const endpoint = bot.status === 'running' ? 'stop' : 'start'
    const response = await fetch(`/api/v1/bots/${bot.id}/${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      bot.status = bot.status === 'running' ? 'stopped' : 'running'
    } else {
      console.error('Failed to toggle bot status')
    }
  } catch (error) {
    console.error('Error toggling bot:', error)
  } finally {
    actionLoading.value[bot.id] = false
  }
}

const startAllBots = async () => {
  bulkActionLoading.value = true
  try {
    const response = await fetch('/api/v1/bots/start-all', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      await loadData() // Reload to get updated status
    }
  } catch (error) {
    console.error('Error starting all bots:', error)
  } finally {
    bulkActionLoading.value = false
  }
}

const stopAllBots = async () => {
  bulkActionLoading.value = true
  try {
    const response = await fetch('/api/v1/bots/stop-all', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })

    if (response.ok) {
      await loadData() // Reload to get updated status
    }
  } catch (error) {
    console.error('Error stopping all bots:', error)
  } finally {
    bulkActionLoading.value = false
  }
}

const editBot = (bot: any) => {
  botForm.value = { ...bot }
  showEditDialog.value = true
}

const deleteBot = async (bot: any) => {
  if (!confirm(`Удалить бота "${bot.name}"?`)) return

  try {
    const response = await fetch(`/api/v1/bots/${bot.id}`, {
      method: 'DELETE'
    })

    if (response.ok) {
      await loadData() // Reload bots list
    } else {
      console.error('Failed to delete bot')
    }
  } catch (error) {
    console.error('Error deleting bot:', error)
  }
}

const saveBot = async () => {
  saveLoading.value = true
  try {
    const method = showEditDialog.value ? 'PUT' : 'POST'
    const url = showEditDialog.value ? `/api/v1/bots/${botForm.value.id}` : '/api/v1/bots/'

    const response = await fetch(url, {
      method,
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(botForm.value)
    })

    if (response.ok) {
      closeDialog()
      await loadData() // Reload bots list
    } else {
      console.error('Failed to save bot')
    }
  } catch (error) {
    console.error('Error saving bot:', error)
  } finally {
    saveLoading.value = false
  }
}

const closeDialog = () => {
  showCreateDialog.value = false
  showEditDialog.value = false
  botForm.value = {
    id: null,
    name: '',
    strategy_name: '',
    exchange: '',
    stake_amount: 100,
    max_open_trades: 5,
    config: '{"timeframe": "5m", "pair_whitelist": ["BTC/USDT"]}',
    freqai_model_id: null
  }
}

// Lifecycle
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.bot-management-dashboard {
  min-height: 100vh;
  background: #f8f9fa;
  padding: 2rem;
}

.dashboard-header {
  text-align: center;
  margin-bottom: 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
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

.bots-section {
  background: white;
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.loading {
  text-align: center;
  padding: 3rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #667eea;
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

.bots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 1.5rem;
}

.bot-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 0.75rem;
  padding: 1.5rem;
  transition: all 0.3s;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.bot-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.bot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.bot-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.25rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.8rem;
  font-weight: bold;
}

.status-badge.running {
  background: #d4edda;
  color: #155724;
}

.status-badge.stopped {
  background: #f8d7da;
  color: #721c24;
}

.bot-details {
  margin-bottom: 1rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.label {
  font-weight: 500;
  color: #666;
}

.value {
  color: #333;
}

.bot-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
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
  max-width: 600px;
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

.bot-form {
  padding: 1.5rem;
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
.form-group select,
.form-group textarea {
  padding: 0.75rem;
  border: 2px solid #e0e0e0;
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #667eea;
}

.form-group textarea {
  resize: vertical;
  min-height: 120px;
  font-family: monospace;
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

.btn-success {
  background: #28a745;
  color: white;
}

.btn-warning {
  background: #ffc107;
  color: #212529;
}

.btn-danger {
  background: #dc3545;
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
  .dashboard-actions {
    flex-direction: column;
  }

  .bots-grid {
    grid-template-columns: 1fr;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .modal-overlay {
    padding: 1rem;
  }

  .modal-content {
    max-height: 95vh;
  }
}
</style>

