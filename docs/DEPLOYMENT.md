# Deployment Guide

Production deployment guide for SwiftDevBot.

## Prerequisites

- Server with Ubuntu 20.04+ or similar
- Python 3.10+
- PostgreSQL 12+
- Redis 6+
- Nginx (for reverse proxy)
- Domain name with SSL certificate

## Quick Deploy

### Using Docker Compose

1. **Clone repository:**
   ```bash
   git clone https://github.com/yourusername/SwiftDevBot.git
   cd SwiftDevBot
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   nano .env  # Edit with your settings
   ```

3. **Start services:**
   ```bash
   docker-compose up -d
   ```

4. **Initialize database:**
   ```bash
   docker-compose exec bot sdb db init
   ```

## Manual Deployment

### 1. Server Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y python3.10 python3.10-venv postgresql redis-server nginx git

# Create application user
sudo useradd -m -s /bin/bash swiftdevbot
sudo su - swiftdevbot
```

### 2. Application Installation

```bash
# Clone repository
git clone https://github.com/yourusername/SwiftDevBot.git
cd SwiftDevBot

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Edit configuration
```

### 3. Database Setup

```bash
# Create PostgreSQL database
sudo -u postgres psql
```

```sql
CREATE DATABASE swiftdevbot;
CREATE USER swiftdevbot_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE swiftdevbot TO swiftdevbot_user;
\q
```

```bash
# Update .env with database credentials
DB_NAME=swiftdevbot
DB_USER=swiftdevbot_user
DB_PASSWORD=secure_password

# Initialize database
sdb db init

# Run migrations
alembic upgrade head
```

### 4. Redis Setup

```bash
# Redis is usually running by default
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Test Redis
redis-cli ping  # Should return PONG
```

### 5. Nginx Configuration

Create `/etc/nginx/sites-available/swiftdevbot`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Frontend static files
    location / {
        root /home/swiftdevbot/SwiftDevBot/Systems/web/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # API proxy
    location /api {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # WebSocket
    location /ws {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/swiftdevbot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. SSL Certificate

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is set up automatically
```

### 7. Systemd Service

Create `/etc/systemd/system/swiftdevbot.service`:

```ini
[Unit]
Description=SwiftDevBot Telegram Bot
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=swiftdevbot
WorkingDirectory=/home/swiftdevbot/SwiftDevBot
Environment="PATH=/home/swiftdevbot/SwiftDevBot/.venv/bin"
ExecStart=/home/swiftdevbot/SwiftDevBot/.venv/bin/python sdb.py bot start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Create `/etc/systemd/system/swiftdevbot-web.service`:

```ini
[Unit]
Description=SwiftDevBot Web Panel
After=network.target

[Service]
Type=simple
User=swiftdevbot
WorkingDirectory=/home/swiftdevbot/SwiftDevBot
Environment="PATH=/home/swiftdevbot/SwiftDevBot/.venv/bin"
ExecStart=/home/swiftdevbot/SwiftDevBot/.venv/bin/uvicorn Systems.web.app:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start services:
```bash
sudo systemctl enable swiftdevbot.service
sudo systemctl enable swiftdevbot-web.service
sudo systemctl start swiftdevbot.service
sudo systemctl start swiftdevbot-web.service
```

## Docker Deployment

### Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p Data/security Logs Backups

# Run application
CMD ["python", "sdb.py", "service", "start"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14
    environment:
      POSTGRES_DB: swiftdevbot
      POSTGRES_USER: swiftdevbot
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    restart: unless-stopped

  bot:
    build: .
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - DB_TYPE=postgresql
      - DB_HOST=postgres
      - DB_NAME=swiftdevbot
      - REDIS_HOST=redis
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  web:
    build: .
    command: uvicorn Systems.web.app:app --host 0.0.0.0 --port 8000
    environment:
      - DB_TYPE=postgresql
      - DB_HOST=postgres
      - REDIS_HOST=redis
    ports:
      - "8000:8000"
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

volumes:
  postgres_data:
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BOT_TOKEN` | Telegram bot token | **Required** |
| `BOT_USERNAME` | Bot username | **Required** |
| `SUPER_ADMIN_ID` | Super admin Telegram ID | **Required** |
| `DB_TYPE` | Database type (postgresql/sqlite) | postgresql |
| `DB_HOST` | Database host | localhost |
| `DB_PORT` | Database port | 5432 |
| `DB_NAME` | Database name | swiftdevbot |
| `DB_USER` | Database user | postgres |
| `DB_PASSWORD` | Database password | **Required** |
| `REDIS_HOST` | Redis host | localhost |
| `REDIS_PORT` | Redis port | 6379 |
| `WEB_PANEL_URL` | Web panel URL | http://localhost:8000 |
| `JWT_SECRET` | JWT secret (32+ chars) | **Required** |
| `LOG_LEVEL` | Logging level | INFO |

### Production Settings

```env
# Production configuration
LOG_LEVEL=WARNING
DB_TYPE=postgresql
DB_HOST=postgres
REDIS_HOST=redis
WEB_PANEL_URL=https://your-domain.com

# Security
JWT_SECRET=<generate_secure_32_char_string>
BOT_TOKEN=<your_bot_token>

# Performance
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

## Database Migration

### Using Alembic

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Review migration file
nano alembic/versions/xxxx_description.py

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Manual Migration

```bash
# Backup first
sdb backup create

# Apply migration
psql -U swiftdevbot_user -d swiftdevbot < migration.sql
```

## Monitoring

### Health Checks

```bash
# Bot health
curl https://your-domain.com/health

# Database connection
sdb db status

# Redis connection
redis-cli ping
```

### Log Monitoring

```bash
# View logs
sudo journalctl -u swiftdevbot -f

# View web logs
sudo journalctl -u swiftdevbot-web -f

# Application logs
tail -f Logs/bot.log
tail -f Logs/web.log
```

### Metrics (Future)

- Prometheus metrics endpoint
- Grafana dashboards
- Alert manager

## Backups

### Automated Backups

Create `/etc/cron.daily/swiftdevbot-backup`:

```bash
#!/bin/bash
cd /home/swiftdevbot/SwiftDevBot
source .venv/bin/activate
sdb backup create --include-db --include-modules
# Keep only last 7 days
find Backups/ -name "*.tar.gz" -mtime +7 -delete
```

Make executable:
```bash
chmod +x /etc/cron.daily/swiftdevbot-backup
```

### Manual Backup

```bash
sdb backup create --name production_backup_$(date +%Y%m%d)
```

### Restore Backup

```bash
sdb backup restore production_backup_20240101
```

## Security Checklist

- [ ] Use strong passwords
- [ ] Enable SSL/HTTPS
- [ ] Configure firewall (allow only 80, 443)
- [ ] Keep system updated
- [ ] Use environment variables for secrets
- [ ] Regular backups
- [ ] Monitor logs for suspicious activity
- [ ] Limit database access
- [ ] Use read-only database user for queries (if needed)
- [ ] Enable audit logging

## Performance Optimization

### Database

```sql
-- Create indexes
CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);

-- Analyze tables
ANALYZE users;
ANALYZE audit_logs;
```

### Redis

```bash
# Configure Redis for production
# Edit /etc/redis/redis.conf
maxmemory 256mb
maxmemory-policy allkeys-lru
```

### Application

```python
# Connection pooling
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Worker processes (for uvicorn)
uvicorn Systems.web.app:app --workers 4
```

## Troubleshooting

### Bot not responding

```bash
# Check bot status
sudo systemctl status swiftdevbot

# Check logs
sudo journalctl -u swiftdevbot -n 50

# Test bot token
sdb config --check
```

### Database connection errors

```bash
# Test connection
psql -h localhost -U swiftdevbot_user -d swiftdevbot

# Check PostgreSQL status
sudo systemctl status postgresql

# View PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### Web panel not accessible

```bash
# Check web service
sudo systemctl status swiftdevbot-web

# Check Nginx
sudo nginx -t
sudo systemctl status nginx

# Check firewall
sudo ufw status
```

See [Troubleshooting Guide](TROUBLESHOOTING.md) for more solutions.

---

For development setup, see [Development Guide](DEVELOPMENT.md).

