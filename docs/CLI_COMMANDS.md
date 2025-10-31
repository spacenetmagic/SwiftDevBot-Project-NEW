# SwiftDevBot CLI Commands

Полный справочник всех команд CLI для SwiftDevBot.

## Общая информация

**Основная команда:** `sdb` или `python sdb.py`

**Версия:** `sdb --version`

**Помощь:** `sdb --help` или `sdb <command> --help`

---

## 🗄️ База данных (db)

Управление базой данных бота.

### `sdb db init`

Инициализировать базу данных: создать все таблицы.

**Опции:**
- `--force` - Удалить существующие таблицы сначала (WARNING: удаляет данные!)

**Примеры:**
```bash
sdb db init
sdb db init --force
```

**Результат:**
- Создает все таблицы из моделей SQLAlchemy
- Применяет миграции Alembic (если настроено)
- Показывает список созданных таблиц

**Вывод:**
```
✓ Created 3 tables: users, module_settings, audit_logs
✓ Migrations applied successfully
```

---

### `sdb db check`

Проверить соединение с базой данных.

**Пример:**
```bash
sdb db check
```

**Результат:**
- Проверяет соединение с БД
- Выход: `✓ Database connection successful` или `✗ Database connection failed`

---

### `sdb db migrate <action>`

Запустить миграции базы данных (Alembic).

**Аргументы:**
- `action` - Действие: `upgrade`, `downgrade`, `history`, `current`

**Опции:**
- `--revision <revision>` - Ревизия для миграции (по умолчанию: `head`)

**Примеры:**
```bash
sdb db migrate upgrade
sdb db migrate upgrade --revision abc123
sdb db migrate downgrade --revision -1
sdb db migrate history
sdb db migrate current
```

**Требования:** Файл `alembic.ini` должен существовать.

---

### `sdb db info`

Показать информацию о базе данных.

**Пример:**
```bash
sdb db info
```

**Вывод:**
```
Database Information:

  Type: postgresql
  URL: postgresql://user:pass@localhost:5432/swiftdevbot
  Host: localhost
  Port: 5432
  Database: swiftdevbot
  User: postgres
  Version: PostgreSQL 14.5
  Tables: 3
    users, module_settings, audit_logs

✓ Connection: OK
```

---

## 🤖 Управление ботом (bot)

Команды для управления и мониторинга бота.

### `sdb bot stats`

Показать статистику бота.

**Пример:**
```bash
sdb bot stats
```

**Вывод:**
```
Bot Statistics:

  Bot Username: @mybot
  Super Admin ID: 123456789
  Total Users: 150
  Active Users: 120
  Installed Modules: 5
  Enabled Modules: 3
  Audit Log Entries: 1250

✓ Statistics retrieved
```

**Информация:**
- Общее количество пользователей
- Активные пользователи
- Количество модулей
- Записи в аудит-логе

---

### `sdb bot version`

Показать версию и информацию о боте.

**Пример:**
```bash
sdb bot version
```

**Вывод:**
```
SwiftDevBot Information:

  Version: 1.0.0
  Bot Username: @mybot
  Database: postgresql
  Redis: localhost:6379
  Log Level: INFO

✓ Information retrieved
```

---

### `sdb bot test`

Тестировать конфигурацию и подключения бота.

**Пример:**
```bash
sdb bot test
```

**Проверяет:**
- ✅ Соединение с базой данных
- ✅ Соединение с Redis
- ✅ Валидность bot token
- ✅ Наличие модулей

**Вывод:**
```
Testing bot configuration...

✓ Database: OK
✓ Redis: OK
✓ Bot Token: OK (@mybot)
✓ Modules: 5 installed

✓ All tests passed!
```

**Выход:** `0` если все тесты прошли, `1` если есть проблемы.

---

### `sdb bot clean`

Очистить временные файлы и старые данные.

**Опции:**
- `--logs` - Удалить старые log файлы (старше 30 дней)
- `--cache` - Удалить cache файлы (__pycache__)
- `--all` - Очистить всё

**Примеры:**
```bash
sdb bot clean --logs
sdb bot clean --cache
sdb bot clean --all
```

**Результат:**
- Удаляет старые логи из `Data/logs/`
- Удаляет `__pycache__` директории
- Показывает количество удаленных файлов

**Вывод:**
```
✓ Cleaned: 25 old log files, 15 cache directories
```

---

## 📦 Модули (module)

Управление модулями бота.

### `sdb module list`

Список всех установленных модулей.

**Опции:**
- `--enabled` - Показать только включенные модули
- `--disabled` - Показать только отключенные модули

**Примеры:**
```bash
sdb module list
sdb module list --enabled
sdb module list --disabled
```

**Вывод:**
```
Installed modules (3):
  ✓ Enabled  example_module (v1.0.0)
  ✗ Disabled template_module (v0.1.0)
  ✓ Enabled  my_module (v2.0.0)
```

---

### `sdb module install <path>`

Установить модуль из директории.

**Аргументы:**
- `path` - Путь к директории модуля (обязательно)

**Опции:**
- `--name <name>` - Имя модуля (по умолчанию: имя директории)

**Примеры:**
```bash
sdb module install ./my_module
sdb module install /path/to/module --name custom_name
```

**Требования:**
- Директория должна содержать `manifest.yaml`
- Директория должна содержать `module.py`

---

### `sdb module uninstall <name>`

Удалить модуль.

**Аргументы:**
- `name` - Имя модуля (обязательно)

**Опции:**
- `--force` - Удалить без подтверждения

**Примеры:**
```bash
sdb module uninstall example_module
sdb module uninstall example_module --force
```

**Внимание:** Модуль будет полностью удален из `Modules/`.

---

### `sdb module enable <name>`

Включить модуль.

**Аргументы:**
- `name` - Имя модуля (обязательно)

**Пример:**
```bash
sdb module enable example_module
```

**Результат:** Модуль загружается и становится активным.

---

### `sdb module disable <name>`

Отключить модуль.

**Аргументы:**
- `name` - Имя модуля (обязательно)

**Пример:**
```bash
sdb module disable example_module
```

**Результат:** Модуль выгружается и становится неактивным.

---

### `sdb module reload <name>`

Перезагрузить модуль (hot reload).

**Аргументы:**
- `name` - Имя модуля (обязательно)

**Пример:**
```bash
sdb module reload example_module
```

**Результат:** Модуль перезагружается без перезапуска бота.

---

### `sdb module update <name>`

Обновить модуль (перезагрузить с применением изменений).

**Аргументы:**
- `name` - Имя модуля (обязательно)

**Пример:**
```bash
sdb module update example_module
```

**Примечание:** В текущей версии эквивалентно `reload`.

---

### `sdb module watch`

Отслеживать изменения модулей и автоматически перезагружать (режим разработки).

**Пример:**
```bash
sdb module watch
```

**Результат:**
- Мониторит директорию `Modules/`
- Автоматически перезагружает модули при изменении `.py` файлов
- Останавливается по `Ctrl+C`

**Требования:** `watchdog` (устанавливается автоматически)

---

## 👤 Пользователи (user)

Управление пользователями бота.

### `sdb user add <telegram_id>`

Добавить нового пользователя.

**Аргументы:**
- `telegram_id` - Telegram ID пользователя (обязательно, число)

**Опции:**
- `--username <username>` - Username (опционально)
- `--full-name <name>` - Полное имя (опционально)
- `--role <role>` - Роль: `user`, `admin`, `super_admin` (по умолчанию: `user`)

**Примеры:**
```bash
sdb user add 123456789
sdb user add 123456789 --username testuser --role admin
sdb user add 987654321 --full-name "John Doe" --role super_admin
```

**Результат:** Пользователь создается или обновляется в базе данных.

---

### `sdb user list`

Список всех пользователей.

**Опции:**
- `--role <role>` - Фильтр по роли: `user`, `admin`, `super_admin`
- `--limit <number>` - Максимальное количество пользователей (по умолчанию: 100)

**Примеры:**
```bash
sdb user list
sdb user list --role admin
sdb user list --limit 50
```

**Вывод:**
```
Users (5):
ID           Username             Role         Status  
------------------------------------------------------------
123456789    testuser             user         Active  
987654321    adminuser            admin        Active  
555555555    superadmin           super_admin  Active  
```

---

### `sdb user role <telegram_id> <role>`

Изменить роль пользователя.

**Аргументы:**
- `telegram_id` - Telegram ID пользователя (обязательно)
- `role` - Новая роль: `user`, `admin`, `super_admin` (обязательно)

**Примеры:**
```bash
sdb user role 123456789 admin
sdb user role 987654321 super_admin
```

**Результат:** Роль пользователя обновляется в базе данных.

---

### `sdb user permissions <telegram_id>`

Показать разрешения пользователя.

**Аргументы:**
- `telegram_id` - Telegram ID пользователя (обязательно)

**Пример:**
```bash
sdb user permissions 123456789
```

**Вывод:**
```
User: testuser (123456789)
Role: admin
Active: True

Permissions (5):
  - user.read
  - user.write
  - module.read
  - module.write
  - admin.access
```

---

## 🤖 Управление ботом (bot)

Команды для управления и мониторинга бота.

### `sdb bot start`

Запустить бота.

**Пример:**
```bash
sdb bot start
```

**Результат:** Запускает бота. Останавливается по `Ctrl+C`.

**Примечание:** Бот запускается в текущем терминале. Для фонового режима используйте systemd или screen/tmux.

---

### `sdb bot stop`

Остановить запущенный бот.

**Пример:**
```bash
sdb bot stop
```

**Результат:** 
- Находит процесс бота
- Отправляет SIGTERM для graceful shutdown
- Если не остановился за 5 секунд - принудительно завершает

**Вывод:**
```
✓ Bot service stopped gracefully
```

**Требования:** `psutil` (устанавливается автоматически с зависимостями)

---

### `sdb bot restart`

Перезапустить бота.

**Пример:**
```bash
sdb bot restart
```

**Результат:** 
1. Останавливает запущенный бот
2. Ждет 1 секунду
3. Запускает бота заново

---

### `sdb bot status`

Показать статус бота и веб-панели.

**Пример:**
```bash
sdb bot status
```

**Вывод:**
```
Bot Service Status:

  Bot: ✓ Running
    PID: 12345
    Status: running
    Uptime: 2:30:15
  Web Panel: ✓ Running (PID: 12346)
```

**Информация:**
- Статус бота (запущен/остановлен)
- PID процесса
- Время работы (uptime)
- Статус веб-панели

**Требования:** `psutil` для детального статуса

---

### `sdb bot stats`

Показать статистику бота.

---

## 🛠️ Разработка (dev)

Инструменты для разработки.

### `sdb dev watch`

Отслеживать изменения модулей (аналог `sdb module watch`).

**Пример:**
```bash
sdb dev watch
```

**Описание:** То же самое, что `sdb module watch`.

---

### `sdb dev logs [service]`

Показать логи сервиса.

**Аргументы:**
- `service` - Имя сервиса (опционально)

**Опции:**
- `--follow`, `-f` - Следовать за логами (аналог `tail -f`)
- `--lines`, `-n <number>` - Количество строк (по умолчанию: 50)

**Примеры:**
```bash
sdb dev logs
sdb dev logs bot
sdb dev logs --follow
sdb dev logs --lines 100
sdb dev logs bot -f -n 200
```

**Результат:**
- Показывает последние N строк логов
- При `--follow` отслеживает новые записи в реальном времени
- Ищет логи в директории `Logs/`

---

### `sdb dev shell`

Открыть Python shell с контекстом приложения.

**Пример:**
```bash
sdb dev shell
```

**Результат:**
- Запускает IPython (если установлен) или стандартный Python shell
- Предзагружает модули SwiftDevBot:
  - `Config`
  - `get_session_factory`
  - `config` (экземпляр конфигурации)

**Использование:**
```python
>>> config.db_type
'sqlite'
>>> async with get_session_factory()() as session:
...     # Работа с базой данных
...
```

---

## 💾 Резервные копии (backup)

Управление резервными копиями.

### `sdb backup create`

Создать резервную копию.

**Опции:**
- `--name <name>` - Имя резервной копии (по умолчанию: timestamp)
- `--include-db` - Включить базу данных
- `--include-modules` - Включить модули
- `--include-logs` - Включить логи

**Примеры:**
```bash
sdb backup create
sdb backup create --name my_backup
sdb backup create --include-db --include-modules
sdb backup create --include-logs
```

**Результат:**
- Создает `.tar.gz` архив в директории `Backups/`
- По умолчанию включает все (БД, модули, логи, `.env`)
- Имя по умолчанию: `backup_YYYYMMDD_HHMMSS`

**Выход:**
```
✓ Backup created: Backups/backup_20240101_120000.tar.gz (2.45 MB)
```

---

### `sdb backup restore <name>`

Восстановить резервную копию.

**Аргументы:**
- `name` - Имя резервной копии (без `.tar.gz` расширения)

**Опции:**
- `--force` - Восстановить без подтверждения

**Примеры:**
```bash
sdb backup restore backup_20240101_120000
sdb backup restore my_backup --force
```

**Внимание:** Перезапишет существующие файлы!

**Процесс:**
1. Проверяет наличие резервной копии
2. Запрашивает подтверждение (если не `--force`)
3. Извлекает файлы из архива

---

### `sdb backup list`

Список всех резервных копий.

**Пример:**
```bash
sdb backup list
```

**Вывод:**
```
Backups (5):
Name                           Size       Date                
----------------------------------------------------------------------
backup_20240115_120000        2.45 MB    2024-01-15 12:00:00
backup_20240114_180000        1.89 MB    2024-01-14 18:00:00
my_backup                     3.12 MB    2024-01-13 10:30:00
backup_20240112_090000        1.23 MB    2024-01-12 09:00:00
```

**Описание:**
- Показывает все `.tar.gz` файлы в `Backups/`
- Сортирует по дате (новые первые)
- Показывает размер и дату создания

---

## 📝 Примеры использования

### Типичные сценарии

#### 1. Установка и настройка модуля
```bash
# Установить модуль
sdb module install ./my_module

# Включить модуль
sdb module enable my_module

# Проверить статус
sdb module list --enabled
```

#### 2. Управление пользователями
```bash
# Добавить админа
sdb user add 123456789 --username admin --role admin

# Изменить роль
sdb user role 123456789 super_admin

# Проверить разрешения
sdb user permissions 123456789
```

#### 3. Разработка модуля
```bash
# Запустить в режиме watch
sdb dev watch

# Просмотреть логи
sdb dev logs bot --follow

# Открыть shell для тестирования
sdb dev shell
```

#### 4. Резервное копирование
```bash
# Создать backup перед изменениями
sdb backup create --name before_update

# Восстановить backup
sdb backup restore before_update

# Просмотреть список backups
sdb backup list
```

#### 5. Запуск бота
```bash
# Запустить бота
sdb bot start

# В другом терминале - проверить логи
sdb dev logs bot --follow
```

---

## 🔍 Получение справки

**Общая справка:**
```bash
sdb --help
sdb --version
```

**Справка по группе команд:**
```bash
sdb module --help
sdb user --help
sdb service --help
sdb dev --help
sdb backup --help
```

**Справка по конкретной команде:**
```bash
sdb module install --help
sdb user add --help
sdb backup create --help
```

---

## ❗ Коды выхода

- `0` - Успешное выполнение
- `1` - Общая ошибка
- `130` - Прервано пользователем (Ctrl+C)

---

## 📌 Замечания

1. **Асинхронные команды:** Команды, работающие с базой данных, выполняются асинхронно
2. **Логирование:** Все команды логируются в `Data/logs/cli.log`
3. **Подтверждения:** Некоторые команды запрашивают подтверждение (можно пропустить с `--force`)
4. **Hot Reload:** `module reload` и `module watch` работают без перезапуска бота
5. **Shell:** `dev shell` требует IPython для лучшего опыта (устанавливается автоматически)

---

## 🔗 Связанная документация

- [Modules Documentation](MODULES.md) - Создание модулей
- [Development Guide](DEVELOPMENT.md) - Разработка
- [Architecture](ARCHITECTURE.md) - Архитектура системы

