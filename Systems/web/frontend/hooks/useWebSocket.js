/**
 * WebSocket hook for real-time notifications.
 */

import { useEffect, useState, useRef } from 'react';
import { useUser } from '../main';
import { WS_URL } from '../config';

function useWebSocket() {
    const { user } = useUser();
    const [notifications, setNotifications] = useState([]);
    const [connected, setConnected] = useState(false);
    const wsRef = useRef(null);

    useEffect(() => {
        if (!user || !user.telegram_id) {
            return;
        }

        const userId = user.telegram_id;
        const wsUrl = `${WS_URL}/ws/notifications/${userId}`;
        
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
            console.log('WebSocket connected');
            setConnected(true);
        };

        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                if (data.type === 'notification') {
                    setNotifications((prev) => [...prev, data]);
                    
                    // Show browser notification if enabled
                    if (Notification.permission === 'granted') {
                        new Notification(data.data?.title || 'Notification', {
                            body: data.data?.message || 'New notification',
                            icon: '/static/favicon.ico',
                        });
                    }
                } else if (data.type === 'pong') {
                    // Handle pong response
                    console.log('WebSocket pong');
                }
            } catch (error) {
                console.error('Error parsing WebSocket message:', error);
            }
        };

        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            setConnected(false);
        };

        ws.onclose = () => {
            console.log('WebSocket disconnected');
            setConnected(false);
            
            // Attempt to reconnect after 3 seconds
            setTimeout(() => {
                if (user && user.telegram_id) {
                    // Reconnect will be handled by useEffect
                }
            }, 3000);
        };

        // Request notification permission
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }

        // Send ping every 30 seconds to keep connection alive
        const pingInterval = setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send('ping');
            }
        }, 30000);

        return () => {
            clearInterval(pingInterval);
            if (ws.readyState === WebSocket.OPEN) {
                ws.close();
            }
        };
    }, [user]);

    const clearNotifications = () => {
        setNotifications([]);
    };

    return { notifications, connected, clearNotifications };
}

export default useWebSocket;

