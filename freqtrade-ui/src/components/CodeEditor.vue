<template>
  <div class="code-editor-wrapper">
    <codemirror
      v-model="internalCode"
      placeholder="Enter your Python code here..."
      :style="{ height: '400px' }"
      :autofocus="true"
      :indent-with-tab="true"
      :tab-size="4"
      :extensions="extensions"
      @update:modelValue="handleCodeChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';
import { Codemirror } from 'vue-codemirror';
import { python } from '@codemirror/lang-python';
import { oneDark } from '@codemirror/theme-one-dark';

const props = defineProps({
  modelValue: {
    type: String,
    default: '',
  },
});

const emit = defineEmits(['update:modelValue']);

const internalCode = ref(props.modelValue);
const extensions = [python(), oneDark];

watch(() => props.modelValue, (newValue) => {
  if (newValue !== internalCode.value) {
    internalCode.value = newValue;
  }
});

const handleCodeChange = (newCode: string) => {
  emit('update:modelValue', newCode);
};
</script>

<style scoped>
.code-editor-wrapper {
  border: 1px solid #ccc;
  border-radius: 4px;
  overflow: hidden;
}
</style>
