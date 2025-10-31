/**
 * Login page with Telegram Widget authentication.
 */

import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useUser } from '../main';
import api from '../api/client';
import { BOT_USERNAME } from '../config';

function LoginPage() {
    const navigate = useNavigate();
    const { login } = useUser();
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        // Initialize Telegram Widget callback
        window.onTelegramAuth = async (user) => {
            setLoading(true);
            setError(null);

            try {
                // Send Telegram auth data to backend
                const response = await api.post('/api/auth/telegram', {
                    id: user.id,
                    first_name: user.first_name,
                    last_name: user.last_name,
                    username: user.username,
                    photo_url: user.photo_url,
                    auth_date: user.auth_date,
                    hash: user.hash,
                });

                const { access_token, refresh_token, user: userData } = response.data;
                login(userData, access_token, refresh_token);
                navigate('/dashboard');
            } catch (err) {
                setError(err.message || 'Authentication failed');
            } finally {
                setLoading(false);
            }
        };
    }, [login, navigate]);

    return (
        <div className="login-page">
            <div className="login-container">
                <div className="login-header">
                    <h1>SwiftDevBot Web Panel</h1>
                    <p>Sign in with Telegram to continue</p>
                </div>

                {error && (
                    <div className="alert alert-error">
                        <p>{error}</p>
                    </div>
                )}

                {loading ? (
                    <div className="loading-container">
                        <div className="spinner"></div>
                        <p>Authenticating...</p>
                    </div>
                ) : (
                    <div className="telegram-widget-container">
                        <script
                            async
                            src="https://telegram.org/js/telegram-widget.js?22"
                            data-telegram-login={BOT_USERNAME}
                            data-size="large"
                            data-request-access="write"
                            data-auth-url="/api/auth/telegram"
                            data-onauth="onTelegramAuth(user)"
                        ></script>
                    </div>
                )}
            </div>
        </div>
    );
}

export default LoginPage;

