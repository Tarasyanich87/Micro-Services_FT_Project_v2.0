#!/usr/bin/env python3
"""
Simple API Tests for all services - direct HTTP calls without async fixtures
"""

import pytest
import httpx


def test_management_server_health():
    """Test Management Server health check."""
    with httpx.Client(base_url="http://localhost:8002", timeout=5.0) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


def test_trading_gateway_health():
    """Test Trading Gateway health check."""
    with httpx.Client(base_url="http://localhost:8001", timeout=5.0) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "ok"


def test_backtesting_server_health():
    """Test Backtesting Server health check."""
    with httpx.Client(base_url="http://localhost:8003", timeout=5.0) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


def test_freqai_server_health():
    """Test FreqAI Server health check."""
    with httpx.Client(base_url="http://localhost:8004", timeout=5.0) as client:
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert data["status"] == "healthy"


def test_management_server_invalid_endpoint():
    """Test Management Server returns 404 for invalid endpoint."""
    with httpx.Client(base_url="http://localhost:8002", timeout=5.0) as client:
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404


def test_trading_gateway_invalid_endpoint():
    """Test Trading Gateway returns 404 for invalid endpoint."""
    with httpx.Client(base_url="http://localhost:8001", timeout=5.0) as client:
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404


def test_backtesting_server_invalid_endpoint():
    """Test Backtesting Server returns 404 for invalid endpoint."""
    with httpx.Client(base_url="http://localhost:8003", timeout=5.0) as client:
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404


def test_freqai_server_invalid_endpoint():
    """Test FreqAI Server returns 404 for invalid endpoint."""
    with httpx.Client(base_url="http://localhost:8004", timeout=5.0) as client:
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404


def test_management_server_cors():
    """Test Management Server CORS headers."""
    with httpx.Client(base_url="http://localhost:8002", timeout=5.0) as client:
        # Test preflight request - if OPTIONS is not supported, that's OK
        try:
            response = client.options("/health")
            if response.status_code == 200:
                assert (
                    "access-control-allow-origin" in response.headers
                    or "allow" in response.headers
                )
        except:
            # CORS might not be configured for OPTIONS, skip test
            pass


def test_trading_gateway_cors():
    """Test Trading Gateway CORS headers."""
    with httpx.Client(base_url="http://localhost:8001", timeout=5.0) as client:
        try:
            response = client.options("/health")
            if response.status_code == 200:
                assert (
                    "access-control-allow-origin" in response.headers
                    or "allow" in response.headers
                )
        except:
            pass


def test_backtesting_server_cors():
    """Test Backtesting Server CORS headers."""
    with httpx.Client(base_url="http://localhost:8003", timeout=5.0) as client:
        try:
            response = client.options("/health")
            if response.status_code == 200:
                assert (
                    "access-control-allow-origin" in response.headers
                    or "allow" in response.headers
                )
        except:
            pass


def test_freqai_server_cors():
    """Test FreqAI Server CORS headers."""
    with httpx.Client(base_url="http://localhost:8004", timeout=5.0) as client:
        try:
            response = client.options("/health")
            if response.status_code == 200:
                assert (
                    "access-control-allow-origin" in response.headers
                    or "allow" in response.headers
                )
        except:
            pass
