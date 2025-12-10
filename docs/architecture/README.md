# Архитектура системы

Этот раздел содержит документацию по архитектуре Freqtrade Multi-Bot System.

## Документы

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Общая архитектура системы, компоненты и принципы взаимодействия
- **[MCP_PROTOCOL.md](./MCP_PROTOCOL.md)** - Спецификация Machine Control Protocol для управления ботами
- **[AUDIT_SYSTEM_DESIGN.md](./AUDIT_SYSTEM_DESIGN.md)** - Дизайн системы аудита и логирования

## Ключевые компоненты

### Management Server
Основной API сервер для управления ботами, стратегиями и аналитики.

### Trading Gateway
Сервис для прямого управления процессами Freqtrade ботов.

### Redis Streams
Система очередей для надежной коммуникации между сервисами.

### PostgreSQL/SQLite
База данных для хранения конфигураций, результатов и метрик.