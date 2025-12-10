# Проектирование Системы Аудита и Аналитики

## 1. Введение

Этот документ описывает дизайн улучшенной системы для сбора, хранения и отображения данных аудита в проекте "Freqtrade Multi-Bot System".

## 2. Модель Данных (Database)

Существующая модель `AuditLog` будет расширена для хранения более детальной информации о каждом событии.

**Файл:** `management_server/models/models.py`

**Обновленная модель `AuditLog`:**
```python
class AuditLog(Base, TimestampMixin):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True) # Может быть Null для системных событий
    username = Column(String(50), nullable=True, index=True) # Дублируем для удобства запросов

    # --- Новые поля ---
    ip_address = Column(String(45), nullable=True) # Для IPv4 и IPv6
    http_method = Column(String(10), nullable=False, index=True)
    path = Column(String(255), nullable=False, index=True)
    status_code = Column(Integer, nullable=False, index=True)
    # --- Конец новых полей ---

    action = Column(String(100), nullable=False) # Краткое описание действия
    details = Column(JSON, nullable=True) # Тело запроса или другая полезная информация
```

## 3. Сбор Данных (Backend)

Сбор данных будет реализован через **FastAPI Middleware**. Это позволит автоматически логировать все запросы к API без необходимости изменять код каждого эндпоинта.

**Новый файл:** `management_server/middleware/audit_middleware.py`

**Логика Middleware:**
1. Перехватывает каждый входящий запрос (`request`).
2. Извлекает `ip_address`, `http_method`, `path`.
3. Извлекает информацию о пользователе из токена аутентификации.
4. Выполняет запрос, дожидаясь ответа (`response`).
5. Извлекает `status_code` из ответа.
6. Формирует запись `AuditLog`.
7. Асинхронно сохраняет запись в базу данных, чтобы не замедлять ответ пользователю.

## 4. API для доступа к логам

Будет создан новый роутер и эндпоинт для получения данных аудита.

**Новый файл:** `management_server/api/v1/audit.py`

**Эндпоинт:** `GET /api/v1/audit-logs/`

**Параметры запроса (Query Params):**
- `skip: int = 0`: Для пагинации.
- `limit: int = 100`: Для пагинации.
- `user_id: Optional[int] = None`: Для фильтрации по пользователю.
- `start_date: Optional[datetime] = None`: Для фильтрации по дате.
- `end_date: Optional[datetime] = None`: Для фильтрации по дате.
- `status_code: Optional[int] = None`: Для фильтрации по HTTP-статусу.

**Ответ:**
```json
{
  "total": 125,
  "logs": [
    {
      "id": 1,
      "timestamp": "2025-12-04T12:00:00Z",
      "username": "admin",
      "ip_address": "127.0.0.1",
      "http_method": "POST",
      "path": "/api/v1/bots/1/start",
      "status_code": 200,
      "action": "Start Bot"
    }
  ]
}
```

## 5. Пользовательский Интерфейс (Frontend)

Будет создана новая страница "Журнал аудита".

**Новый файл:** `freqtrade-ui/src/views/AuditLogView.vue`

**Ключевые компоненты:**
1.  **Таблица (PrimeVue DataTable):**
    - Колонки: `Timestamp`, `Пользователь`, `IP Адрес`, `Действие`, `Метод`, `Путь`, `Статус`.
    - Сортировка по колонкам.
2.  **Панель фильтров:**
    - Выпадающий список для выбора пользователя.
    - Поле для ввода текста для поиска по `Действию` или `Пути`.
    - Календарь для выбора диапазона дат.
3.  **Пагинация (PrimeVue Paginator):** Для навигации по большому объему логов.

**Хранилище состояния (Pinia):**
- **Новый файл:** `freqtrade-ui/src/stores/audit.ts`.
- Будет содержать `state` для хранения логов и `actions` для асинхронной загрузки данных с бэкенда с учетом фильтров и пагинации.

**Роутинг:**
- Будет добавлен новый маршрут в `freqtrade-ui/src/router/index.ts`.
- Будет добавлена ссылка в главное меню навигации в `App.vue`.
