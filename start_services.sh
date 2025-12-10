#!/bin/bash

# Freqtrade Multi-Bot System - Complete Services Startup Script
# This script starts all services in the correct order with proper error handling

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
UI_DIR="$PROJECT_DIR/freqtrade-ui"
REDIS_PORT=6379
MGMT_PORT=8002
TG_PORT=8001
BACKTESTING_PORT=8003
FREQAI_PORT=8004
VITE_PORT=5176
LOG_DIR="$PROJECT_DIR/logs"

# Create log directory
mkdir -p "$LOG_DIR"

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✓ $1${NC}"
}

error() {
    echo -e "${RED}✗ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Check if port is in use
check_port() {
    local port=$1
    local service=$2
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        error "Port $port is already in use ($service)"
        return 1
    fi
    return 0
}

# Check if process is running
check_process() {
    local process_name=$1
    if pgrep -f "$process_name" >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Wait for service to be ready
wait_for_service() {
    local host=$1
    local port=$2
    local service=$3
    local max_attempts=30
    local attempt=1

    log "Waiting for $service to be ready on $host:$port..."

    while [ $attempt -le $max_attempts ]; do
        if nc -z "$host" "$port" 2>/dev/null; then
            success "$service is ready!"
            return 0
        fi

        echo -n "."
        sleep 1
        ((attempt++))
    done

    error "$service failed to start within ${max_attempts}s"
    return 1
}

# Start Redis
start_redis() {
    log "Starting Redis server..."

    if check_process "redis-server"; then
        warning "Redis is already running"
        return 0
    fi

    if ! check_port $REDIS_PORT "Redis"; then
        return 1
    fi

    # Start Redis in daemon mode
    redis-server --daemonize yes --port $REDIS_PORT

    if wait_for_service "localhost" $REDIS_PORT "Redis"; then
        success "Redis started successfully"
        return 0
    else
        error "Failed to start Redis"
        return 1
    fi
}

# Initialize database
init_database() {
    log "Initializing database..."

    if [ ! -d "$VENV_DIR" ]; then
        error "Virtual environment not found at $VENV_DIR"
        error "Please run setup first"
        return 1
    fi

    source "$VENV_DIR/bin/activate"

    # Set environment variables
    export PYTHONPATH="$PROJECT_DIR"
    export DATABASE_URL="sqlite+aiosqlite:///./freqtrade.db"

    # Initialize database
    if python init_db.py; then
        success "Database initialized successfully"
        return 0
    else
        error "Failed to initialize database"
        return 1
    fi
}

# Start Trading Gateway
start_trading_gateway() {
    log "Starting Trading Gateway..."

    if check_process "trading_gateway.main:app"; then
        warning "Trading Gateway is already running"
        return 0
    fi

    if ! check_port $TG_PORT "Trading Gateway"; then
        return 1
    fi

    if [ ! -d "$VENV_DIR" ]; then
        error "Virtual environment not found"
        return 1
    fi

    source "$VENV_DIR/bin/activate"

    # Set environment variables
    export PYTHONPATH="$PROJECT_DIR"
    export REDIS_URL="redis://localhost:$REDIS_PORT"

    # Start Trading Gateway in background
    nohup uvicorn trading_gateway.main:app \
        --host 0.0.0.0 \
        --port $TG_PORT \
        --no-access-log \
        > "$LOG_DIR/trading_gateway.log" 2>&1 &

    local pid=$!
    echo $pid > "$LOG_DIR/trading_gateway.pid"

    if wait_for_service "localhost" $TG_PORT "Trading Gateway"; then
        success "Trading Gateway started successfully (PID: $pid)"
        return 0
    else
        error "Failed to start Trading Gateway"
        return 1
    fi
}

# Start Management Server
start_management_server() {
    log "Starting Management Server..."

    if check_process "management_server.main:app"; then
        warning "Management Server is already running"
        return 0
    fi

    if ! check_port $MGMT_PORT "Management Server"; then
        return 1
    fi

    if [ ! -d "$VENV_DIR" ]; then
        error "Virtual environment not found"
        return 1
    fi

    source "$VENV_DIR/bin/activate"

    # Set environment variables
    export PYTHONPATH="$PROJECT_DIR"
    export DATABASE_URL="sqlite+aiosqlite:///./freqtrade.db"
    export REDIS_URL="redis://localhost:$REDIS_PORT"
    export TRADING_GATEWAY_URL="http://localhost:$TG_PORT"
    export ENABLE_METRICS="true"

    # Start Management Server in background
    nohup uvicorn management_server.main:app \
        --host 0.0.0.0 \
        --port $MGMT_PORT \
        --no-access-log \
        > "$LOG_DIR/management_server.log" 2>&1 &

    local pid=$!
    echo $pid > "$LOG_DIR/management_server.pid"

    if wait_for_service "localhost" $MGMT_PORT "Management Server"; then
        success "Management Server started successfully (PID: $pid)"
        return 0
    else
        error "Failed to start Management Server"
        return 1
    fi
}

# Start Backtesting Server
start_backtesting_server() {
    log "Starting Backtesting Server..."

    if check_process "backtesting_server.main:app"; then
        warning "Backtesting Server is already running"
        return 0
    fi

    if ! check_port $BACKTESTING_PORT "Backtesting Server"; then
        return 1
    fi

    if [ ! -d "$VENV_DIR" ]; then
        error "Virtual environment not found"
        return 1
    fi

    source "$VENV_DIR/bin/activate"

    # Set environment variables
    export PYTHONPATH="$PROJECT_DIR"
    export REDIS_URL="redis://localhost:$REDIS_PORT"

    # Start Backtesting Server in background
    nohup uvicorn backtesting_server.main:app \
        --host 0.0.0.0 \
        --port $BACKTESTING_PORT \
        --no-access-log \
        > "$LOG_DIR/backtesting_server.log" 2>&1 &

    local pid=$!
    echo $pid > "$LOG_DIR/backtesting_server.pid"

    if wait_for_service "localhost" $BACKTESTING_PORT "Backtesting Server"; then
        success "Backtesting Server started successfully (PID: $pid)"
        return 0
    else
        error "Failed to start Backtesting Server"
        return 1
    fi
}

# Start FreqAI Server
start_freqai_server() {
    log "Starting FreqAI Server..."

    if check_process "freqai_server.main:app"; then
        warning "FreqAI Server is already running"
        return 0
    fi

    if ! check_port $FREQAI_PORT "FreqAI Server"; then
        return 1
    fi

    if [ ! -d "$VENV_DIR" ]; then
        error "Virtual environment not found"
        return 1
    fi

    source "$VENV_DIR/bin/activate"

    # Set environment variables
    export PYTHONPATH="$PROJECT_DIR"
    export REDIS_URL="redis://localhost:$REDIS_PORT"

    # Start FreqAI Server in background
    nohup uvicorn freqai_server.main:app \
        --host 0.0.0.0 \
        --port $FREQAI_PORT \
        --no-access-log \
        > "$LOG_DIR/freqai_server.log" 2>&1 &

    local pid=$!
    echo $pid > "$LOG_DIR/freqai_server.pid"

    if wait_for_service "localhost" $FREQAI_PORT "FreqAI Server"; then
        success "FreqAI Server started successfully (PID: $pid)"
        return 0
    else
        error "Failed to start FreqAI Server"
        return 1
    fi
}

# Start Vite Dev Server
start_vite() {
    log "Starting Vite Dev Server..."

    if check_process "vite"; then
        warning "Vite is already running"
        return 0
    fi

    if ! check_port $VITE_PORT "Vite"; then
        return 1
    fi

    if [ ! -d "$UI_DIR" ]; then
        error "Frontend directory not found at $UI_DIR"
        return 1
    fi

    if [ ! -f "$UI_DIR/package.json" ]; then
        error "package.json not found in $UI_DIR"
        return 1
    fi

    cd "$UI_DIR"

    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        log "Installing npm dependencies..."
        if ! npm install; then
            error "Failed to install npm dependencies"
            return 1
        fi
    fi

    # Start Vite in background
    nohup npm run dev > "$LOG_DIR/vite.log" 2>&1 &

    local pid=$!
    echo $pid > "$LOG_DIR/vite.pid"

    # Wait a bit for Vite to start (it takes longer than other services)
    sleep 5

    if wait_for_service "localhost" $VITE_PORT "Vite"; then
        success "Vite Dev Server started successfully (PID: $pid)"
        return 0
    else
        error "Failed to start Vite Dev Server"
        return 1
    fi
}

# Main startup sequence
main() {
    log "🚀 Starting Freqtrade Multi-Bot System..."
    log "Project directory: $PROJECT_DIR"

    # Check if already running
    if check_process "management_server.main:app" && check_process "trading_gateway.main:app" && check_process "backtesting_server.main:app" && check_process "freqai_server.main:app" && check_process "redis-server" && check_process "vite"; then
        warning "All services appear to be running already"
        echo "Use './stop_services.sh' to stop them first if you want to restart"
        exit 0
    fi

    # Start services in order
    if ! start_redis; then
        error "Failed to start Redis. Aborting."
        exit 1
    fi

    if ! init_database; then
        error "Failed to initialize database. Aborting."
        exit 1
    fi

    if ! start_trading_gateway; then
        error "Failed to start Trading Gateway. Aborting."
        exit 1
    fi

    if ! start_management_server; then
        error "Failed to start Management Server. Aborting."
        exit 1
    fi

    if ! start_backtesting_server; then
        error "Failed to start Backtesting Server. Aborting."
        exit 1
    fi

    if ! start_freqai_server; then
        error "Failed to start FreqAI Server. Aborting."
        exit 1
    fi

    if ! start_vite; then
        error "Failed to start Vite Dev Server. Aborting."
        exit 1
    fi

    # Success message
    echo
    success "🎉 All services started successfully!"
    echo
    echo "Services running:"
    echo "  • Redis: localhost:$REDIS_PORT"
    echo "  • Trading Gateway: http://localhost:$TG_PORT"
    echo "  • Management Server: http://localhost:$MGMT_PORT"
    echo "  • Backtesting Server: http://localhost:$BACKTESTING_PORT"
    echo "  • FreqAI Server: http://localhost:$FREQAI_PORT"
    echo "  • Vite Dev Server: http://localhost:$VITE_PORT"
    echo
    echo "Logs available in: $LOG_DIR"
    echo "PIDs saved in: $LOG_DIR/*.pid"
    echo
    echo "To stop all services, run: ./stop_services.sh"
}

# Run main function
main "$@"