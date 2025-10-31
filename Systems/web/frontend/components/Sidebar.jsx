/**
 * Sidebar component with navigation menu.
 */

import { Link, useLocation } from 'react-router-dom';
import { useUser } from '../main';

function Sidebar() {
    const location = useLocation();
    const { isAdmin } = useUser();

    const menuItems = [
        { path: '/dashboard', label: 'Dashboard', icon: '📊' },
        { path: '/profile', label: 'Profile', icon: '👤' },
        { path: '/modules', label: 'Modules', icon: '📦' },
        { path: '/settings', label: 'Settings', icon: '⚙️' },
    ];

    if (isAdmin) {
        menuItems.push({ path: '/admin', label: 'Administration', icon: '🛡️' });
    }

    return (
        <aside className="sidebar">
            <nav className="sidebar-nav">
                <ul className="nav-list">
                    {menuItems.map((item) => (
                        <li key={item.path}>
                            <Link
                                to={item.path}
                                className={`nav-link ${location.pathname === item.path ? 'active' : ''}`}
                            >
                                <span className="nav-icon">{item.icon}</span>
                                <span className="nav-label">{item.label}</span>
                            </Link>
                        </li>
                    ))}
                </ul>
            </nav>
        </aside>
    );
}

export default Sidebar;

