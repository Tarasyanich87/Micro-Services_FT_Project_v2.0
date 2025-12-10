<template>
  <div class="monitoring-dashboard">
    <div class="dashboard-header">
      <h1>🔍 Мониторинг системы</h1>
      <p>Статус компонентов и системных метрик в реальном времени</p>
    </div>

    <div class="monitoring-grid">
      <!-- System Components -->
      <div class="components-section">
        <h2>🖥️ Компоненты системы</h2>
        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <p>Проверка статуса...</p>
        </div>
        <div v-else class="components-grid">
          <div v-for="component in systemComponents" :key="component.name" class="component-card">
            <div class="component-header">
              <h3>{{ component.name }}</h3>
              <div :class="['status-indicator', component.status]">
                <span class="status-dot"></span>
                <span class="status-text">{{ component.status }}</span>
              </div>
            </div>

            <div class="component-details">
              <div class="metric">
                <span class="label">Response Time:</span>
                <span class="value">{{ component.response_time || 'N/A' }}ms</span>
              </div>
              <div class="metric">
                <span class="label">Uptime:</span>
                <span class="value">{{ component.uptime || 'N/A' }}%</span>
              </div>
              <div class="metric">
                <span class="label">Last Check:</span>
                <span class="value">{{ formatDate(component.last_check) }}</span>
              </div>
            </div>

            <div class="component-actions">
              <button class="btn btn-secondary btn-sm" @click="checkComponent(component)">
                🔄 Проверить
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Performance Metrics -->
      <div class="performance-section">
        <h2>⚡ Производительность</h2>
        <div class="metrics-cards">
          <div class="metric-card">
            <div class="metric-icon">🧠</div>
            <div class="metric-content">
              <h3>{{ performance.cpu }}%</h3>
              <p>CPU Usage</p>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-icon">💾</div>
            <div class="metric-content">
              <h3>{{ performance.memory }}%</h3>
              <p>Memory Usage</p>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-icon">💿</div>
            <div class="metric-content">
              <h3>{{ performance.disk }}%</h3>
              <p>Disk Usage</p>
            </div>
          </div>
          <div class="metric-card">
            <div class="metric-icon">🌐</div>
            <div class="metric-content">
              <h3>{{ performance.network }} Mbps</h3>
              <p>Network Speed</p>
            </div>
          </div>
        </div>
      </div>

      <!-- Active Processes -->
      <div class="processes-section">
        <h2>🔄 Активные процессы</h2>
        <div class="processes-list">
          <div v-for="process in activeProcesses" :key="process.id" class="process-item">
            <div class="process-info">
              <h4>{{ process.name }}</h4>
              <p>PID: {{ process.pid }}</p>
            </div>
            <div class="process-status">
              <span :class="['status-badge', process.status]">
                {{ process.status === 'running' ? '🟢' : '🔴' }} {{ process.status }}
              </span>
            </div>
            <div class="process-metrics">
              <span>CPU: {{ process.cpu }}%</span>
              <span>Memory: {{ process.memory }}MB</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Alerts & Notifications -->
      <div class="alerts-section">
        <h2>🚨 Уведомления</h2>
        <div v-if="alerts.length === 0" class="no-alerts">
          <p>✅ Все системы работают нормально</p>
        </div>
        <div v-else class="alerts-list">
          <div v-for="alert in alerts" :key="alert.id" :class="['alert-item', alert.severity]">
            <div class="alert-icon">{{ alert.severity === 'error' ? '❌' : alert.severity === 'warning' ? '⚠️' : 'ℹ️' }}</div>
            <div class="alert-content">
              <h4>{{ alert.title }}</h4>
              <p>{{ alert.message }}</p>
              <span class="alert-time">{{ formatDate(alert.timestamp) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Logs Preview -->
      <div class="logs-section">
        <h2>📋 Недавние логи</h2>
        <div class="logs-container">
          <div v-for="log in recentLogs" :key="log.timestamp" class="log-entry">
            <span :class="['log-level', log.level]">{{ log.level }}</span>
            <span class="log-message">{{ log.message }}</span>
            <span class="log-time">{{ formatTime(log.timestamp) }}</span>
          </div>
        </div>
        <button class="btn btn-secondary" @click="viewAllLogs">
          📄 Просмотреть все логи
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'

// Reactive data
const systemComponents = ref([])
const performance = ref({
  cpu: 0,
  memory: 0,
  disk: 0,
  network: 0
})
const activeProcesses = ref([])
const alerts = ref([])
const recentLogs = ref([])
const loading = ref(true)

// Methods
const loadMonitoringData = async () => {
  try {
    loading.value = true

    // Load system components status
    const componentsResponse = await fetch('/api/v1/monitoring/monitoring/status')
    if (componentsResponse.ok) {
      const data = await componentsResponse.json()
      systemComponents.value = data.components.map((comp: any) => ({
        ...comp,
        response_time: Math.floor(Math.random() * 100) + 10,
        uptime: Math.floor(Math.random() * 20) + 80,
        last_check: new Date()
      }))
    }

    // Mock performance data
    performance.value = {
      cpu: Math.floor(Math.random() * 30) + 20,
      memory: Math.floor(Math.random() * 40) + 30,
      disk: Math.floor(Math.random() * 20) + 10,
      network: Math.floor(Math.random() * 50) + 50
    }

    // Mock active processes
    activeProcesses.value = [
      { id: 1, name: 'Management Server', pid: 1234, status: 'running', cpu: 15, memory: 256 },
      { id: 2, name: 'Trading Gateway', pid: 1235, status: 'running', cpu: 8, memory: 128 },
      { id: 3, name: 'Redis', pid: 1236, status: 'running', cpu: 3, memory: 64 },
      { id: 4, name: 'Vite Dev Server', pid: 1237, status: 'running', cpu: 5, memory: 89 }
    ]

    // Mock alerts (empty for healthy system)
    alerts.value = []

    // Mock recent logs
    recentLogs.value = [
      { timestamp: new Date(), level: 'info', message: 'System startup completed' },
      { timestamp: new Date(Date.now() - 300000), level: 'info', message: 'Bot BTC_Bot started successfully' },
      { timestamp: new Date(Date.now() - 600000), level: 'warning', message: 'High memory usage detected' },
      { timestamp: new Date(Date.now() - 900000), level: 'info', message: 'Database backup completed' }
    ]

  } catch (error) {
    console.error('Error loading monitoring data:', error)
  } finally {
    loading.value = false
  }
}

const checkComponent = async (component: any) => {
  // Simulate component check
  component.status = 'checking'
  setTimeout(() => {
    component.status = Math.random() > 0.1 ? 'healthy' : 'unhealthy'
    component.last_check = new Date()
  }, 2000)
}

const viewAllLogs = () => {
  // Navigate to audit logs
  window.location.href = '#/audit'
}

const formatDate = (date: Date) => {
  return date.toLocaleString('ru-RU')
}

const formatTime = (date: Date) => {
  return date.toLocaleTimeString('ru-RU', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// Lifecycle
onMounted(() => {
  loadMonitoringData()

  // Auto-refresh every 30 seconds
  setInterval(loadMonitoringData, 30000)
})
</script>

<style scoped>
.monitoring-dashboard {
  min-height: 100vh;
  background: #f8f9fa;
  padding: 2rem;
}

.dashboard-header {
  text-align: center;
  margin-bottom: 2rem;
  background: linear-gradient(135deg, #20c997 0%, #17a2b8 100%);
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

.monitoring-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.components-section, .performance-section, .processes-section, .alerts-section, .logs-section {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.components-section h2, .performance-section h2, .processes-section h2, .alerts-section h2, .logs-section h2 {
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
  border-top: 4px solid #20c997;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem auto;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.components-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
}

.component-card {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 0.75rem;
  padding: 1.5rem;
  transition: all 0.3s;
}

.component-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.component-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.component-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.1rem;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.8rem;
  font-weight: bold;
}

.status-indicator.healthy {
  background: #d4edda;
  color: #155724;
}

.status-indicator.unhealthy {
  background: #f8d7da;
  color: #721c24;
}

.status-indicator.checking {
  background: #fff3cd;
  color: #856404;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: currentColor;
}

.component-details {
  margin-bottom: 1rem;
}

.metric {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #f0f0f0;
}

.metric:last-child {
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

.component-actions {
  text-align: center;
}

.metrics-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.metric-card {
  background: linear-gradient(135deg, #20c997 0%, #17a2b8 100%);
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

.processes-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.process-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  padding: 1rem;
  transition: box-shadow 0.3s;
}

.process-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.process-info h4 {
  margin: 0 0 0.25rem 0;
  color: #333;
}

.process-info p {
  margin: 0;
  color: #666;
  font-size: 0.9rem;
}

.process-status {
  flex-shrink: 0;
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

.process-metrics {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  font-size: 0.9rem;
  color: #666;
}

.no-alerts {
  text-align: center;
  padding: 3rem;
  color: #28a745;
  font-size: 1.1rem;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.alert-item {
  display: flex;
  gap: 1rem;
  padding: 1rem;
  border-radius: 0.5rem;
  border-left: 4px solid;
}

.alert-item.error {
  background: #f8d7da;
  border-left-color: #dc3545;
}

.alert-item.warning {
  background: #fff3cd;
  border-left-color: #ffc107;
}

.alert-item.info {
  background: #d1ecf1;
  border-left-color: #17a2b8;
}

.alert-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.alert-content h4 {
  margin: 0 0 0.5rem 0;
  color: #333;
}

.alert-content p {
  margin: 0 0 0.5rem 0;
  color: #666;
}

.alert-time {
  font-size: 0.8rem;
  color: #999;
}

.logs-container {
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
}

.log-entry {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  border-bottom: 1px solid #f0f0f0;
  font-family: monospace;
  font-size: 0.9rem;
}

.log-entry:last-child {
  border-bottom: none;
}

.log-level {
  font-weight: bold;
  min-width: 60px;
}

.log-level.info {
  color: #17a2b8;
}

.log-level.warning {
  color: #ffc107;
}

.log-level.error {
  color: #dc3545;
}

.log-message {
  flex: 1;
  color: #333;
}

.log-time {
  color: #666;
  font-size: 0.8rem;
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
  .monitoring-grid {
    grid-template-columns: 1fr;
  }

  .components-grid {
    grid-template-columns: 1fr;
  }

  .metrics-cards {
    grid-template-columns: 1fr;
  }

  .process-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .process-metrics {
    align-items: flex-start;
    flex-direction: row;
    gap: 1rem;
  }

  .alert-item {
    flex-direction: column;
    gap: 0.5rem;
  }

  .log-entry {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
}
</style>