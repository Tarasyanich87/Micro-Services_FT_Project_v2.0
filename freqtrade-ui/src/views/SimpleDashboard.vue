<template>
  <div class="simple-dashboard">
    <header class="dashboard-header">
      <h1>🚀 Freqtrade Multi-Bot Dashboard</h1>
      <p>Управление торговыми ботами и аналитика</p>
    </header>

    <nav class="dashboard-nav">
      <button
        v-for="tab in tabs"
        :key="tab.id"
        :class="['nav-button', { active: activeTab === tab.id }]"
        @click="activeTab = tab.id"
      >
        {{ tab.name }}
      </button>
    </nav>

    <main class="dashboard-content">
      <!-- Home Tab -->
      <div v-if="activeTab === 'home'" class="tab-content">
        <h2>🏠 Главная панель</h2>
        <div class="stats-grid">
          <div class="stat-card">
            <h3>🤖 Активные боты</h3>
            <p class="stat-number">{{ bots.filter(b => b.status === 'running').length }}</p>
          </div>
          <div class="stat-card">
            <h3>📊 Всего стратегий</h3>
            <p class="stat-number">{{ strategies.length }}</p>
          </div>
          <div class="stat-card">
            <h3>💰 Портфель</h3>
            <p class="stat-number">$12,500.50</p>
          </div>
          <div class="stat-card">
            <h3>📈 Win Rate</h3>
            <p class="stat-number">60%</p>
          </div>
        </div>

        <div class="bots-list">
          <h3>Список ботов</h3>
          <div v-for="bot in bots" :key="bot.id" class="bot-item">
            <span>{{ bot.name }}</span>
            <span :class="['status', bot.status]">{{ bot.status }}</span>
          </div>
        </div>
      </div>

      <!-- Bots Tab -->
      <div v-if="activeTab === 'bots'" class="tab-content">
        <h2>🤖 Управление ботами</h2>
        <div class="bots-grid">
          <div v-for="bot in bots" :key="bot.id" class="bot-card">
            <h3>{{ bot.name }}</h3>
            <p>Стратегия: {{ bot.strategy_name }}</p>
            <p>Статус: <span :class="['status', bot.status]">{{ bot.status }}</span></p>
            <div class="bot-actions">
              <button class="btn btn-success" @click="startBot(bot)">▶️ Start</button>
              <button class="btn btn-danger" @click="stopBot(bot)">⏹️ Stop</button>
            </div>
          </div>
        </div>
        <button class="btn btn-primary" @click="showCreateDialog = true">➕ Создать бота</button>
      </div>

      <!-- Strategies Tab -->
      <div v-if="activeTab === 'strategies'" class="tab-content">
        <h2>📈 Стратегии</h2>
        <div class="strategies-list">
          <div v-for="strategy in strategies" :key="strategy" class="strategy-item">
            <span>{{ strategy }}</span>
            <button class="btn btn-secondary">⚙️ Настроить</button>
          </div>
        </div>
      </div>



      <!-- Audit Tab -->
      <div v-if="activeTab === 'audit'" class="tab-content">
        <h2>📝 Журнал аудита</h2>
        <div class="audit-list">
          <div v-for="log in auditLogs" :key="log.timestamp" class="audit-item">
            <span>{{ log.timestamp }}</span>
            <span>{{ log.user }}</span>
            <span>{{ log.action }}</span>
            <span :class="['status-code', `status-${log.status}`]">{{ log.status }}</span>
          </div>
        </div>
      </div>

      <!-- Monitoring Tab -->
      <div v-if="activeTab === 'monitoring'" class="tab-content">
        <h2>🔍 Мониторинг системы</h2>
        <div class="monitoring-grid">
          <div v-for="component in monitoring" :key="component.name" class="component-card">
            <h3>{{ component.name }}</h3>
            <span :class="['status', component.status]">{{ component.status }}</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// Data
const activeTab = ref('home')
const bots = ref([])
const strategies = ref([])

const auditLogs = ref([])
const monitoring = ref([])

// Tabs configuration
const tabs = [
  { id: 'home', name: 'Главная' },
  { id: 'bots', name: 'Боты' },
  { id: 'strategies', name: 'Стратегии' },
  { id: 'audit', name: 'Аудит' },
  { id: 'monitoring', name: 'Мониторинг' }
]

// Mock data loading
const loadData = async () => {
  try {
    // Load bots
    const botsResponse = await fetch('/api/v1/bots/')
    bots.value = await botsResponse.json()

    // Load strategies
    const strategiesResponse = await fetch('/api/v1/strategies/')
    strategies.value = await strategiesResponse.json()



    // Load audit logs
    const auditResponse = await fetch('/api/v1/audit/logs')
    auditLogs.value = await auditResponse.json()

    // Load monitoring
    const monitoringResponse = await fetch('/api/v1/monitoring/status')
    const monitoringData = await monitoringResponse.json()
    monitoring.value = monitoringData.components || []

  } catch (error) {
    console.error('Error loading data:', error)
  }
}

// Bot actions
const startBot = async (bot: any) => {
  try {
    await fetch(`/api/v1/bots/${bot.id}/start`, { method: 'POST' })
    bot.status = 'running'
  } catch (error) {
    console.error('Error starting bot:', error)
  }
}

const stopBot = async (bot: any) => {
  try {
    await fetch(`/api/v1/bots/${bot.id}/stop`, { method: 'POST' })
    bot.status = 'stopped'
  } catch (error) {
    console.error('Error stopping bot:', error)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.simple-dashboard {
  min-height: 100vh;
  background: #f5f5f5;
}

.dashboard-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 2rem;
  text-align: center;
}

.dashboard-nav {
  background: white;
  padding: 1rem;
  display: flex;
  gap: 1rem;
  overflow-x: auto;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.nav-button {
  padding: 0.5rem 1rem;
  border: none;
  background: #f0f0f0;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.3s;
}

.nav-button:hover {
  background: #e0e0e0;
}

.nav-button.active {
  background: #667eea;
  color: white;
}

.dashboard-content {
  padding: 2rem;
}

.tab-content {
  background: white;
  border-radius: 0.5rem;
  padding: 2rem;
  box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 0.5rem;
  text-align: center;
}

.stat-card h3 {
  margin: 0 0 1rem 0;
  color: #666;
}

.stat-number {
  font-size: 2rem;
  font-weight: bold;
  color: #667eea;
}

.bots-list, .strategies-list, .audit-list {
  margin-top: 2rem;
}

.bot-item, .strategy-item, .audit-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  margin-bottom: 0.5rem;
}

.status.running {
  color: #28a745;
  font-weight: bold;
}

.status.stopped {
  color: #dc3545;
  font-weight: bold;
}

.status.completed {
  color: #28a745;
}

.status-code.status-200 {
  color: #28a745;
}

.status-code.status-201 {
  color: #007bff;
}

.bots-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.bot-card, .component-card, .metric-card {
  background: #f8f9fa;
  padding: 1.5rem;
  border-radius: 0.5rem;
  border: 1px solid #e0e0e0;
}

.bot-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 1rem;
}

.btn {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 0.25rem;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.3s;
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

.btn-secondary {
  background: #6c757d;
  color: white;
}

.btn:hover {
  opacity: 0.8;
}



.monitoring-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

@media (max-width: 768px) {
  .dashboard-nav {
    flex-wrap: wrap;
  }

  .stats-grid, .bots-grid, .monitoring-grid {
    grid-template-columns: 1fr;
  }
}
</style>