# MCP Protocol Specification

## Overview

The Machine Control Protocol (MCP) defines the WebSocket-based communication interface between AI Agents (Clients) and the Trading Gateway (Server). This protocol enables real-time control and monitoring of Freqtrade trading bots through a structured message format.

## Connection

### Establishing Connection
Clients must establish a WebSocket connection to the `/ws/agent` endpoint on the Trading Gateway.

**WebSocket URL:** `ws://trading-gateway:8001/ws/agent`

### Connection Parameters
- **Protocol:** WebSocket (RFC 6455)
- **Message Format:** JSON
- **Encoding:** UTF-8
- **Heartbeat:** Optional, client-initiated

## Message Format

All messages follow a consistent JSON structure:

```json
{
  "type": "MESSAGE_TYPE",
  "id": "unique_message_id",
  "data": {
    // Message-specific payload
  },
  "timestamp": "2025-12-08T10:00:00Z"
}
```

### Message Fields
- **type** (string): Message type identifier
- **id** (string): Unique message identifier for correlation
- **data** (object): Message payload (varies by type)
- **timestamp** (string): ISO 8601 timestamp

## Message Types

### 1. Bot Control Messages

#### START_BOT
Initiates a new Freqtrade bot instance.

**Direction:** Client → Server

```json
{
  "type": "START_BOT",
  "id": "msg_001",
  "data": {
    "bot_name": "my_trading_bot",
    "bot_config": {
      "trading_mode": "spot",
      "stake_currency": "USDT",
      "stake_amount": 100,
      "dry_run": true,
      "exchange": {
        "name": "binance",
        "key": "",
        "secret": ""
      },
      "pair_whitelist": ["BTC/USDT", "ETH/USDT"],
      "strategy": "MyStrategy"
    },
    "freqai_model": {
      "filename": "LightGBMRegressor_model.pkl",
      "content_b64": "U29tZUJpZ0Jhc2U2NENvbnRlbnQ..."
    }
  }
}
```

#### STOP_BOT
Stops a running Freqtrade bot instance.

**Direction:** Client → Server

```json
{
  "type": "STOP_BOT",
  "id": "msg_002",
  "data": {
    "bot_name": "my_trading_bot"
  }
}
```

#### RESTART_BOT
Restarts a Freqtrade bot instance.

**Direction:** Client → Server

```json
{
  "type": "RESTART_BOT",
  "id": "msg_003",
  "data": {
    "bot_name": "my_trading_bot",
    "freqai_model": {
      "filename": "updated_model.pkl",
      "content_b64": "TmV3TW9kZWxEYXRh..."
    }
  }
}
```

#### GET_BOT_STATUS
Requests the current status of a specific bot.

**Direction:** Client → Server

```json
{
  "type": "GET_BOT_STATUS",
  "id": "msg_004",
  "data": {
    "bot_name": "my_trading_bot"
  }
}
```

#### GET_ALL_BOTS_STATUS
Requests status of all running bots.

**Direction:** Client → Server

```json
{
  "type": "GET_ALL_BOTS_STATUS",
  "id": "msg_005",
  "data": {}
}
```

### 2. Status Response Messages

#### BOT_STATUS
Provides detailed bot status information.

**Direction:** Server → Client

```json
{
  "type": "BOT_STATUS",
  "id": "msg_006",
  "data": {
    "bot_name": "my_trading_bot",
    "status": "running",
    "pid": 12345,
    "uptime": 3600,
    "active_trades": 2,
    "total_trades": 150,
    "profit": 1250.50,
    "last_update": "2025-12-08T10:30:00Z",
    "error_message": null
  }
}
```

#### ALL_BOTS_STATUS
Provides status of all bots.

**Direction:** Server → Client

```json
{
  "type": "ALL_BOTS_STATUS",
  "id": "msg_007",
  "data": {
    "bots": [
      {
        "bot_name": "bot_1",
        "status": "running",
        "pid": 12345
      },
      {
        "bot_name": "bot_2",
        "status": "stopped",
        "pid": null
      }
    ]
  }
}
```

### 3. Error Messages

#### ERROR
Indicates an error condition.

**Direction:** Server → Client

```json
{
  "type": "ERROR",
  "id": "msg_008",
  "data": {
    "code": "BOT_NOT_FOUND",
    "message": "Bot 'nonexistent_bot' not found",
    "details": {
      "bot_name": "nonexistent_bot"
    }
  }
}
```

### 4. System Messages

#### HEARTBEAT
Connection health check.

**Direction:** Client ↔ Server

```json
{
  "type": "HEARTBEAT",
  "id": "msg_009",
  "data": {
    "timestamp": "2025-12-08T10:00:00Z"
  }
}
```

#### SYSTEM_STATUS
Overall system health information.

**Direction:** Server → Client

```json
{
  "type": "SYSTEM_STATUS",
  "id": "msg_010",
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "uptime": 86400,
    "active_bots": 5,
    "total_bots": 10
  }
}
```

## Error Codes

| Code | Description |
|------|-------------|
| `BOT_NOT_FOUND` | Specified bot does not exist |
| `BOT_ALREADY_RUNNING` | Bot is already in running state |
| `BOT_NOT_RUNNING` | Bot is not currently running |
| `INVALID_CONFIG` | Bot configuration is invalid |
| `MODEL_LOAD_FAILED` | FreqAI model loading failed |
| `SYSTEM_ERROR` | Internal system error |
| `AUTH_FAILED` | Authentication failed |

## FreqAI Model Transfer

### Model Encoding Process
1. **Compression:** Models are compressed using standard algorithms
2. **Base64 Encoding:** Binary data is converted to Base64 string
3. **Metadata:** Model information is included in transfer payload

### Transfer Payload Structure
```json
{
  "filename": "model_name.pkl",
  "content_b64": "Base64EncodedModelData...",
  "metadata": {
    "algorithm": "LightGBM",
    "features": ["rsi", "macd", "volume"],
    "accuracy": 0.85
  }
}
```

### Model Loading Process
1. **Decoding:** Base64 string is decoded to binary
2. **Decompression:** Data is decompressed if needed
3. **Validation:** Model integrity is verified
4. **Loading:** Model is loaded into Freqtrade FreqAI system

## Connection Management

### Connection States
- **CONNECTING:** Establishing WebSocket connection
- **CONNECTED:** Active connection established
- **AUTHENTICATING:** Authentication in progress
- **AUTHENTICATED:** Successfully authenticated
- **DISCONNECTED:** Connection lost

### Reconnection Strategy
- **Exponential Backoff:** Progressive delay between reconnection attempts
- **Maximum Retries:** Configurable retry limit
- **State Preservation:** Maintain session state across reconnections

### Authentication
```json
{
  "type": "AUTHENTICATE",
  "id": "auth_001",
  "data": {
    "token": "jwt_token_here",
    "agent_id": "ai_agent_001"
  }
}
```

## Best Practices

### Client Implementation
1. **Message Correlation:** Always include unique `id` for request tracking
2. **Error Handling:** Implement proper error handling for all message types
3. **Connection Monitoring:** Monitor connection health and implement reconnection logic
4. **Rate Limiting:** Respect server rate limits and implement backoff strategies

### Server Implementation
1. **Validation:** Validate all incoming messages and data
2. **Idempotency:** Ensure operations are idempotent where possible
3. **Logging:** Log all operations for debugging and auditing
4. **Resource Management:** Properly manage bot processes and resources

### Performance Considerations
- **Message Size:** Keep messages reasonably sized (< 1MB)
- **Frequency:** Avoid excessive status polling; use subscriptions
- **Compression:** Consider message compression for large payloads
- **Batching:** Batch multiple operations when possible

## Versioning

### Protocol Versions
- **v1.0:** Initial release with basic bot control
- **v1.1:** Added FreqAI model transfer capabilities
- **v1.2:** Enhanced error handling and status reporting

### Backward Compatibility
- New message types are additive
- Existing message formats remain unchanged
- Version negotiation during connection handshake

## Security Considerations

### Transport Security
- **WSS Required:** Use WebSocket Secure (WSS) in production
- **TLS 1.3:** Minimum TLS version requirement
- **Certificate Validation:** Proper certificate chain validation

### Authentication
- **JWT Tokens:** Bearer token authentication
- **Token Expiration:** Implement proper token lifecycle management
- **Agent Identification:** Unique agent identification and authorization

### Authorization
- **Role-Based Access:** Different permission levels for operations
- **Bot Ownership:** Users can only control their own bots
- **Operation Limits:** Rate limiting and resource quotas

---

**Version:** 1.2.0
**Last Updated:** 2025-12-08
**Status:** Active</content>
<parameter name="filePath">/home/taras/Documents/Opencode_NEW/jules_freqtrade_project/MCP_PROTOCOL.md