<template>
  <div v-if="results" class="backtest-results-container">
    <h4 class="font-semibold">Backtest Results</h4>
    <DataTable :value="formattedResults" :showGridlines="true" size="small">
      <Column field="key" header="Metric"></Column>
      <Column field="value" header="Value">
         <template #body="slotProps">
           {{ formatValue(slotProps.data.value) }}
         </template>
      </Column>
    </DataTable>
  </div>
  <div v-else>
    <p>No backtest results available for this model.</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import DataTable from 'primevue/datatable';
import Column from 'primevue/column';

const props = defineProps({
  results: {
    type: Object,
    default: () => null,
  },
});

const formattedResults = computed(() => {
  if (!props.results) return [];
  return Object.entries(props.results).map(([key, value]) => ({ key, value }));
});

const formatValue = (value: any) => {
  if (typeof value === 'number') {
    // Round floats to a reasonable number of decimal places
    return Number.isInteger(value) ? value : value.toFixed(4);
  }
  if (typeof value === 'object' && value !== null) {
    return JSON.stringify(value);
  }
  return value;
};
</script>

<style scoped>
.backtest-results-container {
  padding: 1rem;
  background-color: #f9fafb;
  border-radius: 8px;
}
</style>
