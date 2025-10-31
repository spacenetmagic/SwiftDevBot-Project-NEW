# GitHub Actions для SwiftDevBot

## Что такое GitHub Actions?

**GitHub Actions** — это встроенная платформа CI/CD (Continuous Integration / Continuous Deployment) от GitHub, которая позволяет автоматизировать различные задачи при работе с кодом:

- ✅ **Автоматическое тестирование** при каждом push/PR
- ✅ **Проверка качества кода** (linting, type checking)
- ✅ **Автоматический деплой** в production
- ✅ **Сборка Docker образов**
- ✅ **Публикация релизов**

## Как это работает?

GitHub Actions выполняет **workflows** (workflow-файлы), которые находятся в `.github/workflows/` вашего репозитория. Эти файлы описывают, что нужно сделать при определенных событиях (push, pull request, создание release и т.д.).

### Структура Workflow

```yaml
name: Название workflow

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Run tests
        run: pytest tests/
```

## Workflows в SwiftDevBot

В проекте SwiftDevBot уже настроены два workflow:

### 1. `.github/workflows/test.yml` — Тестирование

**Что делает:**
- Запускается при каждом push или pull request
- Проверяет код (linting, type checking)
- Запускает все тесты
- Проверяет покрытие кода
- Собирает Docker образ

**Как запустить:**
Просто сделайте `git push` в репозиторий — workflow запустится автоматически!

### 2. `.github/workflows/deploy.yml` — Деплой

**Что делает:**
- Запускается при push в ветку `main`
- Развертывает проект на production сервер
- Собирает и публикует Docker образ

**Как запустить:**
Настройте secrets в GitHub и сделайте push в `main`.

## Настройка GitHub Actions

### Шаг 1: Создайте репозиторий на GitHub

```bash
# Если у вас еще нет репозитория
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/yourusername/SwiftDevBot.git
git push -u origin main
```

### Шаг 2: Workflows уже настроены

В проекте уже есть:
- ✅ `.github/workflows/test.yml` — автоматическое тестирование
- ✅ `.github/workflows/deploy.yml` — автоматический деплой

### Шаг 3: Настройте Secrets (для деплоя)

Если хотите использовать автоматический деплой, добавьте secrets в GitHub:

**Settings → Secrets and variables → Actions → New repository secret**

Нужные secrets для `.github/workflows/deploy.yml`:

```
SSH_PRIVATE_KEY          # SSH ключ для подключения к серверу
SERVER_HOST              # IP или домен сервера (например, 192.168.1.100)
SERVER_USER               # Пользователь SSH (например, ubuntu)
DEPLOY_PATH               # Путь на сервере (например, /home/swiftdevbot/SwiftDevBot)
WEB_PANEL_URL             # URL веб-панели (например, https://bot.example.com)
DOCKER_REGISTRY           # Docker registry URL (опционально)
DOCKER_USERNAME           # Docker username (опционально)
DOCKER_PASSWORD           # Docker password (опционально)
```

### Шаг 4: Проверьте работу

1. **Сделайте изменения** в коде
2. **Создайте коммит**:
   ```bash
   git add .
   git commit -m "Test GitHub Actions"
   git push
   ```
3. **Проверьте GitHub**:
   - Откройте ваш репозиторий на GitHub
   - Перейдите в **Actions** (верхнее меню)
   - Увидите запущенный workflow
   - Кликните на него, чтобы увидеть прогресс

## Детали workflows

### Test Workflow (`.github/workflows/test.yml`)

**Триггеры:**
- Push в `main` или `develop`
- Pull request в `main` или `develop`

**Что происходит:**
1. Запускается виртуальная машина Ubuntu
2. Настраивается PostgreSQL и Redis (для тестов)
3. Устанавливается Python 3.10
4. Устанавливаются зависимости
5. Проверяется код (flake8, mypy, black)
6. Инициализируется база данных
7. Запускаются тесты с покрытием
8. Собирается Docker образ
9. Результаты загружаются в Codecov

**Результат:**
- ✅ Все тесты прошли → зеленая галочка
- ❌ Тесты упали → красный крестик + детали ошибки

### Deploy Workflow (`.github/workflows/deploy.yml`)

**Триггеры:**
- Push в `main`
- Ручной запуск (workflow_dispatch)

**Что происходит:**
1. Подключается к production серверу по SSH
2. Выполняет `scripts/deploy.sh` на сервере
3. Делает backup (если включен)
4. Обновляет код (git pull)
5. Устанавливает зависимости
6. Применяет миграции БД
7. Перезапускает сервисы
8. Проверяет health checks

**Результат:**
- ✅ Деплой успешен → проект обновлен
- ❌ Деплой упал → детали ошибки в логах

## Примеры использования

### Пример 1: Автоматическое тестирование

```bash
# Вы сделали изменения
git add .
git commit -m "Add new feature"
git push

# GitHub Actions автоматически:
# 1. Запустит все тесты
# 2. Проверит код
# 3. Отобразит результаты в интерфейсе GitHub
```

### Пример 2: Автоматический деплой

```bash
# Вы готовы к production
git checkout main
git merge develop
git push origin main

# GitHub Actions автоматически:
# 1. Развернет код на сервере
# 2. Применит миграции
# 3. Перезапустит сервисы
# 4. Проверит, что всё работает
```

### Пример 3: Ручной запуск деплоя

1. Откройте GitHub репозиторий
2. Перейдите в **Actions**
3. Выберите **Deploy** workflow
4. Нажмите **Run workflow**
5. Выберите ветку и нажмите **Run**

## Просмотр результатов

### В GitHub интерфейсе:

1. Откройте ваш репозиторий
2. Кликните **Actions** (верхнее меню)
3. Увидите список всех запусков
4. Кликните на конкретный запуск, чтобы увидеть:
   - Логи каждого шага
   - Результаты тестов
   - Покрытие кода
   - Ошибки (если есть)

### В терминале (опционально):

```bash
# Установите GitHub CLI
gh auth login
gh run list                    # Список запусков
gh run watch                   # Смотреть последний запуск
gh run view <run-id>          # Детали запуска
```

## Кастомизация

### Добавить новые проверки

Отредактируйте `.github/workflows/test.yml`:

```yaml
- name: Custom check
  run: |
    python scripts/custom_check.py
```

### Добавить уведомления

Добавьте в workflow:

```yaml
- name: Notify on failure
  if: failure()
  run: |
    # Отправить уведомление в Slack/Discord/Telegram
    curl -X POST https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Изменить условия запуска

```yaml
on:
  push:
    branches: [ main, develop ]
    tags:
      - 'v*'  # Запуск при создании тега
  schedule:
    - cron: '0 0 * * *'  # Ежедневно в полночь
```

## Частые проблемы

### Проблема: Tests не запускаются

**Решение:**
- Проверьте, что workflow файлы находятся в `.github/workflows/`
- Проверьте синтаксис YAML (можно использовать валидатор)
- Убедитесь, что файлы закоммичены и запушены

### Проблема: Deploy не работает

**Решение:**
- Проверьте, что все secrets настроены
- Убедитесь, что SSH ключ правильный
- Проверьте права доступа на сервере
- Посмотрите логи в GitHub Actions

### Проблема: Тесты падают в CI, но работают локально

**Решение:**
- Убедитесь, что все зависимости в `requirements.txt`
- Проверьте, что тесты не зависят от локальных настроек
- Используйте переменные окружения для тестов

## Полезные ссылки

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Marketplace Actions](https://github.com/marketplace?type=actions)

## Заключение

GitHub Actions — это мощный инструмент для автоматизации разработки. В SwiftDevBot уже настроены workflows для тестирования и деплоя, вам нужно только:

1. ✅ Загрузить проект в GitHub
2. ✅ Настроить secrets (для деплоя)
3. ✅ Наслаждаться автоматизацией! 🚀

