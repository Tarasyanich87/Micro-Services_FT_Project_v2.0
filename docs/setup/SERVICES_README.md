# Freqtrade Multi-Bot System - Service Management Scripts

Эти скрипты обеспечивают правильный запуск и остановку всех сервисов системы в корректной последовательности.

## Скрипты

### `start_services.sh`
Запускает все сервисы системы в правильном порядке:
1. **Redis** - база данных для очередей и кэширования
2. **Database Initialization** - создание таблиц и начальных данных
3. **Trading Gateway** - сервис управления ботами
4. **Management Server** - основной API сервер

### `stop_services.sh`
Останавливает все сервисы в обратном порядке:
1. **Management Server**
2. **Trading Gateway**
3. **Freqtrade процессы** (если остались)
4. **Redis**

## Использование

### Запуск системы
```bash
./start_services.sh
```

### Остановка системы
```bash
./stop_services.sh
```

### Остановка с очисткой логов
```bash
./stop_services.sh --clean
```

## Что делают скрипты

### start_services.sh
- ✅ Проверяет, что порты свободны
- ✅ Проверяет, что сервисы не запущены
- ✅ Запускает Redis в фоне
- ✅ Инициализирует базу данных
- ✅ Запускает Trading Gateway (порт 8001)
- ✅ Запускает Management Server (порт 8002)
- ✅ Сохраняет PID файлы для управления
- ✅ Проверяет готовность сервисов

### stop_services.sh
- ✅ Graceful остановка Management Server
- ✅ Graceful остановка Trading Gateway
- ✅ Принудительная остановка Freqtrade процессов
- ✅ Остановка Redis
- ✅ Очистка PID файлов
- ✅ Опциональная очистка логов

## Мониторинг

### Проверка статуса
```bash
# Проверить запущенные процессы
ps aux | grep -E "(uvicorn|redis)"

# Проверить порты
netstat -tlnp | grep -E ":(6379|8001|8002)"

# Проверить Redis
redis-cli ping

# Проверить API
curl http://localhost:8002/docs
curl http://localhost:8001/health
```

### Логи
Логи сохраняются в директории `logs/`:
- `management_server.log`
- `trading_gateway.log`
- `*.pid` - файлы с PID процессами

## Безопасность

- Скрипты проверяют состояние перед операциями
- Graceful shutdown с таймаутами
- Принудительная остановка только при необходимости
- Очистка ресурсов при остановке

## Troubleshooting

### Проблема: "Port already in use"
```bash
# Найти процесс, занимающий порт
lsof -i :8002

# Или остановить все сервисы
./stop_services.sh
```

### Проблема: "Virtual environment not found"
```bash
# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Проблема: Сервисы не запускаются
```bash
# Проверить логи
tail -f logs/management_server.log
tail -f logs/trading_gateway.log

# Проверить зависимости
python -c "import fastapi, redis, sqlalchemy"
```

## Production использование

Для production развертывания:
1. Настроить systemd сервисы на основе этих скриптов
2. Добавить health checks
3. Настроить логирование в файлы
4. Добавить мониторинг (Prometheus/Grafana)

## Архитектура

```
User Request → Management Server (8002) → Redis Streams → Trading Gateway (8001) → Freqtrade Bots
                      ↓                           ↓                           ↓
                 Database Updates           Process Management         Live Trading
```

Скрипты обеспечивают корректный запуск этой распределенной системы.