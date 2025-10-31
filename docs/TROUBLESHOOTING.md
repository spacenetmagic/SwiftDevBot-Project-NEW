# Troubleshooting Guide

Common issues and solutions for SwiftDevBot.

## Table of Contents

- [Bot Issues](#bot-issues)
- [Web Panel Issues](#web-panel-issues)
- [Database Issues](#database-issues)
- [Module Issues](#module-issues)
- [Authentication Issues](#authentication-issues)
- [Performance Issues](#performance-issues)

## Bot Issues

### Bot Not Responding

**Symptoms:**
- Bot doesn't respond to commands
- No messages received

**Solutions:**

1. **Check bot token:**
   ```bash
   sdb config --check
   ```

2. **Check service status:**
   ```bash
   sudo systemctl status swiftdevbot
   # Or for development
   ps aux | grep sdb.py
   ```

3. **Check logs:**
   ```bash
   sudo journalctl -u swiftdevbot -n 50
   # Or
   tail -f Logs/bot.log
   ```

4. **Verify bot token:**
   ```bash
   curl https://api.telegram.org/bot<BOT_TOKEN>/getMe
   ```

5. **Restart bot:**
   ```bash
   sudo systemctl restart swiftdevbot
   ```

### Commands Not Working

**Symptoms:**
- Commands don't trigger handlers
- "Unknown command" responses

**Solutions:**

1. **Check command registration:**
   ```bash
   sdb module list
   # Verify modules are enabled
   ```

2. **Check handler registration:**
   ```python
   # In module.py, verify router is included
   await self.router.include_router(commands_router)
   ```

3. **Reload module:**
   ```bash
   sdb module reload module_name
   ```

4. **Check permissions:**
   - Verify user has required permissions
   - Check RBAC middleware logs

### Middleware Errors

**Symptoms:**
- Messages not processed
- Permission errors

**Solutions:**

1. **Check middleware order:**
   ```python
   # Correct order: Auth → RBAC → Logging
   ```

2. **Verify user exists:**
   ```bash
   sdb user list
   ```

3. **Check audit logs:**
   ```bash
   # Via web panel or database
   ```

## Web Panel Issues

### Cannot Access Web Panel

**Symptoms:**
- Connection refused
- 502 Bad Gateway
- 404 Not Found

**Solutions:**

1. **Check web service:**
   ```bash
   sudo systemctl status swiftdevbot-web
   # Or
   ps aux | grep uvicorn
   ```

2. **Check port:**
   ```bash
   netstat -tulpn | grep 8000
   # Or
   lsof -i :8000
   ```

3. **Check firewall:**
   ```bash
   sudo ufw status
   sudo ufw allow 8000  # If needed
   ```

4. **Check Nginx:**
   ```bash
   sudo nginx -t
   sudo systemctl status nginx
   ```

5. **Restart services:**
   ```bash
   sudo systemctl restart swiftdevbot-web
   sudo systemctl restart nginx
   ```

### Authentication Fails

**Symptoms:**
- Cannot login
- "Invalid token" errors
- 401 Unauthorized

**Solutions:**

1. **Check JWT keys:**
   ```bash
   ls -la Data/security/
   # Should have jwt_private_key.pem and jwt_public_key.pem
   ```

2. **Regenerate keys:**
   ```bash
   rm Data/security/jwt_*.pem
   # Restart application (keys will be regenerated)
   ```

3. **Check token expiration:**
   - Access tokens expire after 24 hours
   - Use refresh token to get new access token

4. **Verify Telegram hash:**
   - Check bot token matches
   - Verify auth_date is not too old

### WebSocket Not Connecting

**Symptoms:**
- No real-time notifications
- WebSocket connection errors

**Solutions:**

1. **Check WebSocket endpoint:**
   ```bash
   curl -i -N -H "Connection: Upgrade" \
        -H "Upgrade: websocket" \
        http://localhost:8000/ws/notifications/123456789
   ```

2. **Check Nginx WebSocket config:**
   ```nginx
   location /ws {
       proxy_http_version 1.1;
       proxy_set_header Upgrade $http_upgrade;
       proxy_set_header Connection "upgrade";
   }
   ```

3. **Check Redis connection:**
   ```bash
   redis-cli ping
   ```

## Database Issues

### Connection Errors

**Symptoms:**
- "Connection refused"
- "Authentication failed"
- Timeout errors

**Solutions:**

1. **Check PostgreSQL status:**
   ```bash
   sudo systemctl status postgresql
   ```

2. **Test connection:**
   ```bash
   psql -h localhost -U swiftdevbot_user -d swiftdevbot
   ```

3. **Check credentials:**
   ```bash
   # Verify .env file
   grep DB_ .env
   ```

4. **Check PostgreSQL logs:**
   ```bash
   sudo tail -f /var/log/postgresql/postgresql-*.log
   ```

5. **Check connection limits:**
   ```sql
   SELECT count(*) FROM pg_stat_activity;
   SHOW max_connections;
   ```

### Migration Errors

**Symptoms:**
- Alembic errors
- Schema mismatches

**Solutions:**

1. **Check current revision:**
   ```bash
   alembic current
   ```

2. **View migration history:**
   ```bash
   alembic history
   ```

3. **Rollback if needed:**
   ```bash
   alembic downgrade -1
   ```

4. **Reapply migration:**
   ```bash
   alembic upgrade head
   ```

5. **Manual fix:**
   ```bash
   # Backup first!
   sdb backup create
   
   # Fix manually in database
   psql -U swiftdevbot_user -d swiftdevbot
   ```

### Performance Issues

**Symptoms:**
- Slow queries
- High CPU usage
- Timeout errors

**Solutions:**

1. **Check database size:**
   ```sql
   SELECT pg_size_pretty(pg_database_size('swiftdevbot'));
   ```

2. **Check slow queries:**
   ```sql
   SELECT * FROM pg_stat_statements 
   ORDER BY total_exec_time DESC 
   LIMIT 10;
   ```

3. **Create indexes:**
   ```sql
   CREATE INDEX idx_users_telegram_id ON users(telegram_id);
   CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);
   ```

4. **Analyze tables:**
   ```sql
   ANALYZE users;
   ANALYZE audit_logs;
   ```

5. **Check connection pool:**
   - Increase pool size in .env
   - Monitor active connections

## Module Issues

### Module Won't Load

**Symptoms:**
- Module not in list
- Import errors
- Load errors

**Solutions:**

1. **Check module structure:**
   ```bash
   ls -la Modules/my_module/
   # Should have: module.py, manifest.yaml, __init__.py
   ```

2. **Validate manifest:**
   ```bash
   cat Modules/my_module/manifest.yaml
   # Check YAML syntax
   ```

3. **Check for syntax errors:**
   ```bash
   python -m py_compile Modules/my_module/module.py
   ```

4. **Check dependencies:**
   ```yaml
   # In manifest.yaml
   dependencies:
     - required_module  # Ensure this module is loaded first
   ```

5. **Check logs:**
   ```bash
   tail -f Logs/bot.log | grep my_module
   ```

### Module Crashes

**Symptoms:**
- Module stops working
- Error messages in logs
- Bot becomes unresponsive

**Solutions:**

1. **Disable module:**
   ```bash
   sdb module disable my_module
   ```

2. **Check error logs:**
   ```bash
   tail -f Logs/bot.log | grep -A 10 "ERROR"
   ```

3. **Fix code:**
   - Review error message
   - Fix the issue
   - Test locally

4. **Reload module:**
   ```bash
   sdb module reload my_module
   ```

### Hot Reload Not Working

**Symptoms:**
- Changes not applied
- Still using old code

**Solutions:**

1. **Force reload:**
   ```bash
   sdb module disable my_module
   sdb module enable my_module
   ```

2. **Check Python cache:**
   ```bash
   find Modules/my_module -name "*.pyc" -delete
   find Modules/my_module -name "__pycache__" -type d -exec rm -r {} +
   ```

3. **Restart bot:**
   ```bash
   sudo systemctl restart swiftdevbot
   ```

## Authentication Issues

### JWT Token Errors

**Symptoms:**
- "Invalid token"
- "Token expired"
- 401 errors

**Solutions:**

1. **Check token expiration:**
   - Access tokens: 24 hours
   - Refresh tokens: 7 days
   - Use refresh endpoint to get new token

2. **Verify token format:**
   ```bash
   echo $TOKEN | cut -d. -f1 | base64 -d
   ```

3. **Check JWT keys:**
   ```bash
   ls -la Data/security/
   # Ensure keys exist and are readable
   ```

4. **Regenerate keys:**
   ```bash
   rm Data/security/jwt_*.pem
   # Restart application
   ```

### Telegram Login Fails

**Symptoms:**
- "Invalid hash"
- "Authentication failed"

**Solutions:**

1. **Verify bot token:**
   ```bash
   # Check .env matches Telegram Bot token
   grep BOT_TOKEN .env
   ```

2. **Check auth_date:**
   - Must be within 24 hours
   - Check system time is correct

3. **Verify hash calculation:**
   - Check Telegram documentation
   - Ensure all fields included in hash

4. **Check network:**
   - Ensure server can reach Telegram API
   - Check firewall rules

## Performance Issues

### High Memory Usage

**Symptoms:**
- Server runs out of memory
- OOM killer activated

**Solutions:**

1. **Check memory usage:**
   ```bash
   free -h
   ps aux --sort=-%mem | head
   ```

2. **Check for memory leaks:**
   - Review code for unclosed connections
   - Check for circular references

3. **Optimize database queries:**
   - Use pagination
   - Add indexes
   - Limit query results

4. **Reduce connection pool:**
   ```env
   DB_POOL_SIZE=10
   DB_MAX_OVERFLOW=20
   ```

### Slow Response Times

**Symptoms:**
- API responses slow
- Bot commands delayed

**Solutions:**

1. **Check database performance:**
   ```sql
   EXPLAIN ANALYZE SELECT * FROM users WHERE telegram_id = 123;
   ```

2. **Check Redis:**
   ```bash
   redis-cli --latency
   ```

3. **Review logs:**
   ```bash
   grep "slow" Logs/*.log
   ```

4. **Optimize code:**
   - Use async properly
   - Cache frequently accessed data
   - Batch database operations

### High CPU Usage

**Symptoms:**
- CPU at 100%
- System unresponsive

**Solutions:**

1. **Identify process:**
   ```bash
   top
   # Or
   htop
   ```

2. **Check for infinite loops:**
   - Review code
   - Check event handlers

3. **Limit concurrent operations:**
   - Use semaphores
   - Add rate limiting

4. **Optimize algorithms:**
   - Review slow functions
   - Use profiling tools

## General Solutions

### Logs Location

```bash
# Application logs
Logs/bot.log
Logs/web.log

# System logs
/var/log/swiftdevbot/

# Systemd logs
sudo journalctl -u swiftdevbot
sudo journalctl -u swiftdevbot-web
```

### Common Commands

```bash
# Check status
sdb bot status

# View logs
sdb dev logs

# Test configuration
sdb config --check

# Backup
sdb backup create

# Module management
sdb module list
sdb module reload module_name
```

### Getting Help

1. **Check logs first**
2. **Search documentation**
3. **Check GitHub Issues**
4. **Ask in Discussions**

---

For more information, see:
- [Architecture Documentation](ARCHITECTURE.md)
- [Modules Documentation](MODULES.md)
- [API Documentation](API.md)
- [Deployment Guide](DEPLOYMENT.md)

