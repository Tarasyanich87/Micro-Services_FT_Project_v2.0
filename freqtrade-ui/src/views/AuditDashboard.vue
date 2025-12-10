<template>
  <div class="audit-dashboard">
    <div class="dashboard-header">
      <h1>📝 Журнал аудита</h1>
      <p>Отслеживание всех действий в системе</p>
    </div>

    <div class="audit-controls">
      <div class="filters">
        <select v-model="statusFilter">
          <option value="">Все статусы</option>
          <option value="200">Успешные (200)</option>
          <option value="400">Ошибки клиента (400+)</option>
          <option value="500">Серверные ошибки (500+)</option>
        </select>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Поиск по действию или пользователю..."
        />
      </div>
      <button class="btn btn-primary" @click="refreshLogs">
        🔄 Обновить
      </button>
    </div>

    <div class="audit-section">
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Загрузка журнала аудита...</p>
      </div>

      <div v-else-if="filteredLogs.length === 0" class="empty-state">
        <h3>Записи не найдены</h3>
        <p>Нет записей аудита соответствующих фильтрам</p>
      </div>

      <div v-else class="audit-table">
        <div class="table-header">
          <div class="col-timestamp">Время</div>
          <div class="col-user">Пользователь</div>
          <div class="col-action">Действие</div>
          <div class="col-method">Метод</div>
          <div class="col-status">Статус</div>
          <div class="col-details">Детали</div>
        </div>

        <div v-for="log in paginatedLogs" :key="log.timestamp + log.user + log.action" class="table-row">
          <div class="col-timestamp">{{ formatDate(log.timestamp) }}</div>
          <div class="col-user">{{ log.user }}</div>
          <div class="col-action">{{ log.action }}</div>
          <div class="col-method">
            <span :class="['method-badge', log.method.toLowerCase()]">{{ log.method }}</span>
          </div>
          <div class="col-status">
            <span :class="['status-badge', getStatusClass(log.status)]">{{ log.status }}</span>
          </div>
          <div class="col-details">
            <button class="btn-link" @click="showDetails(log)">Подробнее</button>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div v-if="totalPages > 1" class="pagination">
        <button
          class="btn btn-secondary"
          :disabled="currentPage === 1"
          @click="currentPage--"
        >
          ← Предыдущая
        </button>

        <span class="page-info">
          Страница {{ currentPage }} из {{ totalPages }}
        </span>

        <button
          class="btn btn-secondary"
          :disabled="currentPage === totalPages"
          @click="currentPage++"
        >
          Следующая →
        </button>
      </div>
    </div>

    <!-- Details Modal -->
    <div v-if="selectedLog" class="modal-overlay" @click="closeDetails">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>Детали записи аудита</h2>
          <button class="close-btn" @click="closeDetails">✕</button>
        </div>

        <div class="log-details">
          <div class="detail-row">
            <span class="label">Время:</span>
            <span class="value">{{ formatDate(selectedLog.timestamp) }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Пользователь:</span>
            <span class="value">{{ selectedLog.user }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Действие:</span>
            <span class="value">{{ selectedLog.action }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Метод:</span>
            <span class="value">{{ selectedLog.method }}</span>
          </div>
          <div class="detail-row">
            <span class="label">Статус:</span>
            <span class="value">{{ selectedLog.status }}</span>
          </div>
          <div class="detail-row">
            <span class="label">URL:</span>
            <span class="value">{{ selectedLog.url || 'N/A' }}</span>
          </div>
          <div class="detail-row">
            <span class="label">IP адрес:</span>
            <span class="value">{{ selectedLog.ip || 'N/A' }}</span>
          </div>
          <div class="detail-row">
            <span class="label">User Agent:</span>
            <span class="value">{{ selectedLog.user_agent || 'N/A' }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'

// Reactive data
const auditLogs = ref([])
const loading = ref(true)
const statusFilter = ref('')
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const selectedLog = ref(null)

// Computed properties
const filteredLogs = computed(() => {
  let filtered = auditLogs.value

  // Filter by status
  if (statusFilter.value) {
    if (statusFilter.value === '200') {
      filtered = filtered.filter(log => log.status === 200)
    } else if (statusFilter.value === '400') {
      filtered = filtered.filter(log => log.status >= 400 && log.status < 500)
    } else if (statusFilter.value === '500') {
      filtered = filtered.filter(log => log.status >= 500)
    }
  }

  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(log =>
      log.action.toLowerCase().includes(query) ||
      log.user.toLowerCase().includes(query)
    )
  }

  return filtered
})

const totalPages = computed(() => {
  return Math.ceil(filteredLogs.value.length / pageSize.value)
})

const paginatedLogs = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredLogs.value.slice(start, end)
})

// Methods
const loadAuditLogs = async () => {
  try {
    loading.value = true
    const response = await fetch('/api/v1/audit/logs')
    if (response.ok) {
      auditLogs.value = await response.json()
    } else {
      console.error('Failed to load audit logs')
    }
  } catch (error) {
    console.error('Error loading audit logs:', error)
  } finally {
    loading.value = false
  }
}

const refreshLogs = () => {
  loadAuditLogs()
}

const showDetails = (log: any) => {
  selectedLog.value = log
}

const closeDetails = () => {
  selectedLog.value = null
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString('ru-RU')
}

const getStatusClass = (status: number) => {
  if (status >= 500) return 'error'
  if (status >= 400) return 'warning'
  if (status >= 300) return 'info'
  if (status >= 200) return 'success'
  return 'secondary'
}

// Lifecycle
onMounted(() => {
  loadAuditLogs()
})
</script>

<style scoped>
.audit-dashboard {
  min-height: 100vh;
  background: #f8f9fa;
  padding: 2rem;
}

.dashboard-header {
  text-align: center;
  margin-bottom: 2rem;
  background: linear-gradient(135deg, #6f42c1 0%, #5a359a 100%);
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

.audit-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  background: white;
  padding: 1.5rem;
  border-radius: 0.75rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  flex-wrap: wrap;
  gap: 1rem;
}

.filters {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.filters select,
.filters input {
  padding: 0.5rem;
  border: 2px solid #e0e0e0;
  border-radius: 0.25rem;
  font-size: 1rem;
}

.filters select:focus,
.filters input:focus {
  outline: none;
  border-color: #6f42c1;
}

.audit-section {
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
  border-top: 4px solid #6f42c1;
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

.audit-table {
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  overflow: hidden;
}

.table-header {
  display: grid;
  grid-template-columns: 180px 120px 1fr 80px 80px 100px;
  gap: 1rem;
  background: #f8f9fa;
  padding: 1rem;
  font-weight: bold;
  color: #333;
  border-bottom: 1px solid #e0e0e0;
}

.table-row {
  display: grid;
  grid-template-columns: 180px 120px 1fr 80px 80px 100px;
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

.col-timestamp {
  font-size: 0.9rem;
  color: #666;
}

.col-user {
  font-weight: 500;
  color: #333;
}

.col-action {
  color: #555;
}

.method-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.8rem;
  font-weight: bold;
}

.method-badge.get {
  background: #d1ecf1;
  color: #0c5460;
}

.method-badge.post {
  background: #d4edda;
  color: #155724;
}

.method-badge.put {
  background: #fff3cd;
  color: #856404;
}

.method-badge.delete {
  background: #f8d7da;
  color: #721c24;
}

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.8rem;
  font-weight: bold;
  text-align: center;
}

.status-badge.success {
  background: #d4edda;
  color: #155724;
}

.status-badge.warning {
  background: #fff3cd;
  color: #856404;
}

.status-badge.error {
  background: #f8d7da;
  color: #721c24;
}

.status-badge.info {
  background: #d1ecf1;
  color: #0c5460;
}

.btn-link {
  background: none;
  border: none;
  color: #6f42c1;
  cursor: pointer;
  text-decoration: underline;
  font-size: 0.9rem;
}

.btn-link:hover {
  color: #5a359a;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 2rem;
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #e0e0e0;
}

.page-info {
  font-weight: 500;
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

.log-details {
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.detail-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid #f0f0f0;
}

.detail-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.label {
  font-weight: 500;
  color: #666;
}

.value {
  color: #333;
  word-break: break-all;
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
  .audit-controls {
    flex-direction: column;
    align-items: stretch;
  }

  .filters {
    flex-direction: column;
    align-items: stretch;
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

  .pagination {
    flex-direction: column;
    gap: 1rem;
  }

  .modal-overlay {
    padding: 1rem;
  }

  .modal-content {
    max-height: 95vh;
  }

  .log-details {
    padding: 1rem;
  }

  .detail-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.25rem;
  }
}
</style>