<template>
  <div class="prediction-container mt-4">
    <h3 class="text-lg font-semibold leading-6 text-gray-900">FreqAI Predictions</h3>
    <button
      @click="fetchData"
      :disabled="botsStore.isPredictionLoading"
      class="mt-2 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:bg-gray-400"
    >
      {{ botsStore.isPredictionLoading ? 'Loading...' : 'Refresh Predictions' }}
    </button>
    <div v-if="botsStore.isPredictionLoading" class="mt-4">
      Loading...
    </div>
    <div v-else-if="!botsStore.activeBotPredictions.length" class="mt-4 text-gray-500">
      No prediction data available. Click "Refresh Predictions" to fetch.
    </div>
    <div v-else class="mt-4 overflow-x-auto">
      <table class="min-w-full divide-y divide-gray-200">
        <thead class="bg-gray-50">
          <tr>
            <th v-for="key in headers" :key="key" scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              {{ key }}
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="(prediction, index) in botsStore.activeBotPredictions" :key="index">
            <td v-for="key in headers" :key="key" class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
              {{ formatValue(prediction[key]) }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from 'vue';
import { useBotsStore } from '@/stores/bots';

const props = defineProps({
  botId: {
    type: Number,
    required: true,
  },
});

const botsStore = useBotsStore();

const fetchData = () => {
  botsStore.fetchPredictions(props.botId);
};

// Fetch data when the component is first mounted
onMounted(fetchData);

// Dynamically compute table headers from the keys of the first prediction object
const headers = computed(() => {
  if (botsStore.activeBotPredictions.length > 0) {
    return Object.keys(botsStore.activeBotPredictions[0]);
  }
  return [];
});

// Helper to format values for display
const formatValue = (value: any) => {
  if (typeof value === 'number') {
    // Round floats to a reasonable number of decimal places
    return Number.isInteger(value) ? value : value.toFixed(4);
  }
  return value;
};
</script>

<style scoped>
.prediction-container {
  /* Add any specific styling if needed */
}
</style>
