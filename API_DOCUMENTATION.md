# Freqtrade Multi-Bot System - API Documentation

## Overview

This document provides comprehensive API documentation for all four microservices in the Freqtrade Multi-Bot System.

## Table of Contents

1. [Management Server API (Port 8002)](#management-server-api)
2. [Trading Gateway API (Port 8001)](#trading-gateway-api)
3. [Backtesting Server API (Port 8003)](#backtesting-server-api)
4. [FreqAI Server API (Port 8004)](#freqai-server-api)
5. [Authentication](#authentication)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)

## Management Server API

**Base URL**: `http://localhost:8002/api/v1`

### Authentication Endpoints

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "username": "string",
  "email": "string",
  "password": "string"
}
```

**Response (201):**
```json
{
  "id": 1,
  "username": "string",
  "email": "string",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### POST /auth/login/json
Authenticate user and return JWT tokens.

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAi...",
  "refresh_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Strategy Management

#### GET /strategies
List all strategies for authenticated user.

**Headers:**
```
Authorization: Bearer <token>
```

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "RSIStrategy",
    "description": "RSI-based strategy",
    "code": "class RSIStrategy(IStrategy): ...",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
]
```

#### POST /strategies
Create a new trading strategy.

**Request Body:**
```json
{
  "name": "MyStrategy",
  "description": "Custom strategy",
  "code": "class MyStrategy(IStrategy):\\n    pass"
}
```

#### POST /strategies/backtest
Start asynchronous backtesting for a strategy.

**Request Body:**
```json
{
  "strategy_name": "MyStrategy",
  "timerange": "20240101-20240131",
  "stake_amount": 100.0,
  "config": {
    "dry_run": true,
    "max_open_trades": 3
  }
}
```

**Response (200):**
```json
{
  "id": 123,
  "celery_task_id": "abc-123-def",
  "status": "queued",
  "strategy_name": "MyStrategy",
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### GET /strategies/backtest/results/{result_id}
Get backtest results.

**Response (200):**
```json
{
  "id": 123,
  "status": "completed",
  "strategy_name": "MyStrategy",
  "results": {
    "total_trades": 150,
    "profitable_trades": 90,
    "win_rate": 60.0,
    "max_drawdown": 15.5,
    "profit_total": 1250.0
  },
  "created_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T00:05:00Z"
}
```

### Analytics Endpoints

#### GET /analytics/portfolio
Get portfolio analytics.

**Response (200):**
```json
{
  "portfolio_value": 12500.0,
  "total_invested": 10000.0,
  "total_profit": 2500.0,
  "active_bots": 3,
  "total_trades": 450
}
```

#### GET /analytics/performance
Get performance metrics.

**Query Parameters:**
- `bot_id` (optional): Filter by specific bot
- `timeframe` (optional): "24h", "7d", "30d", "1y"

**Response (200):**
```json
{
  "total_trades": 150,
  "profitable_trades": 90,
  "win_rate": 60.0,
  "avg_profit": 2.5,
  "max_drawdown": 15.5,
  "sharpe_ratio": 1.2
}
```

### Audit Logging

#### GET /audit/logs
Get audit logs with pagination.

**Query Parameters:**
- `limit` (default: 100): Number of logs to return
- `offset` (default: 0): Pagination offset
- `user_id` (optional): Filter by user
- `action` (optional): Filter by action type

**Response (200):**
```json
{
  "logs": [
    {
      "id": 1,
      "user_id": 123,
      "action": "CREATE_STRATEGY",
      "resource_type": "strategy",
      "resource_id": 456,
      "details": {"strategy_name": "MyStrategy"},
      "ip_address": "192.168.1.100",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

## Trading Gateway API

**Base URL**: `http://localhost:8001/api/v1`

### Bot Management

#### GET /bots
List all active bots.

**Response (200):**
```json
[
  {
    "id": "bot_123",
    "name": "MyBot",
    "strategy": "RSIStrategy",
    "status": "running",
    "config": {
      "stake_amount": 100,
      "dry_run": true,
      "exchange": "binance"
    },
    "created_at": "2024-01-01T00:00:00Z",
    "pid": 12345
  }
]
```

#### POST /bots
Create a new bot.

**Request Body:**
```json
{
  "name": "MyBot",
  "strategy_name": "RSIStrategy",
  "config": {
    "stake_amount": 100.0,
    "dry_run": true,
    "exchange": {
      "name": "binance",
      "key": "your_api_key",
      "secret": "your_api_secret"
    },
    "pair_whitelist": ["BTC/USDT", "ETH/USDT"]
  }
}
```

#### PUT /bots/{bot_id}/start
Start a bot.

**Response (200):**
```json
{
  "bot_id": "bot_123",
  "status": "starting",
  "message": "Bot start initiated"
}
```

#### PUT /bots/{bot_id}/stop
Stop a bot.

**Response (200):**
```json
{
  "bot_id": "bot_123",
  "status": "stopping",
  "message": "Bot stop initiated"
}
```

#### DELETE /bots/{bot_id}
Delete a bot.

**Response (200):**
```json
{
  "bot_id": "bot_123",
  "status": "deleted",
  "message": "Bot deleted successfully"
}
```

### WebSocket Endpoints

#### WebSocket /ws
Real-time bot updates and MCP protocol communication.

**Connection:**
```javascript
const ws = new WebSocket('ws://localhost:8001/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Received:', data);
};
```

**Message Format:**
```json
{
  "type": "BOT_STATUS_UPDATE",
  "data": {
    "bot_id": "bot_123",
    "status": "running",
    "active_trades": 2,
    "profit": 150.50
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## Backtesting Server API

**Base URL**: `http://localhost:8003`

### Backtesting Tasks

#### POST /backtest
Start a backtesting task.

**Request Body:**
```json
{
  "strategy_name": "MyStrategy",
  "config": {
    "stake_amount": 100.0,
    "timerange": "20240101-20240131",
    "dry_run": true
  },
  "request_id": "user_123_request_456"
}
```

**Response (202):**
```json
{
  "task_id": "backtest_123",
  "status": "accepted",
  "message": "Backtest task queued",
  "estimated_time": "30-60 seconds"
}
```

#### GET /task/{task_id}
Get task status and results.

**Response (200):**
```json
{
  "task_id": "backtest_123",
  "status": "completed",
  "progress": 100,
  "result": {
    "total_trades": 150,
    "profitable_trades": 90,
    "win_rate": 60.0,
    "profit_total": 1250.0,
    "max_drawdown": 15.5
  },
  "created_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T00:30:00Z"
}
```

#### GET /tasks
List all tasks.

**Query Parameters:**
- `status` (optional): Filter by status
- `limit` (default: 50): Number of tasks to return

**Response (200):**
```json
{
  "tasks": [
    {
      "task_id": "backtest_123",
      "status": "completed",
      "strategy_name": "MyStrategy",
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "total": 25,
  "limit": 50,
  "offset": 0
}
```

### Hyperopt Tasks

#### POST /hyperopt
Start hyperopt optimization task.

**Request Body:**
```json
{
  "strategy_name": "MyStrategy",
  "config": {
    "stake_amount": 100.0,
    "timerange": "20240101-20240131"
  },
  "epochs": 100,
  "spaces": "buy sell",
  "request_id": "user_123_hyperopt_789"
}
```

**Response (202):**
```json
{
  "task_id": "hyperopt_456",
  "status": "accepted",
  "message": "Hyperopt task queued",
  "estimated_time": "5-15 minutes"
}
```

## FreqAI Server API

**Base URL**: `http://localhost:8004`

### Model Management

#### GET /models
List all trained models.

**Response (200):**
```json
[
  {
    "name": "LightGBMRegressor_20240101",
    "strategy": "MyStrategy",
    "status": "completed",
    "created_at": "2024-01-01T00:00:00Z",
    "accuracy": 0.85,
    "features": 25
  }
]
```

#### POST /train
Start model training.

**Request Body:**
```json
{
  "model_name": "MyModel",
  "strategy_name": "MyStrategy",
  "timerange": "20240101-20241201",
  "stake_amount": 100.0,
  "config": {
    "feature_parameters": {
      "include_timeframes": ["5m", "15m", "1h"],
      "include_corr_pairlist": ["BTC/USDT", "ETH/USDT"]
    },
    "data_split_parameters": {
      "test_size": 0.25
    }
  }
}
```

**Response (202):**
```json
{
  "model_name": "MyModel",
  "status": "training",
  "task_id": "train_789",
  "message": "Model training started",
  "estimated_time": "5-15 minutes"
}
```

#### GET /training-status/{model_name}
Get training status.

**Response (200):**
```json
{
  "model_name": "MyModel",
  "status": "completed",
  "progress": 100,
  "accuracy": 0.85,
  "features_used": 25,
  "training_time": "8m 30s"
}
```

#### GET /model/{model_name}
Get model information.

**Response (200):**
```json
{
  "name": "MyModel",
  "strategy": "MyStrategy",
  "status": "completed",
  "created_at": "2024-01-01T00:00:00Z",
  "accuracy": 0.85,
  "features": 25,
  "model_type": "LightGBMRegressor",
  "config": {...}
}
```

#### POST /predict
Make predictions with a trained model.

**Request Body:**
```json
{
  "model_name": "MyModel",
  "features": {
    "rsi": 65.5,
    "bb_upper": 45000,
    "bb_lower": 43000,
    "volume": 1250000
  }
}
```

**Response (200):**
```json
{
  "model_name": "MyModel",
  "prediction": 0.75,
  "confidence": 0.82,
  "features_used": 25,
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### DELETE /model/{model_name}
Delete a trained model.

**Response (200):**
```json
{
  "model_name": "MyModel",
  "status": "deleted",
  "message": "Model deleted successfully"
}
```

## Authentication

All API endpoints (except `/auth/register` and `/auth/login`) require authentication using JWT tokens.

### JWT Token Usage

**Header Format:**
```
Authorization: Bearer <access_token>
```

### Token Refresh

#### POST /auth/refresh
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJ0eXAi..."
}
```

**Response (200):**
```json
{
  "access_token": "eyJ0eXAi...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

## Error Handling

All APIs return consistent error responses:

### Error Response Format
```json
{
  "detail": "Error message description",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Common HTTP Status Codes

- **200**: Success
- **201**: Created
- **202**: Accepted (async operation)
- **400**: Bad Request
- **401**: Unauthorized
- **403**: Forbidden
- **404**: Not Found
- **422**: Validation Error
- **429**: Too Many Requests
- **500**: Internal Server Error

### Validation Errors
```json
{
  "detail": [
    {
      "loc": ["body", "username"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Rate Limiting

API endpoints are protected by rate limiting:

- **Authenticated endpoints**: 100 requests per minute
- **Public endpoints**: 10 requests per minute
- **WebSocket connections**: 1000 concurrent connections

### Rate Limit Headers
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
X-RateLimit-Retry-After: 60
```

### Rate Limit Exceeded Response
```json
{
  "detail": "Rate limit exceeded",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 60
}
```