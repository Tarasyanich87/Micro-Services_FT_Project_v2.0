<template>
  <div class="freqai-lab-dashboard">
    <div class="dashboard-header">
      <h1>🧠 FreqAI Lab</h1>
      <p>Машинное обучение и предсказательные модели</p>
    </div>

    <div class="freqai-grid">
      <!-- Models List -->
      <div class="models-section">
        <h2>🤖 Модели FreqAI</h2>
        <div class="models-controls">
          <button class="btn btn-primary" @click="showCreateDialog = true">
            ➕ Создать модель
          </button>
        </div>
        <div class="models-list">
          <div v-for="model in models" :key="model.id" class="model-card">
            <div class="model-header">
              <h3>{{ model.name }}</h3>
              <span :class="['status-badge', model.status]">
                {{ model.status === 'trained' ? '✅' : model.status === 'training' ? '⏳' : '❌' }}
              </span>
            </div>
            <p>{{ model.description }}</p>
            <div class="model-metrics">
              <div class="metric">
                <span>Accuracy:</span>
                <span>{{ model.accuracy || 'N/A' }}%</span>
              </div>
              <div class="metric">
                <span>Features:</span>
                <span>{{ model.features || 0 }}</span>
              </div>
            </div>
            <div class="model-actions">
              <button class="btn btn-success btn-sm" @click="runBacktest(model)">
                🧪 Бектест
              </button>
              <button class="btn btn-warning btn-sm" @click="retrainModel(model)">
                🔄 Retrain
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Training Progress -->
      <div class="training-section">
        <h2>📈 Обучение моделей</h2>
        <div v-if="trainingJobs.length === 0" class="empty-state">
          <p>Нет активных задач обучения</p>
        </div>
        <div v-else class="training-list">
          <div v-for="job in trainingJobs" :key="job.id" class="training-card">
            <div class="training-header">
              <h4>{{ job.modelName }}</h4>
              <span class="progress-text">{{ job.progress }}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: job.progress + '%' }"></div>
            </div>
            <p class="training-status">{{ job.status }}</p>
          </div>
        </div>
      </div>

      <!-- Backtest Results -->
      <div class="backtest-section">
        <h2>📊 Результаты бектестинга</h2>
        <div class="backtest-results">
          <div v-for="result in backtestResults" :key="result.id" class="result-card">
            <h4>{{ result.model }} + {{ result.strategy }}</h4>
            <div class="result-metrics">
              <div class="metric">
                <span>Sharpe:</span>
                <span>{{ result.sharpe }}</span>
              </div>
              <div class="metric">
                <span>Max DD:</span>
                <span>{{ result.maxDrawdown }}%</span>
              </div>
              <div class="metric">
                <span>Win Rate:</span>
                <span>{{ result.winRate }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Feature Importance -->
      <div class="features-section">
        <h2>🎯 Важность признаков</h2>
        <div class="features-chart">
          <div v-for="feature in featureImportance" :key="feature.name" class="feature-item">
            <span class="feature-name">{{ feature.name }}</span>
            <div class="feature-bar">
              <div class="feature-fill" :style="{ width: feature.importance + '%' }"></div>
            </div>
            <span class="feature-value">{{ feature.importance }}%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Model Dialog -->
    <div v-if="showCreateDialog" class="modal-overlay" @click="closeDialog">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>🚀 Создать FreqAI модель</h2>
          <button class="close-btn" @click="closeDialog">✕</button>
        </div>

        <form @submit.prevent="createModel" class="model-form">
          <div class="form-group">
            <label for="model-name">Название модели *</label>
            <input
              id="model-name"
              v-model="newModel.name"
              type="text"
              required
              placeholder="Например: BTC_Predictor"
            />
          </div>

          <div class="form-group">
            <label for="model-description">Описание</label>
            <textarea
              id="model-description"
              v-model="newModel.description"
              rows="3"
              placeholder="Описание модели..."
            ></textarea>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label for="model-type">Тип модели</label>
              <select id="model-type" v-model="newModel.type">
                <option value="regression">Регрессия</option>
                <option value="classification">Классификация</option>
                <option value="reinforcement">Усиление</option>
              </select>
            </div>

            <div class="form-group">
              <label for="target">Целевая переменная</label>
              <select id="target" v-model="newModel.target">
                <option value="price">Цена</option>
                <option value="trend">Тренд</option>
                <option value="volatility">Волатильность</option>
              </select>
            </div>
          </div>

          <div class="form-actions">
            <button type="button" class="btn btn-secondary" @click="closeDialog">
              Отмена
            </button>
            <button type="submit" class="btn btn-primary" :disabled="createLoading">
              <span v-if="createLoading" class="spinner"></span>
              {{ createLoading ? 'Создание...' : '🚀 Создать модель' }}
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
const models = ref([])
const trainingJobs = ref([])
const backtestResults = ref([])
const featureImportance = ref([])
const showCreateDialog = ref(false)
const createLoading = ref(false)

const newModel = ref({
  name: '',
  description: '',
  type: 'regression',
  target: 'price'
})

// Methods
const loadData = async () => {
  // Load FreqAI models
  const modelsResponse = await fetch('/api/v1/freqai/models')
  if (modelsResponse.ok) {
    models.value = await modelsResponse.json()
  }

  // Mock data
  models.value = [
    { id: 1, name: 'BTC_Predictor', description: 'Bitcoin price prediction model', status: 'trained', accuracy: 78, features: 25 },
    { id: 2, name: 'ETH_Trend', description: 'Ethereum trend analysis', status: 'training', accuracy: null, features: 18 },
    { id: 3, name: 'ADA_Volatility', description: 'Cardano volatility predictor', status: 'failed', accuracy: null, features: 12 }
  ]

  trainingJobs.value = [
    { id: 1, modelName: 'ETH_Trend', progress: 65, status: 'Training neural network...' }
  ]

  backtestResults.value = [
    { id: 1, model: 'BTC_Predictor', strategy: 'SampleStrategy', sharpe: 1.45, maxDrawdown: 12.5, winRate: 68 },
    { id: 2, model: 'ETH_Trend', strategy: 'AnotherStrategy', sharpe: 0.89, maxDrawdown: 18.2, winRate: 55 }
  ]

  featureImportance.value = [
    { name: 'RSI', importance: 85 },
    { name: 'Volume', importance: 72 },
    { name: 'MACD', importance: 68 },
    { name: 'Bollinger Bands', importance: 61 },
    { name: 'Moving Average', importance: 55 }
  ]
}

const runBacktest = async (model: any) => {
  alert(`Запуск бектестинга для модели ${model.name}`)
}

const retrainModel = async (model: any) => {
  alert(`Переобучение модели ${model.name}`)
}

const createModel = async () => {
  createLoading.value = true
  try {
    const response = await fetch('/api/v1/freqai/models', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(newModel.value)
    })

    if (response.ok) {
      closeDialog()
      loadData()
    } else {
      alert('Ошибка создания модели')
    }
  } catch (error) {
    console.error('Error creating model:', error)
    alert('Ошибка создания модели')
  } finally {
    createLoading.value = false
  }
}

const closeDialog = () => {
  showCreateDialog.value = false
  newModel.value = {
    name: '',
    description: '',
    type: 'regression',
    target: 'price'
  }
}

// Lifecycle
onMounted(() => {
  loadData()
})
</script>

<style scoped>
.freqai-lab-dashboard {
  min-height: 100vh;
  background: #f8f9fa;
  padding: 2rem;
}

.dashboard-header {
  text-align: center;
  margin-bottom: 2rem;
  background: linear-gradient(135deg, #ff6b6b 0%, #feca57 100%);
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

.freqai-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.models-section, .training-section, .backtest-section, .features-section {
  background: white;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.models-section h2, .training-section h2, .backtest-section h2, .features-section h2 {
  margin: 0 0 1.5rem 0;
  color: #333;
  font-size: 1.5rem;
}

.models-controls {
  margin-bottom: 1.5rem;
}

.models-list {
  display: grid;
  gap: 1rem;
}

.model-card {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 0.75rem;
  padding: 1.5rem;
  transition: all 0.3s;
}

.model-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.model-header h3 {
  margin: 0;
  color: #333;
  font-size: 1.1rem;
}

.status-badge {
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.8rem;
  font-weight: bold;
}

.status-badge.trained {
  background: #d4edda;
  color: #155724;
}

.status-badge.training {
  background: #fff3cd;
  color: #856404;
}

.status-badge.failed {
  background: #f8d7da;
  color: #721c24;
}

.model-card p {
  margin: 0.5rem 0;
  color: #666;
}

.model-metrics {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.metric {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.5rem;
  background: white;
  border-radius: 0.25rem;
  min-width: 80px;
}

.metric span:first-child {
  font-size: 0.8rem;
  color: #666;
  margin-bottom: 0.25rem;
}

.metric span:last-child {
  font-weight: bold;
  color: #333;
}

.model-actions {
  display: flex;
  gap: 0.5rem;
}

.training-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.training-card {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  padding: 1rem;
}

.training-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.training-header h4 {
  margin: 0;
  color: #333;
}

.progress-text {
  font-weight: bold;
  color: #007bff;
}

.progress-bar {
  width: 100%;
  height: 8px;
  background: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #28a745 0%, #007bff 100%);
  transition: width 0.3s;
}

.training-status {
  font-size: 0.9rem;
  color: #666;
}

.backtest-results {
  display: grid;
  gap: 1rem;
}

.result-card {
  background: #f8f9fa;
  border: 1px solid #e0e0e0;
  border-radius: 0.5rem;
  padding: 1rem;
}

.result-card h4 {
  margin: 0 0 1rem 0;
  color: #333;
}

.result-metrics {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  gap: 1rem;
}

.features-chart {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.feature-name {
  min-width: 120px;
  font-weight: 500;
  color: #333;
}

.feature-bar {
  flex: 1;
  height: 20px;
  background: #e0e0e0;
  border-radius: 10px;
  overflow: hidden;
}

.feature-fill {
  height: 100%;
  background: linear-gradient(90deg, #ff6b6b 0%, #feca57 100%);
  transition: width 0.3s;
}

.feature-value {
  min-width: 60px;
  text-align: right;
  font-weight: bold;
  color: #333;
}

.empty-state {
  text-align: center;
  padding: 3rem;
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
  max-width: 500px;
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

.model-form {
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
  border-color: #ff6b6b;
}

.form-group textarea {
  resize: vertical;
  min-height: 80px;
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

.btn-secondary {
  background: #6c757d;
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

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

@media (max-width: 768px) {
  .freqai-grid {
    grid-template-columns: 1fr;
  }

  .model-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .model-actions {
    flex-direction: column;
  }

  .training-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .result-metrics {
    grid-template-columns: 1fr;
  }

  .feature-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
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