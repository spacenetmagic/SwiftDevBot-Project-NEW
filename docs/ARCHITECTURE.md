# Architecture

This document describes the architecture and design of SwiftDevBot.

## Overview

SwiftDevBot follows a modular, event-driven architecture with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                    SwiftDevBot                          │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────┐ │
│  │   Bot Core   │    │  Web Panel   │    │   CLI    │ │
│  │  (aiogram)   │◄──►│   (FastAPI)  │◄──►│ (Click)  │ │
│  └──────────────┘    └──────────────┘    └──────────┘ │
│         │                    │                         │
│         ▼                    ▼                         │
│  ┌──────────────────────────────────────────────┐     │
│  │           Module System                      │     │
│  │  ┌────────┐  ┌────────┐  ┌────────┐         │     │
│  │  │Module1 │  │Module2 │  │Module3 │  ...     │     │
│  │  └────────┘  └────────┘  └────────┘         │     │
│  └──────────────────────────────────────────────┘     │
│         │                    │                         │
│         ▼                    ▼                         │
│  ┌──────────────┐    ┌──────────────┐                │
│  │  Event Bus   │    │ Task Scheduler│               │
│  └──────────────┘    └──────────────┘                │
│         │                    │                         │
│         └────────┬───────────┘                         │
│                  ▼                                     │
│         ┌────────────────────┐                         │
│         │   Database Layer   │                         │
│         │  (SQLAlchemy)      │                         │
│         └────────────────────┘                         │
│                  │                                     │
│         ┌─────────┴──────────┐                         │
│         ▼                    ▼                         │
│    PostgreSQL          Redis                            │
│    (Main DB)        (FSM/Queue)                        │
└─────────────────────────────────────────────────────────┘
```

## Components

### 1. Bot Core

**Location:** `Systems/core/bot/`

The bot core is built on aiogram 3.22 and handles:
- Message routing
- Command handling
- Middleware stack (Auth, RBAC, Logging)
- FSM (Finite State Machine) with Redis storage
- Persistent keyboards

**Key Components:**
- `dispatcher.py` - Main dispatcher setup
- `main.py` - Bot entry point
- Middleware for authentication and authorization

**Data Flow:**
```
Telegram Update → Middleware Stack → Router → Handler → Response
```

### 2. Web Panel

**Location:** `Systems/web/`

**Backend (FastAPI):**
- RESTful API endpoints
- JWT authentication (RS256)
- WebSocket for real-time notifications
- Static file serving

**Frontend (React):**
- React 18+ with React Router v6
- Axios for API calls
- WebSocket client for notifications
- Dark/Light theme support

**API Routes:**
- `/api/auth/*` - Authentication
- `/api/users/*` - User management
- `/api/modules/*` - Module management
- `/api/settings/*` - Settings management
- `/api/admin/*` - Admin operations
- `/ws/notifications/{user_id}` - WebSocket

### 3. Module System

**Location:** `Systems/core/modules/`

The module system enables hot-reloadable extensions:

```
┌─────────────────────────────────┐
│      ModuleManager              │
│  ┌──────────────────────────┐   │
│  │    ModuleLoader          │   │
│  │  - Discover modules      │   │
│  │  - Load/reload/unload    │   │
│  └──────────────────────────┘   │
│  ┌──────────────────────────┐   │
│  │    CommandRegistry       │   │
│  │  - Register commands     │   │
│  │  - Route handlers        │   │
│  └──────────────────────────┘   │
│  ┌──────────────────────────┐   │
│  │    SettingsManager        │   │
│  │  - User/Admin settings    │   │
│  └──────────────────────────┘   │
└─────────────────────────────────┘
```

**Module Lifecycle:**
1. **Discovery** - Scan `Modules/` directory
2. **Load** - Import module, read manifest
3. **Initialize** - Call `on_load()`
4. **Enable** - Register handlers, start tasks
5. **Disable** - Unregister handlers, stop tasks
6. **Unload** - Call `on_unload()`, cleanup

See [Modules Documentation](MODULES.md) for details.

### 4. Database Layer

**Location:** `Systems/core/database/`

**Architecture:**
```
┌──────────────┐
│   Models     │  (SQLAlchemy ORM)
│  - User      │
│  - ModuleSetting│
│  - AuditLog  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ Repositories │  (Data Access Layer)
│  - UserRepo  │
│  - SettingsRepo│
│  - AuditRepo │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Services   │  (Business Logic)
│  - UserService│
└──────────────┘
```

**Database Models:**

| Model | Description |
|-------|-------------|
| `User` | Telegram users with roles |
| `ModuleSetting` | Module-specific settings (user/admin level) |
| `AuditLog` | Audit trail for all operations |

### 5. Event Bus

**Location:** `Systems/core/events/`

Publish/subscribe event system for module communication:

```
Module A → Event Bus → [Module B, Module C] → Handlers
```

**Event Flow:**
1. Module publishes event: `await event_bus.emit("user.created", data)`
2. Event Bus notifies all subscribers
3. Subscribers execute their handlers asynchronously
4. Errors are logged but don't block other handlers

**Common Events:**
- `user.created` - New user registered
- `user.updated` - User profile updated
- `module.loaded` - Module loaded
- `module.enabled` - Module enabled
- `command.executed` - Command executed

### 6. Task Scheduler

**Location:** `Systems/core/tasks/`

**Components:**

1. **TaskScheduler** (APScheduler)
   - Cron jobs: `0 9 * * *` (daily at 9 AM)
   - Interval tasks: Every 1 hour
   - Dynamic registration from modules

2. **TaskQueue** (Redis)
   - Background job queue
   - Retry logic with exponential backoff
   - Job status tracking

**Task Registration:**
```python
# In manifest.yaml
background_tasks:
  - cleanup_old_data
  - send_daily_report

# In module.py
async def cleanup_old_data(self):
    # Runs every hour
    pass
```

### 7. Authentication & Authorization

**Location:** `Systems/web/auth/`

**Authentication Flow:**
```
Telegram Login Widget
    ↓
[Hash Verification]
    ↓
[Get/Create User]
    ↓
[Generate JWT Token]
    ↓
[Return Token]
```

**JWT Token Structure:**
- **Access Token**: 24 hours, RS256 signed
- **Refresh Token**: 7 days, RS256 signed
- **Payload**: `{sub: user_id, role, username, exp, iat, type}`

**RBAC System:**
```
Super Admin → All permissions (*)
    ↓
Admin → Admin permissions + user permissions
    ↓
User → Basic user permissions
```

See [API Documentation](API.md#authentication) for details.

## Data Flow

### Bot Command Flow

```
1. User sends /command
2. Telegram → Bot Core
3. Middleware Stack:
   - Auth Middleware (check user)
   - RBAC Middleware (check permissions)
   - Logging Middleware
4. Router matches command
5. Handler executes
6. Module logic (if module command)
7. Response sent to user
8. Event emitted (command.executed)
9. Audit log entry
```

### Web Panel Request Flow

```
1. User makes request
2. Frontend → API (with JWT token)
3. JWT verification
4. User lookup from database
5. Permission check (RBAC)
6. Business logic execution
7. Database operations
8. Response sent
9. Audit log entry
```

### Module Hot Reload Flow

```
1. Developer modifies module code
2. sdb module reload my_module
3. ModuleManager:
   - Unload old module
   - Clear imports
   - Reload module.py
   - Call on_load()
   - Register handlers
   - Re-enable if was enabled
4. Event emitted (module.reloaded)
```

## Design Patterns

### 1. Repository Pattern
Separates data access from business logic.

```python
# Repository (Data Access)
user_repo = UserRepository(session)
user = await user_repo.get_by_id(telegram_id)

# Service (Business Logic)
user_service = UserService(user_repo)
permissions = await user_service.get_user_permissions(telegram_id)
```

### 2. Dependency Injection
FastAPI dependencies and module dependencies.

```python
@router.get("/api/users/me")
async def get_me(user: User = Depends(get_current_user)):
    # user is injected by FastAPI
    return user
```

### 3. Observer Pattern
Event Bus for module communication.

```python
# Subscribe
await event_bus.subscribe("user.created", handler)

# Publish
await event_bus.emit("user.created", user_data)
```

### 4. Factory Pattern
Module loader creates module instances.

```python
module = loader.load_module("my_module")
# Creates instance of MyModule class
```

## Scalability

### Horizontal Scaling

Currently, SwiftDevBot runs as a single instance. For horizontal scaling:

1. **Stateless Design**: All state in Redis/PostgreSQL
2. **Shared Redis**: FSM storage shared across instances
3. **Database Pooling**: Connection pooling for concurrent requests
4. **Load Balancer**: Multiple bot instances behind load balancer

### Vertical Scaling

- Database connection pooling
- Async operations throughout
- Efficient Redis usage
- Caching where appropriate

## Security Architecture

```
┌─────────────────────────────────────┐
│      Security Layers                │
├─────────────────────────────────────┤
│ 1. Telegram Hash Verification      │
│ 2. JWT Token (RS256)                │
│ 3. RBAC Permission Checks           │
│ 4. Audit Logging                    │
│ 5. Rate Limiting (future)           │
└─────────────────────────────────────┘
```

All security-sensitive operations:
- Verify authentication
- Check permissions
- Log to audit trail
- Validate input
- Sanitize output

## Performance Considerations

1. **Async/Await**: All I/O operations are async
2. **Connection Pooling**: Database and Redis connections pooled
3. **Lazy Loading**: Modules loaded on demand
4. **Caching**: Settings cached in memory
5. **Batch Operations**: Bulk database operations where possible

## Monitoring & Observability

- **Logging**: Structured logging with levels
- **Audit Log**: All operations logged
- **Health Checks**: `/health` endpoint
- **Metrics**: (Future) Prometheus integration

---

For module development, see [Modules Documentation](MODULES.md).

For API usage, see [API Documentation](API.md).

