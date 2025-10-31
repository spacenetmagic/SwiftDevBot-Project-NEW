# Contributing to SwiftDevBot

Thank you for your interest in contributing to SwiftDevBot! This document provides guidelines for contributing.

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Accept constructive criticism gracefully
- Focus on what is best for the project

## Getting Started

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/SwiftDevBot.git
   cd SwiftDevBot
   ```

2. **Create a branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**
   - Follow code style guidelines
   - Add tests for new features
   - Update documentation

4. **Test your changes**
   ```bash
   pytest tests/
   ```

5. **Submit a Pull Request**
   - Provide clear description
   - Link related issues
   - Ensure all tests pass

## Development Setup

See [Development Guide](docs/DEVELOPMENT.md) for complete setup instructions.

## Coding Standards

### Python Style

- Follow **PEP 8**
- Use **type hints** everywhere
- Maximum line length: **100 characters**
- Use **f-strings** for string formatting
- Write **docstrings** for all functions/classes

### Code Formatting

We use:
- **black** for code formatting
- **isort** for import sorting
- **flake8** for linting
- **mypy** for type checking

```bash
# Format code
black Systems/
isort Systems/

# Check formatting
black --check Systems/
isort --check Systems/
flake8 Systems/
mypy Systems/
```

### Example Code

```python
from typing import Optional

async def example_function(
    user_id: int,
    username: Optional[str] = None,
) -> dict[str, Any]:
    """
    Example function with type hints and docstring.
    
    Args:
        user_id: User Telegram ID
        username: User username (optional)
        
    Returns:
        Dictionary with user data
        
    Raises:
        ValueError: If user_id is invalid
        
    Examples:
        >>> await example_function(123456789, "testuser")
        {'user_id': 123456789, 'username': 'testuser'}
    """
    if user_id <= 0:
        raise ValueError("User ID must be positive")
    
    return {"user_id": user_id, "username": username}
```

## Testing

### Writing Tests

- Write tests for all new features
- Test both success and error cases
- Use fixtures from `tests/conftest.py`
- Target **80%+ coverage**

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/unit/test_user_service.py

# With coverage
pytest --cov=Systems --cov-report=html
```

## Documentation

### Docstrings

All functions and classes must have docstrings:

```python
def my_function(param: str) -> int:
    """
    Brief description.
    
    Longer description explaining what the function does,
    its parameters, return values, and exceptions.
    
    Args:
        param: Parameter description
        
    Returns:
        Return value description
        
    Raises:
        ValueError: When parameter is invalid
        
    Examples:
        >>> my_function("test")
        42
    """
    pass
```

### Documentation Updates

- Update relevant docs when adding features
- Add examples to docstrings
- Update README if needed
- Keep API documentation current

## Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
type(scope): subject

body

footer
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style (formatting)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Maintenance tasks

**Examples:**
```
feat(modules): add hot reload functionality
fix(auth): resolve JWT token expiration issue
docs(api): update authentication documentation
```

## Pull Request Process

1. **Update CHANGELOG.md** with your changes
2. **Ensure all tests pass**
3. **Update documentation** if needed
4. **Request review** from maintainers
5. **Address review comments**
6. **Wait for approval** before merging

### PR Checklist

- [ ] Code follows style guidelines
- [ ] All tests pass
- [ ] Documentation updated
- [ ] No linting errors
- [ ] Type hints added
- [ ] Docstrings added
- [ ] CHANGELOG updated

## Issue Reporting

### Bug Reports

Include:
- **Description** of the bug
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Environment** (OS, Python version, etc.)
- **Logs** (if applicable)

### Feature Requests

Include:
- **Description** of the feature
- **Use case** / motivation
- **Proposed solution** (if any)
- **Alternatives** considered

## Module Development

See [Modules Documentation](docs/MODULES.md) for module development guide.

When contributing modules:
- Use the template in `Modules/template/`
- Follow module structure
- Add tests for your module
- Document module usage

## Questions?

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and discussions
- **Documentation**: Check relevant docs first

## Recognition

Contributors will be recognized in:
- CONTRIBUTORS.md (if applicable)
- Release notes
- Project documentation

Thank you for contributing! 🎉

