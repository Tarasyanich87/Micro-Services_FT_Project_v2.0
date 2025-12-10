# Trading Gateway

Легковесный сервис для прямого управления процессами Freqtrade ботов. Реализует Machine Control Protocol (MCP) для коммуникации с AI агентами.

## Архитектура

```
trading_gateway/
├── api/              # API эндпоинты
│   ├── endpoints/    # Конкретные эндпоинты
│   └── v1/          # Версия API v1
├── core/            # Ядро приложения
├── services/        # Бизнес-логика
│   ├── bot_process_manager.py    # Управление процессами ботов
│   ├── bot_service.py           # Логика управления ботами
│   ├── freqai_integration_service.py  # FreqAI интеграция
│   └── ft_rest_client_service.py      # REST клиент для Freqtrade
├── adapters/        # Адаптеры (WebSocket)
└── interfaces/      # Интерфейсы
```

## Основные компоненты

### Bot Process Manager (`services/bot_process_manager.py`)
Отвечает за:
- Запуск процессов Freqtrade
- Управление жизненным циклом ботов
- Обработку FreqAI моделей
- Мониторинг состояния процессов

### Bot Service (`services/bot_service.py`)
Предоставляет API для:
- Управления ботами через REST
- Получения статуса ботов
- Управления конфигурациями

### FreqAI Integration (`services/freqai_integration_service.py`)
Обрабатывает:
- Загрузку ML моделей
- Base64 декодирование
- Сохранение моделей в файловой системе

## Запуск

```bash
# Из корня проекта
cd trading_gateway
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## API

### REST эндпоинты
- `GET /health` - Health check
- `POST /api/v1/bots/{bot_name}/start` - Запуск бота
- `POST /api/v1/bots/{bot_name}/stop` - Остановка бота
- `GET /api/v1/bots/status` - Статус всех ботов

### WebSocket
- `ws://localhost:8001/ws/agent` - MCP протокол для AI агентов

## MCP Protocol

Trading Gateway реализует WebSocket-based протокол для управления ботами:

### Сообщения
- `START_BOT` - Запуск нового бота
- `STOP_BOT` - Остановка бота
- `RESTART_BOT` - Перезапуск бота
- `GET_BOT_STATUS` - Получение статуса
- `BOT_STARTED` - Событие успешного запуска
- `BOT_STOPPED` - Событие остановки

### Формат сообщений
```json
{
  "type": "START_BOT",
  "id": "msg_001",
  "data": {
    "bot_name": "my_bot",
    "bot_config": {...},
    "freqai_model": {...}
  },
  "timestamp": "2025-12-08T10:00:00Z"
}
```

## Управление процессами

### Запуск бота
1. Получение команды START_BOT
2. Валидация конфигурации
3. Обработка FreqAI модели (если есть)
4. Создание директории бота
5. Сохранение config.json
6. Запуск Freqtrade процесса через subprocess
7. Отправка события BOT_STARTED

### Структура директории бота
```
bots_data/
└── {bot_name}/
    ├── config.json          # Конфигурация Freqtrade
    ├── freqaimodels/       # ML модели
    │   └── model.pkl
    └── tradesv3.sqlite     # База данных торгов
```

## Конфигурация

- **Redis**: Подключение для коммуникации с Management Server
- **Bot directory**: `bots_data/` - место хранения конфигураций ботов
- **Free ports**: Автоматический поиск свободных портов для API серверов ботов

## Мониторинг

- **Process monitoring**: Отслеживание PID процессов
- **Port allocation**: Управление портами API серверов
- **Error handling**: Graceful обработка ошибок запуска/остановки

## Безопасность

- **Process isolation**: Каждый бот запускается в отдельном процессе
- **File system isolation**: Отдельные директории для каждого бота
- **Resource limits**: Ограничения на использование ресурсов

## Разработка

### Добавление нового типа команд
1. Добавить обработчик в `BotProcessManager`
2. Обновить MCP протокол
3. Добавить соответствующие эндпоинты

### Тестирование
```bash
# Запуск с отладкой
uvicorn main:app --host 0.0.0.0 --port 8001 --log-level debug
```

## Интеграция

Trading Gateway интегрируется с:
- **Management Server**: Через Redis Streams
- **Freqtrade**: Через subprocess и REST API
- **FreqAI**: Через файловую систему моделей
- **AI Agents**: Через MCP WebSocket протокол