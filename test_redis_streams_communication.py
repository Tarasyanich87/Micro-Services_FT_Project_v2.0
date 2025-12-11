#!/usr/bin/env python3
"""
Test Redis Streams межсервисной коммуникации
Проверяет реализацию функционала из заметки Redis_Streams_Microservices_Communication.md
"""

import asyncio
import json
import redis.asyncio as redis
import time
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RedisStreamsTester:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis = None

    async def connect(self):
        """Подключение к Redis"""
        try:
            self.redis = redis.from_url(self.redis_url)
            await self.redis.ping()
            logger.info("✅ Подключение к Redis успешно")
            return True
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Redis: {e}")
            return False

    async def test_basic_streams_operations(self):
        """Тест базовых операций с Redis Streams"""
        logger.info("🧪 Тестирование базовых операций Redis Streams...")

        test_stream = "test:basic:operations"
        test_group = "test_consumers"

        try:
            # Очистка предыдущих данных
            await self.redis.delete(test_stream)

            # Тест XADD - добавление сообщения
            message_id = await self.redis.xadd(
                test_stream,
                {
                    "type": "test_message",
                    "data": json.dumps({"test": "data"}),
                    "timestamp": str(time.time()),
                },
            )
            logger.info(
                f"✅ Сообщение добавлено в stream {test_stream}, ID: {message_id}"
            )

            # Тест XREAD - чтение сообщений
            messages = await self.redis.xread({test_stream: "0"}, count=1, block=1000)
            if messages:
                stream_name, message_list = messages[0]
                msg_id, msg_data = message_list[0]
                logger.info(
                    f"✅ Сообщение прочитано из stream {stream_name}: {msg_data}"
                )
            else:
                logger.error("❌ Не удалось прочитать сообщение")
                return False

            # Тест Consumer Groups
            try:
                await self.redis.xgroup_create(
                    test_stream, test_group, "0", mkstream=True
                )
                logger.info(
                    f"✅ Consumer group '{test_group}' создан для stream '{test_stream}'"
                )
            except redis.ResponseError as e:
                if "BUSYGROUP" in str(e):
                    logger.info(f"ℹ️ Consumer group '{test_group}' уже существует")
                else:
                    raise

            # Тест XREADGROUP - чтение через consumer group
            consumer_messages = await self.redis.xreadgroup(
                test_group, "test_consumer_1", {test_stream: ">"}, count=1, block=1000
            )

            if consumer_messages:
                stream_name, message_list = consumer_messages[0]
                msg_id, msg_data = message_list[0]

                # Подтверждение обработки
                await self.redis.xack(test_stream, test_group, msg_id)
                logger.info(f"✅ Сообщение обработано через consumer group: {msg_data}")
            else:
                logger.warning("⚠️ Нет новых сообщений для consumer group")

            # Очистка тестовых данных
            await self.redis.delete(test_stream)
            logger.info("🧹 Тестовые данные очищены")

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка в базовых операциях: {e}")
            return False

    async def test_namespacing_strategy(self):
        """Тест namespacing стратегии из заметки"""
        logger.info("🧪 Тестирование namespacing стратегии...")

        # Проверяем streams из заметки
        expected_streams = [
            "mgmt:backtesting:commands",
            "backtesting:mgmt:results",
            "backtesting:status",
        ]

        try:
            # Проверяем информацию о streams
            for stream_name in expected_streams:
                try:
                    info = await self.redis.xinfo_stream(stream_name)
                    length = info.get("length", 0)
                    groups = info.get("groups", 0)
                    logger.info(
                        f"✅ Stream '{stream_name}': {length} сообщений, {groups} групп"
                    )
                except redis.ResponseError:
                    logger.info(f"ℹ️ Stream '{stream_name}' еще не создан")

            # Создаем тестовые consumer groups для backtesting
            stream_groups = [
                ("mgmt:backtesting:commands", "backtesting_workers"),
                ("backtesting:mgmt:results", "management_consumers"),
                ("backtesting:status", "monitoring_consumers"),
            ]

            for stream_name, group_name in stream_groups:
                try:
                    await self.redis.xgroup_create(
                        stream_name, group_name, "0", mkstream=True
                    )
                    logger.info(
                        f"✅ Consumer group '{group_name}' готов для stream '{stream_name}'"
                    )
                except redis.ResponseError as e:
                    if "BUSYGROUP" in str(e):
                        logger.info(
                            f"ℹ️ Consumer group '{group_name}' уже существует для '{stream_name}'"
                        )
                    else:
                        logger.warning(f"⚠️ Ошибка создания consumer group: {e}")

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка в тестировании namespacing: {e}")
            return False

    async def test_inter_service_communication(self):
        """Тест межсервисной коммуникации"""
        logger.info("🧪 Тестирование межсервисной коммуникации...")

        try:
            # Имитация команды от Management к Backtesting
            command_stream = "mgmt:backtesting:commands"
            result_stream = "backtesting:mgmt:results"

            # Отправляем тестовую команду
            command_data = {
                "type": "backtest",
                "data": json.dumps(
                    {
                        "strategy_name": "TestStrategy",
                        "timerange": "20240101-20241201",
                        "task_id": f"test_{int(time.time())}",
                    }
                ),
                "timestamp": str(time.time()),
                "source": "management_server",
            }

            message_id = await self.redis.xadd(command_stream, command_data)
            logger.info(f"✅ Команда отправлена в {command_stream} (ID: {message_id})")

            # Имитируем ответ от Backtesting
            result_data = {
                "task_id": json.loads(command_data["data"])["task_id"],
                "status": "completed",
                "result": json.dumps(
                    {
                        "total_trades": 150,
                        "win_rate": 65.5,
                        "profit": 12.3,
                        "max_drawdown": 8.7,
                    }
                ),
                "timestamp": str(time.time()),
                "source": "backtesting_server",
            }

            result_id = await self.redis.xadd(result_stream, result_data)
            logger.info(f"✅ Результат отправлен в {result_stream} (ID: {result_id})")

            # Проверяем consumer groups
            pending = await self.redis.xpending(command_stream, "backtesting_workers")
            logger.info(
                f"ℹ️ Pending messages in {command_stream}: {pending.get('pending', 0)}"
            )

            pending_results = await self.redis.xpending(
                result_stream, "management_consumers"
            )
            logger.info(
                f"ℹ️ Pending results in {result_stream}: {pending_results.get('pending', 0)}"
            )

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка в межсервисной коммуникации: {e}")
            return False

    async def test_error_handling_and_retry(self):
        """Тест обработки ошибок и retry логики"""
        logger.info("🧪 Тестирование обработки ошибок и retry...")

        try:
            # Создаем dead letter queue
            dead_letter_stream = "mgmt:backtesting:commands:dead"

            # Имитируем failed message
            failed_message = {
                "type": "backtest",
                "data": json.dumps({"strategy_name": "FailedStrategy"}),
                "timestamp": str(time.time()),
                "source": "management_server",
                "retry_count": "2",
                "error": "processing_failed",
            }

            dlq_id = await self.redis.xadd(dead_letter_stream, failed_message)
            logger.info(
                f"✅ Failed message перемещен в dead letter queue (ID: {dlq_id})"
            )

            # Проверяем dead letter queue
            dlq_info = await self.redis.xinfo_stream(dead_letter_stream)
            logger.info(
                f"ℹ️ Dead letter queue содержит {dlq_info.get('length', 0)} сообщений"
            )

            return True

        except Exception as e:
            logger.error(f"❌ Ошибка в тестировании error handling: {e}")
            return False

    async def run_all_tests(self):
        """Запуск всех тестов"""
        logger.info("🚀 Запуск комплексного тестирования Redis Streams...")

        tests = [
            ("Подключение к Redis", self.connect),
            ("Базовые операции Streams", self.test_basic_streams_operations),
            ("Namespacing стратегия", self.test_namespacing_strategy),
            ("Межсервисная коммуникация", self.test_inter_service_communication),
            ("Обработка ошибок", self.test_error_handling_and_retry),
        ]

        results = []
        for test_name, test_func in tests:
            logger.info(f"\n{'=' * 60}")
            logger.info(f"Выполнение: {test_name}")
            logger.info("=" * 60)

            try:
                result = await test_func()
                results.append((test_name, result))
                if result:
                    logger.info(f"✅ {test_name} - ПРОЙДЕН")
                else:
                    logger.error(f"❌ {test_name} - ПРОВАЛЕН")
            except Exception as e:
                logger.error(f"❌ {test_name} - ОШИБКА: {e}")
                results.append((test_name, False))

        # Итоговый отчет
        logger.info(f"\n{'=' * 60}")
        logger.info("📊 ИТОГОВЫЙ ОТЧЕТ ТЕСТИРОВАНИЯ")
        logger.info("=" * 60)

        passed = 0
        total = len(results)

        for test_name, result in results:
            status = "✅ ПРОЙДЕН" if result else "❌ ПРОВАЛЕН"
            logger.info(f"{status}: {test_name}")
            if result:
                passed += 1

        logger.info("=" * 60)
        logger.info(f"РЕЗУЛЬТАТ: {passed}/{total} тестов пройдено")

        if passed == total:
            logger.info("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Redis Streams работают корректно.")
        else:
            logger.warning(
                f"⚠️ {total - passed} тест(ов) провалено. Требуется доработка."
            )

        return passed == total


async def main():
    """Главная функция"""
    tester = RedisStreamsTester()

    try:
        success = await tester.run_all_tests()
        return 0 if success else 1
    except KeyboardInterrupt:
        logger.info("🛑 Тестирование прервано пользователем")
        return 1
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        return 1
    finally:
        if tester.redis:
            await tester.redis.close()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
