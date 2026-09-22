/**
 * Inventory-Management-Tracking-System - Main JavaScript
 * Core utilities and WebSocket connection management
 */

// Global state
const GSIP = window.GSIP || {
    socket: null,
    connected: false,
    config: {}
};
window.GSIP = GSIP;

// Initialize on page load
const initMain = () => {
    initResponsiveSidebar();

    // Keep realtime socket available across all pages for live status/alerts.
    ensureWebSocket();

    updateAlertBadge();
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMain);
} else {
    initMain();
}

// Reconnect when page is restored from the back/forward cache.
window.addEventListener('pageshow', (event) => {
    if (event.persisted) {
        ensureWebSocket();
    }
});

/**
 * Initialize responsive sidebar controls for mobile layouts.
 */
function initResponsiveSidebar() {
    const toggleBtn = document.getElementById('btn-sidebar-toggle');
    const backdrop = document.getElementById('sidebar-backdrop');
    const navLinks = document.querySelectorAll('.nav-menu a');

    if (!toggleBtn || !backdrop) {
        return;
    }

    const setSidebarOpen = (open) => {
        document.body.classList.toggle('sidebar-open', open);
        toggleBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
    };

    toggleBtn.addEventListener('click', () => {
        const isOpen = document.body.classList.contains('sidebar-open');
        setSidebarOpen(!isOpen);
    });

    backdrop.addEventListener('click', () => {
        setSidebarOpen(false);
    });

    navLinks.forEach((link) => {
        link.addEventListener('click', () => {
            if (window.innerWidth <= 768) {
                setSidebarOpen(false);
            }
        });
    });

    window.addEventListener('resize', () => {
        if (window.innerWidth > 768) {
            setSidebarOpen(false);
        }
    });
}

/**
 * Initialize WebSocket connection
 */
function initWebSocket() {
    if (GSIP.socket) {
        return;
    }

    if (typeof io !== 'function') {
        console.warn('Socket.IO client is unavailable; cannot connect.');
        updateConnectionStatus(false);
        return;
    }

    // Connect to SocketIO server
    GSIP.socket = io({
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionAttempts: 5,
        reconnectionDelay: 1000
    });

    // Connection handlers
    GSIP.socket.on('connect', () => {
        console.log('Connected to Inventory-Management-Tracking-System server');
        GSIP.connected = true;
        updateConnectionStatus(true);
    });

    GSIP.socket.on('disconnect', () => {
        console.log('Disconnected from Inventory-Management-Tracking-System server');
        GSIP.connected = false;
        updateConnectionStatus(false);
    });

    GSIP.socket.on('connect_error', (error) => {
        console.error('Connection error:', error);
        updateConnectionStatus(false);
    });

    // Event handlers
    GSIP.socket.on('event', (data) => {
        console.log('Event received:', data);
        handleNewEvent(data);
    });

    GSIP.socket.on('inventory_update', (data) => {
        console.log('Inventory update:', data);
        handleInventoryUpdate(data);
    });

    GSIP.socket.on('alert', (data) => {
        console.log('Alert received:', data);
        handleNewAlert(data);
    });
}

/**
 * Ensure WebSocket connection is initialized.
 */
function ensureWebSocket() {
    if (GSIP.socket) {
        if (GSIP.socket.connected) {
            updateConnectionStatus(true);
            return;
        }

        // Socket exists but is disconnected; let Socket.IO reconnect.
        updateConnectionStatus(false);
        return;
    }

    initWebSocket();
}

/**
 * Update connection status indicator
 */
function updateConnectionStatus(connected) {
    const statusDot = document.getElementById('connection-status');
    const statusText = document.getElementById('status-text');

    if (statusDot && statusText) {
        if (connected) {
            statusDot.classList.remove('disconnected');
            statusDot.classList.add('connected');
            statusText.textContent = 'Connected';
        } else {
            statusDot.classList.remove('connected');
            statusDot.classList.add('disconnected');
            statusText.textContent = 'Disconnected';
        }
    }
}

/**
 * Fetch data from API
 */
async function fetchAPI(endpoint, options = {}) {
    try {
        const response = await fetch(`/api${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`API fetch error (${endpoint}):`, error);
        throw error;
    }
}

/**
 * POST to API
 */
async function postAPI(endpoint, data) {
    return fetchAPI(endpoint, {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

/**
 * Format timestamp for display
 */
function formatTime(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });
}

/**
 * Format date for display
 */
function formatDate(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Get event type icon (emoji fallback)
 */
function getEventIcon(eventType) {
    const icons = {
        'item_removed': '−',
        'item_added': '+',
        'item_misplaced': '⚠',
        'uncertain_state': '?',
        'low_stock': '↓',
        'state_stabilized': '✓'
    };
    return icons[eventType] || '•';
}

/**
 * Get event type label
 */
function getEventLabel(eventType) {
    const labels = {
        'item_removed': 'Item Removed',
        'item_added': 'Item Added',
        'item_misplaced': 'Item Misplaced',
        'uncertain_state': 'Uncertain State',
        'low_stock': 'Low Stock',
        'state_stabilized': 'State Stabilized'
    };
    return labels[eventType] || eventType;
}

/**
 * Get event type icon name (Lucide)
 */
function getEventIconName(eventType) {
    const icons = {
        'item_removed': 'minus-circle',
        'item_added': 'plus-circle',
        'item_misplaced': 'alert-triangle',
        'uncertain_state': 'help-circle',
        'low_stock': 'trending-down',
        'state_stabilized': 'check-circle'
    };
    return icons[eventType] || 'info';
}

/**
 * Handle new event
 */
function handleNewEvent(data) {
    const recentEvents = document.getElementById('recent-events');
    if (recentEvents) {
        const eventHtml = createEventHTML(data);
        recentEvents.insertAdjacentHTML('afterbegin', eventHtml);

        // Remove empty state
        const emptyState = recentEvents.querySelector('.text-secondary');
        if (emptyState) emptyState.remove();

        // Limit items
        const events = recentEvents.querySelectorAll('.event-item');
        if (events.length > 8) {
            events[events.length - 1].remove();
        }

        // Refresh icons
        if (window.lucide) lucide.createIcons();
    }
}

/**
 * Create event HTML
 */
function createEventHTML(event) {
    return `
        <div class="event-item" style="display:flex; align-items:center; gap:0.75rem; padding:0.75rem; border-bottom:1px solid rgba(255,255,255,0.05);">
            <div style="color:var(--accent);">
                <i data-lucide="${getEventIconName(event.event_type)}"></i>
            </div>
            <div style="flex:1;">
                <div style="font-weight:500; font-size:0.875rem;">
                    ${event.event_type.replace('_', ' ').toUpperCase()} 
                    ${event.item_class ? `- ${event.item_class}` : ''}
                </div>
                <div style="font-size:0.75rem; color:var(--text-muted);">${formatTime(event.timestamp)}</div>
            </div>
        </div>
    `;
}

/**
 * Handle inventory update from WebSocket
 */
function handleInventoryUpdate(data) {
    // Trigger refresh if on inventory page
    if (typeof loadInventory === 'function') {
        loadInventory();
    }
}

/**
 * Handle new alert from WebSocket
 */
function handleNewAlert(data) {
    updateAlertBadge();

    // Show notification toast
    showToast(`Alert: ${data.title}`, data.level);
}

/**
 * Update alert badge in navigation
 */
async function updateAlertBadge() {
    try {
        const data = await fetchAPI('/alerts');
        const badge = document.getElementById('alert-badge');

        if (badge) {
            const activeCount = data.counts?.active || 0;
            badge.textContent = activeCount;

            if (activeCount > 0) {
                badge.classList.remove('hidden');
            } else {
                badge.classList.add('hidden');
            }
        }
    } catch (error) {
        console.error('Error updating alert badge:', error);
    }
}

/**
 * Show toast notification
 */
function showToast(message, type = 'info') {
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;

    // Style toast
    Object.assign(toast.style, {
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        padding: '1rem 1.5rem',
        background: type === 'warning' ? '#f59e0b' :
            type === 'critical' ? '#ef4444' : '#3b82f6',
        color: 'white',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        zIndex: '9999',
        animation: 'slideIn 0.3s ease'
    });

    document.body.appendChild(toast);

    // Remove after 3 seconds
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Utility to show/hide elements
function show(element) {
    if (element) element.classList.remove('hidden');
}

function hide(element) {
    if (element) element.classList.add('hidden');
}
