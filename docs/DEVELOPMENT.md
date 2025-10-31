# Development Guide

Guide for developers contributing to SwiftDevBot.

## Development Setup

### Prerequisites

- Python 3.10+
- PostgreSQL 12+ (or SQLite for testing)
- Redis 6+
- Node.js 18+ (for frontend)
- Git

### Initial Setup

```bash
# Clone repository
git clone https://github.com/yourusername/SwiftDevBot.git
cd SwiftDevBot

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Dev dependencies

# Setup pre-commit hooks (optional)
pre-commit install

# Configure environment
cp .env.example .env
# Edit .env for local development
```

### Local Environment Configuration

`.env` for development:

```env
# Development settings
BOT_TOKEN=your_dev_bot_token
BOT_USERNAME=your_bot_username
SUPER_ADMIN_ID=your_telegram_id

# Use SQLite for development (easier)
DB_TYPE=sqlite
DB_PATH=./Data/swiftdevbot.db

# Or PostgreSQL
# DB_TYPE=postgresql
# DB_HOST=localhost
# DB_NAME=swiftdevbot_dev

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Development web panel
WEB_PANEL_URL=http://localhost:8000
JWT_SECRET=dev_secret_key_minimum_32_characters_long

# Logging
LOG_LEVEL=DEBUG
```

## Running Locally

### Start Bot

```bash
# Terminal 1: Bot service
sdb bot start

# Or with hot reload
sdb dev watch
```

### Start Web Panel

```bash
# Terminal 2: Web panel
uvicorn Systems.web.app:app --reload --port 8000
```

### Start Frontend (Development)

```bash
# Terminal 3: Frontend
cd Systems/web/frontend
npm install
npm run dev
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/my-new-feature
```

### 2. Make Changes

- Follow code style (PEP 8)
- Add type hints
- Write docstrings
- Add tests

### 3. Run Tests

```bash
# All tests
pytest tests/

# Specific test file
pytest tests/unit/test_user_service.py

# With coverage
pytest --cov=Systems tests/

# Watch mode
pytest-watch
```

### 4. Check Code Quality

```bash
# Linting
flake8 Systems/

# Type checking
mypy Systems/

# Format code
black Systems/
isort Systems/
```

### 5. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
```

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): subject

body

footer
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

### 6. Push and Create PR

```bash
git push origin feature/my-new-feature
# Create Pull Request on GitHub
```

## Hot Reload

### Module Hot Reload

```bash
# Watch for changes and auto-reload
sdb dev watch

# Or manually reload
sdb module reload my_module
```

### Web Panel Hot Reload

Uvicorn automatically reloads on code changes when using `--reload` flag.

### Frontend Hot Reload

Vite automatically reloads on changes when running `npm run dev`.

## Debugging

### Bot Debugging

```bash
# Run with debug logging
LOG_LEVEL=DEBUG sdb bot start

# Use Python debugger
python -m pdb sdb.py bot start
```

### Web Panel Debugging

```bash
# Run with debug mode
uvicorn Systems.web.app:app --reload --log-level debug

# Add breakpoints
import pdb; pdb.set_trace()
```

### Database Debugging

```bash
# Connect to database
psql -h localhost -U swiftdevbot_user -d swiftdevbot

# Or for SQLite
sqlite3 Data/swiftdevbot.db
```

### Using VS Code Debugger

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Bot",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/sdb.py",
      "args": ["service", "start"],
      "console": "integratedTerminal"
    },
    {
      "name": "Python: Web Panel",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["Systems.web.app:app", "--reload"],
      "console": "integratedTerminal"
    }
  ]
}
```

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific test
pytest tests/unit/test_user_service.py::test_create_user

# With verbose output
pytest -v

# With coverage
pytest --cov=Systems --cov-report=html
```

### Writing Tests

Test structure:

```python
import pytest
from Systems.core.database import get_session_factory

@pytest.mark.asyncio
async def test_my_function():
    """Test description."""
    # Arrange
    async with get_session_factory()() as session:
        # Act
        result = await my_function(session)
        
        # Assert
        assert result is not None
```

### Test Fixtures

Common fixtures available in `tests/conftest.py`:

- `db_session` - Database session
- `test_user` - Test user
- `test_admin` - Test admin user
- `mock_redis` - Mock Redis client
- `mock_bot` - Mock Telegram bot

### Test Coverage

Target: **80%+ coverage**

```bash
# Generate coverage report
pytest --cov=Systems --cov-report=html

# View report
open htmlcov/index.html
```

## Code Style

### Python Style Guide

- Follow **PEP 8**
- Use **type hints** everywhere
- Maximum line length: **100 characters**
- Use **f-strings** for formatting
- Use **async/await** for I/O operations

### Example

```python
from typing import Optional
from Systems.core.database.models.user import User

async def get_user(
    telegram_id: int,
    session: AsyncSession,
) -> Optional[User]:
    """
    Get user by Telegram ID.
    
    Args:
        telegram_id: Telegram user ID
        session: Database session
        
    Returns:
        User object or None if not found
    """
    repo = UserRepository(session)
    return await repo.get_by_id(telegram_id)
```

### Formatting Tools

```bash
# Format code
black Systems/
isort Systems/

# Check formatting
black --check Systems/
isort --check Systems/
```

### Linting

```bash
# Run linter
flake8 Systems/

# Type checking
mypy Systems/
```

## Project Structure

### Adding New Features

1. **Core Feature**: Add to `Systems/core/`
2. **Module Feature**: Add as module in `Modules/`
3. **Web Feature**: Add to `Systems/web/api/` or `Systems/web/frontend/`
4. **CLI Feature**: Add to `Systems/cli/commands/`

### File Organization

```
Systems/
├── core/              # Core functionality
│   ├── bot/          # Bot-specific
│   ├── database/     # Database layer
│   └── modules/      # Module system
├── web/              # Web panel
│   ├── api/          # API routes
│   └── frontend/     # React frontend
└── cli/              # CLI commands
```

## Common Tasks

### Add New API Endpoint

1. Create route in `Systems/web/api/`
2. Add schema in `Systems/web/api/schemas.py`
3. Add tests in `tests/integration/test_api.py`
4. Update API documentation

### Add New CLI Command

1. Add command in `Systems/cli/commands/`
2. Register in `sdb.py`
3. Add tests
4. Update README

### Add New Database Model

1. Create model in `Systems/core/database/models/`
2. Create repository in `Systems/core/database/repositories/`
3. Create Alembic migration
4. Add tests

## Contributing

### Before Submitting PR

- [ ] All tests pass
- [ ] Code follows style guide
- [ ] Documentation updated
- [ ] No linting errors
- [ ] Type hints added
- [ ] Docstrings added
- [ ] Changelog updated (if applicable)

### PR Checklist

1. **Description**: Clear description of changes
2. **Tests**: New tests for new features
3. **Documentation**: Updated relevant docs
4. **Breaking Changes**: Documented if any
5. **Screenshots**: For UI changes

### Review Process

1. Automated checks (CI) must pass
2. Code review by maintainers
3. Address review comments
4. Merge after approval

## Resources

- [Architecture Documentation](ARCHITECTURE.md)
- [Modules Documentation](MODULES.md)
- [API Documentation](API.md)
- [Troubleshooting](TROUBLESHOOTING.md)

## Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and discussions
- **Documentation**: Check relevant docs first

---

Happy coding! 🚀

