<template>
  <div class="monitoring-container">
    <h1>Audit Log</h1>
    <DataTable :value="logs" :loading="loading">
      <Column field="created_at" header="Timestamp"></Column>
      <Column field="action" header="Action"></Column>
      <Column field="user_id" header="User ID"></Column>
      <Column field="details" header="Details"></Column>
    </DataTable>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { useAuthStore } from '../stores/authStore'
import DataTable from 'primevue/datatable'
import Column from 'primevue/column'

const authStore = useAuthStore()
const API_URL = '/api/v1/monitoring'

const logs = ref([])
const loading = ref(false)

const fetchLogs = async () => {
  loading.value = true
  try {
    const response = await axios.get(`${API_URL}/audit-logs`, {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    logs.value = response.data
  } catch (error) {
    console.error('Failed to fetch audit logs:', error)
  } finally {
    loading.value = false
  }
}

onMounted(fetchLogs)
</script>

<style scoped>
.monitoring-container {
  padding: 20px;
}
</style>
