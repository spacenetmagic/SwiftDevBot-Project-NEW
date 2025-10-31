/**
 * API client for backend communication.
 */

import axios from 'axios';
import { API_URL, STORAGE_KEYS } from '../config';

// Create axios instance
const api = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Request interceptor - Add JWT token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem(STORAGE_KEYS.TOKEN);
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => {
        return Promise.reject(error);
    }
);

// Response interceptor - Handle errors and refresh token
api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        // Handle 401 Unauthorized - Token expired
        if (error.response?.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const refreshToken = localStorage.getItem(STORAGE_KEYS.REFRESH_TOKEN);
                if (refreshToken) {
                    // Try to refresh token
                    const response = await axios.post(`${API_URL}/api/auth/refresh`, {
                        refresh_token: refreshToken,
                    });

                    const { access_token, refresh_token: newRefreshToken } = response.data;
                    localStorage.setItem(STORAGE_KEYS.TOKEN, access_token);
                    if (newRefreshToken) {
                        localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, newRefreshToken);
                    }

                    // Retry original request
                    originalRequest.headers.Authorization = `Bearer ${access_token}`;
                    return api(originalRequest);
                }
            } catch (refreshError) {
                // Refresh failed, logout user
                localStorage.removeItem(STORAGE_KEYS.TOKEN);
                localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
                localStorage.removeItem(STORAGE_KEYS.USER);
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }

        // Handle other errors
        const errorMessage = error.response?.data?.detail || error.message || 'An error occurred';
        return Promise.reject({ ...error, message: errorMessage });
    }
);

export default api;

