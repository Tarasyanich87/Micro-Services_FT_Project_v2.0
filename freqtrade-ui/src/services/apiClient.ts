import axios from 'axios';
import { useAuthStore } from '@/stores/auth';

// Management Server API (порт 8002) - основной API
const managementApi = axios.create({
  baseURL: import.meta.env.VITE_MANAGEMENT_API_URL || '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Backtesting Server API (порт 8003) - бэктестирование
const backtestingApi = axios.create({
  baseURL: import.meta.env.VITE_BACKTESTING_API_URL || '/api/backtesting',
  headers: {
    'Content-Type': 'application/json',
  },
});

// FreqAI Server API (порт 8004) - ML модели
const freqaiApi = axios.create({
  baseURL: import.meta.env.VITE_FREQAI_API_URL || '/api/freqai',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Trading Gateway API (порт 8001) - управление ботами
const tradingApi = axios.create({
  baseURL: import.meta.env.VITE_TRADING_API_URL || '/api/trading',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Добавляем интерцепторы аутентификации ко всем клиентам
const addAuthInterceptor = (client: any) => {
  client.interceptors.request.use(
    (config: any) => {
      const authStore = useAuthStore();
      console.log(`API Request to ${client.defaults.baseURL}:`, config.url, 'Token:', authStore.token);
      if (authStore.token) {
        config.headers.Authorization = `Bearer ${authStore.token}`;
      }
      return config;
    },
    (error: any) => {
      return Promise.reject(error);
    }
  );
};

addAuthInterceptor(managementApi);
addAuthInterceptor(backtestingApi);
addAuthInterceptor(freqaiApi);
addAuthInterceptor(tradingApi);

// Основной клиент (для обратной совместимости)
const apiClient = managementApi;

export default apiClient;
export { managementApi, backtestingApi, freqaiApi, tradingApi };
