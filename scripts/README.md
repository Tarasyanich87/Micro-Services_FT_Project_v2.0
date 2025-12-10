# Scripts

Вспомогательные скрипты для обслуживания и управления системой Freqtrade Multi-Bot.

## Структура

```
scripts/
├── backup_db.sh              # Резервное копирование базы данных
├── create_dummy_model.py    # Создание тестовых ML моделей
└── verify_redis_streams.py  # Проверка Redis Streams
```

## Скрипты

### backup_db.sh
Скрипт для создания резервных копий базы данных.

**Использование:**
```bash
./scripts/backup_db.sh
```

**Функции:**
- Создание timestamp-based бэкапов
- Очистка старых бэкапов
- Проверка целостности бэкапа

### create_dummy_model.py
Создает тестовые FreqAI модели для разработки и тестирования.

**Использование:**
```bash
cd scripts
python create_dummy_model.py --model-type LightGBM --output ../bots_data/models/
```

**Параметры:**
- `--model-type`: Тип модели (LightGBM, XGBoost, etc.)
- `--output`: Директория для сохранения
- `--features`: Количество признаков

### verify_redis_streams.py
Проверяет состояние Redis Streams и consumer groups.

**Использование:**
```bash
cd scripts
python verify_redis_streams.py --stream mcp_events --group trading_gateway
```

**Функции:**
- Проверка подключения к Redis
- Анализ consumer groups
- Статистика pending сообщений
- Очистка устаревших consumer groups

## Добавление новых скриптов

### Шаблон для bash скриптов
```bash
#!/bin/bash

# Script description
# Usage: ./script_name.sh [options]

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Functions
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}ERROR: $1${NC}" >&2
    exit 1
}

# Main logic
main() {
    log "Starting script execution..."

    # Your code here

    log "Script completed successfully"
}

# Run main function
main "$@"
```

### Шаблон для Python скриптов
```python
#!/usr/bin/env python3
"""
Script description.

Usage:
    python script_name.py [options]
"""

import argparse
import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from management_server.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    # Add your arguments here

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    logger.info("Starting script execution...")

    # Your code here

    logger.info("Script completed successfully")


if __name__ == '__main__':
    main()
```

## Лучшие практики

### 1. Обработка ошибок
```bash
# Bash
set -e  # Exit on error
trap 'error "Script failed at line $LINENO"' ERR

# Python
try:
    # Your code
except Exception as e:
    logger.error(f"Script failed: {e}")
    sys.exit(1)
```

### 2. Логирование
```bash
# Bash
log "Processing file: $filename"

# Python
logger.info("Processing file: %s", filename)
```

### 3. Проверка зависимостей
```bash
# Bash
command -v redis-cli >/dev/null 2>&1 || error "redis-cli not found"

# Python
try:
    import redis
except ImportError:
    logger.error("redis package not installed")
    sys.exit(1)
```

### 4. Безопасность
- Не хранить секреты в скриптах
- Использовать переменные окружения для конфиденциальных данных
- Проверять права доступа к файлам

## Интеграция с CI/CD

### GitHub Actions
```yaml
- name: Run backup script
  run: |
    chmod +x scripts/backup_db.sh
    ./scripts/backup_db.sh

- name: Verify Redis streams
  run: |
    python scripts/verify_redis_streams.py
```

### Cron jobs
```bash
# Ежедневное резервное копирование в 2:00
0 2 * * * /path/to/project/scripts/backup_db.sh

# Проверка Redis каждый час
0 * * * * /path/to/project/scripts/verify_redis_streams.py
```

## Мониторинг

### Health checks
```bash
#!/bin/bash
# health_check.sh

# Check Redis
redis-cli ping >/dev/null 2>&1 || echo "Redis: DOWN"

# Check database
# Add your DB check here

# Check services
curl -s http://localhost:8002/health >/dev/null 2>&1 || echo "Management Server: DOWN"
curl -s http://localhost:8001/health >/dev/null 2>&1 || echo "Trading Gateway: DOWN"

echo "All services healthy"
```

### Метрики
```python
#!/usr/bin/env python3
"""
System metrics collection script.
"""

import psutil
import redis
from management_server.core.config import settings

def collect_metrics():
    # System metrics
    cpu_percent = psutil.cpu_percent()
    memory = psutil.virtual_memory()

    # Redis metrics
    r = redis.from_url(settings.REDIS_URL)
    redis_info = r.info()

    # Application metrics
    # Add your metrics here

    return {
        'cpu_percent': cpu_percent,
        'memory_percent': memory.percent,
        'redis_connected_clients': redis_info['connected_clients'],
        # Add more metrics
    }

if __name__ == '__main__':
    metrics = collect_metrics()
    print(metrics)
```