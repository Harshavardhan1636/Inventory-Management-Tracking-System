/**
 * Inventory-Management-Tracking-System - Inventory JavaScript
 * Handles inventory management page functionality
 */

// State
let currentItem = null;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadInventory();

    document.getElementById('btn-refresh').addEventListener('click', loadInventory);
    document.getElementById('search-input').addEventListener('input', filterInventory);
    document.getElementById('btn-add-item').addEventListener('click', openAddItemModal);
});

/**
 * Load inventory data
 */
async function loadInventory() {
    try {
        const data = await fetchAPI('/inventory');

        // Update summary stats
        document.getElementById('total-items').textContent = data.total_items || 0;
        document.getElementById('total-units').textContent = data.total_units || 0;

        // Count low stock and out of stock
        const inventory = data.inventory || {};
        let lowStock = 0;
        let outOfStock = 0;

        Object.values(inventory).forEach(qty => {
            if (qty === 0) outOfStock++;
            else if (qty <= 2) lowStock++;
        });

        document.getElementById('low-stock-count').textContent = lowStock;
        document.getElementById('out-of-stock-count').textContent = outOfStock;

        // Render table
        renderInventoryTable(inventory);

        // Keep search results consistent after manual refreshes.
        const searchInput = document.getElementById('search-input');
        if (searchInput && searchInput.value.trim()) {
            filterInventory({ target: searchInput });
        }

    } catch (error) {
        console.error('Error loading inventory:', error);
        showToast('Error loading inventory', 'critical');
    }
}

/**
 * Render inventory table
 */
function renderInventoryTable(inventory) {
    const tbody = document.getElementById('inventory-body');
    const emptyState = document.getElementById('empty-state');

    const items = Object.entries(inventory);

    if (items.length === 0) {
        tbody.innerHTML = '';
        show(emptyState);
        return;
    }

    hide(emptyState);

    tbody.innerHTML = items.map(([itemClass, quantity]) => {
        let statusClass, statusText;

        if (quantity === 0) {
            statusClass = 'badge-danger';
            statusText = 'Out of Stock';
        } else if (quantity <= 2) {
            statusClass = 'badge-warning';
            statusText = 'Low Stock';
        } else {
            statusClass = 'badge-success';
            statusText = 'In Stock';
        }

        return `
            <tr data-item="${itemClass}">
                <td>
                    <div style="display:flex; align-items:center; gap:0.5rem;">
                        <div style="width:32px; height:32px; background:rgba(255,255,255,0.05); border-radius:6px; display:flex; align-items:center; justify-content:center;">
                            <i data-lucide="box" style="width:16px;"></i>
                        </div>
                        <span style="font-weight: 500;">${itemClass}</span>
                    </div>
                </td>
                <td>
                    <span class="quantity-display" style="font-weight:600;">${quantity}</span>
                </td>
                <td>
                    <span class="badge ${statusClass}">${statusText}</span>
                </td>
                <td>
                    <span style="color: var(--text-muted); font-size:0.875rem;">Just now</span>
                </td>
                <td>
                    <button class="btn btn-secondary btn-sm" onclick="openEditModal('${itemClass}', ${quantity})">
                        <i data-lucide="edit-2" style="width:14px;"></i> Edit
                    </button>
                </td>
            </tr>
        `;
    }).join('');

    if (window.lucide) lucide.createIcons();
}

/**
 * Filter inventory by search term
 */
function filterInventory(event) {
    const searchTerm = event.target.value.toLowerCase();
    const rows = document.querySelectorAll('#inventory-body tr');

    rows.forEach(row => {
        const itemName = row.dataset.item.toLowerCase();
        if (itemName.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

/**
 * Close edit modal
 */
function closeModal() {
    hide(document.getElementById('edit-modal'));
    currentItem = null;
}

/**
 * Change quantity input value
 */
function changeQuantity(delta) {
    const input = document.getElementById('quantity-change');
    const currentValue = parseInt(input.value) || 0;
    input.value = currentValue + delta;
}

// Close modal on escape key
document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
        closeModal();
    }
});

// Close modal on backdrop click
document.getElementById('edit-modal')?.addEventListener('click', (event) => {
    if (event.target.id === 'edit-modal') {
        closeModal();
    }
});

/**
 * Open Add Item modal
 */
function openAddItemModal() {
    currentItem = null; // null means we're adding, not editing

    document.getElementById('item-name').value = '';
    document.getElementById('item-name').readOnly = false;
    document.getElementById('quantity-change').value = 1;
    document.getElementById('update-reason').value = 'Initial stock';

    // Update modal title
    document.querySelector('#edit-modal .card-title').textContent = 'Add New Item';

    show(document.getElementById('edit-modal'));
}

/**
 * Override saveChanges to handle both add and edit
 */
async function saveChanges() {
    const itemName = document.getElementById('item-name').value.trim();
    const quantity = parseInt(document.getElementById('quantity-change').value) || 0;
    const reason = document.getElementById('update-reason').value || 'Manual update';

    if (!itemName) {
        showToast('Please enter an item name', 'warning');
        return;
    }

    if (currentItem === null) {
        // Adding new item
        if (quantity <= 0) {
            showToast('Quantity must be at least 1', 'warning');
            return;
        }

        try {
            await postAPI('/inventory/add', {
                item_class: itemName,
                quantity: quantity,
                reason: reason
            });

            showToast(`Added ${itemName}`, 'info');
            closeModal();
            loadInventory();

        } catch (error) {
            console.error('Error adding item:', error);
            showToast('Error adding item', 'critical');
        }
    } else {
        // Editing existing item
        if (quantity === 0) {
            showToast('No changes to save', 'info');
            closeModal();
            return;
        }

        if (currentItem.currentQuantity + quantity < 0) {
            showToast('Cannot reduce below 0', 'warning');
            return;
        }

        try {
            await postAPI(`/inventory/${currentItem.itemClass}/update`, {
                quantity_change: quantity,
                reason: reason
            });

            showToast(`Updated ${currentItem.itemClass}`, 'info');
            closeModal();
            loadInventory();

        } catch (error) {
            console.error('Error updating inventory:', error);
            showToast('Error updating inventory', 'critical');
        }
    }
}

/**
 * Reset modal when opening for edit
 */
function openEditModal(itemClass, currentQuantity) {
    currentItem = { itemClass, currentQuantity };

    document.getElementById('item-name').value = itemClass;
    document.getElementById('item-name').readOnly = true;
    document.getElementById('quantity-change').value = 0;
    document.getElementById('update-reason').value = '';

    // Update modal title
    document.querySelector('#edit-modal .card-title').textContent = 'Edit Item';

    show(document.getElementById('edit-modal'));
}
