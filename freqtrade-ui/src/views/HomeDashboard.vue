<template>
  <div class="home-dashboard">
    <div class="dashboard-header">
      <h1>🏠 Freqtrade Dashboard</h1>
      <p>Главная панель управления торговыми ботами</p>
    </div>

    <div class="dashboard-grid">
      <!-- Quick Stats -->
      <div class="stats-section">
        <h2>📊 Быстрая статистика</h2>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">🤖</div>
            <div class="stat-content">
              <h3>{{ stats.activeBots }}</h3>
              <p>Активных ботов</p>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">📈</div>
            <div class="stat-content">
              <h3>{{ stats.totalStrategies }}</h3>
              <p>Стратегий</p>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">💰</div>
            <div class="stat-content">
              <h3>${{ stats.portfolioValue.toLocaleString() }}</h3>
              <p>Портфель</p>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">📊</div>
            <div class="stat-content">
              <h3>{{ stats.winRate }}%</h3>
              <p>Win Rate</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Recent Bots -->
      <div class="bots-section">
        <h2>🤖 Недавние боты</h2>
        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <p>Загрузка...</p>
        </div>
        <div v-else-if="bots.length === 0" class="empty-state">
          <p>Нет активных ботов</p>
          <router-link to="/bots" class="btn btn-primary">Создать бота</router-link>
        </div>
        <div v-else class="bots-list">
          <div v-for="bot in recentBots" :key="bot.id" class="bot-card">
            <div class="bot-header">
              <h3>{{ bot.name }}</h3>
              <span :class="['status-badge', bot.status]">
                {{ bot.status === 'running' ? '🟢' : '🔴' }} {{ bot.status }}
              </span>
            </div>
            <div class="bot-details">
              <p><strong>Стратегия:</strong> {{ bot.strategy_name }}</p>
              <p><strong>Обновлено:</strong> {{ formatDate(bot.updated_at) }}</p>
            </div>
            <div class="bot-actions">
              <button
                class="btn btn-sm"
                :class="bot.status === 'running' ? 'btn-danger' : 'btn-success'"
                @click="toggleBot(bot)"
                :disabled="actionLoading[bot.id]"
              >
                {{ actionLoading[bot.id] ? '...' : (bot.status === 'running' ? '⏹️ Stop' : '▶️ Start') }}
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="actions-section">
        <h2>⚡ Быстрые действия</h2>
        <div class="actions-grid">
          <router-link to="/bots" class="action-card">
            <div class="action-icon">🤖</div>
            <h3>Управление ботами</h3>
            <p>Создание и настройка торговых ботов</p>
          </router-link>
          <router-link to="/strategies" class="action-card">
            <div class="action-icon">📈</div>
            <h3>Стратегии</h3>
            <p>Управление торговыми стратегиями</p>
          </router-link>
          <router-link to="/analytics" class="action-card">
            <div class="action-icon">📊</div>
            <h3>Аналитика</h3>
            <p>Просмотр метрик и отчетов</p>
          </router-link>
          <router-link to="/freqai-lab" class="action-card">
            <div class="action-icon">🧠</div>
            <h3>FreqAI Lab</h3>
            <p>Машинное обучение и предсказания</p>
          </router-link>
        </div>
      </div>

      <!-- System Status -->
      <div class="status-section">
        <h2>🔍 Статус системы</h2>
        <div class="status-grid">
          <div v-for="service in systemStatus" :key="service.name" class="status-item">
            <div class="status-indicator" :class="service.status"></div>
            <div class="status-content">
              <h4>{{ service.name }}</h4>
              <p>{{ service.status === 'healthy' ? 'Работает' : 'Проблемы' }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import type { Bot, SystemService } from '@/types/api'

// Reactive data
const bots = ref<Bot[]>([])
const systemStatus = ref<SystemService[]>([])
const loading = ref(true)
const actionLoading = ref<Record<number, boolean>>({})

// Computed properties
const stats = computed(() => ({
  activeBots: bots.value.filter((bot: any) => bot.status === 'running').length,
  totalStrategies: 5, // Mock data
  portfolioValue: 12500.50, // Mock data
  winRate: 60 // Mock data
}))

const recentBots = computed(() => bots.value.slice(0, 4))

// Methods
const loadData = async () => {
  try {
    loading.value = true

    // Load bots
    const botsResponse = await fetch('/api/v1/bots/')
    if (botsResponse.ok) {
      bots.value = await botsResponse.json()
    }

    // Load system status
    const statusResponse = await fetch('/api/v1/monitoring/monitoring/status')
    if (statusResponse.ok) {
      const statusData = await statusResponse.json()
      systemStatus.value = statusData.components || []
    }

  } catch (error) {
    console.error('Error loading dashboard data:', error)
  } finally {
    loading.value = false
  }
}

const toggleBot = async (bot: any) => {
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

const formatDate = (dateString: string) => {
  if (!dateString) return 'Недавно'
  return new Date(dateString).toLocaleString('ru-RU')
}

// Lifecycle
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.home-dashboard {
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

.dashboard-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.stats-section, .bots-section, .actions-section, .status-section {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stats-section h2, .bots-section h2, .actions-section h2, .status-section h2 {
  margin: 0 0 1.5rem 0;
  color: #333;
  font-size: 1.5rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  color: white;
  padding: 1.5rem;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-icon {
  font-size: 2rem;
}

.stat-content h3 {
  margin: 0 0 0.25rem 0;
  font-size: 1.8rem;
  font-weight: bold;
}

.stat-content p {
  margin: 0;
  opacity: 0.9;
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

.bots-list {
  display: grid;
  gap: 1rem;
}

.bot-card {
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  padding: 1rem;
  transition: box-shadow 0.3s;
}

.bot-card:hover {
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.bot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.bot-header h3 {
  margin: 0;
  color: #333;
}

.status-badge {
  padding: 0.25rem 0.5rem;
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

.bot-details p {
  margin: 0.25rem 0;
  color: #666;
  font-size: 0.9rem;
}

.bot-actions {
  margin-top: 1rem;
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.action-card {
  display: block;
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  padding: 1.5rem;
  text-decoration: none;
  color: inherit;
  transition: all 0.3s;
  text-align: center;
}

.action-card:hover {
  background: #667eea;
  color: white;
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
}

.action-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.action-card h3 {
  margin: 0.5rem 0;
  font-size: 1.2rem;
}

.action-card p {
  margin: 0;
  opacity: 0.8;
  font-size: 0.9rem;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  background: #f8f9fa;
  border-radius: 0.5rem;
}

.status-indicator {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.status-indicator.healthy {
  background: #28a745;
}

.status-indicator.unhealthy {
  background: #dc3545;
}

.status-content h4 {
  margin: 0 0 0.25rem 0;
  color: #333;
}

.status-content p {
  margin: 0;
  font-size: 0.9rem;
  color: #666;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
  text-decoration: none;
  display: inline-block;
  text-align: center;
}

.btn-primary {
  background: #007bff;
  color: white;
}

.btn-success {
  background: #28a745;
  color: white;
}

.btn-danger {
  background: #dc3545;
  color: white;
}

.btn-sm {
  padding: 0.25rem 0.5rem;
  font-size: 0.8rem;
}

.btn:hover {
  opacity: 0.8;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 768px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid, .actions-grid, .status-grid {
    grid-template-columns: 1fr;
  }

  .dashboard-header {
    padding: 1rem;
  }

  .dashboard-header h1 {
    font-size: 2rem;
  }
}
</style>