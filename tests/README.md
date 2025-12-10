# Тесты

Набор автоматизированных тестов для обеспечения качества и надежности Freqtrade Multi-Bot System.

## Структура

```
tests/
├── api/                    # API endpoint tests
│   ├── test_analytics_api.py
│   ├── test_comprehensive_api.py
│   ├── test_strategy_management.py
│   └── test_strategy.md
├── bulk_operations/        # Bulk operations tests
│   ├── test_bulk_bot_operations.py
│   └── bulk_operations_test_results.json
├── e2e/                    # End-to-end tests
│   ├── test_all_dashboards.py
│   ├── test_bot_lifecycle.py
│   ├── test_complete_system.py
│   ├── test_dashboards_http.py
│   └── test_strategy_ui.py
├── freqai/                 # FreqAI specific tests
│   ├── test_freqai_handler.py
│   ├── test_freqai_model.joblib
│   └── create_test_model.py
├── integration/            # Integration tests
│   ├── test_analytics_audit.py
│   ├── test_command_cycle.py
│   └── test_freqai_integration.py
├── performance/            # Performance tests
│   └── test_api_performance.py
├── services/               # Service-specific tests
│   └── backtesting_server/
│       └── test_basic.py
├── unit/                   # Unit tests
│   ├── test_analytics_service.py
│   ├── test_audit_service.py
│   ├── test_bot_service.py
│   ├── test_strategy_analysis_service.py
│   └── test_trading_gateway.py
├── conftest.py             # Pytest configuration
├── test_api.py             # General API tests
└── README.md
```

## Типы тестов

### API Tests (`api/`)
Тесты для отдельных API эндпоинтов и их функциональности:
- Analytics API
- Strategy management
- Comprehensive API coverage

### Bulk Operations Tests (`bulk_operations/`)
Тесты для массовых операций и параллельной обработки:
- Concurrent bot creation
- Bulk emergency operations
- Performance under load

### E2E Tests (`e2e/`)
Полноценные сценарии использования системы:
- Dashboard testing
- Bot lifecycle management
- UI integration testing

### FreqAI Tests (`freqai/`)
Тесты, специфичные для FreqAI функциональности:
- Model training and prediction
- FreqAI integration
- ML model validation

### Integration Tests (`integration/`)
Тесты взаимодействия между компонентами:
- Analytics and audit integration
- Command cycle testing
- FreqAI workflow integration

### Performance Tests (`performance/`)
Тесты производительности под нагрузкой:
- API throughput
- Response times
- Concurrent operations

### Service Tests (`services/`)
Тесты, специфичные для отдельных микросервисов:
- Backtesting server functionality
- Service-specific features

### Unit Tests (`unit/`)
Тестируют отдельные компоненты в изоляции:
- Individual services
- Business logic
- Utility functions
- Data validation

## Запуск тестов

### Все тесты
```bash
pytest
```

### С конкретным типом
```bash
# API tests
pytest tests/api/

# Bulk operations tests
pytest tests/bulk_operations/

# E2E tests
pytest tests/e2e/

# FreqAI tests
pytest tests/freqai/

# Integration tests
pytest tests/integration/

# Performance tests
pytest tests/performance/

# Service tests
pytest tests/services/

# Unit tests
pytest tests/unit/
```

### С конкретным тестом
```bash
pytest tests/unit/test_strategy_analysis_service.py
pytest tests/test_api.py::test_create_bot
```

### С дополнительными опциями
```bash
# С подробным выводом
pytest -v

# С покрытием кода
pytest --cov=management_server --cov-report=html

# Только неудачные тесты
pytest --lf

# С отладкой
pytest --pdb
```

## Конфигурация тестирования

### pytest.ini
```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    unit: Unit тесты
    integration: Интеграционные тесты
    e2e: End-to-end тесты
    slow: Медленные тесты
```

### conftest.py
Общие фикстуры:
- **test_app**: FastAPI тестовое приложение
- **test_client**: HTTP клиент для тестирования API
- **test_db**: Тестовая база данных
- **test_redis**: Redis для тестирования
- **auth_headers**: JWT токены для аутентификации

## Написание тестов

### Unit тест примера
```python
import pytest
from management_server.services.strategy_analysis_service import StrategyAnalysisService

class TestStrategyAnalysisService:
    def test_validate_strategy_success(self):
        service = StrategyAnalysisService()
        code = """
class MyStrategy(IStrategy):
    def populate_indicators(self, dataframe, metadata):
        return dataframe
"""
        result = service.validate_strategy(code)
        assert result["valid"] is True

    def test_validate_strategy_missing_class(self):
        service = StrategyAnalysisService()
        code = "print('Hello World')"
        result = service.validate_strategy(code)
        assert result["valid"] is False
        assert "IStrategy" in result["errors"]
```

### API тест примера
```python
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_create_bot(test_client: AsyncClient, auth_headers: dict):
    bot_data = {
        "name": "test_bot",
        "strategy_name": "MyStrategy",
        "exchange": "binance"
    }

    response = await test_client.post(
        "/api/v1/bots/",
        json=bot_data,
        headers=auth_headers
    )

    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "test_bot"
    assert data["status"] == "stopped"
```

## CI/CD интеграция

### GitHub Actions
```yaml
- name: Run tests
  run: |
    pytest --cov=management_server --cov-report=xml
- name: Upload coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./coverage.xml
```

### Pre-commit hooks
```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
        pass_filenames: false
        always_run: true
```

## Лучшие практики

### 1. Изоляция тестов
- Каждый тест должен быть независимым
- Использовать фикстуры для подготовки данных
- Очищать состояние после тестов

### 2. Названия тестов
- `test_should_create_bot_when_valid_data`
- `test_should_fail_when_invalid_strategy`
- Описывать ожидаемое поведение

### 3. Mocking
- Mock внешние зависимости (Redis, API calls)
- Использовать pytest-mock для моков
- Тестировать только логику компонента

### 4. Coverage
- Стремиться к 80%+ покрытия
- Исключать из покрытия:
  - `__init__.py` файлы
  - Конфигурационные файлы
  - Сгенерированный код

## Отладка тестов

### Логирование в тестах
```python
import logging

def test_with_logging(caplog):
    caplog.set_level(logging.DEBUG)
    # Ваш код теста
    assert "expected message" in caplog.text
```

### Отладка API тестов
```python
# Посмотреть ответ
print(response.json())

# Посмотреть запрос
print(response.request.headers)
print(response.request.body)
```

## Производительность

### Бенчмарки
```python
import pytest_benchmark

def test_api_performance(benchmark):
    def api_call():
        # Ваш API вызов
        pass

    benchmark(api_call)
```

### Load testing
```python
import asyncio
import aiohttp

async def test_concurrent_requests():
    async with aiohttp.ClientSession() as session:
        tasks = []
        for i in range(100):
            tasks.append(session.get("http://localhost:8002/api/v1/bots/"))
        results = await asyncio.gather(*tasks)
        assert all(r.status == 200 for r in results)
```