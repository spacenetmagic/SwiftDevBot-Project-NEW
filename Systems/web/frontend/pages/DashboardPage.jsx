/**
 * Dashboard page with overview and navigation.
 */

import { useUser } from '../main';
import { Link } from 'react-router-dom';

function DashboardPage() {
    const { user, isAdmin } = useUser();

    return (
        <div className="page dashboard-page">
            <div className="page-header">
                <h2>Dashboard</h2>
                <p>Welcome back, {user?.username}!</p>
            </div>

            <div className="dashboard-content">
                <div className="dashboard-grid">
                    <div className="dashboard-card">
                        <h3>Profile</h3>
                        <p>View and manage your profile</p>
                        <Link to="/profile" className="btn btn-primary">
                            Go to Profile
                        </Link>
                    </div>

                    <div className="dashboard-card">
                        <h3>Modules</h3>
                        <p>Browse and manage bot modules</p>
                        <Link to="/modules" className="btn btn-primary">
                            View Modules
                        </Link>
                    </div>

                    <div className="dashboard-card">
                        <h3>Settings</h3>
                        <p>Configure your preferences</p>
                        <Link to="/settings" className="btn btn-primary">
                            Open Settings
                        </Link>
                    </div>

                    {isAdmin && (
                        <div className="dashboard-card">
                            <h3>Administration</h3>
                            <p>Manage users and system settings</p>
                            <Link to="/admin" className="btn btn-primary">
                                Admin Panel
                            </Link>
                        </div>
                    )}
                </div>

                <div className="quick-info">
                    <div className="info-card">
                        <h4>Your Role</h4>
                        <p className="role-display">{user?.role || 'user'}</p>
                    </div>
                    <div className="info-card">
                        <h4>Status</h4>
                        <p className={`status ${user?.is_active ? 'active' : 'inactive'}`}>
                            {user?.is_active ? 'Active' : 'Inactive'}
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default DashboardPage;

