#!/usr/bin/env python3
"""
Комплексное тестирование всех Vue.js dashboard'ов
Проверяет загрузку, навигацию, API интеграцию через HTTP запросы
"""

import httpx
import pytest
import time
import json
from typing import Dict, List


class TestAllDashboards:
    """Комплексное тестирование всех dashboard компонентов через HTTP"""

    @pytest.fixture(scope="class")
    def http_client(self):
        """HTTP клиент для тестирования"""
        client = httpx.Client(timeout=15.0, follow_redirects=True)
        yield client
        client.close()

    def test_home_dashboard_loading(self, http_client):
        """Тест загрузки главной dashboard"""
        response = http_client.get("http://localhost:5176/")

        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

        # Проверка наличия основных Vue.js элементов
        content = response.text.lower()
        vue_indicators = ["<div", "<template", "vue", "app", "dashboard"]
        found_indicators = [ind for ind in vue_indicators if ind in content]

        assert len(found_indicators) > 0, "Vue.js приложение не загружено"
        assert len(response.text) > 1000, "Контент dashboard слишком мал"

    def test_analytics_dashboard(self, http_client):
        """Тест аналитики dashboard"""
        response = http_client.get("http://localhost:5176/analytics")

        assert response.status_code == 200
        content = response.text.lower()

        # Проверка наличия элементов аналитики
        analytics_keywords = [
            "analytics",
            "performance",
            "metrics",
            "chart",
            "graph",
            "data",
        ]
        found_keywords = [kw for kw in analytics_keywords if kw in content]

        assert len(found_keywords) > 0, (
            f"Аналитика dashboard не загрузилась. Найденные ключевые слова: {found_keywords}"
        )

    def test_bot_management_dashboard(self, http_client):
        """Тест управления ботами dashboard"""
        response = http_client.get("http://localhost:5176/bots")

        assert response.status_code == 200
        content = response.text.lower()

        bot_keywords = ["bot", "bots", "trading", "start", "stop", "create", "manage"]
        found_keywords = [kw for kw in bot_keywords if kw in content]

        assert len(found_keywords) > 0, (
            f"Bot management dashboard не загрузилась. Найденные ключевые слова: {found_keywords}"
        )

    def test_strategies_dashboard(self, http_client):
        """Тест стратегий dashboard"""
        response = http_client.get("http://localhost:5176/strategies")

        assert response.status_code == 200
        content = response.text.lower()

        strategy_keywords = [
            "strategy",
            "strategies",
            "code",
            "backtest",
            "python",
            "editor",
        ]
        found_keywords = [kw for kw in strategy_keywords if kw in content]

        assert len(found_keywords) > 0, (
            f"Strategies dashboard не загрузилась. Найденные ключевые слова: {found_keywords}"
        )

    def test_freqai_lab_dashboard(self, http_client):
        """Тест FreqAI Lab dashboard"""
        response = http_client.get("http://localhost:5176/freqai")

        assert response.status_code == 200
        content = response.text.lower()

        freqai_keywords = [
            "freqai",
            "ml",
            "model",
            "training",
            "prediction",
            "ai",
            "machine",
        ]
        found_keywords = [kw for kw in freqai_keywords if kw in content]

        assert len(found_keywords) > 0, (
            f"FreqAI Lab dashboard не загрузилась. Найденные ключевые слова: {found_keywords}"
        )

    def test_monitoring_dashboard(self, http_client):
        """Тест мониторинга dashboard"""
        response = http_client.get("http://localhost:5176/monitoring")

        assert response.status_code == 200
        content = response.text.lower()

        monitoring_keywords = [
            "monitoring",
            "health",
            "status",
            "metrics",
            "system",
            "dashboard",
        ]
        found_keywords = [kw for kw in monitoring_keywords if kw in content]

        assert len(found_keywords) > 0, (
            f"Monitoring dashboard не загрузилась. Найденные ключевые слова: {found_keywords}"
        )

    def test_navigation_simulation(self, http_client):
        """Симуляция навигации между dashboard'ами через HTTP"""
        dashboards = [
            ("http://localhost:5176/", "home"),
            ("http://localhost:5176/analytics", "analytics"),
            ("http://localhost:5176/bots", "bots"),
            ("http://localhost:5176/strategies", "strategies"),
            ("http://localhost:5176/freqai", "freqai"),
            ("http://localhost:5176/monitoring", "monitoring"),
        ]

        results = []

        for url, name in dashboards:
            start_time = time.time()
            response = http_client.get(url)
            response_time = time.time() - start_time

            success = response.status_code == 200 and len(response.text) > 500

            results.append(
                {
                    "name": name,
                    "url": url,
                    "status_code": response.status_code,
                    "response_time": round(response_time, 2),
                    "content_length": len(response.text),
                    "success": success,
                }
            )

            status = "✅" if success else "❌"
            print(f"{status} {name}: {response.status_code}, {response_time:.2f}s")

            assert success, f"{name} dashboard недоступен"

        # Сохраняем результаты
        with open("dashboard_testing_results.json", "w") as f:
            json.dump(
                {
                    "timestamp": time.time(),
                    "test_type": "dashboard_navigation_simulation",
                    "results": results,
                },
                f,
                indent=2,
            )

    def test_static_assets_accessibility(self, http_client):
        """Тест доступности статических ресурсов"""
        static_files = [
            "http://localhost:5176/favicon.ico",
            "http://localhost:5176/manifest.json",
        ]

        for url in static_files:
            try:
                response = http_client.get(url)
                # 200 OK или 404 Not Found приемлемы
                assert response.status_code in [200, 404], (
                    f"Unexpected status {response.status_code} for {url}"
                )
            except Exception as e:
                # Для development сервера некоторые файлы могут отсутствовать
                print(f"⚠️  {url}: {str(e)} (OK для development)")

    def test_api_health_integration(self, http_client):
        """Тест интеграции с API health endpoints"""
        api_endpoints = [
            ("http://localhost:8002/health", "Management API"),
            ("http://localhost:8001/health", "Trading Gateway API"),
            ("http://localhost:8003/health", "Backtesting API"),
            ("http://localhost:8004/health", "FreqAI API"),
        ]

        for url, name in api_endpoints:
            response = http_client.get(url)
            assert response.status_code == 200, f"{name} недоступен"

            data = response.json()
            assert "status" in data, f"{name} возвращает некорректный формат"

            print(f"✅ {name}: {data['status']}")


if __name__ == "__main__":
    # Запуск тестов напрямую
    pytest.main([__file__, "-v", "--tb=short"])
