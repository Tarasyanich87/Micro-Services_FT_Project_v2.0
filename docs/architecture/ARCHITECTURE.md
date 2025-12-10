# Architecture Document: Freqtrade Multi-Bot System

## 1. Core Principles

The architecture is designed around the following principles:

- **Separation of Concerns:** Business logic is separated from operational trading logic.
- **Scalability:** The system can be deployed across multiple servers to optimize for both computational power and low-latency trading.
- **Extensibility:** The system is designed to be easily integrated with external AI agents and other trading systems via a well-defined protocol.
- **Microservices Design:** Two independent services communicate via Redis Streams for reliability and decoupling.
- **AI Integration:** Native support for FreqAI machine learning models with real-time prediction capabilities.

## 2. System Architecture

### High-Level Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Management     │    │     Redis       │    │   Trading       │
│    Server       │◄──►│    Streams      │◄──►│   Gateway       │
│                 │    │                 │    │                 │
│ • User API      │    │ • Event Bus     │    │ • Bot Control   │
│ • FreqAI API    │    │ • Message Queue │    │ • Model Transfer│
│ • Analytics     │    │ • Pub/Sub       │    │ • Health Checks │
└─────────────────┘    └─────────────────┘    └─────────────────┘
          │                       │                       │
          └───────────────────────┼───────────────────────┘
                                  ▼
                     ┌─────────────────┐
                     │   Freqtrade     │
                     │     Bots        │
                     │                 │
                     │ • Live Trading  │
                     │ • FreqAI Models │
                     │ • Risk Mgmt     │
                     └─────────────────┘
```

### Service Components

#### Management Server
- **Technology:** FastAPI, SQLAlchemy, Pydantic
- **Responsibilities:**
  - User authentication and authorization
  - Bot lifecycle management (CRUD operations)
  - Strategy management and validation
  - FreqAI model training and deployment
  - Analytics and performance monitoring
  - REST API for external integrations

#### Trading Gateway
- **Technology:** FastAPI, WebSocket support
- **Responsibilities:**
  - Direct Freqtrade bot process management
  - Real-time status monitoring
  - Model transfer and loading
  - FreqAI model caching and lifecycle management
  - WebSocket MCP protocol implementation
  - Emergency stop functionality

#### Redis Streams
- **Purpose:** Reliable inter-service communication
- **Features:**
  - Event-driven architecture
  - Message persistence
  - Consumer groups for load balancing
  - Real-time event streaming

## 3. Data Flow

### Bot Startup Sequence

1. **Management Server** receives start command via REST API
2. **Management Server** validates user permissions and bot configuration
3. **Management Server** prepares FreqAI model (if applicable):
   - Loads model file from storage
   - Compresses and Base64 encodes model
   - Prepares model metadata
4. **Management Server** publishes `START_BOT` event to Redis Stream
5. **Trading Gateway** consumes event and validates data
6. **Trading Gateway** starts Freqtrade process with configuration
7. **Trading Gateway** loads FreqAI model into running bot
8. **Trading Gateway** monitors bot status and reports back

### FreqAI Model Transfer

The system implements a sophisticated model transfer mechanism:

1. **Model Encoding:** FreqAI models are compressed and Base64 encoded for transfer
2. **Redis Transfer:** Models are sent via Redis Streams for reliability
3. **Model Decoding:** Trading Gateway decodes and loads models into Freqtrade
4. **Live Updates:** Models can be updated without restarting bots

Example transfer payload:
```json
{
  "type": "START_BOT",
  "data": {
    "bot_name": "freqai_bot_1",
    "freqai_model": {
      "filename": "LightGBMRegressor_model.pkl",
      "content_b64": "U29tZUJpZ0Jhc2U2NENvbnRlbnQ..."
    }
  }
}
```

## 4. Security Architecture

### Authentication & Authorization
- **JWT Tokens:** Bearer token authentication for API access
- **Role-Based Access Control:** User, Admin, and Service roles
- **Password Security:** Argon2 hashing with salt
- **Session Management:** Secure token expiration and refresh

### API Security
- **Rate Limiting:** Redis-backed rate limiting per user/IP
- **Input Validation:** Pydantic models for all API inputs
- **SQL Injection Protection:** SQLAlchemy ORM usage
- **CORS Configuration:** Controlled cross-origin access

### Data Protection
- **Model Encryption:** FreqAI models encrypted at rest
- **Secure Storage:** Isolated file system access
- **Audit Logging:** Comprehensive action logging

## 5. Scalability Considerations

### Horizontal Scaling
- **Stateless Services:** Both services can be scaled independently
- **Load Balancing:** Redis consumer groups for event processing
- **Database Connection Pooling:** Efficient connection management

### Performance Optimization
- **Async Operations:** Full async/await implementation
- **Caching:** Redis caching for frequent queries
- **Background Tasks:** Celery for long-running operations
- **Connection Pooling:** Optimized database and Redis connections

## 6. Deployment Architecture

### Docker Containerization
- **Multi-service Setup:** Postgres, Redis, Management Server, Trading Gateway
- **Volume Management:** Persistent data storage
- **Network Isolation:** Secure inter-service communication

### Production Considerations
- **Health Checks:** Comprehensive service monitoring
- **Logging:** Structured logging with correlation IDs
- **Metrics:** Performance monitoring and alerting
- **Backup:** Automated database and model backups

## 7. Integration Points

### Freqtrade Integration
- **API Communication:** REST API calls to Freqtrade bots
- **Configuration Management:** Dynamic config updates
- **Status Monitoring:** Real-time bot status tracking

### FreqAI Integration
- **Model Management:** Training, storage, and deployment
- **Prediction Pipeline:** Real-time prediction serving
- **Feature Engineering:** Automated feature generation

### External Systems
- **MCP Protocol:** WebSocket-based AI agent communication
- **REST APIs:** Standard HTTP APIs for integrations
- **Event Streaming:** Redis Streams for event-driven integrations

## 8. Monitoring & Observability

### Application Metrics
- **Bot Performance:** Win rate, P&L, drawdown tracking
- **System Health:** CPU, memory, disk usage
- **API Performance:** Response times, error rates
- **Event Processing:** Message throughput and latency

### Logging Strategy
- **Structured Logging:** JSON format with context
- **Log Levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Correlation IDs:** Request tracing across services
- **Audit Logs:** Security and compliance logging

## 9. Disaster Recovery

### Backup Strategy
- **Database Backups:** Automated PostgreSQL dumps
- **Model Backups:** FreqAI model versioning
- **Configuration Backups:** Bot and strategy configs

### Recovery Procedures
- **Service Restart:** Automated recovery from failures
- **Data Recovery:** Point-in-time database restoration
- **Model Recovery:** Model rollback capabilities

## 10. Future Enhancements

### Planned Features
- **Multi-tenant Architecture:** User isolation improvements
- **Advanced Analytics:** Machine learning-based insights
- **Real-time Alerts:** Notification system integration
- **API Versioning:** Backward compatibility management

### Technology Evolution
- **Kubernetes:** Container orchestration
- **Service Mesh:** Advanced service communication
- **Event Sourcing:** Complete audit trail
- **GraphQL:** Enhanced API capabilities

---

**Version:** 1.0.0
**Last Updated:** 2025-12-08
**Status:** Production Ready</content>
<parameter name="filePath">/home/taras/Documents/Opencode_NEW/jules_freqtrade_project/ARCHITECTURE.md