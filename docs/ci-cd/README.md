# CI/CD Pipeline

Freqtrade Multi-Bot System использует GitHub Actions для автоматизированного тестирования, сборки и развертывания.

## Обзор Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  Code Push  │ -> │   Lint &    │ -> │ Unit Tests  │ -> │Integration  │
│   / PR       │    │   Format    │    │             │    │   Tests     │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   │                   │
       v                   v                   v                   v
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│Performance  │ -> │  Docker     │ -> │  Security   │ -> │   Deploy    │
│   Tests     │    │   Build     │    │   Scan      │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## Стадии Pipeline

### 1. Code Quality (lint-and-format)
**Цель:** Проверка качества кода перед тестированием

**Инструменты:**
- **Black**: Форматирование Python кода
- **isort**: Сортировка импортов
- **flake8**: Линтинг и проверка стиля
- **mypy**: Статическая типизация

**Команды:**
```bash
black --check --diff .
isort --check-only --diff .
flake8 . --count --select=E9,F63,F7,F82
mypy management_server trading_gateway --ignore-missing-imports
```

### 2. Unit Tests (unit-tests)
**Цель:** Тестирование отдельных компонентов

**Особенности:**
- Запуск Redis в контейнере
- Измерение покрытия кода
- Отправка результатов в Codecov

**Ключевые метрики:**
- Coverage: >80% для основных компонентов
- Test execution time: <5 минут
- No flaky tests

### 3. Integration Tests (integration-tests)
**Цель:** Тестирование взаимодействия компонентов

**Особенности:**
- Запуск всех сервисов в фоне
- Тестирование Redis Streams коммуникации
- API endpoint testing с реальной БД

**Тесты:**
- Command cycle: API → Redis → Processing
- Database operations
- Service health checks

### 4. Performance Tests (performance-tests)
**Цель:** Измерение производительности под нагрузкой

**Метрики:**
- API response times (<100ms для health)
- Concurrent user load (10+ users)
- Memory usage (<50MB increase)
- Database query performance

### 5. Docker Build (docker-build)
**Цель:** Сборка production-ready контейнеров

**Особенности:**
- Multi-stage builds для оптимизации размера
- Security scanning с Trivy
- Tagging по Git SHA и latest

### 6. Security Scan (security-scan)
**Цель:** Поиск уязвимостей в зависимостях

**Инструменты:**
- **Trivy**: Сканирование контейнеров и зависимостей
- **SARIF reports**: Интеграция с GitHub Security tab

### 7. Deploy (deploy-staging/production)
**Цель:** Автоматическое развертывание

**Условия:**
- **Staging**: На develop branch
- **Production**: На main branch

## Конфигурация GitHub Actions

### Основной workflow (.github/workflows/ci-cd.yml)

```yaml
name: Freqtrade Multi-Bot CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  lint-and-format:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install black isort flake8 mypy
      - run: black --check --diff .
      - run: isort --check-only --diff .
      - run: flake8 . --count --select=E9,F63,F7,F82
      - run: mypy management_server trading_gateway --ignore-missing-imports
```

### Переменные окружения

```yaml
env:
  PYTHON_VERSION: '3.11'
  REDIS_URL: redis://localhost:6379
  DATABASE_URL: sqlite+aiosqlite:///./test.db
```

### Secrets

```yaml
secrets:
  DOCKERHUB_USERNAME: ${{ secrets.DOCKERHUB_USERNAME }}
  DOCKERHUB_TOKEN: ${{ secrets.DOCKERHUB_TOKEN }}
```

## Локальная разработка с CI/CD

### Pre-commit hooks
```bash
pip install pre-commit
pre-commit install

# Запуск всех проверок
pre-commit run --all-files
```

### Makefile для локального CI
```makefile
.PHONY: lint format test clean

lint:
    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

format:
    black .
    isort .

test:
    pytest --cov=. --cov-report=html

clean:
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -delete
    rm -rf .pytest_cache htmlcov
```

## Мониторинг Pipeline

### GitHub Actions Dashboard
- **Workflow runs**: История запусков
- **Job status**: Статус каждого этапа
- **Artifacts**: Coverage reports, test results
- **Security alerts**: Trivy findings

### Metrics и KPIs

**Code Quality:**
- Code coverage: >80%
- Cyclomatic complexity: <10
- Duplication: <5%

**Performance:**
- Pipeline execution time: <15 минут
- Test execution time: <5 минут
- Build time: <10 минут

**Reliability:**
- Success rate: >95%
- Mean time to failure: >24 часа
- False positive rate: <5%

## Troubleshooting

### Pipeline fails

**Linting errors:**
```bash
# Локальная проверка
black --check --diff .
isort --check-only --diff .

# Автоматическое исправление
black .
isort .
```

**Test failures:**
```bash
# Запуск конкретного теста
pytest tests/unit/test_bot_service.py::TestBotService::test_create_bot_success -v

# С отладкой
pytest --pdb --tb=long
```

**Coverage issues:**
```bash
# Проверка покрытия
pytest --cov=management_server --cov-report=html
# Отчет в htmlcov/index.html
```

### Docker build fails

**Size optimization:**
```dockerfile
# Multi-stage build
FROM python:3.11-slim as builder
# Build dependencies

FROM python:3.11-slim as runtime
# Copy only runtime dependencies
```

**Security issues:**
```bash
# Локальное сканирование
trivy image freqtrade-management-server:latest
```

### Deployment issues

**Environment differences:**
- Проверить переменные окружения
- Проверить connectivity между сервисами
- Проверить permissions

**Rollback strategy:**
```bash
# Rollback to previous version
kubectl rollout undo deployment/management-server
```

## Best Practices

### 1. Fast Feedback
- Lint и format в начале pipeline
- Fail fast на critical issues
- Parallel execution где возможно

### 2. Security First
- Dependency scanning на каждом PR
- Secrets management
- Image signing

### 3. Observability
- Detailed logging
- Metrics collection
- Alerting on failures

### 4. Incremental Changes
- Small, focused commits
- Feature flags для gradual rollouts
- Blue-green deployments

## Расширение Pipeline

### Добавление нового сервиса
```yaml
docker-build:
  steps:
    - name: Build New Service
      uses: docker/build-push-action@v5
      with:
        context: ./new_service
        tags: freqtrade-new-service:${{ github.sha }}
```

### Добавление нового тестового типа
```yaml
load-tests:
  runs-on: ubuntu-latest
  steps:
    - name: Run Load Tests
      run: |
        npm install -g artillery
        artillery run load-test.yml
```

### Интеграция с внешними инструментами
```yaml
- name: Send to Slack
  if: failure()
  run: |
    curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"Pipeline failed!"}' \
    ${{ secrets.SLACK_WEBHOOK }}
```

## Production Deployment

### Kubernetes Manifests
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: management-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: management-server
  template:
    spec:
      containers:
      - name: management-server
        image: freqtrade-management-server:latest
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
```

### Helm Charts
```yaml
# Chart.yaml
apiVersion: v2
name: freqtrade-multi-bot
version: 1.0.0

# values.yaml
managementServer:
  image: freqtrade-management-server:latest
  replicas: 3

tradingGateway:
  image: freqtrade-trading-gateway:latest
  replicas: 2
```

## Заключение

CI/CD pipeline обеспечивает:
- **Quality Gates**: Автоматическая проверка качества кода
- **Fast Feedback**: Быстрое обнаружение проблем
- **Reliable Deployments**: Автоматизированное развертывание
- **Security**: Постоянный мониторинг уязвимостей
- **Scalability**: Легкое добавление новых этапов и сервисов

Pipeline готов к production и может быть легко расширен для новых требований.