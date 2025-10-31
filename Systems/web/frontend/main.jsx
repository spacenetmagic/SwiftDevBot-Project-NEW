/**
 * Main React application entry point.
 */

import React, { createContext, useContext, useState, useEffect } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';

import { STORAGE_KEYS } from './config';
import api from './api/client';
import ProtectedRoute from './components/ProtectedRoute';
import Header from './components/Header';
import Sidebar from './components/Sidebar';

import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ProfilePage from './pages/ProfilePage';
import ModulesPage from './pages/ModulesPage';
import SettingsPage from './pages/SettingsPage';
import AdminPage from './pages/AdminPage';

import './styles/app.css';
import useWebSocket from './hooks/useWebSocket';

// User Context
const UserContext = createContext(null);

export const useUser = () => {
    const context = useContext(UserContext);
    if (!context) {
        throw new Error('useUser must be used within UserProvider');
    }
    return context;
};

// User Provider Component
function UserProvider({ children }) {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        // Load user from localStorage
        const storedUser = localStorage.getItem(STORAGE_KEYS.USER);
        const token = localStorage.getItem(STORAGE_KEYS.TOKEN);

        if (storedUser && token) {
            try {
                setUser(JSON.parse(storedUser));
                // Verify token by fetching current user
                api.get('/api/users/me')
                    .then(response => {
                        setUser(response.data);
                        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(response.data));
                    })
                    .catch(() => {
                        // Token invalid, clear storage
                        logout();
                    })
                    .finally(() => setLoading(false));
            } catch (e) {
                setLoading(false);
            }
        } else {
            setLoading(false);
        }
    }, []);

    const login = (userData, token, refreshToken) => {
        setUser(userData);
        localStorage.setItem(STORAGE_KEYS.USER, JSON.stringify(userData));
        localStorage.setItem(STORAGE_KEYS.TOKEN, token);
        if (refreshToken) {
            localStorage.setItem(STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
        }
    };

    const logout = () => {
        setUser(null);
        localStorage.removeItem(STORAGE_KEYS.USER);
        localStorage.removeItem(STORAGE_KEYS.TOKEN);
        localStorage.removeItem(STORAGE_KEYS.REFRESH_TOKEN);
    };

    const value = {
        user,
        loading,
        login,
        logout,
        isAdmin: user?.role === 'admin' || user?.role === 'super_admin',
        isSuperAdmin: user?.role === 'super_admin',
    };

    return <UserContext.Provider value={value}>{children}</UserContext.Provider>;
}

// Main App Component
function App() {
    const { loading, user } = useUser();
    
    // Initialize WebSocket for notifications (only when user is logged in)
    useWebSocket();

    if (loading) {
        return (
            <div className="loading-container">
                <div className="spinner"></div>
                <p>Loading...</p>
            </div>
        );
    }

    return (
        <BrowserRouter>
            <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route
                    path="/"
                    element={
                        <ProtectedRoute>
                            <div className="app-layout">
                                <Sidebar />
                                <div className="main-content">
                                    <Header />
                                    <div className="page-content">
                                        <Routes>
                                            <Route path="/" element={<Navigate to="/dashboard" replace />} />
                                            <Route path="/dashboard" element={<DashboardPage />} />
                                            <Route path="/profile" element={<ProfilePage />} />
                                            <Route path="/modules" element={<ModulesPage />} />
                                            <Route path="/settings" element={<SettingsPage />} />
                                            <Route path="/admin" element={<AdminPage />} />
                                        </Routes>
                                    </div>
                                </div>
                            </div>
                        </ProtectedRoute>
                    }
                />
            </Routes>
        </BrowserRouter>
    );
}

// Render App
const container = document.getElementById('root');
const root = createRoot(container);
root.render(
    <React.StrictMode>
        <UserProvider>
            <App />
        </UserProvider>
    </React.StrictMode>
);

