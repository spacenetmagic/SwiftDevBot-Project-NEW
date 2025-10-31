/**
 * Header component with navigation and user info.
 */

import { useState } from 'react';
import { useUser } from '../main';
import useWebSocket from '../hooks/useWebSocket';
import api from '../api/client';

function Header() {
    const { user, logout, isAdmin } = useUser();
    const { notifications, connected } = useWebSocket();
    const [showNotifications, setShowNotifications] = useState(false);

    const handleLogout = async () => {
        try {
            await api.post('/api/auth/logout');
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            logout();
            window.location.href = '/login';
        }
    };

    const unreadCount = notifications.filter((n) => !n.read).length;

    return (
        <header className="header">
            <div className="header-content">
                <div className="header-title">
                    <h1>SwiftDevBot Web Panel</h1>
                    <span className={`connection-status ${connected ? 'connected' : 'disconnected'}`}>
                        {connected ? '🟢' : '🔴'}
                    </span>
                </div>
                <div className="header-actions">
                    {user && (
                        <div className="user-info">
                            <span className="username">{user.username}</span>
                            {user.role && (
                                <span className={`role-badge role-${user.role}`}>{user.role}</span>
                            )}
                            {isAdmin && <span className="admin-badge">Admin</span>}
                        </div>
                    )}
                    <div className="notifications-container">
                        <button
                            className="btn btn-icon"
                            onClick={() => setShowNotifications(!showNotifications)}
                            title="Notifications"
                        >
                            🔔
                            {unreadCount > 0 && <span className="notification-badge">{unreadCount}</span>}
                        </button>
                        {showNotifications && (
                            <div className="notifications-dropdown">
                                <div className="notifications-header">
                                    <h4>Notifications</h4>
                                    <button onClick={() => setShowNotifications(false)}>×</button>
                                </div>
                                <div className="notifications-list">
                                    {notifications.length > 0 ? (
                                        notifications.map((notif, idx) => (
                                            <div key={idx} className="notification-item">
                                                <p>{notif.data?.message || 'New notification'}</p>
                                                <small>{new Date(notif.timestamp || Date.now()).toLocaleString()}</small>
                                            </div>
                                        ))
                                    ) : (
                                        <p className="no-notifications">No notifications</p>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>
                    <button className="btn btn-secondary" onClick={handleLogout}>
                        Logout
                    </button>
                </div>
            </div>
        </header>
    );
}

export default Header;

