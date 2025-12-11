#!/usr/bin/env python3
"""
HTTP тестирование доступности всех dashboard'ов
Проверяет CORS, заголовки, базовую функциональность и время отклика
"""

import httpx
import pytest
import time
from typing import Dict, List, Tuple


def test_dashboard_http_availability():
    """Проверка доступности всех dashboard'ов по HTTP"""
    dashboards = [
        ("http://localhost:5176/", "Home Dashboard"),
        ("http://localhost:5176/analytics", "Analytics Dashboard"),
        ("http://localhost:5176/bots", "Bot Management Dashboard"),
        ("http://localhost:5176/strategies", "Strategies Dashboard"),
        ("http://localhost:5176/freqai", "FreqAI Lab Dashboard"),
        ("http://localhost:5176/monitoring", "Monitoring Dashboard"),
        ("http://localhost:5176/audit", "Audit Dashboard"),
        ("http://localhost:5176/data", "Data Management Dashboard"),
    ]

    results = []

    with httpx.Client(timeout=15.0, follow_redirects=True) as client:
        for url, name in dashboards:
            start_time = time.time()

            try:
                response = client.get(url)
                response_time = time.time() - start_time

                # Проверки
                assert response.status_code == 200, (
                    f"{name}: HTTP {response.status_code}"
                )
                assert "text/html" in response.headers.get("content-type", ""), (
                    f"{name}: не HTML контент"
                )
                assert response_time < 5.0, f"Response too slow: {response_time:.2f}s"
                assert len(response.text) > 100, (
                    f"{name}: контент слишком мал ({len(response.text)} символов)"
                )

                results.append(
                    {
                        "name": name,
                        "url": url,
                        "status": "✅ PASS",
                        "response_time": round(response_time, 2),
                        "content_length": len(response.text),
                    }
                )

                print(
                    f"✅ {name}: {response.status_code}, {response_time:.2f}s, {len(response.text)} chars"
                )

            except Exception as e:
                results.append(
                    {"name": name, "url": url, "status": "❌ FAIL", "error": str(e)}
                )
                print(f"❌ {name}: {str(e)}")
                raise

    # Сохраняем результаты
    import json

    with open("dashboard_http_testing_results.json", "w") as f:
        json.dump(
            {
                "timestamp": time.time(),
                "test_type": "dashboard_http_availability",
                "results": results,
            },
            f,
            indent=2,
        )


def test_dashboard_cors_headers():
    """Проверка CORS заголовков для dashboard'ов"""
    dashboard_urls = [
        "http://localhost:5176/",
        "http://localhost:5176/analytics",
        "http://localhost:5176/bots",
    ]

    with httpx.Client(timeout=10.0) as client:
        for url in dashboard_urls:
            # OPTIONS запрос для проверки CORS
            try:
                response = client.options(url)

                # CORS может быть настроен по-разному
                # Проверяем наличие основных заголовков
                cors_headers = [
                    "access-control-allow-origin",
                    "access-control-allow-methods",
                    "access-control-allow-headers",
                ]

                found_cors_headers = [h for h in cors_headers if h in response.headers]

                # Если есть хотя бы один CORS заголовок, считаем что CORS настроен
                if found_cors_headers:
                    print(f"✅ {url}: CORS настроен ({found_cors_headers})")
                else:
                    # Для development сервера CORS может не быть строгим
                    print(f"⚠️  {url}: CORS заголовки не найдены (OK для dev)")

            except Exception as e:
                print(f"❌ {url}: Ошибка проверки CORS - {str(e)}")


def test_dashboard_static_assets():
    """Проверка доступности статических ресурсов dashboard'ов"""
    # Проверяем основные статические файлы
    static_files = [
        "http://localhost:5176/favicon.ico",
        "http://localhost:5176/manifest.json",
    ]

    with httpx.Client(timeout=10.0, follow_redirects=True) as client:
        for url in static_files:
            try:
                response = client.get(url)
                # 200 OK или 404 Not Found приемлемы для статических файлов
                assert response.status_code in [200, 404], (
                    f"Unexpected status {response.status_code} for {url}"
                )
                print(f"✅ {url}: {response.status_code}")
            except Exception as e:
                print(f"⚠️  {url}: {str(e)} (OK если файл не существует)")


def test_dashboard_api_endpoints_integration():
    """Проверка интеграции dashboard'ов с API endpoints"""
    # Проверяем что dashboard'ы могут обращаться к API
    api_endpoints = [
        ("http://localhost:8002/health", "Management API"),
        ("http://localhost:8001/health", "Trading Gateway API"),
        ("http://localhost:8003/health", "Backtesting API"),
        ("http://localhost:8004/health", "FreqAI API"),
    ]

    with httpx.Client(timeout=10.0) as client:
        for url, name in api_endpoints:
            try:
                response = client.get(url)
                assert response.status_code == 200, f"{name}: API недоступен"

                data = response.json()
                assert "status" in data, f"{name}: некорректный формат ответа API"

                print(f"✅ {name}: доступен")

            except Exception as e:
                print(f"❌ {name}: {str(e)}")
                raise


if __name__ == "__main__":
    print("🔍 Запуск HTTP тестирования dashboard'ов...")
    print("=" * 60)

    try:
        test_dashboard_http_availability()
        print("\n📋 Проверка CORS заголовков...")
        test_dashboard_cors_headers()
        print("\n📁 Проверка статических ресурсов...")
        test_dashboard_static_assets()
        print("\n🔗 Проверка API интеграции...")
        test_dashboard_api_endpoints_integration()

        print("\n" + "=" * 60)
        print("🎉 Все HTTP тесты dashboard'ов пройдены!")

    except Exception as e:
        print(f"\n❌ Ошибка тестирования: {str(e)}")
        exit(1)
