#!/bin/bash
#
# SwiftDevBot Production Deployment Script
#
# This script handles production deployment:
# - Git pull
# - Install dependencies
# - Run migrations
# - Restart services
# - Health checks
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="${PROJECT_DIR:-/home/swiftdevbot/SwiftDevBot}"
VENV_DIR="${VENV_DIR:-${PROJECT_DIR}/.venv}"
BRANCH="${BRANCH:-main}"
BACKUP_BEFORE_DEPLOY="${BACKUP_BEFORE_DEPLOY:-true}"

# Logging
LOG_FILE="${LOG_FILE:-/var/log/swiftdevbot/deploy.log}"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1" | tee -a "$LOG_FILE"
}

# Check if running as correct user
if [ "$EUID" -eq 0 ]; then
    error "Do not run as root. Use sudo -u swiftdevbot"
fi

# Navigate to project directory
cd "$PROJECT_DIR" || error "Project directory not found: $PROJECT_DIR"

log "Starting deployment..."

# Step 1: Create backup if enabled
if [ "$BACKUP_BEFORE_DEPLOY" = "true" ]; then
    log "Creating backup..."
    source "$VENV_DIR/bin/activate"
    python "$PROJECT_DIR/sdb.py" backup create --name "pre_deploy_$(date +%Y%m%d_%H%M%S)" || warning "Backup creation failed"
    deactivate
fi

# Step 2: Git pull
log "Updating code from Git..."
git fetch origin
CURRENT_COMMIT=$(git rev-parse HEAD)
NEW_COMMIT=$(git rev-parse origin/$BRANCH)

if [ "$CURRENT_COMMIT" = "$NEW_COMMIT" ]; then
    log "Already up to date (commit: $CURRENT_COMMIT)"
else
    log "Pulling changes (${CURRENT_COMMIT:0:7} -> ${NEW_COMMIT:0:7})..."
    git checkout "$BRANCH" || error "Failed to checkout branch"
    git pull origin "$BRANCH" || error "Failed to pull changes"
    log "Code updated successfully"
fi

# Step 3: Activate virtual environment
log "Activating virtual environment..."
if [ ! -d "$VENV_DIR" ]; then
    log "Creating virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate" || error "Failed to activate virtual environment"

# Step 4: Install/update dependencies
log "Installing dependencies..."
pip install --upgrade pip || error "Failed to upgrade pip"
pip install -r requirements.txt || error "Failed to install dependencies"

# Step 5: Run database migrations
log "Running database migrations..."

# Check if using Alembic
if [ -f "alembic.ini" ]; then
    alembic upgrade head || warning "Migrations failed"
else
    log "Alembic not configured, running init_db..."
    python "$PROJECT_DIR/scripts/init_db.py" || warning "Database initialization failed"
fi

# Step 6: Restart services
log "Restarting services..."

# Bot service
if systemctl is-active --quiet swiftdevbot.service 2>/dev/null; then
    log "Restarting bot service..."
    sudo systemctl restart swiftdevbot.service || warning "Failed to restart bot service"
    sleep 2
    systemctl is-active --quiet swiftdevbot.service && log "✓ Bot service restarted" || warning "Bot service not running"
fi

# Web service
if systemctl is-active --quiet swiftdevbot-web.service 2>/dev/null; then
    log "Restarting web service..."
    sudo systemctl restart swiftdevbot-web.service || warning "Failed to restart web service"
    sleep 2
    systemctl is-active --quiet swiftdevbot-web.service && log "✓ Web service restarted" || warning "Web service not running"
fi

# Docker Compose (if used)
if [ -f "docker-compose.yml" ] && docker compose ps 2>/dev/null | grep -q "swiftdevbot"; then
    log "Restarting Docker containers..."
    docker compose restart || warning "Failed to restart Docker containers"
fi

# Step 7: Health checks
log "Running health checks..."

# Wait for services to start
sleep 3

# Check bot service
if systemctl is-active --quiet swiftdevbot.service 2>/dev/null; then
    log "✓ Bot service is running"
else
    warning "Bot service is not running"
fi

# Check web service
if systemctl is-active --quiet swiftdevbot-web.service 2>/dev/null; then
    log "✓ Web service is running"
    
    # Check HTTP endpoint
    WEB_URL="${WEB_PANEL_URL:-http://localhost:8000}"
    if curl -f -s "$WEB_URL/health" > /dev/null 2>&1; then
        log "✓ Web panel health check passed"
    else
        warning "Web panel health check failed"
    fi
else
    warning "Web service is not running"
fi

# Check database
if python "$PROJECT_DIR/scripts/init_db.py" --check > /dev/null 2>&1; then
    log "✓ Database connection successful"
else
    warning "Database connection failed"
fi

# Check Redis
if command -v redis-cli > /dev/null 2>&1; then
    if redis-cli ping > /dev/null 2>&1; then
        log "✓ Redis connection successful"
    else
        warning "Redis connection failed"
    fi
fi

# Deactivate virtual environment
deactivate

log "Deployment complete!"

# Show service status
log "Service status:"
if systemctl is-active --quiet swiftdevbot.service 2>/dev/null; then
    systemctl status swiftdevbot.service --no-pager -l | head -n 5
fi

if systemctl is-active --quiet swiftdevbot-web.service 2>/dev/null; then
    systemctl status swiftdevbot-web.service --no-pager -l | head -n 5
fi

