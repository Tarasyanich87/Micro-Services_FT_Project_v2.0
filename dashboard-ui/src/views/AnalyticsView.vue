<template>
  <div class="analytics-container">
    <h1>Analytics Dashboard</h1>

    <!-- Backtesting Section -->
    <div class="card">
      <h2>Backtesting</h2>
      <form @submit.prevent="runBacktest">
        <InputText placeholder="Strategy" v-model="backtestParams.strategy" />
        <InputText placeholder="Pair (e.g., BTC/USDT)" v-model="backtestParams.pair" />
        <InputText placeholder="Timeframe (e.g., 5m)" v-model="backtestParams.timeframe" />
        <Button type="submit" label="Run Backtest" :disabled="loading.backtest" />
      </form>
      <DataTable :value="backtestTasks" :loading="loading.backtest">
        <Column field="task_id" header="Task ID"></Column>
        <Column field="status" header="Status"></Column>
        <Column header="Actions">
          <template #body="slotProps">
            <Button v-if="slotProps.data.status === 'completed'" label="View Results" @click="viewResults(slotProps.data.task_id)" />
          </template>
        </Column>
      </DataTable>
    </div>

    <!-- ... (Hyperopt Section is the same) ... -->

    <Dialog header="Backtest Results" v-model:visible="showResultsDialog" modal>
      <pre>{{ backtestResults }}</pre>
    </Dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
// ... (other imports)
import Dialog from 'primevue/dialog'

// ... (existing script setup logic)

const showResultsDialog = ref(false)
const backtestResults = ref(null)

const viewResults = async (taskId) => {
  try {
    const response = await axios.get(`${API_URL}/backtest/result/${taskId}`, authHeader)
    backtestResults.value = response.data
    showResultsDialog.value = true
  } catch (error) {
    console.error('Failed to fetch backtest results:', error)
  }
}

// ... (rest of the script)
</script>
