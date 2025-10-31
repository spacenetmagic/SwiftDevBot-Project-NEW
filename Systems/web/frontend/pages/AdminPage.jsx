/**
 * Admin page with user management and statistics.
 */

import { useState, useEffect } from 'react';
import { useUser } from '../main';
import api from '../api/client';
import ProtectedRoute from '../components/ProtectedRoute';

function AdminPage() {
    const { isAdmin } = useUser();
    const [users, setUsers] = useState([]);
    const [stats, setStats] = useState(null);
    const [auditLogs, setAuditLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('users');

    useEffect(() => {
        if (isAdmin) {
            fetchData();
        }
    }, [isAdmin]);

    const fetchData = async () => {
        try {
            setLoading(true);
            const [usersRes, statsRes, logsRes] = await Promise.all([
                api.get('/api/users/').catch(() => ({ data: [] })),
                api.get('/api/admin/stats').catch(() => ({ data: null })),
                api.get('/api/admin/audit-logs').catch(() => ({ data: [] })),
            ]);

            setUsers(usersRes.data || []);
            setStats(statsRes.data);
            setAuditLogs(logsRes.data || []);
        } catch (err) {
            setError(err.message || 'Failed to load admin data');
        } finally {
            setLoading(false);
        }
    };

    if (!isAdmin) {
        return (
            <div className="page">
                <div className="alert alert-error">
                    <p>Access denied. Admin privileges required.</p>
                </div>
            </div>
        );
    }

    if (loading) {
        return (
            <div className="page">
                <div className="loading-container">
                    <div className="spinner"></div>
                    <p>Loading admin data...</p>
                </div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="page">
                <div className="alert alert-error">
                    <p>{error}</p>
                </div>
            </div>
        );
    }

    return (
        <ProtectedRoute requireAdmin={true}>
            <div className="page admin-page">
                <div className="page-header">
                    <h2>Administration</h2>
                </div>

                <div className="admin-tabs">
                    <button
                        className={`tab-btn ${activeTab === 'stats' ? 'active' : ''}`}
                        onClick={() => setActiveTab('stats')}
                    >
                        Statistics
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'users' ? 'active' : ''}`}
                        onClick={() => setActiveTab('users')}
                    >
                        Users
                    </button>
                    <button
                        className={`tab-btn ${activeTab === 'logs' ? 'active' : ''}`}
                        onClick={() => setActiveTab('logs')}
                    >
                        Audit Logs
                    </button>
                </div>

                <div className="admin-content">
                    {activeTab === 'stats' && stats && (
                        <div className="stats-grid">
                            <div className="stat-card">
                                <h4>Total Users</h4>
                                <p className="stat-value">{stats.total_users}</p>
                            </div>
                            <div className="stat-card">
                                <h4>Active Users</h4>
                                <p className="stat-value">{stats.active_users}</p>
                            </div>
                            <div className="stat-card">
                                <h4>Total Modules</h4>
                                <p className="stat-value">{stats.total_modules}</p>
                            </div>
                            <div className="stat-card">
                                <h4>Enabled Modules</h4>
                                <p className="stat-value">{stats.enabled_modules}</p>
                            </div>
                            <div className="stat-card">
                                <h4>Total Commands</h4>
                                <p className="stat-value">{stats.total_commands}</p>
                            </div>
                            <div className="stat-card">
                                <h4>Total Settings</h4>
                                <p className="stat-value">{stats.total_settings}</p>
                            </div>
                        </div>
                    )}

                    {activeTab === 'users' && (
                        <div className="users-table">
                            <table>
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Username</th>
                                        <th>Full Name</th>
                                        <th>Role</th>
                                        <th>Status</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {users.map((user) => (
                                        <tr key={user.telegram_id}>
                                            <td>{user.telegram_id}</td>
                                            <td>{user.username}</td>
                                            <td>{user.full_name || 'N/A'}</td>
                                            <td>
                                                <span className={`role-badge role-${user.role}`}>
                                                    {user.role}
                                                </span>
                                            </td>
                                            <td>
                                                <span className={`status ${user.is_active ? 'active' : 'inactive'}`}>
                                                    {user.is_active ? 'Active' : 'Inactive'}
                                                </span>
                                            </td>
                                            <td>
                                                <button className="btn btn-sm btn-primary">Edit</button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {activeTab === 'logs' && (
                        <div className="logs-list">
                            {auditLogs.length > 0 ? (
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Timestamp</th>
                                            <th>User</th>
                                            <th>Action</th>
                                            <th>Resource</th>
                                            <th>Success</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {auditLogs.map((log) => (
                                            <tr key={log.id}>
                                                <td>{new Date(log.timestamp).toLocaleString()}</td>
                                                <td>{log.user_id}</td>
                                                <td>{log.action}</td>
                                                <td>{log.resource}</td>
                                                <td>
                                                    <span className={`status ${log.success ? 'success' : 'error'}`}>
                                                        {log.success ? 'Yes' : 'No'}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            ) : (
                                <p>No audit logs available</p>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </ProtectedRoute>
    );
}

export default AdminPage;

