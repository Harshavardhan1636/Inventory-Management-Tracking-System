/**
 * Inventory-Management-Tracking-System - Events JavaScript
 * Handles events timeline page functionality
 */

// State
let allEvents = [];

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadEvents();

    document.getElementById('btn-refresh').addEventListener('click', loadEvents);
    document.getElementById('event-filter').addEventListener('change', filterEvents);
});

/**
 * Load events data
 */
async function loadEvents() {
    try {
        const data = await fetchAPI('/events?limit=100');
        allEvents = data.events || [];

        // Update stats
        updateEventStats();

        // Render timeline using the active filter selection.
        renderFilteredTimeline();

    } catch (error) {
        console.error('Error loading events:', error);
        showToast('Error loading events', 'critical');
    }
}

/**
 * Update event statistics
 */
function updateEventStats() {
    document.getElementById('total-events').textContent = allEvents.length;

    const counts = {
        item_added: 0,
        item_removed: 0,
        item_misplaced: 0
    };

    allEvents.forEach(event => {
        if (counts.hasOwnProperty(event.event_type)) {
            counts[event.event_type]++;
        }
    });

    document.getElementById('additions-count').textContent = counts.item_added;
    document.getElementById('removals-count').textContent = counts.item_removed;
    document.getElementById('misplaced-count').textContent = counts.item_misplaced;
}

/**
 * Render events timeline
 */
function renderTimeline(events) {
    const container = document.getElementById('events-timeline');
    const emptyState = document.getElementById('empty-state');

    if (!events || events.length === 0) {
        container.innerHTML = '';
        show(emptyState);
        return;
    }

    hide(emptyState);

    container.innerHTML = events.map(event => {
        const metadata = parseMetadata(event.metadata);
        const metadataReason = metadata && typeof metadata === 'object' ? metadata.reason : null;

        return `
            <div class="card" style="margin-bottom: 1rem; padding: 1rem;">
                <div style="display:flex; gap:1rem; align-items: flex-start;">
                    <div style="color:var(--accent); padding-top:4px;">
                        <i data-lucide="${getEventIconName(event.event_type)}"></i>
                    </div>
                    <div style="flex:1;">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.25rem;">
                            <h4 style="font-weight:600; font-size:1rem;">
                                ${event.event_type.replace('_', ' ').toUpperCase()}
                            </h4>
                            <span style="font-size:0.75rem; color:var(--text-muted);">${formatDate(event.timestamp)}</span>
                        </div>
                        <p style="color:var(--text-secondary); margin-bottom:0.5rem;">
                            ${event.item_class ? `<strong>${event.item_class}</strong>` : ''}
                            ${event.slot_id ? `at ${event.slot_id}` : ''}
                        </p>
                        <div style="display:flex; gap:0.5rem;">
                            <span class="badge" style="background:rgba(255,255,255,0.05); color:var(--text-muted); font-weight:normal;">
                                Confidence: ${Math.round(event.confidence * 100)}%
                            </span>
                            ${metadataReason ? `<span class="badge" style="background:rgba(255,255,255,0.05); color:var(--text-muted); font-weight:normal;">Reason: ${metadataReason}</span>` : ''}
                        </div>
                    </div>
                </div>
            </div>
        `;
    }).join('');

    if (window.lucide) lucide.createIcons();
}

function parseMetadata(value) {
    if (!value) {
        return {};
    }

    if (typeof value !== 'string') {
        return value;
    }

    try {
        return JSON.parse(value);
    } catch (error) {
        console.warn('Skipping malformed event metadata payload:', error);
        return {};
    }
}

/**
 * Filter events by type
 */
function filterEvents(event) {
    renderFilteredTimeline(event.target.value);
}

function renderFilteredTimeline(filterValue = null) {
    const selectedFilter = filterValue || document.getElementById('event-filter')?.value || 'all';

    if (selectedFilter === 'all') {
        renderTimeline(allEvents);
        return;
    }

    const filtered = allEvents.filter(e => e.event_type === selectedFilter);
    renderTimeline(filtered);
}
