# Management Server

Основной API сервер Freqtrade Multi-Bot System, предоставляющий REST API для управления ботами, стратегиями и аналитикой.

## Архитектура

```
management_server/
├── api/              # API эндпоинты
│   └── v1/          # Версия API v1
├── auth/            # Аутентификация и авторизация
├── core/            # Ядро приложения (конфиг, app factory)
├── database/        # Настройки подключения к БД
├── db/              # Репозитории данных
├── freqai/          # Интеграция с FreqAI
├── middleware/      # HTTP middleware (логирование, rate limiting)
├── models/          # SQLAlchemy модели данных
├── schemas/         # Pydantic схемы
├── services/        # Бизнес-логика
├── tasks/           # Celery задачи
├── tools/           # Утилиты (Redis streams)
└── utils/           # Вспомогательные функции
```

## Основные компоненты

### API слой (`api/`)
- **FastAPI** приложение с автоматической документацией
- JWT аутентификация
- RESTful эндпоинты для CRUD операций
- WebSocket поддержка (опционально)

### Сервисы (`services/`)
- **BotService** - управление жизненным циклом ботов
- **StrategyService** - валидация и хранение стратегий
- **FreqAIService** - обучение и предсказание ML моделей
- **AuditService** - логирование действий пользователей

### Модели данных (`models/`)
- **User** - пользователи системы
- **Bot** - конфигурации торговых ботов
- **Strategy** - торговые стратегии
- **FreqAIModel** - ML модели
- **AuditLog** - журнал аудита

## Запуск

```bash
# Из корня проекта
cd management_server
uvicorn main:app --host 0.0.0.0 --port 8002 --reload
```

## API документация

После запуска доступна по адресу: `http://localhost:8002/docs`

## Конфигурация

Настройки в `core/config.py`:
- База данных (SQLite/PostgreSQL)
- Redis подключение
- JWT секреты
- Rate limiting
- CORS настройки

## Разработка

### Добавление нового эндпоинта
1. Создать схему в `schemas/`
2. Добавить метод в соответствующий сервис в `services/`
3. Создать эндпоинт в `api/v1/`
4. Зарегистрировать в роутере

### Добавление новой модели
1. Создать модель в `models/models.py`
2. Создать репозиторий в `db/repositories/`
3. Создать сервис в `services/`
4. Добавить API эндпоинты

## Тестирование

```bash
# Запуск тестов
pytest tests/

# С конкретным сервисом
pytest tests/unit/test_bot_service.py
```

## Мониторинг

- **Health checks**: `/health` эндпоинт
- **Метрики**: Интеграция с Prometheus (планируется)
- **Логи**: Структурированное логирование с уровнями