# SwiftDevBot

**Advanced modular Telegram bot framework with web panel**

SwiftDevBot is a powerful, modular Telegram bot framework built with Python, featuring a web panel for administration, hot-reloadable modules, role-based access control, and comprehensive testing.

## 🚀 Quick Start

**🆕 Новичок? Начните здесь:** [QUICKSTART.md](QUICKSTART.md) - пошаговая инструкция за 5 минут!

**Быстрый запуск:**

```bash
# 1. Clone repository
git clone https://github.com/yourusername/SwiftDevBot.git
cd SwiftDevBot

# 2. Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your bot token and settings

# 5. Initialize database
sdb db init

# 6. Create super admin
sdb user add YOUR_TELEGRAM_ID --role super_admin

# 7. Start bot
sdb bot start

# 8. Start web panel (optional, in another terminal)
uvicorn Systems.web.app:app --reload --port 8000
```

**Готово!** Откройте Telegram и найдите вашего бота. Веб-панель: `http://localhost:8000`

📖 **Полное руководство:** [QUICKSTART.md](QUICKSTART.md) | **Все CLI команды:** [docs/CLI_COMMANDS.md](docs/CLI_COMMANDS.md)

## ✨ Features

- **Modular Architecture**: Hot-reloadable modules with lifecycle management
- **Web Panel**: React-based admin interface with real-time notifications
- **RBAC**: Role-based access control (user, admin, super_admin)
- **JWT Authentication**: Secure RS256 token-based authentication
- **Module System**: Easy module creation with manifest-based configuration
- **Event Bus**: Publish/subscribe event system for module communication
- **Task Scheduler**: Cron and interval-based background tasks
- **CLI Tools**: Comprehensive command-line interface for management
- **Testing**: Full test suite with 190+ tests

## 📋 Table of Contents

- [Installation](#-installation)
- [Configuration](#-configuration)
- [Running](#-running)
- [Project Structure](#-project-structure)
- [Creating a Module](#-creating-a-module)
- [API Documentation](#-api-documentation)
- [Development](#-development)
- [Contributing](#-contributing)

## 📦 Installation

### Requirements

- Python 3.10+
- PostgreSQL 12+ (or SQLite for development)
- Redis 6+ (for FSM and task queue)
- Node.js 18+ (for frontend development)

### Step-by-Step Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/SwiftDevBot.git
   cd SwiftDevBot
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install frontend dependencies** (optional, for frontend development)
   ```bash
   cd Systems/web/frontend
   npm install
   cd ../../..
   ```

5. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

6. **Initialize database**
   ```bash
   sdb db init
   ```

7. **Run migrations** (if using Alembic)
   ```bash
   alembic upgrade head
   ```

## ⚙️ Configuration

Create a `.env` file in the project root:

```env
# Bot Configuration
BOT_TOKEN=your_bot_token_here
BOT_USERNAME=your_bot_username
SUPER_ADMIN_ID=123456789

# Database Configuration
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=swiftdevbot
DB_USER=postgres
DB_PASSWORD=your_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379

# Web Panel
WEB_PANEL_URL=http://localhost:8000
JWT_SECRET=your_32_character_secret_key_here

# Logging
LOG_LEVEL=INFO
```

See [Configuration Guide](docs/DEPLOYMENT.md#configuration) for more details.

## 🏃 Running

### Local Development

**Start bot only:**
```bash
sdb bot start
```

**Start web panel only:**
```bash
uvicorn Systems.web.app:app --reload --port 8000
```

**Start both** (recommended for development):
```bash
# Terminal 1: Bot
sdb bot start

# Terminal 2: Web Panel
uvicorn Systems.web.app:app --reload
```

### Docker (Production)

```bash
docker-compose up -d
```

See [Deployment Guide](docs/DEPLOYMENT.md) for production setup.

## 📁 Project Structure

```
SwiftDevBot/
├── Systems/
│   ├── core/              # Core functionality
│   │   ├── bot/           # Bot service (aiogram)
│   │   ├── database/      # Database models & repositories
│   │   ├── modules/       # Module system
│   │   ├── rbac/          # Role-based access control
│   │   ├── events/        # Event bus
│   │   └── tasks/         # Task scheduler & queue
│   ├── web/               # Web panel
│   │   ├── app.py         # FastAPI application
│   │   ├── api/           # API routes
│   │   ├── auth/          # Authentication
│   │   └── frontend/      # React frontend
│   ├── cli/               # CLI commands
│   └── user/              # User management
├── Modules/                # Bot modules
│   └── template/          # Module template
├── tests/                  # Test suite
├── docs/                   # Documentation
├── sdb.py                  # CLI entry point
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

For detailed structure, see [Architecture Documentation](docs/ARCHITECTURE.md).

## 🧩 Creating a Module

### Quick Start

1. **Use the template:**
   ```bash
   cp -r Modules/template Modules/my_module
   cd Modules/my_module
   ```

2. **Edit `manifest.yaml`:**
   ```yaml
   name: my_module
   display_name: My Module
   version: 1.0.0
   description: My awesome module
   author: Your Name
   ```

3. **Implement your module in `module.py`:**
   ```python
   from Systems.core.modules.base_module import BaseModule
   
   class MyModule(BaseModule):
       async def on_load(self) -> None:
           # Initialize your module
           pass
       
       async def on_unload(self) -> None:
           # Cleanup
           pass
   ```

4. **Add command handlers in `handlers/commands.py`:**
   ```python
   from aiogram import Router
   from aiogram.filters import Command
   
   router = Router()
   
   @router.message(Command("mycommand"))
   async def handle_my_command(message):
       await message.answer("Hello from my module!")
   ```

5. **Enable your module:**
   ```bash
   sdb module enable my_module
   ```

See [Modules Documentation](docs/MODULES.md) for complete guide.

## 📚 API Documentation

### Authentication

All protected endpoints require JWT Bearer token:

```bash
curl -H "Authorization: Bearer <token>" http://localhost:8000/api/users/me
```

### Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/telegram` | POST | Telegram login |
| `/api/auth/refresh` | POST | Refresh token |
| `/api/users/me` | GET | Current user info |
| `/api/modules/` | GET | List modules |
| `/api/modules/{name}/enable` | POST | Enable module |
| `/api/settings/{module}/user` | GET | Get user settings |

Full API documentation: [API Reference](docs/API.md)

## 🛠️ Development

### Setup Development Environment

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Setup pre-commit hooks (optional)
pre-commit install

# Run tests
pytest tests/
```

### Hot Reload (Development Mode)

```bash
# Watch for module changes
sdb dev watch

# Or watch logs
sdb dev logs bot --follow
```

See [Development Guide](docs/DEVELOPMENT.md) for more information.

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](docs/DEVELOPMENT.md#contributing).

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow PEP 8
- Use type hints
- Write docstrings for all functions/classes
- Add tests for new features

## 📖 Documentation

- [Architecture](docs/ARCHITECTURE.md) - System architecture and design
- [Modules](docs/MODULES.md) - Module development guide
- [API Reference](docs/API.md) - API documentation
- [Deployment](docs/DEPLOYMENT.md) - Production deployment guide
- [Development](docs/DEVELOPMENT.md) - Development setup and workflows
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions

## 📝 CLI Commands

SwiftDevBot provides a comprehensive CLI:

```bash
# Module Management
sdb module list                    # List all modules
sdb module install ./my_module    # Install module
sdb module enable my_module        # Enable module
sdb module disable my_module      # Disable module
sdb module reload my_module       # Hot reload module
sdb module watch                  # Auto-reload on changes

# User Management
sdb user add 123456789 --role admin
sdb user list
sdb user role 123456789 admin

# Service Management
sdb bot start                  # Start bot
sdb bot stop                   # Stop bot
sdb bot status                 # Check status

# Development
sdb dev watch                     # Watch for changes
sdb dev logs [service]            # View logs
sdb dev shell                     # Python shell

# Backups
sdb backup create                 # Create backup
sdb backup list                   # List backups
sdb backup restore backup_name    # Restore backup
```

## 🔒 Security

- JWT tokens use RS256 (RSA 2048-bit) signing
- All sensitive operations are logged in audit log
- Role-based access control enforced
- Telegram hash verification required
- HTTPS recommended for production

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [aiogram](https://github.com/aiogram/aiogram) - Telegram Bot Framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - Database ORM

## 📧 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/SwiftDevBot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/SwiftDevBot/discussions)
- **Email**: support@swiftdevbot.example

---

**Made with ❤️ by the SwiftDevBot team**
