# FreqTrade UI

Пользовательский интерфейс для Freqtrade Multi-Bot System на базе Vue.js + TypeScript.

## Технологии

- **Vue 3** - Прогрессивный JavaScript фреймворк
- **TypeScript** - Типизированный JavaScript
- **Vite** - Быстрый билдер и dev server
- **Tailwind CSS** - Utility-first CSS фреймворк
- **Pinia** - State management
- **Vue Router** - Официальный роутер

## Структура проекта

```
freqtrade-ui/
├── public/              # Статические файлы
├── src/
│   ├── components/      # Vue компоненты
│   ├── views/          # Страницы/представления
│   ├── stores/         # Pinia stores
│   ├── router/         # Vue Router конфигурация
│   ├── types/          # TypeScript типы
│   ├── utils/          # Утилиты
│   ├── api/            # API клиенты
│   └── assets/         # Стили и изображения
├── tests/              # Тесты
├── docs/               # Документация
└── dist/               # Сборка (создается автоматически)
```

## Быстрый старт

### Установка зависимостей
```bash
cd freqtrade-ui
npm install
```

### Запуск в режиме разработки
```bash
npm run dev
```

Приложение будет доступно на `http://localhost:3000`

### Сборка для production
```bash
npm run build
```

### Предварительный просмотр сборки
```bash
npm run preview
```

## Основные возможности

### 📊 Dashboard
- Обзор всех запущенных ботов
- Метрики производительности в реальном времени
- Графики прибыли/убытков
- Статус подключения к сервисам

### 🤖 Управление ботами
- Создание новых ботов
- Запуск/остановка ботов
- Настройка стратегий
- Мониторинг логов

### 📈 Стратегии
- Просмотр доступных стратегий
- Загрузка новых стратегий
- Тестирование стратегий (backtesting)
- Оптимизация параметров

### 🎯 FreqAI
- Управление ML моделями
- Обучение новых моделей
- Мониторинг предсказаний
- Анализ производительности

### 👤 Профиль пользователя
- Настройки аккаунта
- API ключи
- Логи аудита

## API интеграция

### Backend endpoints
```typescript
const API_BASE = 'http://localhost:8002/api/v1'

// Примеры запросов
const bots = await api.get('/bots/')
const bot = await api.post('/bots/', botData)
const status = await api.get(`/bots/${id}/status`)
```

### WebSocket подключение
```typescript
import { io } from 'socket.io-client'

const socket = io('http://localhost:8001', {
  transports: ['websocket']
})

// Прослушивание событий
socket.on('bot_status_update', (data) => {
  console.log('Bot status changed:', data)
})
```

## Архитектура компонентов

### State Management (Pinia)
```typescript
// stores/bots.ts
import { defineStore } from 'pinia'

export const useBotsStore = defineStore('bots', {
  state: () => ({
    bots: [],
    loading: false
  }),

  actions: {
    async fetchBots() {
      this.loading = true
      try {
        const response = await api.get('/bots/')
        this.bots = response.data
      } finally {
        this.loading = false
      }
    }
  }
})
```

### Компоненты
```vue
<!-- components/BotCard.vue -->
<template>
  <div class="bot-card">
    <h3>{{ bot.name }}</h3>
    <div class="status" :class="bot.status">
      {{ bot.status }}
    </div>
    <button @click="startBot" :disabled="bot.status === 'running'">
      Start
    </button>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

interface Props {
  bot: Bot
}

const props = defineProps<Props>()

const startBot = async () => {
  await api.post(`/bots/${props.bot.id}/start`)
}
</script>
```

## Стилизация

### Tailwind CSS
```vue
<template>
  <div class="max-w-md mx-auto bg-white rounded-xl shadow-md overflow-hidden">
    <div class="p-6">
      <h2 class="text-2xl font-bold text-gray-900">{{ title }}</h2>
      <p class="text-gray-600 mt-2">{{ description }}</p>
    </div>
  </div>
</template>
```

### Кастомные стили
```scss
// src/assets/styles/main.scss
.bot-card {
  @apply bg-white rounded-lg shadow-md p-4;

  .status {
    &.running { @apply text-green-600; }
    &.stopped { @apply text-red-600; }
    &.starting { @apply text-yellow-600; }
  }
}
```

## Тестирование

### Unit тесты
```bash
npm run test:unit
```

### E2E тесты с Playwright
```bash
# Установка браузеров
npx playwright install

# Запуск всех E2E тестов
npx playwright test

# Запуск в видимом браузере
npx playwright test --headed

# Запуск конкретного теста
npx playwright test --grep "Home Dashboard"

# Просмотр HTML отчета
npx playwright show-report
```

### Структура E2E тестов
```
tests/
├── dashboard.spec.ts    # Тесты всех дашбордов
└── README.md           # Документация по тестированию
```

### Тестируемые дашборды
- ✅ **Home Dashboard** - Главная панель с обзором
- ✅ **Bot Management** - Управление ботами
- ✅ **Strategies** - Стратегии и бектестирование
- ✅ **Analytics** - Аналитика и метрики
- ✅ **FreqAI Lab** - ML модели и предсказания
- ✅ **Data Management** - Управление данными
- ✅ **Hyperopt** - Оптимизация параметров
- ✅ **Monitoring** - Мониторинг компонентов
- ✅ **Audit** - Журнал аудита

### Visual Testing
- Автоматический захват скриншотов для каждого дашборда
- Сохранение в `test-results/*.png`
- Baseline изображения в `test-results/baseline/`

### CI/CD интеграция
E2E тесты запускаются автоматически в GitHub Actions:
- При push в `main` или `develop`
- При создании pull request
- Результаты доступны в artifacts workflow

### Пример Playwright теста
```typescript
// tests/dashboard.spec.ts
import { test, expect } from '@playwright/test';

test('Home Dashboard - Load and Display', async ({ page }) => {
  // Автоматический логин
  await page.goto('/login');
  await page.fill('input[id="username"]', 'analytics_user');
  await page.fill('input[id="password"]', 'testpass123');
  await page.click('button[type="submit"]');

  // Проверка загрузки дашборда
  await expect(page.locator('h1:has-text("🏠 Freqtrade Dashboard")')).toBeVisible();

  // Захват скриншота для визуального тестирования
  await page.screenshot({ path: 'test-results/home-dashboard.png' });
});
```

## Развертывание

### Docker
```dockerfile
FROM node:18-alpine as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:stable-alpine as production-stage
COPY --from=build-stage /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### Nginx конфигурация
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Разработка

### Добавление нового компонента
1. Создать файл в `src/components/`
2. Зарегистрировать в родительском компоненте
3. Добавить стили при необходимости

### Добавление нового роута
```typescript
// router/index.ts
{
  path: '/bots/:id',
  name: 'BotDetail',
  component: () => import('@/views/BotDetail.vue')
}
```

### Работа с API
```typescript
// src/api/bots.ts
import axios from 'axios'

export const botsApi = {
  async getAll() {
    const response = await axios.get('/api/v1/bots/')
    return response.data
  },

  async create(data: CreateBotData) {
    const response = await axios.post('/api/v1/bots/', data)
    return response.data
  }
}
```

## Troubleshooting

### Проблема: API недоступен
```bash
# Проверить запущен ли backend
curl http://localhost:8002/health

# Проверить CORS настройки
# В backend добавить origins для localhost:3000
```

### Проблема: Hot reload не работает
```bash
# Очистить кэш
rm -rf node_modules/.vite

# Перезапустить dev server
npm run dev
```

### Проблема: Сборка падает
```bash
# Проверить TypeScript ошибки
npm run type-check

# Проверить линтер
npm run lint
```

## Contributing

1. Fork репозиторий
2. Создать feature branch (`git checkout -b feature/amazing-feature`)
3. Commit изменения (`git commit -m 'Add amazing feature'`)
4. Push в branch (`git push origin feature/amazing-feature`)
5. Создать Pull Request

## Лицензия

Этот проект лицензирован под MIT License.