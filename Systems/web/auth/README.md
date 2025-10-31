# Authentication Service

JWT-based authentication service для веб-панели SwiftDevBot.

## Компоненты

### JWTHandler
- **RS256 (RSA 2048-bit)** для подписи токенов
- Автоматическая генерация ключей при первом запуске
- Ключи сохраняются в `Data/security/`
- Access token: 24 часа
- Refresh token: 7 дней

### TelegramAuth
- Проверка hash от Telegram WebApp
- Использование HMAC SHA256
- Проверка временной метки (не старше 24 часов)
- Автоматическое создание/обновление пользователя

### FastAPI Routes
- `POST /api/auth/telegram-login` - Вход через Telegram
- `POST /api/auth/refresh` - Обновление токена
- `POST /api/auth/logout` - Выход

### Dependencies
- `get_current_user` - Получить текущего пользователя
- `require_admin` - Требовать роль admin/super_admin
- `require_super_admin` - Требовать роль super_admin

## Использование

### Защита эндпоинтов

```python
from fastapi import Depends
from Systems.web.auth.dependencies import get_current_user, require_admin
from Systems.core.database.models.user import User

@app.get("/api/profile")
async def get_profile(user: User = Depends(get_current_user)):
    return {"user_id": user.telegram_id, "username": user.username}

@app.get("/api/admin/stats")
async def admin_stats(user: User = Depends(require_admin)):
    return {"stats": "..."}
```

### Регистрация роутов

```python
from Systems.web.auth.routes import router as auth_router

app.include_router(auth_router)
```

## Безопасность

- RSA 2048-bit ключи для подписи токенов
- Проверка Telegram hash обязательна
- Токены содержат минимальную информацию
- Все операции логируются в audit_log

