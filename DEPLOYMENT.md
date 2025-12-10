# Deployment Guide

This guide covers deployment options for the Freqtrade Multi-Bot System.

## Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Browser   │────│   Vue.js UI     │────│ Management API  │
│                 │    │  (Port 5176)   │    │  (Port 8002)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                     │
                                                     │
┌─────────────────┐    ┌─────────────────┐           │
│  Freqtrade Bots │────│ Trading Gateway │◄──────────┘
│                 │    │  (Port 8001)   │
└─────────────────┘    └─────────────────┘
                                                     │
┌─────────────────┐                                   │
│     Redis       │◄──────────────────────────────────┘
│  (Port 6379)    │
└─────────────────┘
```

## Deployment Options

### 1. Docker Compose (Recommended)

#### Prerequisites
- Docker Engine 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

#### Quick Start
```bash
# Clone repository
git clone <repository-url>
cd freqtrade-multibot-system

# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Access application
open http://localhost:5176
```

#### Docker Compose Configuration
```yaml
version: '3.8'
services:
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  management-server:
    build: ./management_server
    ports:
      - "8002:8002"
    environment:
      - DATABASE_URL=sqlite:///./freqtrade.db
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  trading-gateway:
    build: ./trading_gateway
    ports:
      - "8001:8001"
    environment:
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis

  frontend:
    build: ./freqtrade-ui
    ports:
      - "5176:80"
    depends_on:
      - management-server

volumes:
  redis_data:
```

### 2. Kubernetes Deployment

#### Prerequisites
- Kubernetes cluster (1.24+)
- kubectl configured
- Helm 3.x
- 8GB RAM minimum per node

#### Deploy with Helm
```bash
# Add helm repository
helm repo add freqtrade https://charts.freqtrade.io
helm repo update

# Install the chart
helm install freqtrade-multibot freqtrade/freqtrade-multibot \
  --set ingress.enabled=true \
  --set ingress.hosts[0].host=freqtrade.example.com
```

#### Manual Kubernetes Deployment
```bash
# Apply manifests
kubectl apply -f k8s/

# Check deployment status
kubectl get pods
kubectl get services
kubectl get ingress
```

### 3. Local Development Setup

#### Backend Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Initialize database
python init_db.py

# Start services
./start_services.sh
```

#### Frontend Setup
```bash
cd freqtrade-ui

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
```

## Environment Configuration

### Environment Variables

#### Management Server
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/freqtrade

# Redis
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret
JWT_EXPIRATION_HOURS=24

# External Services
TRADING_GATEWAY_URL=http://localhost:8001
```

#### Trading Gateway
```bash
# Redis
REDIS_URL=redis://localhost:6379

# Freqtrade
FREQTRADE_CONFIG_PATH=/path/to/config
FREQTRADE_USER_DATA_DIR=/path/to/user_data
```

#### Frontend
```bash
# API URLs
VITE_API_BASE_URL=http://localhost:8002/api/v1
VITE_WS_URL=ws://localhost:8001/ws
```

### Database Setup

#### SQLite (Development)
```bash
# Automatic setup with init_db.py
python init_db.py
```

#### PostgreSQL (Production)
```sql
CREATE DATABASE freqtrade;
CREATE USER freqtrade_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE freqtrade TO freqtrade_user;
```

### Redis Configuration

#### Single Instance
```redis.conf
# Basic configuration
port 6379
timeout 0
tcp-keepalive 300

# Persistence
save 900 1
save 300 10
save 60 10000

# Memory management
maxmemory 256mb
maxmemory-policy allkeys-lru
```

#### Redis Cluster (Production)
```bash
# Start Redis cluster
redis-cli --cluster create 127.0.0.1:7001 127.0.0.1:7002 127.0.0.1:7003
```

## Security Configuration

### SSL/TLS Setup

#### Nginx Reverse Proxy
```nginx
server {
    listen 443 ssl http2;
    server_name freqtrade.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:5176;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api {
        proxy_pass http://localhost:8002;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### Certbot (Let's Encrypt)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d freqtrade.example.com
```

### Authentication & Authorization

#### JWT Configuration
```python
# settings.py
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-jwt-secret")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = int(os.getenv("JWT_EXPIRATION_HOURS", 24))
```

#### User Management
```bash
# Create admin user
python -c "
from management_server.auth.service import AuthService
from management_server.database import SessionLocal

service = AuthService(SessionLocal())
user = service.create_user('admin@example.com', 'Admin User', 'secure_password')
print(f'Created user: {user.username}')
"
```

## Monitoring & Logging

### Application Monitoring

#### Prometheus Metrics
```python
# Add to management_server/main.py
from prometheus_fastapi_instrumentator import Instrumentator

app = create_application()
Instrumentator().instrument(app).expose(app)
```

#### Health Checks
```bash
# Application health
curl http://localhost:8002/health

# Database health
curl http://localhost:8002/api/v1/monitoring/health

# Redis health
redis-cli ping
```

### Logging Configuration

#### Structured Logging
```python
# logging.conf
[loggers]
keys=root,app

[handlers]
keys=console,file

[formatters]
keys=json

[formatter_json]
class=pythonjsonlogger.jsonlogger.JsonFormatter
format=%(asctime)s %(name)s %(levelname)s %(message)s

[handler_console]
class=StreamHandler
formatter=json
args=(sys.stdout,)

[handler_file]
class=FileHandler
formatter=json
args=('app.log', 'a')

[logger_app]
level=INFO
handlers=console,file
qualname=app
```

## Backup & Recovery

### Database Backup

#### SQLite
```bash
# Daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
sqlite3 freqtrade.db ".backup freqtrade_backup_$DATE.db"
```

#### PostgreSQL
```bash
# Daily backup
pg_dump freqtrade > freqtrade_backup_$(date +%Y%m%d).sql

# Restore
psql freqtrade < freqtrade_backup_20241201.sql
```

### Configuration Backup
```bash
# Backup configs
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
  freqtrade-ui/.env \
  management_server/.env \
  trading_gateway/.env \
  docker-compose.yml
```

## Troubleshooting

### Common Issues

#### Service Won't Start
```bash
# Check logs
docker-compose logs management-server
docker-compose logs trading-gateway

# Check resource usage
docker stats

# Restart services
docker-compose restart
```

#### Database Connection Issues
```bash
# Test database connection
python -c "
import sqlalchemy
engine = sqlalchemy.create_engine('DATABASE_URL')
connection = engine.connect()
print('Database connection successful')
"
```

#### Redis Connection Issues
```bash
# Test Redis connection
redis-cli -h localhost -p 6379 ping

# Check Redis logs
docker-compose logs redis
```

### Performance Tuning

#### Database Optimization
```sql
-- Create indexes
CREATE INDEX idx_bots_status ON bots(status);
CREATE INDEX idx_trades_bot_id ON trades(bot_id);
CREATE INDEX idx_audit_timestamp ON audit_logs(timestamp);
```

#### Redis Optimization
```redis.conf
# Connection pooling
tcp-keepalive 300
timeout 300

# Memory optimization
maxmemory 512mb
maxmemory-policy volatile-lru
```

## Scaling

### Horizontal Scaling

#### Load Balancer Configuration
```nginx
upstream management_servers {
    server 10.0.0.1:8002;
    server 10.0.0.2:8002;
    server 10.0.0.3:8002;
}

server {
    listen 80;
    location / {
        proxy_pass http://management_servers;
    }
}
```

#### Database Scaling
```bash
# Use connection pooling
# Configure read replicas
# Implement database sharding if needed
```

### Vertical Scaling

#### Resource Allocation
```yaml
# docker-compose.yml
services:
  management-server:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
        reservations:
          memory: 512M
          cpus: '0.5'
```

## Maintenance

### Regular Tasks

#### Update Dependencies
```bash
# Update Python packages
pip install --upgrade -r requirements.txt

# Update Node.js packages
cd freqtrade-ui && npm update

# Update Docker images
docker-compose pull
```

#### Clean Up
```bash
# Remove old Docker images
docker image prune -f

# Clean npm cache
npm cache clean --force

# Remove old logs
find . -name "*.log" -mtime +30 -delete
```

#### Security Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Docker images
docker-compose build --no-cache

# Rotate secrets
# Update passwords and API keys
```

This deployment guide provides comprehensive instructions for deploying the Freqtrade Multi-Bot System in various environments, from local development to production Kubernetes clusters.</content>
<parameter name="filePath">jules_freqtrade_project/DEPLOYMENT.md