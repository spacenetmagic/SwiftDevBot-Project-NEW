# API Documentation

Complete API reference for SwiftDevBot Web Panel.

## Base URL

```
Development: http://localhost:8000
Production: https://your-domain.com
```

## Authentication

All protected endpoints require JWT Bearer token in Authorization header:

```
Authorization: Bearer <access_token>
```

### Getting a Token

1. **Telegram Login** (see [Telegram Login](#telegram-login))
2. **Refresh Token** (see [Refresh Token](#refresh-token))

## Endpoints

### Authentication

#### Telegram Login

Login using Telegram authentication data.

**Endpoint:** `POST /api/auth/telegram`

**Request Body:**
```json
{
  "id": "123456789",
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "photo_url": "https://...",
  "auth_date": "1234567890",
  "hash": "telegram_hash_here"
}
```

**Response:** `200 OK`
```json
{
  "user": {
    "telegram_id": 123456789,
    "username": "johndoe",
    "full_name": "John Doe",
    "role": "user",
    "is_active": true
  },
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIs..."
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid Telegram hash
- `400 Bad Request` - Missing required fields

#### Refresh Token

Get new access token using refresh token.

**Endpoint:** `POST /api/auth/refresh`

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJSUzI1NiIs..."
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIs..."
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or expired refresh token

#### Logout

Invalidate refresh token.

**Endpoint:** `POST /api/auth/logout`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "message": "Logged out successfully"
}
```

### Users

#### Get Current User

Get current authenticated user information.

**Endpoint:** `GET /api/users/me`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "telegram_id": 123456789,
  "username": "johndoe",
  "full_name": "John Doe",
  "role": "user",
  "is_active": true,
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

#### List Users

List all users (admin only).

**Endpoint:** `GET /api/users/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `limit` (optional, default: 100) - Maximum number of users
- `offset` (optional, default: 0) - Pagination offset
- `role` (optional) - Filter by role (user, admin, super_admin)

**Response:** `200 OK`
```json
[
  {
    "telegram_id": 123456789,
    "username": "johndoe",
    "full_name": "John Doe",
    "role": "user",
    "is_active": true
  },
  ...
]
```

#### Update User Role

Change user role (admin only).

**Endpoint:** `PUT /api/users/{telegram_id}/role`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "role": "admin"
}
```

**Response:** `200 OK`
```json
{
  "message": "Role updated successfully"
}
```

**Error Responses:**
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - User not found

### Modules

#### List Modules

Get list of all modules.

**Endpoint:** `GET /api/modules/`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
[
  {
    "name": "example_module",
    "display_name": "Example Module",
    "version": "1.0.0",
    "description": "Example module",
    "enabled": true,
    "commands": [
      {
        "name": "example",
        "description": "Example command",
        "admin": false
      }
    ],
    "settings": {...}
  },
  ...
]
```

#### Get Module

Get specific module information.

**Endpoint:** `GET /api/modules/{module_name}`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "name": "example_module",
  "display_name": "Example Module",
  "version": "1.0.0",
  "enabled": true,
  "commands": [...],
  "settings": {...}
}
```

**Error Responses:**
- `404 Not Found` - Module not found

#### Enable Module

Enable a module (admin only).

**Endpoint:** `POST /api/modules/{module_name}/enable`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "message": "Module enabled successfully"
}
```

**Error Responses:**
- `403 Forbidden` - Admin only
- `404 Not Found` - Module not found

#### Disable Module

Disable a module (admin only).

**Endpoint:** `POST /api/modules/{module_name}/disable`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "message": "Module disabled successfully"
}
```

#### Reload Module

Hot reload a module (admin only).

**Endpoint:** `POST /api/modules/{module_name}/reload`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "message": "Module reloaded successfully"
}
```

### Settings

#### Get User Settings

Get user settings for a module.

**Endpoint:** `GET /api/settings/{module_name}/user`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "theme": "dark",
  "notifications_enabled": true
}
```

**Error Responses:**
- `404 Not Found` - Module not found

#### Update User Setting

Update a user setting.

**Endpoint:** `PUT /api/settings/{module_name}/user/{setting_key}`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "value": "dark"
}
```

**Response:** `200 OK`
```json
{
  "message": "Setting updated successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid value
- `404 Not Found` - Module or setting not found

#### Get Admin Settings

Get admin settings for a module (admin only).

**Endpoint:** `GET /api/settings/{module_name}/admin`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "max_users": 1000,
  "rate_limit": 100
}
```

#### Update Admin Setting

Update an admin setting (admin only).

**Endpoint:** `PUT /api/settings/{module_name}/admin/{setting_key}`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Request Body:**
```json
{
  "value": 500
}
```

**Response:** `200 OK`
```json
{
  "message": "Setting updated successfully"
}
```

#### Get Setting Schema

Get setting schema for a module.

**Endpoint:** `GET /api/settings/{module_name}/schema`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "user_settings": {
    "theme": {
      "type": "string",
      "default": "light",
      "description": "Theme preference"
    }
  },
  "admin_settings": {
    "max_users": {
      "type": "integer",
      "default": 100,
      "min": 1,
      "max": 1000
    }
  }
}
```

### Admin

#### Get Statistics

Get system statistics (admin only).

**Endpoint:** `GET /api/admin/stats`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`
```json
{
  "total_users": 150,
  "active_users": 120,
  "total_modules": 10,
  "enabled_modules": 8,
  "total_commands": 25,
  "total_settings": 50
}
```

#### Get Audit Logs

Get audit logs (admin only).

**Endpoint:** `GET /api/admin/audit-logs`

**Headers:**
```
Authorization: Bearer <access_token>
```

**Query Parameters:**
- `limit` (optional, default: 100) - Maximum number of logs
- `offset` (optional, default: 0) - Pagination offset
- `user_id` (optional) - Filter by user ID
- `action` (optional) - Filter by action

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "user_id": 123456789,
    "action": "module.enabled",
    "resource": "example_module",
    "success": true,
    "timestamp": "2024-01-01T00:00:00",
    "ip_address": "192.168.1.1"
  },
  ...
]
```

### WebSocket

#### Notifications

Real-time notifications via WebSocket.

**Endpoint:** `WS /ws/notifications/{user_id}`

**Authentication:** JWT token as query parameter:
```
ws://localhost:8000/ws/notifications/123456789?token=<access_token>
```

**Message Format:**
```json
{
  "type": "notification",
  "data": {
    "message": "Module reloaded",
    "module": "example_module"
  },
  "timestamp": "2024-01-01T00:00:00"
}
```

### Health Check

**Endpoint:** `GET /health`

**Response:** `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00",
  "version": "1.0.0"
}
```

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message here",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 201 | Created | Resource created |
| 400 | Bad Request | Invalid request data |
| 401 | Unauthorized | Authentication required or failed |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 422 | Unprocessable Entity | Validation error |
| 500 | Internal Server Error | Server error |

### Common Error Codes

| Error Code | HTTP Status | Description |
|------------|-------------|-------------|
| `INVALID_TOKEN` | 401 | Invalid or expired token |
| `PERMISSION_DENIED` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Request validation failed |
| `INTERNAL_ERROR` | 500 | Internal server error |

## Rate Limiting

Rate limiting is applied to prevent abuse:

- **Authentication endpoints**: 5 requests per minute
- **API endpoints**: 100 requests per minute per user
- **Admin endpoints**: 50 requests per minute

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1234567890
```

## Examples

### Python (httpx)

```python
import httpx

# Login
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:8000/api/auth/telegram",
        json={
            "id": "123456789",
            "first_name": "John",
            "username": "johndoe",
            "auth_date": "1234567890",
            "hash": "telegram_hash"
        }
    )
    data = response.json()
    token = data["access_token"]

    # Use token
    response = await client.get(
        "http://localhost:8000/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    user = response.json()
```

### JavaScript (axios)

```javascript
// Login
const loginResponse = await axios.post('http://localhost:8000/api/auth/telegram', {
  id: '123456789',
  first_name: 'John',
  username: 'johndoe',
  auth_date: '1234567890',
  hash: 'telegram_hash'
});

const { access_token } = loginResponse.data;

// Use token
const userResponse = await axios.get('http://localhost:8000/api/users/me', {
  headers: { Authorization: `Bearer ${access_token}` }
});
```

### cURL

```bash
# Login
TOKEN=$(curl -X POST http://localhost:8000/api/auth/telegram \
  -H "Content-Type: application/json" \
  -d '{"id":"123456789","first_name":"John","username":"johndoe","hash":"..."}' \
  | jq -r '.access_token')

# Get user info
curl http://localhost:8000/api/users/me \
  -H "Authorization: Bearer $TOKEN"
```

---

For architecture details, see [Architecture Documentation](ARCHITECTURE.md).

For module development, see [Modules Documentation](MODULES.md).

