/**
 * Settings page for user preferences.
 */

import { useState, useEffect } from 'react';
import { STORAGE_KEYS, DEFAULT_SETTINGS } from '../config';

function SettingsPage() {
    const [settings, setSettings] = useState(DEFAULT_SETTINGS);
    const [saved, setSaved] = useState(false);

    useEffect(() => {
        // Load settings from localStorage
        const theme = localStorage.getItem(STORAGE_KEYS.THEME) || DEFAULT_SETTINGS.theme;
        const language = localStorage.getItem(STORAGE_KEYS.LANGUAGE) || DEFAULT_SETTINGS.language;
        const notifications = localStorage.getItem('notifications') !== 'false';

        setSettings({ theme, language, notifications });

        // Apply theme
        document.documentElement.setAttribute('data-theme', theme);
    }, []);

    const handleSettingChange = (key, value) => {
        const newSettings = { ...settings, [key]: value };
        setSettings(newSettings);
        localStorage.setItem(key === 'theme' ? STORAGE_KEYS.THEME : key === 'language' ? STORAGE_KEYS.LANGUAGE : key, value);
        
        // Apply theme immediately
        if (key === 'theme') {
            document.documentElement.setAttribute('data-theme', value);
        }

        setSaved(true);
        setTimeout(() => setSaved(false), 2000);
    };

    return (
        <div className="page settings-page">
            <div className="page-header">
                <h2>Settings</h2>
                {saved && <span className="save-indicator">Settings saved!</span>}
            </div>

            <div className="settings-content">
                <div className="settings-section">
                    <h3>Appearance</h3>
                    <div className="setting-item">
                        <label>Theme</label>
                        <select
                            value={settings.theme}
                            onChange={(e) => handleSettingChange('theme', e.target.value)}
                        >
                            <option value="light">Light</option>
                            <option value="dark">Dark</option>
                        </select>
                    </div>
                </div>

                <div className="settings-section">
                    <h3>Language</h3>
                    <div className="setting-item">
                        <label>Interface Language</label>
                        <select
                            value={settings.language}
                            onChange={(e) => handleSettingChange('language', e.target.value)}
                        >
                            <option value="en">English</option>
                            <option value="ru">Русский</option>
                        </select>
                    </div>
                </div>

                <div className="settings-section">
                    <h3>Notifications</h3>
                    <div className="setting-item">
                        <label>
                            <input
                                type="checkbox"
                                checked={settings.notifications}
                                onChange={(e) => handleSettingChange('notifications', e.target.checked)}
                            />
                            Enable notifications
                        </label>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default SettingsPage;

