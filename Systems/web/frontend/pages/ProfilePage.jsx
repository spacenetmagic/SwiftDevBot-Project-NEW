/**
 * Profile page showing user information.
 */

import { useState, useEffect } from 'react';
import { useUser } from '../main';
import api from '../api/client';

function ProfilePage() {
    const { user } = useUser();
    const [profile, setProfile] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchProfile = async () => {
            try {
                const response = await api.get('/api/users/me');
                setProfile(response.data);
            } catch (err) {
                setError(err.message || 'Failed to load profile');
            } finally {
                setLoading(false);
            }
        };

        fetchProfile();
    }, []);

    if (loading) {
        return (
            <div className="page">
                <div className="loading-container">
                    <div className="spinner"></div>
                    <p>Loading profile...</p>
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
        <div className="page profile-page">
            <div className="page-header">
                <h2>Profile</h2>
            </div>

            <div className="profile-content">
                <div className="profile-card">
                    <div className="profile-header">
                        <h3>User Information</h3>
                    </div>
                    <div className="profile-details">
                        <div className="detail-item">
                            <label>Telegram ID:</label>
                            <span>{profile?.telegram_id}</span>
                        </div>
                        <div className="detail-item">
                            <label>Username:</label>
                            <span>{profile?.username || 'N/A'}</span>
                        </div>
                        <div className="detail-item">
                            <label>Full Name:</label>
                            <span>{profile?.full_name || 'N/A'}</span>
                        </div>
                        <div className="detail-item">
                            <label>Role:</label>
                            <span className={`role-badge role-${profile?.role}`}>
                                {profile?.role || 'user'}
                            </span>
                        </div>
                        <div className="detail-item">
                            <label>Status:</label>
                            <span className={`status ${profile?.is_active ? 'active' : 'inactive'}`}>
                                {profile?.is_active ? 'Active' : 'Inactive'}
                            </span>
                        </div>
                        {profile?.created_at && (
                            <div className="detail-item">
                                <label>Created:</label>
                                <span>{new Date(profile.created_at).toLocaleDateString()}</span>
                            </div>
                        )}
                        {profile?.updated_at && (
                            <div className="detail-item">
                                <label>Last Updated:</label>
                                <span>{new Date(profile.updated_at).toLocaleDateString()}</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

export default ProfilePage;

