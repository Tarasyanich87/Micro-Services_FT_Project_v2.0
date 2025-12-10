# Тестирование системы

Freqtrade Multi-Bot System имеет комплексную систему тестирования, обеспечивающую качество и надежность кода.

## Архитектура тестирования

```
tests/
├── conftest.py           # Общие фикстуры и настройки
├── test_api.py          # REST API тесты
├── unit/                # Unit тесты
│   ├── test_bot_service.py
│   ├── test_trading_gateway.py
│   └── test_strategy_analysis_service.py
├── integration/         # Integration тесты
│   └── test_command_cycle.py
├── e2e/                 # End-to-end тесты
│   └── test_bot_lifecycle.py
└── performance/         # Performance тесты
    └── test_api_performance.py
```

## Типы тестов

### 🔍 Unit Tests
**Цель:** Тестирование отдельных компонентов в изоляции
- **Framework:** pytest
- **Coverage:** 80%+ для critical paths
- **Mocking:** unittest.mock для внешних зависимостей

**Примеры:**
- BotService CRUD операции
- Strategy validation
- Trading Gateway command processing

### 🔗 Integration Tests
**Цель:** Тестирование взаимодействия между компонентами
- **Services:** Redis, Database, API
- **Communication:** HTTP, WebSocket, Redis Streams
- **Real dependencies:** Минимальный mocking

**Примеры:**
- API endpoints с реальной БД
- Redis Streams event processing
- Command cycle: API → Redis → Processing

### 🌐 E2E Tests
**Цель:** Тестирование полных пользовательских сценариев
- **Full stack:** Frontend → API → Database → External services
- **Real environment:** Все сервисы запущены
- **User workflows:** Registration → Bot creation → Trading

**Примеры:**
- Complete bot lifecycle
- Concurrent operations
- Error handling and recovery

### ⚡ Performance Tests
**Цель:** Измерение производительности под нагрузкой
- **Metrics:** Response time, throughput, memory usage
- **Load testing:** Concurrent users, sustained load
- **Benchmarks:** API performance, database queries

**Примеры:**
- API response times (<100ms for health, <500ms for operations)
- Concurrent user load (10+ simultaneous users)
- Memory usage under load (<50MB increase)

## Запуск тестов

### Все тесты
```bash
pytest
```

### По типам
```bash
pytest tests/unit/          # Unit тесты
pytest tests/integration/   # Integration тесты
pytest tests/e2e/           # E2E тесты
pytest tests/performance/   # Performance тесты
```

### С опциями
```bash
pytest -v                    # Verbose output
pytest --cov=. --cov-report=html  # Coverage report
pytest --lf                  # Run only failed tests
pytest -k "test_bot"         # Run tests matching pattern
pytest --durations=10        # Show slowest tests
```

## Code Coverage

### Требования
- **Unit tests:** 80%+ coverage
- **Integration tests:** 70%+ coverage
- **Critical paths:** 90%+ coverage

### Измерение
```bash
pytest --cov=management_server --cov=trading_gateway --cov-report=html
# Отчет в htmlcov/index.html
```

### Исключения из покрытия
```ini
# .coveragerc
[run]
omit =
    */tests/*
    */venv/*
    */migrations/*
    */__pycache__/*
```

## Test Fixtures

### conftest.py
```python
@pytest.fixture
async def app_client():
    """FastAPI test client"""
    from httpx import AsyncClient
    # Setup test client

@pytest.fixture
async def auth_headers(app_client):
    """JWT authentication headers"""
    # Login and return headers

@pytest.fixture
async def test_user(app_client):
    """Create test user"""
    # Register and return user data
```

### Database fixtures
```python
@pytest.fixture(autouse=True)
async def setup_test_database():
    """Clean database before each test"""
    # Setup test DB
    yield
    # Cleanup after test
```

## Best Practices

### 1. Test Organization
```python
class TestBotService:
    """Test cases for BotService"""

    @pytest.mark.asyncio
    async def test_create_bot_success(self, service):
        # Arrange
        # Act
        # Assert
```

### 2. Naming Conventions
- `test_should_create_bot_when_valid_data`
- `test_should_fail_when_invalid_strategy`
- `test_performance_under_concurrent_load`

### 3. Assertions
```python
# Good
assert result.status_code == 201
assert "bot_id" in result.json()

# Better
assert result.status_code == HTTPStatus.CREATED
assert result.json()["name"] == expected_name
```

### 4. Mocking Strategy
```python
# Mock external dependencies
with patch('redis.Redis') as mock_redis:
    mock_redis.return_value.ping.return_value = True
    # Test code
```

## CI/CD Integration

### GitHub Actions
```yaml
- name: Run tests
  run: |
    pytest --cov=. --cov-report=xml
- name: Upload coverage
  uses: codecov/codecov-action@v3
```

### Pre-commit Hooks
```yaml
repos:
  - repo: local
    hooks:
      - id: pytest
        name: pytest
        entry: pytest
        language: system
```

## Performance Benchmarks

### API Response Times
- **Health check:** <100ms
- **Bot list:** <200ms
- **Bot create:** <500ms
- **Bot start/stop:** <300ms

### Concurrent Load
- **10 users:** <1s average response
- **50 users:** <2s average response
- **Memory increase:** <50MB

### Database Queries
- **Simple select:** <50ms
- **Complex query:** <200ms
- **Bulk operations:** <1000ms

## Debugging Tests

### Verbose Output
```bash
pytest -v -s --tb=long
```

### PDB Debugging
```python
import pdb; pdb.set_trace()
```

### Logging in Tests
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Test Data Management

### Factory Pattern
```python
def create_test_bot(**overrides):
    defaults = {
        "name": "test_bot",
        "strategy_name": "TestStrategy",
        "exchange": "binance"
    }
    return {**defaults, **overrides}
```

### Cleanup Strategy
```python
@pytest.fixture(autouse=True)
async def cleanup():
    yield
    # Cleanup test data
    await db.execute("DELETE FROM bots WHERE name LIKE 'test_%'")
```

## Continuous Testing

### Test-Driven Development
1. Write failing test
2. Implement feature
3. Test passes
4. Refactor
5. Test still passes

### Regression Testing
- Run full test suite before releases
- Automated nightly runs
- Performance regression detection

## Troubleshooting

### Common Issues

**Tests fail randomly:**
- Race conditions in async code
- Database state not cleaned properly
- External service dependencies

**Slow tests:**
- Too many database operations
- Inefficient queries
- Heavy mocking

**Flaky tests:**
- Time-dependent logic
- Network timeouts
- Resource contention

### Solutions

**For async issues:**
```python
@pytest.mark.asyncio
async def test_async_function():
    await asyncio.sleep(0.1)  # Allow async operations
```

**For database cleanup:**
```python
@pytest.fixture(autouse=True)
async def clean_db(db_session):
    await db_session.execute("TRUNCATE TABLE bots CASCADE")
    await db_session.commit()
```

**For performance:**
```python
@pytest.mark.slow
def test_slow_operation():
    # Mark slow tests
    pass
```