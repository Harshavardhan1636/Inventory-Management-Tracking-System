/**
 * Inventory-Management-Tracking-System - Live Feed JavaScript
 * Handles video streaming and shelf state visualization
 */

// State
let streaming = false;
let activeMode = null;
let statsInterval = null;
let frameCount = 0;
let fpsTrackingInterval = null;
let lastFrameTime = 0;
let streamActionPending = false;
let attachmentActionPending = false;
let uploadedMedia = null;
let statusSyncInterval = null;
const assignmentBusySlots = new Set();
const defaultShelfItems = ['apple', 'book', 'bottle', 'box', 'coffee', 'cup', 'mug'];

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initLiveFeed();
    loadCurrentMediaAttachment();
    loadShelfState();
    loadStats();
    loadRecentEvents();

    // Start stats refresh every 5 seconds
    statsInterval = setInterval(() => {
        loadStats();
        loadShelfState();
        loadRecentEvents();
    }, 5000);
});

/**
 * Initialize live feed controls
 */
function initLiveFeed() {
    const startBtn = document.getElementById('btn-start-stream');
    const stopBtn = document.getElementById('btn-stop-stream');
    const uploadAttachmentBtn = document.getElementById('btn-upload-attachment');
    const startAttachmentBtn = document.getElementById('btn-start-attachment');
    const stopAttachmentBtn = document.getElementById('btn-stop-attachment');
    const attachmentFileInput = document.getElementById('attachment-file-input');
    const refreshStateBtn = document.getElementById('btn-refresh-state');

    if (startBtn) {
        startBtn.addEventListener('click', startStream);
    }

    if (stopBtn) {
        stopBtn.addEventListener('click', stopStream);
    }

    if (uploadAttachmentBtn && attachmentFileInput) {
        uploadAttachmentBtn.addEventListener('click', () => {
            if (streaming) {
                showToast('Stop the active session before attaching a demo sample.', 'warning');
                return;
            }
            attachmentFileInput.click();
        });
    }

    if (attachmentFileInput) {
        attachmentFileInput.addEventListener('change', async (event) => {
            const input = event.currentTarget;
            const file = input.files && input.files.length ? input.files[0] : null;
            if (file) {
                await uploadAttachment(file);
            }
            input.value = '';
        });
    }

    if (startAttachmentBtn) {
        startAttachmentBtn.addEventListener('click', startAttachmentStream);
    }

    if (stopAttachmentBtn) {
        stopAttachmentBtn.addEventListener('click', stopAttachmentStream);
    }

    if (refreshStateBtn) {
        refreshStateBtn.addEventListener('click', loadShelfState);
    }

    // Frame handler - setup WebSocket listeners
    if (GSIP.socket) {
        GSIP.socket.on('frame', (data) => {
            if (data && data.image) {
                updateVideoFeed(data.image);
                frameCount++;
            }
        });

        GSIP.socket.on('stream_status', (data) => {
            console.log('Stream status:', data.status);
            handleStreamStatus(data);
        });

        GSIP.socket.on('status', (data) => {
            streamActionPending = false;
            attachmentActionPending = false;

            if (data && data.streaming) {
                streaming = true;
                activeMode = data.stream_mode || data.camera?.input_mode || 'camera';
                startFpsTracking();
                hide(document.getElementById('video-placeholder'));
            } else {
                streaming = false;
                activeMode = null;
                stopFpsTracking();
                show(document.getElementById('video-placeholder'));
            }
            updateStreamButtons();
        });

        GSIP.socket.on('connect', () => {
            requestLiveStatusSync();
            if (!statusSyncInterval) {
                statusSyncInterval = setInterval(requestLiveStatusSync, 2000);
            }
        });

        GSIP.socket.on('disconnect', () => {
            streamActionPending = false;
            attachmentActionPending = false;

            if (statusSyncInterval) {
                clearInterval(statusSyncInterval);
                statusSyncInterval = null;
            }

            updateStreamButtons();
        });

        requestLiveStatusSync();
        if (!statusSyncInterval) {
            statusSyncInterval = setInterval(requestLiveStatusSync, 2000);
        }
    }

    updateAttachmentStatusBadge();
    updateStreamButtons();
}

function requestLiveStatusSync() {
    if (GSIP.socket && GSIP.connected) {
        GSIP.socket.emit('get_status');
    }
}

function updateAttachmentStatusBadge() {
    const statusBadge = document.getElementById('attachment-status');
    if (!statusBadge) {
        return;
    }

    if (!uploadedMedia) {
        statusBadge.textContent = 'Demo: none';
        statusBadge.title = 'No demo sample selected';
        return;
    }

    const mediaName = uploadedMedia.original_name || uploadedMedia.stored_name || 'attachment';
    const mediaType = uploadedMedia.type || 'media';
    statusBadge.textContent = `Demo: ${mediaName}`;
    statusBadge.title = `${mediaType.toUpperCase()} demo ready: ${mediaName}`;
}

function updateStreamButtons() {
    const startBtn = document.getElementById('btn-start-stream');
    const stopBtn = document.getElementById('btn-stop-stream');
    const uploadAttachmentBtn = document.getElementById('btn-upload-attachment');
    const startAttachmentBtn = document.getElementById('btn-start-attachment');
    const stopAttachmentBtn = document.getElementById('btn-stop-attachment');

    const cameraActive = streaming && activeMode === 'camera';
    const attachmentActive = streaming && activeMode === 'attachment';
    const anyActive = cameraActive || attachmentActive;

    if (startBtn) {
        startBtn.disabled = streamActionPending;
        startBtn.innerHTML = streamActionPending
            ? '<i data-lucide="loader" class="spin"></i> Starting...'
            : '<i data-lucide="play"></i> Start Stream';
        if (cameraActive) {
            hide(startBtn);
        } else {
            show(startBtn);
        }
    }

    if (stopBtn) {
        stopBtn.disabled = streamActionPending;
        stopBtn.innerHTML = streamActionPending
            ? '<i data-lucide="loader" class="spin"></i> Stopping...'
            : '<i data-lucide="square"></i> Stop Stream';
        if (cameraActive) {
            show(stopBtn);
        } else {
            hide(stopBtn);
        }
    }

    if (uploadAttachmentBtn) {
        uploadAttachmentBtn.disabled = anyActive || attachmentActionPending;
    }

    if (startAttachmentBtn) {
        startAttachmentBtn.disabled = attachmentActionPending || !uploadedMedia;
        startAttachmentBtn.innerHTML = attachmentActionPending
            ? '<i data-lucide="loader" class="spin"></i> Starting...'
            : '<i data-lucide="play-circle"></i> Start Demo';
        if (attachmentActive) {
            hide(startAttachmentBtn);
        } else {
            show(startAttachmentBtn);
        }
    }

    if (stopAttachmentBtn) {
        stopAttachmentBtn.disabled = attachmentActionPending;
        stopAttachmentBtn.innerHTML = attachmentActionPending
            ? '<i data-lucide="loader" class="spin"></i> Stopping...'
            : '<i data-lucide="stop-circle"></i> Stop Demo';
        if (attachmentActive) {
            show(stopAttachmentBtn);
        } else {
            hide(stopAttachmentBtn);
        }
    }

    if (window.lucide) {
        lucide.createIcons();
    }
}

/**
 * Handle stream status updates from server
 */
function handleStreamStatus(data) {
    const fpsDisplay = document.getElementById('fps-display');
    const placeholder = document.getElementById('video-placeholder');
    const mode = data.mode || activeMode || 'camera';

    if (data.status === 'started') {
        streamActionPending = false;
        attachmentActionPending = false;
        streaming = true;
        activeMode = mode;
        frameCount = 0;
        hide(placeholder);
        updateStreamButtons();
        startFpsTracking();
        showToast(
            mode === 'attachment'
                ? `Demo session started (${data.media_name || 'sample'})`
                : 'Camera stream started',
            'info'
        );
    } else if (data.status === 'stopped') {
        streamActionPending = false;
        attachmentActionPending = false;
        streaming = false;
        activeMode = null;
        show(placeholder);
        updateStreamButtons();

        const videoFeed = document.getElementById('video-feed');
        if (videoFeed) {
            videoFeed.src = 'data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///yH5BAEAAAAALAAAAAABAAEAAAIBRAA7';
        }

        stopFpsTracking();
        showToast(
            mode === 'attachment' ? 'Demo session stopped' : 'Camera stream stopped',
            'info'
        );
        if (fpsDisplay) fpsDisplay.textContent = 'FPS: --';
    } else if (data.status === 'warning') {
        showToast(data.message || 'Camera warning', 'warning');
    } else if (data.status === 'error') {
        streamActionPending = false;
        attachmentActionPending = false;
        if (!streaming || !data.mode || data.mode === activeMode) {
            streaming = false;
            activeMode = null;
            show(placeholder);
            stopFpsTracking();
            if (fpsDisplay) fpsDisplay.textContent = 'FPS: --';
        }
        updateStreamButtons();
        showToast(data.message || 'Stream error', 'warning');
    } else if (data.status === 'already_running') {
        streamActionPending = false;
        attachmentActionPending = false;
        streaming = true;
        activeMode = mode;
        hide(placeholder);
        updateStreamButtons();
        startFpsTracking();
        showToast(
            mode === 'attachment'
                ? 'Demo session is already running'
                : 'Camera stream is already running',
            'info'
        );
    }
}

/**
 * Start video stream
 */
function startStream() {
    if (streamActionPending || attachmentActionPending) {
        return;
    }

    if (streaming && activeMode === 'camera') {
        return;
    }

    if (!GSIP.connected) {
        showToast('Not connected to server', 'warning');
        return;
    }

    streamActionPending = true;
    updateStreamButtons();

    // Request stream from server
    GSIP.socket.emit('start_stream');

    setTimeout(() => {
        if (streamActionPending) {
            streamActionPending = false;
            updateStreamButtons();
            requestLiveStatusSync();
            showToast('Start request timed out, please retry', 'warning');
        }
    }, 4000);
}

/**
 * Stop video stream
 */
function stopStream() {
    if (streamActionPending || attachmentActionPending || !streaming || activeMode !== 'camera') {
        if (streaming && activeMode === 'attachment') {
            showToast('Demo session is active. Use Stop Demo.', 'warning');
        }
        return;
    }

    streamActionPending = true;
    updateStreamButtons();

    // Stop stream on server
    GSIP.socket.emit('stop_stream');

    setTimeout(() => {
        if (streamActionPending) {
            streamActionPending = false;
            updateStreamButtons();
            requestLiveStatusSync();
            showToast('Stop request timed out, retrying connection state...', 'warning');
        }
    }, 4000);
}

async function loadCurrentMediaAttachment() {
    try {
        const data = await fetchAPI('/media/current');
        uploadedMedia = data.media || null;
    } catch (error) {
        console.error('Error loading current media attachment:', error);
        uploadedMedia = null;
    } finally {
        updateAttachmentStatusBadge();
        updateStreamButtons();
    }
}

async function uploadAttachment(file) {
    const uploadBtn = document.getElementById('btn-upload-attachment');

    if (!file) {
        return;
    }

    if (uploadBtn) {
        uploadBtn.disabled = true;
        uploadBtn.innerHTML = '<i data-lucide="loader" class="spin"></i> Uploading...';
    }
    if (window.lucide) lucide.createIcons();

    try {
        const formData = new FormData();
        formData.append('media', file);

        const response = await fetch('/api/media/upload', {
            method: 'POST',
            body: formData
        });

        const payload = await response.json();
        if (!response.ok) {
            throw new Error(payload.error || `Upload failed (${response.status})`);
        }

        uploadedMedia = payload.media || null;
        updateAttachmentStatusBadge();
        updateStreamButtons();

        const mediaName = uploadedMedia?.original_name || file.name;
        showToast(`Demo sample ready: ${mediaName}`, 'info');
    } catch (error) {
        console.error('Error uploading attachment media:', error);
        showToast(error.message || 'Failed to upload demo sample', 'warning');
    } finally {
        if (uploadBtn) {
            uploadBtn.disabled = false;
            uploadBtn.innerHTML = '<i data-lucide="paperclip"></i> Attach Demo Sample';
        }
        if (window.lucide) lucide.createIcons();
    }
}

function startAttachmentStream() {
    if (attachmentActionPending || streamActionPending) {
        return;
    }

    if (streaming && activeMode === 'attachment') {
        return;
    }

    if (!GSIP.connected) {
        showToast('Not connected to server', 'warning');
        return;
    }

    if (!uploadedMedia || !uploadedMedia.id) {
        showToast('Attach a demo sample first.', 'warning');
        return;
    }

    attachmentActionPending = true;
    updateStreamButtons();

    GSIP.socket.emit('start_attachment_stream', {
        media_id: uploadedMedia.id,
        loop: true
    });

    setTimeout(() => {
        if (attachmentActionPending) {
            attachmentActionPending = false;
            updateStreamButtons();
            requestLiveStatusSync();
            showToast('Demo start request timed out, please retry', 'warning');
        }
    }, 5000);
}

function stopAttachmentStream() {
    if (attachmentActionPending || streamActionPending || !streaming || activeMode !== 'attachment') {
        if (streaming && activeMode === 'camera') {
            showToast('Camera stream is active. Use Stop Stream.', 'warning');
        }
        return;
    }

    attachmentActionPending = true;
    updateStreamButtons();

    GSIP.socket.emit('stop_attachment_stream');

    setTimeout(() => {
        if (attachmentActionPending) {
            attachmentActionPending = false;
            updateStreamButtons();
            requestLiveStatusSync();
            showToast('Demo stop request timed out, please retry', 'warning');
        }
    }, 5000);
}

/**
 * Start FPS tracking
 */
function startFpsTracking() {
    frameCount = 0;
    lastFrameTime = Date.now();

    fpsTrackingInterval = setInterval(() => {
        const now = Date.now();
        const elapsed = (now - lastFrameTime) / 1000;
        const fps = Math.round(frameCount / elapsed);

        const fpsDisplay = document.getElementById('fps-display');
        if (fpsDisplay && streaming) {
            fpsDisplay.textContent = `FPS: ${fps}`;
        }

        // Reset for next calculation
        frameCount = 0;
        lastFrameTime = now;
    }, 1000);
}

/**
 * Stop FPS tracking
 */
function stopFpsTracking() {
    if (fpsTrackingInterval) {
        clearInterval(fpsTrackingInterval);
        fpsTrackingInterval = null;
    }
}

/**
 * Update video feed image
 */
function updateVideoFeed(imageData) {
    const videoFeed = document.getElementById('video-feed');
    const placeholder = document.getElementById('video-placeholder');

    if (videoFeed && streaming) {
        videoFeed.src = imageData;
        // Ensure placeholder is hidden when we have frames
        if (placeholder && !placeholder.classList.contains('hidden')) {
            hide(placeholder);
        }
    }
}

/**
 * Load current shelf state
 */
async function loadShelfState() {
    try {
        const data = await fetchAPI('/shelf/state');
        renderShelfGrid(data.state);
    } catch (error) {
        console.error('Error loading shelf state:', error);
    }
}

/**
 * Render shelf grid
 */
function renderShelfGrid(state) {
    const grid = document.getElementById('shelf-grid');
    if (!grid) return;

    // Sort slots by ID for consistent order
    const slots = Object.entries(state).sort((a, b) => a[0].localeCompare(b[0]));
    const assignmentOptions = buildAssignmentOptions(state);

    grid.innerHTML = slots.map(([slotId, slotState]) => {
        let statusClass = 'empty';
        let borderColor = 'var(--border-default)';

        if (slotState.is_misplaced) {
            statusClass = 'misplaced';
            borderColor = 'var(--danger)';
        } else if (slotState.is_occupied) {
            statusClass = 'occupied';
            borderColor = 'var(--success)';
        } else if (slotState.is_uncertain) {
            statusClass = 'uncertain';
            borderColor = 'var(--warning)';
        }

        const verifiedItem = slotState.current_item || 'Empty';
        const expectedItem = slotState.expected_item || 'Unassigned';
        const verification = slotState.verification || {};
        const resolvedConfidence = Number.isFinite(verification.resolved_confidence)
            ? verification.resolved_confidence
            : slotState.confidence;
        const conf = Math.round((resolvedConfidence || 0) * 100);
        const verificationStatus = getVerificationStatusLabel(
            verification.fusion_source,
            slotState
        );
        const iconName = slotState.is_misplaced
            ? 'alert-triangle'
            : (slotState.is_occupied ? 'box' : 'box-select');

        const optionsMarkup = [
            '<option value="">Unassigned</option>',
            ...assignmentOptions.map((item) => {
                const selected = slotState.expected_item === item ? ' selected' : '';
                return `<option value="${item}"${selected}>${item}</option>`;
            })
        ].join('');

        return `
            <div class="shelf-slot ${statusClass}" title="${slotId}" 
                 style="border-color: ${borderColor};">
                <i data-lucide="${iconName}" 
                   style="width:22px; height:22px; color: ${slotState.is_misplaced ? 'var(--danger)' : (slotState.is_occupied ? 'var(--success)' : 'var(--text-muted)')}"></i>
                <div class="slot-id">${slotId}</div>
                <div class="slot-primary">${verifiedItem}</div>
                <div class="slot-secondary">Expected: ${expectedItem}</div>
                <div class="slot-secondary">Validation: ${verificationStatus}</div>
                <small>${conf}% Verified</small>
                <label class="slot-assignment-label" for="assign-${slotId}">Assign expected</label>
                <select id="assign-${slotId}" class="slot-assign-select" data-slot-id="${slotId}" ${assignmentBusySlots.has(slotId) ? 'disabled' : ''}>
                    ${optionsMarkup}
                </select>
            </div>
        `;
    }).join('');

    bindShelfAssignmentHandlers();

    // Initialize icons
    if (window.lucide) lucide.createIcons();
}

function buildAssignmentOptions(state) {
    const options = new Set(defaultShelfItems);

    Object.values(state || {}).forEach((slotState) => {
        const verification = slotState.verification || {};
        [
            slotState.current_item,
            slotState.expected_item,
            verification.resolved_item
        ].forEach((item) => {
            if (item && typeof item === 'string') {
                options.add(item.toLowerCase());
            }
        });
    });

    return Array.from(options).sort((a, b) => a.localeCompare(b));
}

function getVerificationStatusLabel(source, slotState) {
    const labels = {
        hybrid_agree: 'Cross-validated',
        hybrid_expected_override: 'Assignment-corrected',
        hybrid_conflict_penalty: 'Conflict-reviewed',
        gemini_injected: 'Verified presence',
        gemini_empty_confirmed: 'Verified empty',
        yolo_only: 'Detection-confirmed',
        default_empty: 'No item detected',
        uninitialized: 'Initializing',
        reset: 'Reset'
    };

    if (slotState?.is_misplaced) {
        return 'Misplacement confirmed';
    }

    if (slotState?.is_uncertain) {
        return 'Under review';
    }

    return labels[source] || 'Validated';
}

function bindShelfAssignmentHandlers() {
    document.querySelectorAll('.slot-assign-select').forEach((select) => {
        select.addEventListener('change', async (event) => {
            const el = event.currentTarget;
            const slotId = el.dataset.slotId;
            if (!slotId) return;

            const expectedItem = (el.value || '').trim().toLowerCase();
            await assignExpectedItem(slotId, expectedItem, el);
        });
    });
}

async function assignExpectedItem(slotId, expectedItem, control) {
    if (assignmentBusySlots.has(slotId)) {
        return;
    }

    assignmentBusySlots.add(slotId);
    if (control) {
        control.disabled = true;
    }

    try {
        await postAPI('/shelf/assignment', {
            slot_id: slotId,
            expected_item: expectedItem || null
        });
        showToast(`Updated ${slotId} expected item`, 'info');
        await loadShelfState();
    } catch (error) {
        console.error('Error updating shelf assignment:', error);
        showToast(`Failed to update ${slotId} assignment`, 'warning');
    } finally {
        assignmentBusySlots.delete(slotId);
        if (control) {
            control.disabled = false;
        }
    }
}

/**
 * Load dashboard stats
 */
async function loadStats() {
    try {
        // Get inventory
        const invData = await fetchAPI('/inventory');
        const totalItemsEl = document.getElementById('stat-total-items');
        if (totalItemsEl) {
            totalItemsEl.textContent = invData.total_units || 0;
        }

        // Get shelf state
        const stateData = await fetchAPI('/shelf/state');
        const occupied = Object.values(stateData.state || {})
            .filter(s => s.is_occupied).length;
        const occupiedEl = document.getElementById('stat-occupied-slots');
        if (occupiedEl) {
            occupiedEl.textContent = occupied;
        }

        // Get alerts
        const alertData = await fetchAPI('/alerts');
        const alertsEl = document.getElementById('stat-alerts');
        if (alertsEl) {
            alertsEl.textContent = alertData.counts?.active || 0;
        }

        // Count low stock (items with qty <= 2 but > 0)
        const lowStock = Object.values(invData.inventory || {})
            .filter(qty => qty > 0 && qty <= 2).length;
        const lowStockEl = document.getElementById('stat-low-stock');
        if (lowStockEl) {
            lowStockEl.textContent = lowStock;
        }

    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

/**
 * Load recent events
 */
async function loadRecentEvents() {
    try {
        const data = await fetchAPI('/events?limit=8');
        const container = document.getElementById('recent-events');

        if (!container) return;

        if (!data.events || data.events.length === 0) {
            container.innerHTML = '<p class="text-secondary" style="text-align: center; padding: 2rem;">No events yet</p>';
            return;
        }

        container.innerHTML = data.events.map(event => `
            <div class="event-item" style="display:flex; align-items:center; gap:0.75rem; padding:0.75rem; border-bottom:1px solid rgba(255,255,255,0.05);">
                <div style="color:var(--accent); font-size:1.25rem;">
                    ${getEventIcon(event.event_type)}
                </div>
                <div style="flex:1; min-width:0;">
                    <div style="font-weight:500; font-size:0.875rem; color:var(--accent);">
                        ${getEventLabel(event.event_type)}
                        ${event.item_class ? `- ${event.item_class}` : ''}
                    </div>
                    <div style="font-size:0.75rem; color:var(--text-muted);">${formatTime(event.timestamp)}</div>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading events:', error);
    }
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (statsInterval) {
        clearInterval(statsInterval);
    }
    stopFpsTracking();
    if (streaming) {
        if (activeMode === 'attachment') {
            stopAttachmentStream();
        } else {
            stopStream();
        }
    }
});
