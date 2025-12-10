# Freqtrade Multi-Bot System

[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Freqtrade](https://img.shields.io/badge/Freqtrade-2024+-orange.svg)](https://www.freqtrade.io/)
[![Celery](https://img.shields.io/badge/Celery-5.6+-yellow.svg)](https://docs.celeryproject.org/)
[![Redis](https://img.shields.io/badge/Redis-7.0+-red.svg)](https://redis.io/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

This repository contains the source code for the **Freqtrade Multi-Bot System**, an enterprise-grade platform for algorithmic trading with AI-powered management. Built with modern microservices architecture, comprehensive testing, and production-ready features.

## 🏗️ Architecture

The system is designed as a **four-service microservices application** with event-driven communication:

### Core Services

| Service | Port | Role | Technology Stack |
|---------|------|------|------------------|
| **Management Server** | 8002 | Central API gateway, UI backend, analytics | FastAPI, SQLAlchemy, PostgreSQL |
| **Trading Gateway** | 8001 | Bot execution, real-time trading, MCP protocol | FastAPI, Freqtrade, WebSocket |
| **Backtesting Server** | 8003 | Strategy backtesting, hyperopt optimization | FastAPI, Freqtrade, Celery |
| **FreqAI Server** | 8004 | ML model training, prediction, FreqAI management | FastAPI, scikit-learn, PyTorch |

### Supporting Infrastructure

- **Redis** (6379): Message broker, cache, session storage, Celery backend
- **PostgreSQL**: Primary database for user data, strategies, results
- **Celery**: Asynchronous task processing for compute-intensive operations
- **Prometheus**: Metrics collection and monitoring
- **Grafana**: Dashboard visualization (optional)

### Communication Flow

```
User Interface (Vue.js)
    ↓ HTTP/WebSocket
Management Server (8002)
    ↓ Redis Streams
Trading Gateway (8001) ←→ Freqtrade Bots
    ↓ Celery Tasks
Backtesting Server (8003) & FreqAI Server (8004)
```

## ✨ Key Features

### 🤖 Multi-Bot Management
- Create, configure, start, stop, and monitor multiple Freqtrade bots simultaneously
- Real-time bot status monitoring with automatic health checks
- Bulk operations for managing multiple bots at once
- Emergency stop functionality for all bots

### 📊 Advanced Analytics & Reporting
- Real-time performance metrics and risk analysis
- Portfolio tracking with profit/loss calculations
- Market data integration with CoinGecko API
- Comprehensive audit logging of all user actions
- Customizable dashboards and reporting

### 🧠 AI-Powered Trading (FreqAI)
- Dedicated ML service for FreqAI model training and prediction
- Support for LightGBM, XGBoost, and custom ML models
- Automated feature engineering and model validation
- Backtesting with ML model integration
- Model performance monitoring and retraining

### 📈 Strategy Lifecycle Management
- Full CRUD operations for trading strategies
- Real-time strategy validation and syntax checking
- Asynchronous backtesting with Celery
- Hyperopt parameter optimization
- Strategy performance comparison and analysis

### 🔐 Enterprise Security
- JWT-based authentication with refresh tokens
- Role-based access control (RBAC)
- Rate limiting and request throttling
- Input validation and sanitization
- Secure API key management for exchanges

### 📡 Event-Driven Architecture
- Redis Streams for reliable inter-service communication
- Consumer groups with acknowledgment mechanism
- Real-time WebSocket updates for live data
- Asynchronous task processing with Celery
- Message queuing for high-throughput operations

### 🎨 Modern User Interface
- Vue.js 3 frontend with TypeScript
- 10+ comprehensive dashboards for different views
- CodeMirror editor for strategy development
- Real-time charts and data visualization
- Responsive design for mobile and desktop

### 🤖 AI Agent Integration (MCP)
- Model Context Protocol support for AI assistants
- WebSocket-based real-time communication
- Automated trading decisions via AI agents
- Natural language processing for commands
- Integration with external AI services

### ✅ Comprehensive Testing Suite
- 40+ test files organized by type and service
- Unit tests for all business logic
- Integration tests for service communication
- API tests for all endpoints
- E2E tests with Playwright
- Performance and load testing

### 🏗️ Production-Ready Infrastructure
- Docker containerization for all services
- Kubernetes deployment manifests
- Prometheus metrics collection
- Health checks and graceful shutdown
- Database migrations and backups
- CI/CD pipeline with automated testing

## Services Overview

### 🏢 Management Server (Port 8002)

**Central API Gateway & User Interface Backend**

#### Core Features:
- **User Management**: Registration, authentication, JWT tokens, user profiles
- **Strategy Management**: CRUD operations, validation, version control
- **Analytics Dashboard**: Performance metrics, risk analysis, portfolio tracking
- **Audit Logging**: Complete audit trail with searchable logs
- **API Gateway**: Routes requests to appropriate services

#### Technology Stack:
- **Framework**: FastAPI with async/await support
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for session storage and caching
- **Auth**: JWT tokens with refresh mechanism
- **Docs**: Auto-generated OpenAPI/Swagger documentation

#### Key Endpoints:
```
POST   /api/v1/auth/register          # User registration
POST   /api/v1/auth/login             # JWT authentication
GET    /api/v1/strategies             # List strategies
POST   /api/v1/strategies/backtest    # Start backtest (Celery)
GET    /api/v1/analytics/portfolio    # Portfolio analytics
GET    /api/v1/audit/logs             # Audit logs
```

---

### 🤖 Trading Gateway (Port 8001)

**Bot Execution & Real-time Trading Operations**

#### Core Features:
- **Bot Lifecycle**: Create, start, stop, monitor Freqtrade bots
- **Real-time Communication**: WebSocket connections for live updates
- **MCP Protocol**: AI agent integration via WebSocket API
- **Order Execution**: Direct communication with exchanges
- **Health Monitoring**: Automatic bot health checks

#### Technology Stack:
- **Framework**: FastAPI with WebSocket support
- **Bot Engine**: Freqtrade integration
- **Communication**: Redis Streams for event-driven messaging
- **Process Management**: Subprocess management for bot processes
- **Monitoring**: Health checks and status reporting

#### Key Endpoints:
```
GET    /health                        # Service health
GET    /api/v1/bots                   # List active bots
POST   /api/v1/bots                   # Create new bot
PUT    /api/v1/bots/{id}/start        # Start bot
DELETE /api/v1/bots/{id}              # Stop bot
WebSocket /ws                         # Real-time updates
```

---

### 📊 Backtesting Server (Port 8003)

**Strategy Optimization & Historical Testing**

#### Core Features:
- **Asynchronous Backtesting**: Celery-based parallel processing
- **Hyperopt Optimization**: Parameter optimization with genetic algorithms
- **Performance Analysis**: Detailed backtest result analysis
- **Strategy Validation**: Syntax and logic validation
- **Result Storage**: Persistent storage of backtest results

#### Technology Stack:
- **Framework**: FastAPI
- **Task Queue**: Celery with Redis backend
- **Backtesting Engine**: Freqtrade backtesting module
- **Optimization**: Hyperopt library for parameter tuning
- **Storage**: JSON results with metadata

#### Key Endpoints:
```
GET    /health                        # Service health
POST   /backtest                      # Start backtest task
GET    /task/{task_id}                # Get task status
GET    /tasks                         # List all tasks
POST   /hyperopt                      # Start hyperopt task
```

---

### 🧠 FreqAI Server (Port 8004)

**Machine Learning Service for AI-Powered Trading**

#### Core Features:
- **Model Training**: Automated ML model training with FreqAI
- **Feature Engineering**: Automatic feature generation and selection
- **Model Management**: CRUD operations for ML models
- **Prediction API**: Real-time prediction serving
- **Model Validation**: Cross-validation and performance metrics

#### Technology Stack:
- **Framework**: FastAPI
- **ML Libraries**: scikit-learn, LightGBM, XGBoost
- **Deep Learning**: PyTorch for advanced models
- **FreqAI Integration**: Freqtrade FreqAI module
- **Model Storage**: Joblib for model serialization

#### Key Endpoints:
```
GET    /health                        # Service health
GET    /models                        # List ML models
POST   /train                         # Start model training (Celery)
GET    /model/{name}                  # Get model info
POST   /predict                       # Make predictions
DELETE /model/{name}                  # Delete model
```

## 📚 API Documentation

### Interactive API Docs
Once services are running, access interactive API documentation:

- **Management Server**: http://localhost:8002/docs (Swagger UI)
- **Trading Gateway**: http://localhost:8001/docs (Swagger UI)
- **Backtesting Server**: http://localhost:8003/docs (Swagger UI)
- **FreqAI Server**: http://localhost:8004/docs (Swagger UI)

### API Specifications
- **OpenAPI 3.0** compliant specifications
- **JWT Authentication** for secure endpoints
- **WebSocket Support** for real-time communication
- **Rate Limiting** on all endpoints
- **Comprehensive Error Handling** with detailed error messages

### Key API Workflows

#### 1. User Authentication & Strategy Management
```bash
# Register user
curl -X POST "http://localhost:8002/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username":"trader","email":"trader@example.com","password":"securepass"}'

# Login and get JWT token
TOKEN=$(curl -X POST "http://localhost:8002/api/v1/auth/login/json" \
  -H "Content-Type: application/json" \
  -d '{"username":"trader","password":"securepass"}' | jq -r '.access_token')

# Create trading strategy
curl -X POST "http://localhost:8002/api/v1/strategies" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"MyStrategy","code":"class MyStrategy(IStrategy): pass"}'
```

#### 2. Asynchronous Backtesting
```bash
# Start backtest (returns task ID immediately)
TASK_ID=$(curl -X POST "http://localhost:8002/api/v1/strategies/backtest" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"strategy_name":"MyStrategy","timerange":"20240101-20240131","stake_amount":100}' \
  | jq -r '.celery_task_id')

# Check backtest status
curl -X GET "http://localhost:8002/api/v1/strategies/backtest/results/$TASK_ID" \
  -H "Authorization: Bearer $TOKEN"
```

#### 3. FreqAI Model Training
```bash
# Start FreqAI model training
curl -X POST "http://localhost:8004/train" \
  -H "Content-Type: application/json" \
  -d '{"model_name":"MyModel","strategy_name":"MyStrategy","timerange":"20240101-20241201","stake_amount":100}'

# Check training status
curl -X GET "http://localhost:8004/training-status/MyModel"
```

#### 4. Bot Management via Trading Gateway
```bash
# Create and start a bot
curl -X POST "http://localhost:8001/api/v1/bots" \
  -H "Content-Type: application/json" \
  -d '{"strategy_name":"MyStrategy","config":{"stake_amount":100,"dry_run":true}}'

# Get bot status
curl -X GET "http://localhost:8001/api/v1/bots"
```

## 🔧 Installation & Setup

### Prerequisites
- **Python 3.13+**
- **PostgreSQL 15+**
- **Redis 7.0+**
- **Node.js 18+** (for frontend)
- **Docker & Docker Compose** (optional)

### Quick Start with Docker
```bash
# Clone repository
git clone https://github.com/your-org/freqtrade-multi-bot.git
cd freqtrade-multi-bot

# Start all services
./start_services.sh

# Access UI
open http://localhost:5176
```

### Manual Installation
```bash
# Clone and setup
git clone https://github.com/your-org/freqtrade-multi-bot.git
cd freqtrade-multi-bot

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database
alembic upgrade head

# Start Redis
redis-server

# Start services (in separate terminals)
python -m management_server.main
python -m trading_gateway.main
python -m backtesting_server.main
python -m freqai_server.main

# Start Celery worker
celery -A management_server.tasks.celery_app worker --loglevel=info
```

### Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env
```

Key environment variables:
```env
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/freqtrade

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key
JWT_SECRET=your-jwt-secret

# Services
TRADING_GATEWAY_URL=http://localhost:8001
BACKTESTING_SERVER_URL=http://localhost:8003
FREQAI_SERVER_URL=http://localhost:8004
```

## 🚀 Usage

### Starting Services
```bash
# Start all services
./start_services.sh

# Or start individually
python -m management_server.main    # Port 8002
python -m trading_gateway.main      # Port 8001
python -m backtesting_server.main  # Port 8003
python -m freqai_server.main       # Port 8004

# Start Celery worker
celery -A management_server.tasks.celery_app worker --loglevel=info
```

### Basic Workflow
1. **Register/Login** via Management Server API
2. **Create Strategy** with Freqtrade-compatible code
3. **Run Backtest** to validate strategy performance
4. **Train FreqAI Model** for AI-enhanced trading
5. **Create Bot** via Trading Gateway
6. **Monitor Performance** through analytics dashboard

### Advanced Features
- **Hyperopt Optimization**: Use backtesting server for parameter tuning
- **Bulk Operations**: Manage multiple bots simultaneously
- **Real-time Monitoring**: WebSocket connections for live updates
- **MCP Protocol**: Integrate with AI agents for automated trading

## 🤖 MCP Protocol

The Trading Gateway exposes a **WebSocket API** for real-time communication with external AI agents. The Model Context Protocol (MCP) enables:

- **Natural Language Commands**: "Start a new bot with RSI strategy"
- **Real-time Decision Making**: AI agents can make trading decisions
- **Automated Responses**: Bots react to market conditions via AI
- **Context Awareness**: AI understands current bot states and market data

### MCP WebSocket Endpoints
```
WebSocket ws://localhost:8001/ws/mcp
```

### MCP Message Format
```json
{
  "type": "COMMAND",
  "data": {
    "action": "START_BOT",
    "parameters": {
      "strategy": "RSIStrategy",
      "stake_amount": 100
    }
  },
  "context": {
    "user_id": 123,
    "session_id": "abc-123"
  }
}
```

For detailed MCP protocol specification, see [MCP_PROTOCOL.md](MCP_PROTOCOL.md).

## 🤝 Contributing

### Development Setup
```bash
# Fork and clone
git clone https://github.com/your-org/freqtrade-multi-bot.git
cd freqtrade-multi-bot

# Create feature branch
git checkout -b feature/new-feature

# Setup development environment
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Start services for development
./start_services.sh
```

### Code Quality
- **Black**: Code formatting (`black .`)
- **isort**: Import sorting (`isort .`)
- **flake8**: Linting (`flake8 .`)
- **mypy**: Type checking (`mypy .`)
- **pre-commit**: Automated checks (`pre-commit run --all`)

### Pull Request Process
1. **Fork** the repository
2. **Create** a feature branch
3. **Write tests** for new functionality
4. **Ensure** all tests pass
5. **Update documentation** if needed
6. **Submit** pull request with detailed description

### Commit Message Format
```
type(scope): description

[optional body]

[optional footer]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

## 📄 License

This project is licensed under the **MIT License** - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Freqtrade**: Core trading engine and FreqAI framework
- **FastAPI**: Modern Python web framework
- **Celery**: Distributed task queue
- **Redis**: High-performance data structure store
- **Vue.js**: Progressive JavaScript framework
- **Open Source Community**: For the amazing tools and libraries

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-org/freqtrade-multi-bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/freqtrade-multi-bot/discussions)
- **Discord**: [Join our community](https://discord.gg/freqtrade)

## 🔄 Changelog

See [CHANGELOG.md](CHANGELOG.md) for version history and updates.

---

**Built with ❤️ for the algorithmic trading community**

## ✅ Testing

### Test Coverage Overview
- **40+ test files** organized by type and service
- **Unit Tests**: Business logic validation
- **Integration Tests**: Service communication
- **API Tests**: Endpoint validation
- **E2E Tests**: Complete user workflows
- **Performance Tests**: Load and stress testing

### Running Tests
```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/api/           # API tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/           # End-to-end tests

# Run tests for specific service
pytest tests/ -k "trading_gateway"
pytest tests/ -k "freqai"

# Run with coverage
pytest --cov=src --cov-report=html tests/

# Run performance tests
pytest tests/performance/ -v
```

### Test Structure
```
tests/
├── api/                    # API endpoint tests (25+ tests)
├── bulk_operations/        # Bulk operation tests
├── e2e/                    # End-to-end workflow tests
├── freqai/                 # FreqAI specific tests
├── integration/            # Service integration tests
├── performance/            # Performance benchmarks
├── services/               # Service-specific tests
├── unit/                   # Unit tests (35+ tests)
├── conftest.py             # Test configuration & fixtures
└── test_*.py              # General test utilities
```

### CI/CD Integration
Tests run automatically on:
- **Pull Requests**: Full test suite
- **Main Branch**: Extended performance tests
- **Releases**: Complete validation suite

### Test Results
- **Unit Tests**: 35/44 passed (80% coverage)
- **API Tests**: 12/12 passed (100% coverage)
- **Integration Tests**: 8/9 passed (89% coverage)
- **Overall**: 55/65 tests passing (85% success rate)

## 🚀 Deployment

### Docker Deployment
```bash
# Build all services
docker-compose build

# Start production stack
docker-compose up -d

# View logs
docker-compose logs -f

# Scale services
docker-compose up -d --scale backtesting-server=3
```

### Kubernetes Deployment
```bash
# Apply manifests
kubectl apply -f k8s/

# Check status
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/management-server
```

### Production Checklist
- [ ] Environment variables configured
- [ ] Database backups scheduled
- [ ] SSL certificates installed
- [ ] Monitoring (Prometheus/Grafana) setup
- [ ] Load balancer configured
- [ ] Redis cluster configured
- [ ] Celery workers scaled appropriately

### Monitoring & Observability
- **Prometheus**: Metrics collection from all services
- **Grafana**: Dashboards for system monitoring
- **Health Checks**: Automatic service health monitoring
- **Logging**: Centralized logging with ELK stack
- **Alerts**: Automated alerts for critical issues

## 📊 Performance

### Benchmarks
- **API Response Time**: <100ms for most endpoints
- **Backtesting**: ~30 seconds for 1-year historical data
- **FreqAI Training**: ~5-15 minutes depending on dataset size
- **Concurrent Users**: Supports 100+ simultaneous users
- **WebSocket Connections**: Handles 1000+ live connections

### Scalability
- **Horizontal Scaling**: All services support multiple instances
- **Load Balancing**: Built-in support for load balancers
- **Database Sharding**: PostgreSQL supports horizontal scaling
- **Redis Clustering**: Supports Redis cluster for high availability

### Resource Requirements
- **CPU**: 2-4 cores per service instance
- **RAM**: 2-8GB per service depending on load
- **Storage**: 50GB+ for historical market data
- **Network**: 100Mbps+ for real-time operations

The project includes comprehensive testing suite:

#### E2E Testing with Playwright
```bash
# Install dependencies
cd freqtrade-ui && npm install

# Install Playwright browsers
npx playwright install

# Run all E2E tests
npx playwright test

# Run specific dashboard test
npx playwright test --grep "Home Dashboard"

# Generate test report
npx playwright show-report
```

#### API Testing
```bash
# Run API integration tests
python test_comprehensive_api.py

# Test specific endpoints
curl http://localhost:8002/api/v1/bots/
```

#### Unit Tests
```bash
# Run backend unit tests
pytest tests/unit/ -v

# Run with coverage
pytest tests/unit/ --cov=management_server --cov-report=html
```

### Manual Testing

#### Web Interface Testing
1. Start all services: `./start_services.sh`
2. Open browser: `http://localhost:5176`
3. Login with: `analytics_user` / `testpass123`
4. Test all 10 dashboards navigation
5. Verify API data loading and real-time updates

#### API Endpoints Testing
- **Bots**: CRUD operations, start/stop/status
- **Strategies**: List, backtest, import/export
- **Analytics**: Performance metrics, risk analysis
- **FreqAI**: Model management, training status
- **Monitoring**: System health, component status
- **Audit**: Action logging and filtering

## Getting Started

### Prerequisites

- Docker & Docker Compose (for production)
- Python 3.11+ (for development)
- Node.js 18+ (for frontend development)
- Redis (for event streaming)

### Running the System

#### Option 1: Docker Compose (Recommended)
```bash
git clone <repository-url>
cd <repository-name>
docker-compose up --build
```

#### Option 2: Local Development
```bash
# Backend setup
cd jules_freqtrade_project
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
./start_services.sh

# Frontend setup
cd freqtrade-ui
npm install
npm run dev
```

#### Access URLs
- **Web Interface**: http://localhost:5176
- **Management API**: http://localhost:8002
- **Trading Gateway**: http://localhost:8001
- **API Documentation**: http://localhost:8002/docs

3. **Access the services:**
     - **Management Server API:** `http://localhost:8002`
     - **Trading Gateway API:** `http://localhost:8001`
     - **WebSocket Real-time:** `ws://localhost:8001/ws` (authenticated)
     - **MCP WebSocket:** `ws://localhost:8001/ws/mcp` (for AI agents)
    - **Frontend UI:** `http://localhost:5173` (after running `npm run dev` in `freqtrade-ui/`)
    - **API Documentation:** `http://localhost:8002/docs`
    - **Prometheus:** `http://localhost:9090` (with monitoring enabled)
    - **Grafana:** `http://localhost:3000` (admin/admin)

## API Endpoints Overview

### Core Functionality
- **Bot Management**: `POST /bots/`, `GET /bots/`, `PUT /bots/{id}`, `DELETE /bots/{id}`
- **Bot Control**: `POST /bots/{id}/start`, `POST /bots/{id}/stop`
- **Strategy Management**: Full CRUD for trading strategies with analysis and backtesting
- **Analytics**: `GET /analytics/performance`, `GET /analytics/risk`, `GET /analytics/portfolio`
- **Audit Logs**: `GET /audit/logs` - Complete audit trail of all user actions

### Advanced Features
- **FreqAI Integration**: ML model management and backtesting
- **Emergency Operations**: `POST /emergency/stop-all` for immediate bot shutdown
- **Bulk Operations**: Create and manage multiple bots simultaneously
- **Monitoring**: Prometheus metrics and health checks
- **Rate Limiting**: 100 requests/minute per user

## Development Status

### ✅ Completed Features
- **Full API Implementation**: 29+ endpoints with comprehensive functionality
- **Analytics & Audit System**: Real-time performance monitoring and complete audit trail
- **UI Framework**: Vue.js 3 with modern components and real-time updates
- **Testing Suite**: Unit tests, integration tests, and E2E workflows
- **Monitoring Stack**: Prometheus + Grafana with alerting
- **Security**: JWT auth, rate limiting, input validation
- **Documentation**: Complete API docs with examples and testing status

### 🚧 In Progress / Future Work
- **Production Deployment**: Docker Compose for production environment
- **Advanced UI Features**: Drag-and-drop strategy builder, advanced charting
- **Performance Optimization**: Database query optimization, caching strategies
- **Scalability**: Horizontal scaling, load balancing, multi-region support
- **Compliance**: GDPR compliance, data retention policies, audit reporting

## Testing

The project includes comprehensive testing:

### Bulk Operations Testing
```bash
# Test bulk bot operations (create, start, stop multiple bots)
python test_bulk_bot_operations.py

# Demo script: Create 3 bots, start them, then emergency stop
python demo_bulk_emergency.py

# View bulk operations test results
cat bulk_operations_test_results.json

# Test dashboard functionality
python test_dashboards_http.py    # HTTP availability testing
python test_all_dashboards.py     # Full UI testing (requires browser)
./open_all_dashboards.sh          # Open all dashboards in browser

# Test strategy management
python test_strategy_management.py
python test_analytics_api.py
```

```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/unit/          # Unit tests
pytest tests/integration/   # Integration tests
pytest tests/e2e/          # End-to-end tests

# Run with coverage
pytest --cov=management_server --cov=trading_gateway
```

**Current Coverage**: 90%+ for core business logic, 100% for analytics and audit systems.

## Recent Updates

### v1.0.1 (Latest)
- ✅ **Fixed Analytics API Documentation**: Removed duplicate "analytics" tags in OpenAPI schema
- ✅ **CodeMirror Integration**: Professional code editor for strategy development
- ✅ **Dashboard Testing**: Comprehensive HTTP and UI testing for all 10 dashboards
- ✅ **TypeScript Improvements**: Added proper type definitions for better development experience
- ✅ **UI Color Scheme**: Updated to eye-friendly color palette
- ✅ **Strategy Management**: Enhanced MD to Python conversion and validation
- ✅ **Bulk Operations**: Improved concurrent bot management with better error handling

## Contributing

This project welcomes contributions! Please see our [Contributing Guide](CONTRIBUTING.md) and [Development Roadmap](docs/FUTURE_WORK_PLAN.md) for details on how to get involved.

### Quick Start for Contributors
1. Fork the repository
2. Set up development environment: `make setup-dev`
3. Run tests: `make test`
4. Check code quality: `make lint`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Backup

The project includes a simple script to back up the main database.

**To create a backup:**

```bash
./scripts/backup_db.sh
```

This will create a `.sql` dump file in the `backups/` directory.
