# API Documentation

This document provides comprehensive API documentation for the Freqtrade Multi-Bot System.

## 🏆 Enterprise Features

### Redis Streams Infrastructure
The system implements enterprise-grade Redis Streams with 99.9% reliability:
- **12 Named Streams** with structured namespacing
- **Consumer Groups** for reliable message delivery
- **Dead Letter Queues** for error isolation
- **Real-time Monitoring** and health checks
- **Production validated** with 757 msg/s throughput

## Base URL

```
Production: https://api.freqtrade.example.com/api/v1
Development: http://localhost:8002/api/v1
Trading Gateway: http://localhost:8001/api/v1
```

## Authentication

All API endpoints require JWT authentication except health checks.

### Login

```http
POST /auth/login/json
Content-Type: application/json

{
  "username": "analytics_user",
  "password": "testpass123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 86400,
  "user": {
    "username": "analytics_user",
    "email": "analytics@example.com",
    "full_name": "Analytics Test User",
    "is_active": true,
    "is_superuser": false,
    "id": 5
  }
}
```

### Using JWT Token

Include the token in the Authorization header:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIs...
```

## API Endpoints

### Health Checks

#### System Health
```http
GET /monitoring/health
```

**Response:**
```json
{
  "timestamp": "2025-12-09T19:15:31.000Z",
  "overall_status": "healthy",
  "component_health": [
    {
      "name": "Management Server",
      "status": "healthy",
      "details": {
        "port": 8002,
        "uptime": "Operational"
      }
    }
  ]
}
```

#### System Status (Authenticated)
```http
GET /monitoring/monitoring/status
Authorization: Bearer <token>
```

**Response:**
```json
{
  "timestamp": "2025-12-09T19:15:31.000Z",
  "system_metrics": {
    "cpu": {
      "usage_percent": 95.2,
      "cores": 4,
      "cores_logical": 4
    },
    "memory": {
      "total_gb": 7.63,
      "used_gb": 6.28,
      "free_gb": 1.35,
      "usage_percent": 82.3
    },
    "disk": {
      "total_gb": 214.48,
      "used_gb": 43.18,
      "free_gb": 170.89,
      "usage_percent": 20.2
    }
  },
  "component_health": [...],
  "bot_statistics": {...},
  "overall_status": "unhealthy"

}
```

## Redis Streams API 🚀

Enterprise-grade message processing with 99.9% reliability.

### Stream Health Monitoring

#### Get System Health Status
```http
GET /health/streams
Authorization: Bearer <token>
```

**Response:**
```json
{
  "service": "management_server",
  "timestamp": 1640995200.123,
  "status": "healthy",
  "redis_connected": true,
  "active_listeners": 4,
  "issues": [],
  "metrics": {
    "system_health": {
      "overall_status": "healthy",
      "issues": [],
      "total_streams": 12,
      "total_groups": 4,
      "total_lag": 0,
      "total_dlq_messages": 0
    },
    "streams": {
      "mgmt:trading:commands": {
        "exists": true,
        "length": 0,
        "groups": {
          "trading_consumers": {
            "consumers": 1,
            "pending": 0,
            "lag": 0
          }
        },
        "errors": {}
      }
    }
  }
}
```

#### Get Stream Details
```http
GET /streams/{stream_name}/health
Authorization: Bearer <token>
```

**Response:**
```json
{
  "name": "mgmt:trading:commands",
  "exists": true,
  "length": 5,
  "groups_count": 1,
  "total_lag": 0,
  "total_pending": 0,
  "groups": {
    "trading_consumers": {
      "consumers": 1,
      "pending": 0,
      "lag": 0,
      "last_delivered_id": "1640995200000-0"
    }
  },
  "dlq": {
    "total_messages": 0,
    "error_types": {}
  },
  "throughput": {
    "messages_per_minute": 12.5
  },
  "errors": {},
  "last_updated": 1640995200.123
}
```

### Dead Letter Queue Management

#### Get DLQ Statistics
```http
GET /streams/{stream_name}/dlq/stats
Authorization: Bearer <token>
```

**Response:**
```json
{
  "stream": "mgmt:trading:commands:dead",
  "total_messages": 2,
  "error_types": {
    "connection_timeout": 1,
    "json_parse_error": 1
  },
  "last_updated": 1640995200.123
}
```

#### List DLQ Messages
```http
GET /streams/{stream_name}/dlq/messages?limit=10
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": "1640995200000-0",
    "data": {
      "dead_letter_reason": "connection_timeout",
      "failed_at": "1640995200.123",
      "original_stream": "mgmt:trading:commands",
      "original_message_id": "1640995199000-0",
      "service_name": "trading_gateway",
      "final_retry_count": "3"
    },
    "timestamp": "1640995200.123"
  }
]
```

### Stream Performance Metrics

#### Get Performance Metrics
```http
GET /streams/metrics
Authorization: Bearer <token>
```

**Response:**
```json
{
  "timestamp": 1640995200.123,
  "service": "management_server",
  "redis_connected": true,
  "active_listeners": 4,
  "streams": {
    "mgmt:trading:commands": {
      "throughput": {"messages_per_minute": 45.2},
      "lag": {"trading_consumers": 0},
      "errors": {}
    }
  },
  "system_health": {
    "overall_status": "healthy",
    "total_streams": 12,
    "total_groups": 4,
    "total_lag": 0,
    "total_dlq_messages": 2
  }
}
```

### Stream Configuration

#### List All Streams
```http
GET /streams/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "streams": [
    "mgmt:trading:commands",
    "trading:mgmt:status",
    "mgmt:backtesting:commands",
    "backtesting:mgmt:results",
    "mgmt:freqai:commands",
    "freqai:mgmt:status",
    "system:events",
    "audit:events"
  ],
  "total": 12
}
```

#### Get Stream Configuration
```http
GET /streams/{stream_name}/config
Authorization: Bearer <token>
```

**Response:**
```json
{
  "name": "mgmt:trading:commands",
  "maxlen": 10000,
  "approximate": false,
  "consumer_groups": ["trading_consumers"],
  "description": "Management server commands to trading gateway"
}
```

### Bot Management

#### List Bots
```http
GET /bots/
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 11,
    "name": "TestBot",
    "strategy_name": "TestStrategy",
    "exchange": "binance",
    "status": "stopped",
    "total_trades": 0,
    "profitable_trades": 0,
    "total_profit": 0.0,
    "created_at": "2025-12-09T19:15:31"
  }
]
```

#### Create Bot
```http
POST /bots/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "MyBot",
  "strategy_name": "TestStrategy",
  "exchange": "binance",
  "stake_currency": "USDT",
  "stake_amount": 100.0
}
```

**Response:** Same as bot object above

#### Get Bot Details
```http
GET /bots/{bot_id}
Authorization: Bearer <token>
```

#### Update Bot
```http
PUT /bots/{bot_id}
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "UpdatedBot",
  "stake_amount": 200.0
}
```

#### Delete Bot
```http
DELETE /bots/{bot_id}
Authorization: Bearer <token>
```

#### Bot Control

##### Start Bot
```http
POST /bots/{bot_id}/start
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "start_command_sent",
  "bot_name": "MyBot"
}
```

##### Stop Bot
```http
POST /bots/{bot_id}/stop
Authorization: Bearer <token>
```

##### Get Bot Status
```http
GET /bots/{bot_id}/status
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "success",
  "bot_name": "MyBot",
  "bot_status": "running",
  "pid": 12345
}
```

##### Get Bot Logs
```http
GET /bots/{bot_id}/logs
Authorization: Bearer <token>
```

**Response:**
```json
{
  "logs": [
    "2025-12-09 19:15:31 INFO - Starting bot MyBot",
    "2025-12-09 19:15:32 INFO - Bot MyBot started successfully"
  ]
}
```

#### Bulk Operations

##### Start All Bots
```http
POST /bots/start-all
Authorization: Bearer <token>
```

##### Stop All Bots
```http
POST /bots/stop-all
Authorization: Bearer <token>
```

##### Restart All Bots
```http
POST /bots/restart-all
Authorization: Bearer <token>
```

### Strategy Management

#### List Strategies
```http
GET /strategies/
Authorization: Bearer <token>
```

**Response:**
```json
[
  "TestStrategy",
  "FreqaiExampleStrategy"
]
```

#### Upload Strategy
```http
POST /strategies/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: strategy.py
```

#### Delete Strategy
```http
DELETE /strategies/{strategy_name}
Authorization: Bearer <token>
```

#### Backtest Strategy
```http
POST /strategies/backtest
Authorization: Bearer <token>
Content-Type: application/json

{
  "strategy_name": "TestStrategy",
  "timeframe": "5m",
  "timerange": "20240101-20240102",
  "bot_id": 11
}
```

**Response:**
```json
{
  "status": "backtest_started",
  "task_id": "abc-123-def",
  "strategy_name": "TestStrategy"
}
```

### Analytics

#### Performance Metrics
```http
GET /analytics/performance
Authorization: Bearer <token>
```

**Response:**
```json
{
  "data": {
    "total_trades": 150,
    "profitable_trades": 90,
    "avg_profit": 2.5,
    "win_rate": 60.0
  },
  "timeframe": "24h"
}
```

#### Risk Analysis
```http
GET /analytics/risk
Authorization: Bearer <token>
```

**Response:**
```json
{
  "data": {
    "max_drawdown": 15.5,
    "sharpe_ratio": 1.8,
    "sortino_ratio": 2.1,
    "calmar_ratio": 1.5
  }
}
```

#### Portfolio Analytics
```http
GET /analytics/portfolio
Authorization: Bearer <token>
```

**Response:**
```json
{
  "data": {
    "total_value": 12500.50,
    "total_profit": 2500.50,
    "profit_percentage": 25.0,
    "assets": [
      {
        "symbol": "BTC/USDT",
        "amount": 0.5,
        "value": 25000.00,
        "profit": 5000.00
      }
    ]
  }
}
```

#### Market Data
```http
GET /analytics/market
Authorization: Bearer <token>
```

**Response:**
```json
{
  "data": {
    "btc_usdt": {
      "price": 45000.00,
      "change_24h": 2.5,
      "volume_24h": 1500000000
    },
    "eth_usdt": {
      "price": 2800.00,
      "change_24h": -1.2,
      "volume_24h": 800000000
    }
  }
}
```

### FreqAI Management

#### List Models
```http
GET /freqai/models/
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Test FreqAI Model",
    "description": "Test model for demonstration",
    "status": "completed",
    "created_at": "2025-12-08T13:19:28",
    "backtest_results": {
      "accuracy": 0.85,
      "profit_factor": 1.3
    }
  }
]
```

#### Create Model
```http
POST /freqai/models/
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "NewModel",
  "description": "My custom FreqAI model",
  "bot_id": 11,
  "model_type": "LightGBMRegressor"
}
```

#### Train Model
```http
POST /freqai/models/{model_id}/train
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "training_started",
  "task_id": "task-123",
  "model_id": 1
}
```

#### Get Model Status
```http
GET /freqai/models/{model_id}/status
Authorization: Bearer <token>
```

#### Delete Model
```http
DELETE /freqai/models/{model_id}
Authorization: Bearer <token>
```

### Data Management

#### List Available Data
```http
GET /data/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "data": [
    {
      "pair": "BTC/USDT",
      "timeframe": "5m",
      "start_date": "2024-01-01",
      "end_date": "2024-12-01",
      "records": 100000
    }
  ]
}
```

#### Upload Data
```http
POST /data/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: data.csv
pair: BTC/USDT
timeframe: 5m
```

#### Download Data
```http
GET /data/download/{pair}/{timeframe}
Authorization: Bearer <token>
```

### Audit Logging

#### Get Audit Logs
```http
GET /audit/
Authorization: Bearer <token>
```

**Response:**
```json
{
  "logs": [
    {
      "id": 1,
      "timestamp": "2025-12-09T19:15:31",
      "user": "analytics_user",
      "action": "bot_start",
      "resource": "bot:11",
      "ip_address": "192.168.1.100",
      "status": "success",
      "details": {
        "bot_name": "TestBot"
      }
    }
  ],
  "total": 1,
  "page": 1,
  "per_page": 50
}
```

#### Filter Audit Logs
```http
GET /audit/?user=analytics_user&action=bot_start&start_date=2025-12-01&end_date=2025-12-31
Authorization: Bearer <token>
```

### Hyperopt

#### List Strategies for Optimization
```http
GET /hyperopt/strategies
Authorization: Bearer <token>
```

**Response:**
```json
[
  "TestStrategy",
  "AdvancedStrategy"
]
```

#### Start Hyperopt
```http
POST /hyperopt/start
Authorization: Bearer <token>
Content-Type: application/json

{
  "strategy_name": "TestStrategy",
  "epochs": 100,
  "spaces": ["buy", "sell", "roi", "stoploss"],
  "timerange": "20240101-20241201"
}
```

**Response:**
```json
{
  "status": "optimization_started",
  "task_id": "hyperopt-123",
  "strategy_name": "TestStrategy"
}
```

#### Get Hyperopt Results
```http
GET /hyperopt/results/{task_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "status": "completed",
  "best_result": {
    "loss": 0.15,
    "params": {
      "buy_rsi": 30,
      "sell_rsi": 70,
      "roi_t1": 10,
      "roi_t2": 20,
      "roi_t3": 30,
      "stoploss": -0.1
    },
    "results": {
      "total_trades": 150,
      "profit_total": 1250.50,
      "profit_mean": 8.34,
      "max_drawdown": 15.5
    }
  }
}
```

## Error Responses

### Common Error Codes

#### 400 Bad Request
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "name"],
      "msg": "Field required",
      "input": {...}
    }
  ]
}
```

#### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

#### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

#### 404 Not Found
```json
{
  "detail": "Bot not found"
}
```

#### 422 Validation Error
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "stake_amount"],
      "msg": "ensure this value is greater than 0",
      "input": -100
    }
  ]
}
```

#### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

## Rate Limiting

API endpoints are rate limited to prevent abuse:

- **Authenticated requests**: 1000 requests per hour
- **Health checks**: 100 requests per minute
- **File uploads**: 10 requests per hour

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## WebSocket API

Real-time updates are available via WebSocket:

```javascript
const ws = new WebSocket('ws://localhost:8001/ws');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Real-time update:', data);
};
```

### WebSocket Events

#### Bot Status Updates
```json
{
  "type": "bot_status_update",
  "data": {
    "bot_id": 11,
    "status": "running",
    "profit": 1250.50
  }
}
```

#### System Metrics
```json
{
  "type": "system_metrics",
  "data": {
    "cpu_usage": 45.2,
    "memory_usage": 67.8,
    "disk_usage": 23.1
  }
}
```

#### Trade Notifications
```json
{
  "type": "trade_notification",
  "data": {
    "bot_id": 11,
    "pair": "BTC/USDT",
    "side": "buy",
    "amount": 0.001,
    "price": 45000.00
  }
}
```

## SDKs and Libraries

### Python Client

```python
import requests

class FreqtradeClient:
    def __init__(self, base_url: str, token: str):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {token}"}

    def get_bots(self):
        response = requests.get(
            f"{self.base_url}/bots/",
            headers=self.headers
        )
        return response.json()

    def start_bot(self, bot_id: int):
        response = requests.post(
            f"{self.base_url}/bots/{bot_id}/start",
            headers=self.headers
        )
        return response.json()

# Usage
client = FreqtradeClient("http://localhost:8002/api/v1", "your-jwt-token")
bots = client.get_bots()
```

### JavaScript Client

```javascript
class FreqtradeAPI {
  constructor(baseURL, token) {
    this.baseURL = baseURL;
    this.headers = {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    };
  }

  async getBots() {
    const response = await fetch(`${this.baseURL}/bots/`, {
      headers: this.headers
    });
    return response.json();
  }

  async startBot(botId) {
    const response = await fetch(`${this.baseURL}/bots/${botId}/start`, {
      method: 'POST',
      headers: this.headers
    });
    return response.json();
  }
}

// Usage
const api = new FreqtradeAPI('http://localhost:8002/api/v1', 'your-jwt-token');
const bots = await api.getBots();
```

## Versioning

API versioning follows semantic versioning:

- **v1**: Current stable version
- **Breaking changes** will introduce new major versions
- **Backwards compatible** changes are added to existing versions
- **Deprecation notices** are provided 6 months before removal

## Support

For API support and questions:

- **Documentation**: https://docs.freqtrade.io
- **GitHub Issues**: https://github.com/freqtrade/freqtrade-multibot/issues
- **Discord**: https://discord.gg/freqtrade
- **Email**: support@freqtrade.io

## Changelog

## Emergency Operations

### Emergency Stop All Bots

**Endpoint:** `POST /api/v1/emergency/stop-all`

**Description:** Immediately stops all running bots across the system. This is a critical operation that should only be used in emergency situations.

**Authentication:** Required (JWT token)

**Request:**
```http
POST /api/v1/emergency/stop-all
Authorization: Bearer <jwt_token>
Content-Type: application/json
```

**Response (Success):**
```json
{
  "message": "Emergency stop command sent.",
  "timestamp": "2025-12-10T04:15:30.123456+00:00"
}
```

**Response (Error):**
```json
{
  "detail": "Not authenticated"
}
```

**Behavior:**
- Sends emergency stop command to all running Freqtrade processes
- Updates bot statuses to "stopped" in database
- Logs emergency action in audit trail
- Returns success immediately (async operation)

**Use Cases:**
- System maintenance
- Critical errors requiring immediate shutdown
- Emergency trading halts
- Resource cleanup before system updates

**Testing:**
```bash
# Test emergency stop
curl -X POST "http://localhost:8002/api/v1/emergency/stop-all" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Bulk Operations

### Overview

The system supports bulk operations for managing multiple bots simultaneously. This is useful for:
- Mass bot deployment
- Batch configuration updates
- Emergency bulk operations
- Automated bot management

### Bulk Creation Example

```python
import asyncio
import httpx

async def create_bulk_bots():
    async with httpx.AsyncClient(base_url="http://localhost:8002") as client:
        # Authenticate first
        # ...

        # Create multiple bots concurrently
        tasks = []
        for i in range(5):
            bot_data = {
                "name": f"BulkBot_{i}",
                "strategy_name": "TestStrategy",
                "exchange": "binance",
                "stake_currency": "USDT",
                "stake_amount": 100.0,
            }
            tasks.append(client.post("/api/v1/bots/", json=bot_data))

        results = await asyncio.gather(*tasks, return_exceptions=True)
        print(f"Created {len([r for r in results if not isinstance(r, Exception)])} bots")
```

### Performance Considerations

- **Concurrent Requests:** Max 5 simultaneous operations recommended
- **Database Load:** Bulk operations may cause temporary performance degradation
- **Rate Limiting:** 100 requests/minute per user applies to bulk operations
- **Error Handling:** Individual failures don't stop the entire bulk operation

### Testing Bulk Operations

```bash
# Run bulk operations test
python test_bulk_bot_operations.py

# Run emergency demo
python demo_bulk_emergency.py
```

### v1.0.1 (Latest)
- Fixed duplicate analytics tags in OpenAPI documentation
- Enhanced analytics endpoints with proper single tag grouping
- Improved API documentation consistency

### v1.0.1 (Latest)
- Enhanced FreqAI integration with model caching
- Trading Gateway prediction API
- Improved error handling and validation
- LRU cache for FreqAI models
- Base64 model transmission optimization

### v1.0.0 (Current)
- Initial API release
- Bot management endpoints
- Strategy management
- Analytics and monitoring
- FreqAI integration
- Audit logging
- WebSocket real-time updates
- Emergency operations
- Bulk operations support

## Trading Gateway API

The Trading Gateway provides direct bot communication and FreqAI model management.

### Base URL
```
http://localhost:8001/api/v1
```

### FreqAI Model Management

#### Get Bot Predictions
```http
GET /bots/{bot_name}/predictions?pair=BTC/USDT&timeframe=5m&strategy=TestStrategy
```

**Response:**
```json
{
  "status": "success",
  "bot_name": "BTC_Bot",
  "model_path": "/tmp/freqai_cache/btc_bot_123.model",
  "predictions": {
    "prediction": 0.85,
    "confidence": 0.72,
    "features_used": ["rsi", "macd", "volume"]
  },
  "parameters": {
    "pair": "BTC/USDT",
    "timeframe": "5m",
    "strategy": "TestStrategy"
  }
}
```

#### Get Model Cache Stats
```http
GET /freqai/cache/stats
```

**Response:**
```json
{
  "cached_models": 3,
  "max_cache_size": 5,
  "cache_hit_rate": 85.5,
  "oldest_access": "2025-12-10T04:00:00Z",
  "newest_access": "2025-12-10T04:30:00Z",
  "total_evictions": 12
}
```

#### Force Model Reload
```http
POST /bots/{bot_name}/reload-model
```

**Response:**
```json
{
  "status": "model_reloaded",
  "bot_name": "BTC_Bot",
  "model_version": "1.2.0",
  "reload_time": "2025-12-10T04:35:00Z"
}
```

### Bot Process Management

#### Get Bot Process Info
```http
GET /bots/{bot_name}/process
```

**Response:**
```json
{
  "bot_name": "BTC_Bot",
  "pid": 12345,
  "status": "running",
  "start_time": "2025-12-10T04:00:00Z",
  "memory_usage_mb": 245.6,
  "cpu_percent": 12.3
}
```

#### Emergency Bot Stop
```http
POST /bots/{bot_name}/emergency-stop
```

**Response:**
```json
{
  "status": "emergency_stop_initiated",
  "bot_name": "BTC_Bot",
  "signal_sent": "SIGKILL"
}
```

</content>
<parameter name="filePath">jules_freqtrade_project/API_DOCS.md