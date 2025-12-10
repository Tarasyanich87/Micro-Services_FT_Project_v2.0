# Alembic - Миграции базы данных

Alembic используется для управления миграциями базы данных в Freqtrade Multi-Bot System.

## Что такое Alembic?

Alembic - это легковесный инструмент для миграций баз данных для Python, который предоставляет:

- **Отслеживание изменений схемы** - автоматическое обнаружение изменений в моделях
- **Версионирование** - каждая миграция имеет уникальную версию
- **Downgrade/Upgrade** - возможность откатывать и применять миграции
- **Многосервеная поддержка** - работает с PostgreSQL, MySQL, SQLite и др.

## Структура

```
alembic/
├── versions/              # Файлы миграций
│   └── *.py             # Индивидуальные миграции
├── env.py               # Конфигурация Alembic
├── script.py.mako       # Шаблон для генерации миграций
└── README.md            # Эта документация
```

## Основные команды

### Инициализация (уже выполнено)
```bash
alembic init alembic
```

### Создание новой миграции
```bash
# Автоматическое обнаружение изменений
alembic revision --autogenerate -m "Add new table"

# Пустая миграция для ручного написания
alembic revision -m "Custom migration"
```

### Применение миграций
```bash
# Применить все новые миграции
alembic upgrade head

# Применить до конкретной версии
alembic upgrade <revision_id>

# Применить на один шаг вперед
alembic upgrade +1
```

### Откат миграций
```bash
# Откатить на одну миграцию назад
alembic downgrade -1

# Откатить до конкретной версии
alembic downgrade <revision_id>

# Откатить до начального состояния
alembic downgrade base
```

### Просмотр статуса
```bash
# Текущая версия и статус
alembic current

# История миграций
alembic history

# Список всех доступных команд
alembic --help
```

## Рабочий процесс

### 1. Изменение моделей
```python
# management_server/models/models.py
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)  # Новое поле
```

### 2. Генерация миграции
```bash
alembic revision --autogenerate -m "Add email field to users table"
```

### 3. Проверка и корректировка
```python
# alembic/versions/xxxx_add_email_field.py
def upgrade():
    op.add_column('users', sa.Column('email', sa.String(), nullable=True))
    op.create_unique_constraint(None, 'users', ['email'])

def downgrade():
    op.drop_constraint(None, 'users', ['email'], type_='unique')
    op.drop_column('users', 'email')
```

### 4. Применение
```bash
alembic upgrade head
```

## Конфигурация

### alembic.ini
```ini
[alembic]
script_location = alembic
sqlalchemy.url = sqlite+aiosqlite:///./freqtrade.db

[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic
```

### env.py
```python
from management_server.models.base import Base
from management_server.core.config import settings

# Настройка подключения к БД
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("sqlite+aiosqlite", "sqlite"))

# Импорт всех моделей для autogenerate
from management_server.models.models import *
target_metadata = Base.metadata
```

## Типы миграций

### Автоматические (autogenerate)
```bash
alembic revision --autogenerate -m "Auto-generated migration"
```
- Alembic анализирует модели и генерирует SQL
- Подходит для простых изменений (добавление полей, таблиц)
- Требует проверки сгенерированного кода

### Ручные миграции
```bash
alembic revision -m "Manual migration"
```
- Полный контроль над SQL
- Для сложных изменений (переименование, data migration)
- Требует знания SQLAlchemy operations

## Операции с данными

### Добавление данных
```python
def upgrade():
    # Вставка начальных данных
    op.bulk_insert(users_table,
        [
            {'username': 'admin', 'email': 'admin@example.com'},
            {'username': 'user', 'email': 'user@example.com'},
        ]
    )

def downgrade():
    op.execute("DELETE FROM users WHERE username IN ('admin', 'user')")
```

### Миграция данных
```python
def upgrade():
    # Перенос данных из старого формата в новый
    connection = op.get_bind()

    # Получить все записи
    users = connection.execute(sa.text("SELECT id, old_field FROM users")).fetchall()

    for user in users:
        # Преобразовать данные
        new_value = transform_old_field(user.old_field)
        connection.execute(
            sa.text("UPDATE users SET new_field = :new_val WHERE id = :id"),
            {"new_val": new_value, "id": user.id}
        )

    # Удалить старую колонку
    op.drop_column('users', 'old_field')
```

## Лучшие практики

### 1. Тестирование миграций
```bash
# Создать тестовую БД
alembic upgrade head

# Протестировать downgrade
alembic downgrade -1
alembic upgrade +1
```

### 2. Резервное копирование
```bash
# Всегда делайте бэкап перед миграциями
cp freqtrade.db freqtrade.db.backup
```

### 3. Маленькие миграции
- Одна миграция = одно логическое изменение
- Не смешивайте schema и data changes
- Используйте описательные сообщения

### 4. Код ревью
- Все миграции должны проверяться
- Тестировать upgrade/downgrade
- Документировать сложные изменения

## Troubleshooting

### Проблема: "Target database is not up to date"
```bash
# Проверить статус
alembic current

# Применить все миграции
alembic upgrade head
```

### Проблема: Конфликт миграций
```bash
# Посмотреть историю
alembic history

# Откатить проблемную миграцию
alembic downgrade <revision_id>

# Создать новую миграцию
alembic revision --autogenerate -m "Fix conflict"
```

### Проблема: Autogenerate не видит изменения
```python
# В env.py убедитесь, что все модели импортированы
from management_server.models import *
```

### Проблема: Ошибка в миграции
```bash
# Откатить проблемную миграцию
alembic downgrade -1

# Исправить код миграции
# Повторно применить
alembic upgrade +1
```

## Интеграция с CI/CD

### Pre-commit hook
```bash
#!/bin/bash
# Проверка, что миграции актуальны
alembic current
if [ $? -ne 0 ]; then
    echo "Database migrations are not up to date"
    exit 1
fi
```

### GitHub Actions
```yaml
- name: Check migrations
  run: |
    alembic current
    alembic check  # Проверяет, что autogenerate не создаст новых миграций
```

## Полезные команды

```bash
# Показать текущую версию
alembic current

# Показать историю миграций
alembic history --verbose

# Показать SQL для миграции без применения
alembic upgrade <revision> --sql

# Создать миграцию с конкретными изменениями
alembic revision -m "Add index on username"

# Проверить, что нет новых изменений
alembic check
```

## Ресурсы

- [Официальная документация Alembic](https://alembic.sqlalchemy.org/)
- [SQLAlchemy Operations](https://alembic.sqlalchemy.org/en/latest/ops.html)
- [Alembic Tutorials](https://alembic.sqlalchemy.org/en/latest/tutorial.html)