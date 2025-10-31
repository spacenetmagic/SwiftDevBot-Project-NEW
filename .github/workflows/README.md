# GitHub Actions Workflows

Этот каталог содержит автоматизированные workflows для SwiftDevBot.

## 📋 Доступные Workflows

### 1. `test.yml` - Автоматическое тестирование
- Запускается при каждом push/PR
- Проверяет код (linting, type checking)
- Запускает все тесты
- Проверяет покрытие кода

### 2. `deploy.yml` - Автоматический деплой
- Запускается при push в `main`
- Развертывает проект на production сервер
- Собирает Docker образы

## 📖 Подробная документация

См. [docs/GITHUB_ACTIONS.md](../../docs/GITHUB_ACTIONS.md) для полной документации по настройке и использованию.
