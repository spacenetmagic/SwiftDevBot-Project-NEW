# SwiftDevBot Web Panel - Frontend

React frontend for SwiftDevBot web panel.

## Structure

```
Systems/web/frontend/
├── index.html          # HTML entry point
├── main.jsx            # React app entry point
├── config.js           # Configuration
├── api/
│   └── client.js       # API client with axios
├── components/
│   ├── Header.jsx      # Header component
│   ├── Sidebar.jsx     # Sidebar navigation
│   └── ProtectedRoute.jsx  # Protected route wrapper
├── pages/
│   ├── LoginPage.jsx       # Login with Telegram Widget
│   ├── DashboardPage.jsx  # Dashboard overview
│   ├── ProfilePage.jsx     # User profile
│   ├── ModulesPage.jsx     # Modules management
│   ├── SettingsPage.jsx    # User settings
│   └── AdminPage.jsx       # Admin panel
└── styles/
    └── app.css         # Main styles with theme support
```

## Features

- **React 18+** with React Router v6
- **Responsive Design** (mobile, tablet, desktop)
- **Dark/Light Theme** support
- **Telegram Widget** authentication
- **Protected Routes** with role-based access
- **API Client** with JWT token handling
- **Error Handling** and loading states
- **WebSocket** support (ready for real-time notifications)

## Setup

This frontend is designed to be served as static files by the FastAPI backend.

For development with Vite:

```bash
npm install
npm run dev
```

For production:

```bash
npm run build
# Copy dist/ files to Systems/web/static/
```

## Configuration

Edit `config.js` to configure:
- `API_URL` - Backend API URL
- `WS_URL` - WebSocket URL
- `BOT_USERNAME` - Telegram bot username for Widget

## Environment Variables

Create `.env` file:
```
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000
VITE_BOT_USERNAME=SwiftDevBot-Test
```

