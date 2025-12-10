# Repository Migration: From 2-Service to 4-Microservice Architecture

## 🚨 Important Notice

**This repository has undergone a major architectural transformation.**

The Freqtrade Multi-Bot System has evolved from a **2-service architecture** to a **4-microservice enterprise-grade platform**.

## 📋 What Changed

### Before (v1.x)
```
Management Server (8002) ←→ Trading Gateway (8001)
```

### After (v2.0)
```
Management Server (8002) ←→ Trading Gateway (8001)
    ↓                        ↓
Backtesting Server (8003) ←→ FreqAI Server (8004)
```

### Key Improvements in v2.0
- ✅ **4 independent microservices** with Redis Streams communication
- ✅ **Asynchronous task processing** with Celery
- ✅ **Enterprise-grade testing** (40+ test files, 85% coverage)
- ✅ **Production monitoring** with Prometheus/Grafana
- ✅ **Docker & Kubernetes** deployment ready
- ✅ **Comprehensive API documentation**
- ✅ **AI agent integration** via MCP protocol

## 🔄 Migration Guide

### For Existing Users
1. **Backup your data** from the old system
2. **Follow the new installation guide** in README.md
3. **Migrate strategies** using the new API endpoints
4. **Update your deployment scripts**

### For New Users
- Start with the [Quick Start Guide](README.md#quick-start)
- Use Docker for easiest deployment
- Check [API Documentation](API_DOCUMENTATION.md) for integration

## 📚 Documentation Updates

- **README.md**: Complete rewrite with new architecture
- **API_DOCUMENTATION.md**: Full API specs for all 4 services
- **Testing**: 40+ test files with comprehensive coverage
- **Deployment**: Docker, Kubernetes, and manual guides

## 🏗️ Architecture Overview

| Service | Port | Purpose | Tech Stack |
|---------|------|---------|------------|
| Management Server | 8002 | UI, API, Analytics | FastAPI, PostgreSQL |
| Trading Gateway | 8001 | Bot Management, MCP | FastAPI, Freqtrade |
| Backtesting Server | 8003 | Async Backtesting | FastAPI, Celery |
| FreqAI Server | 8004 | ML Training | FastAPI, scikit-learn |

## 🚀 Quick Start (New Architecture)

```bash
# Clone the repository
git clone https://github.com/your-org/freqtrade-multi-bot.git
cd freqtrade-multi-bot

# Start all services
./start_services.sh

# Access UI
open http://localhost:5176

# Check API docs
open http://localhost:8002/docs
```

## 🔗 Related Resources

- **Old Repository**: [v1.x Archive](https://github.com/your-org/freqtrade-multi-bot-v1)
- **Migration Guide**: [Full Migration Documentation](docs/MIGRATION.md)
- **API Documentation**: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

## ❓ Need Help?

- 📖 [Documentation](README.md)
- 🐛 [Issues](https://github.com/your-org/freqtrade-multi-bot/issues)
- 💬 [Discussions](https://github.com/your-org/freqtrade-multi-bot/discussions)

---

**🎉 Welcome to the next generation of algorithmic trading platforms!**