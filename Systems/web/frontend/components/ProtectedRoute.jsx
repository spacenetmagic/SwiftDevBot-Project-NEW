/**
 * Protected route component - requires authentication.
 */

import { Navigate } from 'react-router-dom';
import { useUser } from '../main';

function ProtectedRoute({ children, requireAdmin = false, requireSuperAdmin = false }) {
    const { user, loading, isAdmin, isSuperAdmin } = useUser();

    if (loading) {
        return (
            <div className="loading-container">
                <div className="spinner"></div>
                <p>Loading...</p>
            </div>
        );
    }

    if (!user) {
        return <Navigate to="/login" replace />;
    }

    if (requireSuperAdmin && !isSuperAdmin) {
        return <Navigate to="/dashboard" replace />;
    }

    if (requireAdmin && !isAdmin) {
        return <Navigate to="/dashboard" replace />;
    }

    return children;
}

export default ProtectedRoute;

