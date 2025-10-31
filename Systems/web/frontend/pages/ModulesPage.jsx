/**
 * Modules page showing available modules.
 */

import { useState, useEffect } from 'react';
import api from '../api/client';

function ModulesPage() {
    const [modules, setModules] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedModule, setSelectedModule] = useState(null);
    const [viewMode, setViewMode] = useState('grid'); // 'grid' or 'list'

    useEffect(() => {
        const fetchModules = async () => {
            try {
                const response = await api.get('/api/modules/');
                setModules(response.data);
            } catch (err) {
                setError(err.message || 'Failed to load modules');
            } finally {
                setLoading(false);
            }
        };

        fetchModules();
    }, []);

    const handleToggleModule = async (moduleName, enabled) => {
        try {
            if (enabled) {
                await api.post(`/api/modules/${moduleName}/disable`);
            } else {
                await api.post(`/api/modules/${moduleName}/enable`);
            }
            // Refresh modules list
            const response = await api.get('/api/modules/');
            setModules(response.data);
            if (selectedModule?.name === moduleName) {
                setSelectedModule(response.data.find(m => m.name === moduleName));
            }
        } catch (err) {
            alert(err.message || 'Failed to toggle module');
        }
    };

    if (loading) {
        return (
            <div className="page">
                <div className="loading-container">
                    <div className="spinner"></div>
                    <p>Loading modules...</p>
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
        <div className="page modules-page">
            <div className="page-header">
                <h2>Modules</h2>
                <div className="page-actions">
                    <button
                        className={`btn btn-sm ${viewMode === 'grid' ? 'btn-active' : 'btn-secondary'}`}
                        onClick={() => setViewMode('grid')}
                    >
                        Grid
                    </button>
                    <button
                        className={`btn btn-sm ${viewMode === 'list' ? 'btn-active' : 'btn-secondary'}`}
                        onClick={() => setViewMode('list')}
                    >
                        List
                    </button>
                </div>
            </div>

            <div className={`modules-${viewMode}`}>
                {modules.map((module) => (
                    <div key={module.name} className="module-card">
                        <div className="module-header">
                            <h3>{module.display_name || module.name}</h3>
                            <span className={`module-status ${module.enabled ? 'enabled' : 'disabled'}`}>
                                {module.enabled ? 'Enabled' : 'Disabled'}
                            </span>
                        </div>
                        <div className="module-body">
                            <p className="module-description">{module.description || 'No description'}</p>
                            <div className="module-meta">
                                <span>Version: {module.version}</span>
                                {module.author && <span>Author: {module.author}</span>}
                            </div>
                        </div>
                        <div className="module-actions">
                            <button
                                className={`btn btn-sm ${module.enabled ? 'btn-warning' : 'btn-success'}`}
                                onClick={() => handleToggleModule(module.name, module.enabled)}
                            >
                                {module.enabled ? 'Disable' : 'Enable'}
                            </button>
                            <button
                                className="btn btn-sm btn-primary"
                                onClick={() => setSelectedModule(module)}
                            >
                                Details
                            </button>
                            <a
                                href={`https://t.me/${module.name}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="btn btn-sm btn-secondary"
                            >
                                Open in Bot
                            </a>
                        </div>
                    </div>
                ))}
            </div>

            {selectedModule && (
                <div className="modal-overlay" onClick={() => setSelectedModule(null)}>
                    <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                        <div className="modal-header">
                            <h3>{selectedModule.display_name || selectedModule.name}</h3>
                            <button className="modal-close" onClick={() => setSelectedModule(null)}>
                                ×
                            </button>
                        </div>
                        <div className="modal-body">
                            <div className="module-details">
                                <div className="detail-section">
                                    <h4>Description</h4>
                                    <p>{selectedModule.description || 'No description available'}</p>
                                </div>
                                <div className="detail-section">
                                    <h4>Version</h4>
                                    <p>{selectedModule.version}</p>
                                </div>
                                {selectedModule.author && (
                                    <div className="detail-section">
                                        <h4>Author</h4>
                                        <p>{selectedModule.author}</p>
                                    </div>
                                )}
                                {selectedModule.dependencies && selectedModule.dependencies.length > 0 && (
                                    <div className="detail-section">
                                        <h4>Dependencies</h4>
                                        <ul>
                                            {selectedModule.dependencies.map((dep) => (
                                                <li key={dep}>{dep}</li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                                {selectedModule.commands && selectedModule.commands.length > 0 && (
                                    <div className="detail-section">
                                        <h4>Commands</h4>
                                        <ul>
                                            {selectedModule.commands.map((cmd, idx) => (
                                                <li key={idx}>
                                                    {cmd.name} - {cmd.description || 'No description'}
                                                </li>
                                            ))}
                                        </ul>
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default ModulesPage;

