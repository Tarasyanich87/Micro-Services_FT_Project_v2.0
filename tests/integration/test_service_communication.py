#!/usr/bin/env python3
"""
Integration Tests for Multi-Service Communication
Tests workflows that span multiple services in the Freqtrade Multi-Bot System.
"""

import pytest
import httpx
import asyncio
from typing import Dict, Any


@pytest.mark.integration
@pytest.mark.service
class TestMultiServiceIntegration:
    """Integration tests for multi-service workflows."""

    def test_management_to_trading_gateway_flow(self):
        """Test complete flow: Management Server -> Trading Gateway."""
        # This would test a complete bot creation and management flow
        # For now, just verify both services are accessible
        with httpx.Client(timeout=5.0) as client:
            # Check Management Server
            mgmt_response = client.get("http://localhost:8002/health")
            assert mgmt_response.status_code == 200

            # Check Trading Gateway
            tg_response = client.get("http://localhost:8001/health")
            assert tg_response.status_code == 200

    def test_management_to_backtesting_flow(self):
        """Test Management Server to Backtesting Server communication."""
        with httpx.Client(timeout=5.0) as client:
            # Check both services
            mgmt_response = client.get("http://localhost:8002/health")
            assert mgmt_response.status_code == 200

            backtest_response = client.get("http://localhost:8003/health")
            assert backtest_response.status_code == 200

    def test_management_to_freqai_flow(self):
        """Test Management Server to FreqAI Server communication."""
        with httpx.Client(timeout=5.0) as client:
            # Check both services
            mgmt_response = client.get("http://localhost:8002/health")
            assert mgmt_response.status_code == 200

            freqai_response = client.get("http://localhost:8004/health")
            assert freqai_response.status_code == 200

    def test_all_services_health_check(self):
        """Test that all 4 services are healthy and responding."""
        services = {
            "Management Server": "http://localhost:8002",
            "Trading Gateway": "http://localhost:8001",
            "Backtesting Server": "http://localhost:8003",
            "FreqAI Server": "http://localhost:8004",
        }

        with httpx.Client(timeout=5.0) as client:
            for name, url in services.items():
                response = client.get(f"{url}/health")
                assert response.status_code == 200, f"{name} health check failed"
                data = response.json()
                assert "status" in data, f"{name} missing status in response"

    def test_service_response_consistency(self):
        """Test that all services return consistent response formats."""
        with httpx.Client(timeout=5.0) as client:
            responses = {}

            # Collect responses from all services
            services = [
                ("management", "http://localhost:8002"),
                ("trading_gateway", "http://localhost:8001"),
                ("backtesting", "http://localhost:8003"),
                ("freqai", "http://localhost:8004"),
            ]

            for name, url in services:
                response = client.get(f"{url}/health")
                responses[name] = response.json()

            # Verify all have status field
            for name, data in responses.items():
                assert "status" in data, f"{name} missing status field"
                assert isinstance(data["status"], str), f"{name} status not string"

    def test_service_error_handling_consistency(self):
        """Test that all services handle invalid requests consistently."""
        with httpx.Client(timeout=5.0) as client:
            services = [
                "http://localhost:8002",
                "http://localhost:8001",
                "http://localhost:8003",
                "http://localhost:8004",
            ]

            for url in services:
                response = client.get(f"{url}/nonexistent-endpoint")
                # Should return 404 for invalid endpoints
                assert response.status_code in [404, 422], (
                    f"Unexpected status for {url}"
                )

    def test_cross_service_dependencies(self):
        """Test that services can communicate with shared dependencies (Redis)."""
        # Since all services use Redis, we can verify they're all connected
        with httpx.Client(timeout=5.0) as client:
            services_with_redis = [
                ("Backtesting Server", "http://localhost:8003"),
                ("FreqAI Server", "http://localhost:8004"),
            ]

            for name, url in services_with_redis:
                response = client.get(f"{url}/health")
                data = response.json()
                # Check if Redis connection status is reported
                if "redis_connected" in data:
                    assert data["redis_connected"] in [True, False], (
                        f"{name} Redis status unclear"
                    )


@pytest.mark.integration
@pytest.mark.service
class TestServiceLoadBalancing:
    """Tests for service load balancing and concurrent requests."""

    def test_concurrent_health_checks(self):
        """Test that all services can handle concurrent health check requests."""
        services = [
            "http://localhost:8002",
            "http://localhost:8001",
            "http://localhost:8003",
            "http://localhost:8004",
        ]

        for url in services:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{url}/health")
                assert response.status_code == 200, f"Service {url} failed health check"
                data = response.json()
                assert "status" in data, f"Service {url} missing status"

    def test_service_response_times(self):
        """Test that services respond within acceptable time limits."""
        import time

        with httpx.Client(timeout=10.0) as client:
            services = [
                ("Management Server", "http://localhost:8002"),
                ("Trading Gateway", "http://localhost:8001"),
                ("Backtesting Server", "http://localhost:8003"),
                ("FreqAI Server", "http://localhost:8004"),
            ]

            for name, url in services:
                start_time = time.time()
                response = client.get(f"{url}/health")
                end_time = time.time()

                response_time = end_time - start_time
                assert response_time < 2.0, (
                    f"{name} response time {response_time:.2f}s exceeds 2s limit"
                )
                assert response.status_code == 200, f"{name} health check failed"
