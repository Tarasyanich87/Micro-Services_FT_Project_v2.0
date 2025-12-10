# Локальная Разработка

В этом документе описаны шаги для настройки и запуска проекта "Freqtrade Multi-Bot System" на локальной машине.

## 1. Требования

- Python 3.11+
- Node.js 18+
- `uv` (быстрый менеджер пакетов Python)
- Redis

## 2. Установка

### 2.1. Клонирование репозитория
```bash
git clone <repository-url>
cd freqtrade-multibot-system
```

### 2.2. Настройка Backend (`management_server` и `trading_gateway`)

1.  **Создание и активация виртуального окружения:**
    ```bash
    uv venv
    source .venv/bin/activate
    ```

2.  **Установка Python зависимостей:**
    ```bash
    uv pip install -r requirements.txt
    uv pip install -r requirements-dev.txt
    ```

3.  **Установка пакетов проекта в режиме редактирования:**
    Это необходимо для корректной работы импортов между `management_server` и `trading_gateway`.
    ```bash
    uv pip install -e .
    ```

### 2.3. Настройка Frontend (`freqtrade-ui`)

1.  **Перейдите в каталог `freqtrade-ui`:**
    ```bash
    cd freqtrade-ui
    ```

2.  **Установка Node.js зависимостей:**
    ```bash
    npm install
    ```
3.  **Вернитесь в корневой каталог:**
    ```bash
    cd ..
    ```

## 3. Запуск

Для полноценной работы системы необходимо запустить Redis, оба backend-сервиса и frontend.

### 3.1. Запуск Redis
Откройте новый терминал и запустите сервер Redis.
```bash
redis-server &
```

### 3.2. Запуск Backend

1.  **Терминал 1: Запуск `management_server`**
    ```bash
    uvicorn management_server.main:app --host 0.0.0.0 --port 8000 --reload
    ```
    API будет доступен по адресу `http://localhost:8000`.

2.  **Терминал 2: Запуск `trading_gateway`**
    ```bash
    uvicorn trading_gateway.main:app --host 0.0.0.0 --port 8001 --reload
    ```
    API будет доступен по адресу `http://localhost:8001`.

### 3.3. Запуск Frontend

1.  **Терминал 3: Запуск `freqtrade-ui`**
    ```bash
    cd freqtrade-ui
    npm run dev
    ```
    Веб-интерфейс будет доступен по адресу, указанному в выводе команды (обычно `http://localhost:5173`).
