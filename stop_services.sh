#!/bin/bash

# Freqtrade Multi-Bot System - Complete Services Shutdown Script
# This script stops all services in the correct order

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$PROJECT_DIR/logs"
REDIS_PORT=6379
MGMT_PORT=8002
TG_PORT=8001
BACKTESTING_PORT=8003
FREQAI_PORT=8004
VITE_PORT=5176

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

# Check if process is running
check_process() {
    local process_name=$1
    if pgrep -f "$process_name" >/dev/null 2>&1; then
        return 0
    fi
    return 1
}

# Kill process gracefully
kill_process() {
    local process_name=$1
    local service_name=$2
    local pid_file="$LOG_DIR/${process_name}.pid"

    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            log "Stopping $service_name (PID: $pid)..."
            kill -TERM "$pid"

            # Wait for graceful shutdown
            local count=0
            while kill -0 "$pid" 2>/dev/null && [ $count -lt 10 ]; do
                sleep 1
                ((count++))
            done

            if kill -0 "$pid" 2>/dev/null; then
                warning "$service_name didn't stop gracefully, force killing..."
                kill -KILL "$pid"
                sleep 1
            fi

            if kill -0 "$pid" 2>/dev/null; then
                error "Failed to kill $service_name (PID: $pid)"
                return 1
            else
                success "$service_name stopped"
                rm -f "$pid_file"
                return 0
            fi
        else
            warning "PID file exists but process not running, cleaning up"
            rm -f "$pid_file"
        fi
    fi

    # Fallback: kill by process name
    if check_process "$process_name"; then
        log "Stopping $service_name by process name..."
        pkill -f "$process_name"

        # Wait a bit
        sleep 2

        if check_process "$process_name"; then
            warning "Force killing $service_name..."
            pkill -9 -f "$process_name"
            sleep 1
        fi

        if check_process "$process_name"; then
            error "Failed to stop $service_name"
            return 1
        else
            success "$service_name stopped"
            return 0
        fi
    fi

    success "$service_name was not running"
    return 0
}

# Stop Management Server
stop_management_server() {
    kill_process "management_server.main:app" "Management Server"
}

# Stop Trading Gateway
stop_trading_gateway() {
    kill_process "trading_gateway.main:app" "Trading Gateway"
}

# Stop Backtesting Server
stop_backtesting_server() {
    kill_process "backtesting_server.main:app" "Backtesting Server"
}

# Stop FreqAI Server
stop_freqai_server() {
    kill_process "freqai_server.main:app" "FreqAI Server"
}

# Stop Vite Dev Server
stop_vite() {
    kill_process "vite" "Vite Dev Server"
}

# Stop Redis
stop_redis() {
    if check_process "redis-server"; then
        log "Stopping Redis server..."

        # Try graceful shutdown first
        redis-cli shutdown 2>/dev/null || true

        # Wait a bit
        sleep 2

        if check_process "redis-server"; then
            warning "Redis didn't stop gracefully, force killing..."
            pkill -9 redis-server
            sleep 1
        fi

        if check_process "redis-server"; then
            error "Failed to stop Redis"
            return 1
        else
            success "Redis stopped"
            return 0
        fi
    else
        success "Redis was not running"
        return 0
    fi
}

# Stop Freqtrade processes
stop_freqtrade_processes() {
    log "Stopping any remaining Freqtrade processes..."

    if pgrep -f "freqtrade" >/dev/null 2>&1; then
        warning "Found running Freqtrade processes, stopping them..."

        # Get PIDs of freqtrade processes
        local freqtrade_pids=$(pgrep -f "freqtrade")

        # Send TERM signal first
        echo "$freqtrade_pids" | xargs kill -TERM 2>/dev/null || true

        # Wait for graceful shutdown
        sleep 3

        # Check if any still running
        if pgrep -f "freqtrade" >/dev/null 2>&1; then
            warning "Force killing remaining Freqtrade processes..."
            pgrep -f "freqtrade" | xargs kill -KILL 2>/dev/null || true
            sleep 1
        fi

        if pgrep -f "freqtrade" >/dev/null 2>&1; then
            error "Some Freqtrade processes may still be running"
        else
            success "All Freqtrade processes stopped"
        fi
    else
        success "No Freqtrade processes were running"
    fi
}

# Clean up log files (optional)
cleanup_logs() {
    if [ "$1" = "--clean" ]; then
        log "Cleaning up log files..."
        rm -f "$LOG_DIR"/*.log
        rm -f "$LOG_DIR"/*.pid
        success "Log files cleaned up"
    fi
}

# Check services status
check_services_status() {
    local all_stopped=true

    echo
    echo "Checking services status:"

    if check_process "vite"; then
        echo -e "  • Vite Dev Server: ${RED}RUNNING${NC}"
        all_stopped=false
    else
        echo -e "  • Vite Dev Server: ${GREEN}STOPPED${NC}"
    fi

    if check_process "management_server.main:app"; then
        echo -e "  • Management Server: ${RED}RUNNING${NC}"
        all_stopped=false
    else
        echo -e "  • Management Server: ${GREEN}STOPPED${NC}"
    fi

    if check_process "trading_gateway.main:app"; then
        echo -e "  • Trading Gateway: ${RED}RUNNING${NC}"
        all_stopped=false
    else
        echo -e "  • Trading Gateway: ${GREEN}STOPPED${NC}"
    fi

    if check_process "backtesting_server.main:app"; then
        echo -e "  • Backtesting Server: ${RED}RUNNING${NC}"
        all_stopped=false
    else
        echo -e "  • Backtesting Server: ${GREEN}STOPPED${NC}"
    fi

    if check_process "freqai_server.main:app"; then
        echo -e "  • FreqAI Server: ${RED}RUNNING${NC}"
        all_stopped=false
    else
        echo -e "  • FreqAI Server: ${GREEN}STOPPED${NC}"
    fi

    if check_process "redis-server"; then
        echo -e "  • Redis: ${RED}RUNNING${NC}"
        all_stopped=false
    else
        echo -e "  • Redis: ${GREEN}STOPPED${NC}"
    fi

    if pgrep -f "freqtrade" >/dev/null 2>&1; then
        echo -e "  • Freqtrade processes: ${RED}RUNNING${NC}"
        all_stopped=false
    else
        echo -e "  • Freqtrade processes: ${GREEN}STOPPED${NC}"
    fi

    echo
    return $([ "$all_stopped" = true ] && echo 0 || echo 1)
}

# Main shutdown sequence
main() {
    log "🛑 Stopping Freqtrade Multi-Bot System..."
    log "Project directory: $PROJECT_DIR"

    # Stop services in reverse order
    stop_vite
    stop_management_server
    stop_backtesting_server
    stop_freqai_server
    stop_trading_gateway
    stop_freqtrade_processes
    stop_redis

    # Clean up if requested
    cleanup_logs "$1"

    # Final status check
    if check_services_status; then
        success "🎉 All services stopped successfully!"
    else
        warning "Some services may still be running"
        echo "Use './stop_services.sh --force' to force stop all processes"
        exit 1
    fi
}

# Run main function
main "$@"