# 📋 SwiftDevBot CLI - Полный список команд

## Всего категорий: 6

### 🗄️ db - База данных (4 команды)
- `sdb db init` - Инициализировать БД
- `sdb db check` - Проверить соединение
- `sdb db migrate` - Миграции (upgrade/downgrade/history/current)
- `sdb db info` - Информация о БД

### 🤖 bot - Управление ботом (8 команд)
- `sdb bot start` - Запустить бота
- `sdb bot stop` - Остановить бота
- `sdb bot restart` - Перезапустить бота
- `sdb bot status` - Статус бота и веб-панели
- `sdb bot stats` - Статистика бота
- `sdb bot version` - Версия и информация
- `sdb bot test` - Тест конфигурации
- `sdb bot clean` - Очистка временных файлов

### 📦 module - Модули (8 команд)
- `sdb module list` - Список модулей
- `sdb module install` - Установить модуль
- `sdb module uninstall` - Удалить модуль
- `sdb module enable` - Включить модуль
- `sdb module disable` - Отключить модуль
- `sdb module reload` - Перезагрузить модуль
- `sdb module update` - Обновить модуль
- `sdb module watch` - Автоперезагрузка

### 👤 user - Пользователи (4 команды)
- `sdb user add` - Добавить пользователя
- `sdb user list` - Список пользователей
- `sdb user role` - Изменить роль
- `sdb user permissions` - Показать разрешения


### 🛠️ dev - Разработка (3 команды)
- `sdb dev watch` - Отслеживать изменения
- `sdb dev logs` - Показать логи
- `sdb dev shell` - Python shell

### 💾 backup - Резервные копии (3 команды)
- `sdb backup create` - Создать резервную копию
- `sdb backup restore` - Восстановить резервную копию
- `sdb backup list` - Список резервных копий

---

## Итого: 30 команд (было 30, стало 30 - перенесено из service в bot)

Подробная документация: [docs/CLI_COMMANDS.md](docs/CLI_COMMANDS.md)
