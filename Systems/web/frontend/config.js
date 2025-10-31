/**
 * Configuration for the frontend application.
 */

// API Configuration
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
export const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

// Telegram Widget Configuration
export const BOT_USERNAME = import.meta.env.VITE_BOT_USERNAME || 'SwiftDevBot-Test';

// App Configuration
export const APP_NAME = 'SwiftDevBot Web Panel';
export const APP_VERSION = '1.0.0';

// Storage Keys
export const STORAGE_KEYS = {
    TOKEN: 'auth_token',
    REFRESH_TOKEN: 'refresh_token',
    USER: 'user',
    THEME: 'theme',
    LANGUAGE: 'language',
};

// Default Settings
export const DEFAULT_SETTINGS = {
    theme: 'light',
    language: 'en',
    notifications: true,
};

