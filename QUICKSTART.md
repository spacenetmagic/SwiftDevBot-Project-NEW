# 🚀 SwiftDevBot - Быстрый старт

Пошаговое руководство для быстрого запуска SwiftDevBot.

## 📋 Предварительные требования

- Python 3.10 или выше
- pip или Poetry
- PostgreSQL (рекомендуется) или SQLite (для разработки)
- Redis (для FSM и очередей задач)
- Telegram Bot Token (от [@BotFather](https://t.me/BotFather))

---

## ⚡ Быстрая установка (5 минут)

### Шаг 1: Клонирование и настройка окружения

```bash
# Клонируйте репозиторий
git clone https://github.com/yourusername/SwiftDevBot.git
cd SwiftDevBot

# Создайте виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate  # На Windows: .venv\Scripts\activate

# Установите зависимости
pip install -r requirements.txt
```

### Шаг 2: Создание Telegram бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям для создания бота
4. **Сохраните токен** - он понадобится на следующем шаге
5. **Получите свой Telegram ID** (отправьте `/start` боту [@userinfobot](https://t.me/userinfobot))

### Шаг 3: Настройка конфигурации

```bash
# Скопируйте файл примера
cp .env.example .env

# Откройте .env и заполните обязательные поля
nano .env  # или используйте любой текстовый редактор
```

**Минимальная конфигурация (.env):**

```env
# ОБЯЗАТЕЛЬНЫЕ ПОЛЯ:

# Telegram Bot Token (от @BotFather)
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# Username вашего бота (без @)
BOT_USERNAME=my_awesome_bot

# Ваш Telegram ID (от @userinfobot)
SUPER_ADMIN_ID=123456789

# База данных
DB_TYPE=sqlite  # Для начала используйте sqlite, для production - postgresql

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Секретный ключ для JWT (минимум 32 символа)
JWT_SECRET=your_super_secret_key_minimum_32_characters_long_here

# Остальное оставьте по умолчанию или настройте по необходимости
```

**Для PostgreSQL (production):**

```env
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=swiftdevbot
DB_USER=postgres
DB_PASSWORD=your_password
```

### Шаг 4: Инициализация базы данных

```bash
# Создать таблицы в базе данных
sdb db init

# Проверить соединение
sdb db check
```

**Ожидаемый результат:**
```
✓ Database connection successful: sqlite+aiosqlite:///...
```

### Шаг 5: Создание суперадминистратора

```bash
# Создать суперадминистратора (используйте ваш Telegram ID)
sdb user add YOUR_TELEGRAM_ID --role super_admin --username your_username

# Или используйте скрипт
python scripts/create_superuser.py --telegram-id YOUR_TELEGRAM_ID
```

### Шаг 6: Запуск бота

```bash
# Запустить бота
sdb bot start

# Или для веб-панели в другом терминале
uvicorn Systems.web.app:app --reload --port 8000
```

**Готово! 🎉**

Ваш бот работает! Откройте Telegram и найдите вашего бота, отправьте `/start`.

---

## 🎯 Проверка работоспособности

### 1. Проверка конфигурации

```bash
# Тест всех подключений
sdb bot test

# Должен показать:
# ✓ Database: OK
# ✓ Redis: OK
# ✓ Bot Token: OK (@your_bot)
# ✓ Modules: X installed
```

### 2. Проверка статистики

```bash
sdb bot stats
```

### 3. Проверка в Telegram

1. Найдите вашего бота в Telegram
2. Отправьте `/start`
3. Должен прийти ответ с приветствием
4. Проверьте меню команд (должно появиться меню)

### 4. Проверка веб-панели

1. Откройте браузер: `http://localhost:8000`
2. Должна открыться страница веб-панели
3. Используйте Telegram Login Widget для входа

---

## 📚 Следующие шаги

### Установка модулей

```bash
# Посмотреть доступные модули
sdb module list

# Установить модуль из шаблона
sdb module install Modules/template

# Включить модуль
sdb module enable template

# Перезагрузить модуль после изменений
sdb module reload template
```

### Разработка модуля

```bash
# Запустить в режиме автоперезагрузки
sdb module watch

# В другом терминале - разработка модуля
# Любые изменения в .py файлах автоматически перезагрузят модуль
```

### Управление пользователями

```bash
# Добавить пользователя
sdb user add 123456789 --username user1 --role admin

# Список пользователей
sdb user list

# Изменить роль
sdb user role 123456789 admin
```

### Резервное копирование

```bash
# Создать backup перед обновлением
sdb backup create --name before_update

# Список backups
sdb backup list

# Восстановить backup
sdb backup restore before_update
```

---

## 🔧 Решение проблем

### Проблема: "Database connection failed"

**Решение:**
```bash
# Проверить конфигурацию БД
sdb db info

# Переинициализировать БД
sdb db init --force  # ВНИМАНИЕ: удалит все данные!
```

### Проблема: "Bot Token: FAILED"

**Решение:**
1. Проверьте `BOT_TOKEN` в `.env` файле
2. Убедитесь, что токен правильный (скопирован полностью)
3. Проверьте, что токен не истек (получите новый от @BotFather)

### Проблема: "Redis: FAILED"

**Решение:**
```bash
# Установить Redis (Ubuntu/Debian)
sudo apt-get install redis-server

# Запустить Redis
sudo systemctl start redis-server

# Проверить
redis-cli ping  # Должен ответить: PONG
```

### Проблема: Модули не загружаются

**Решение:**
```bash
# Проверить модули
sdb module list

# Проверить лог ошибок
sdb dev logs bot --lines 100

# Перезагрузить модуль
sdb module reload module_name
```

### Проблема: Веб-панель не открывается

**Решение:**
1. Проверьте, что веб-сервер запущен:
   ```bash
   uvicorn Systems.web.app:app --reload --port 8000
   ```

2. Проверьте порт (может быть занят):
   ```bash
   # Проверить занятые порты
   lsof -i :8000
   
   # Использовать другой порт
   uvicorn Systems.web.app:app --reload --port 8001
   ```

3. Проверьте логи:
   ```bash
   sdb dev logs --follow
   ```

---

## 🐳 Запуск в Docker (Production)

### 1. Создайте docker-compose.yml

```yaml
version: '3.8'

services:
  bot:
    build: .
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - DB_TYPE=postgresql
      - DB_HOST=db
      - REDIS_HOST=redis
    depends_on:
      - db
      - redis

  web:
    build: .
    command: uvicorn Systems.web.app:app --host 0.0.0.0 --port 8000
    ports:
      - "8000:8000"
    environment:
      - DB_TYPE=postgresql
      - DB_HOST=db
      - REDIS_HOST=redis
    depends_on:
      - db
      - redis

  db:
    image: postgres:14
    environment:
      - POSTGRES_DB=swiftdevbot
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=your_password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### 2. Запуск

```bash
# Создать .env файл с конфигурацией
cp .env.example .env
# Отредактировать .env

# Запустить все сервисы
docker-compose up -d

# Проверить логи
docker-compose logs -f

# Инициализировать БД
docker-compose exec bot sdb db init
```

---

## 📖 Полезные команды

### Ежедневное использование

```bash
# Запуск бота
sdb bot start

# Остановка бота
sdb bot stop  # или Ctrl+C

# Проверка статуса
sdb bot stats

# Просмотр логов
sdb dev logs --follow

# Управление модулями
sdb module list
sdb module enable module_name
sdb module reload module_name
```

### Администрирование

```bash
# Управление пользователями
sdb user add 123456789 --role admin
sdb user list
sdb user role 123456789 super_admin

# Управление БД
sdb db info
sdb db migrate upgrade

# Резервное копирование
sdb backup create
sdb backup list
```

### Разработка

```bash
# Автоперезагрузка модулей
sdb module watch

# Python shell
sdb dev shell

# Просмотр логов
sdb dev logs --follow

# Тестирование
pytest tests/
```

---

## 🎓 Обучающие материалы

### Создание первого модуля

1. **Используйте шаблон:**
   ```bash
   cp -r Modules/template Modules/my_first_module
   cd Modules/my_first_module
   ```

2. **Отредактируйте `manifest.yaml`:**
   - Измените `name` на `my_first_module`
   - Обновите `display_name`, `description`

3. **Отредактируйте `module.py`:**
   - Добавьте свои команды
   - Реализуйте логику

4. **Установите модуль:**
   ```bash
   sdb module enable my_first_module
   sdb module reload my_first_module
   ```

5. **Протестируйте:**
   - Отправьте команду боту в Telegram
   - Проверьте работу

Подробнее: [docs/MODULES.md](docs/MODULES.md)

---

## 📚 Документация

- **CLI команды:** [docs/CLI_COMMANDS.md](docs/CLI_COMMANDS.md)
- **Архитектура:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Модули:** [docs/MODULES.md](docs/MODULES.md)
- **API:** [docs/API.md](docs/API.md)
- **Деплой:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)
- **Разработка:** [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)

---

## ✅ Чеклист первого запуска

- [ ] Python 3.10+ установлен
- [ ] Репозиторий склонирован
- [ ] Виртуальное окружение создано
- [ ] Зависимости установлены
- [ ] Telegram бот создан (@BotFather)
- [ ] Telegram ID получен (@userinfobot)
- [ ] `.env` файл создан и заполнен
- [ ] База данных инициализирована (`sdb db init`)
- [ ] Суперадминистратор создан (`sdb user add`)
- [ ] Redis запущен
- [ ] Бот запущен (`sdb bot start`)
- [ ] Бот отвечает в Telegram (`/start`)
- [ ] Веб-панель доступна (`http://localhost:8000`)
- [ ] Тест пройден (`sdb bot test`)

---

## 🆘 Помощь и поддержка

- **GitHub Issues:** [Создать issue](https://github.com/yourusername/SwiftDevBot/issues)
- **Документация:** [docs/](docs/)
- **Примеры:** [Modules/template/](Modules/template/)

---

## 🎉 Готово!

Теперь у вас работает полнофункциональный Telegram бот с веб-панелью!

**Следующие шаги:**
1. Изучите структуру проекта
2. Создайте свой первый модуль
3. Настройте веб-панель под свои нужды
4. Разверните в production

**Удачной разработки! 🚀**

