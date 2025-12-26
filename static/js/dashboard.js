/**
 * NexaAI Dashboard - Widget Management System
 * Handles drag-drop, resize, and customization
 */

class DashboardManager {
    constructor() {
        this.editMode = false;
        this.widgets = [];
        this.draggedWidget = null;
        this.draggedOverWidget = null;
        this.currentDashboardId = window.currentDashboardId || null;
        this.dashboards = [];
        
        this.init();
    }
    
    init() {
        this.loadDashboards();
        this.loadDashboard();
        this.initializeEventListeners();
    }
    
    initializeEventListeners() {
        // Add widget button
        document.getElementById('add-widget-btn')?.addEventListener('click', () => {
            this.showAddWidgetModal();
        });
        
        // Edit layout button
        document.getElementById('edit-layout-btn')?.addEventListener('click', () => {
            this.toggleEditMode();
        });
        
        // Save layout button
        document.getElementById('save-layout-btn')?.addEventListener('click', () => {
            this.saveLayout();
            this.toggleEditMode();
        });
        
        // Reset layout button
        document.getElementById('reset-layout-btn')?.addEventListener('click', () => {
            if (confirm('Reset to default layout? This will remove all customizations.')) {
                this.resetLayout();
            }
        });
        
        // Dashboard switcher button
        document.getElementById('dashboard-switcher-btn')?.addEventListener('click', () => {
            this.showDashboardSwitcher();
        });
        
        // Icon selector
        document.querySelectorAll('.icon-option').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                document.querySelectorAll('.icon-option').forEach(b => b.classList.remove('selected'));
                btn.classList.add('selected');
                document.getElementById('dashboard-icon').value = btn.dataset.icon;
            });
        });
        
        // Modal close
        document.querySelector('.modal-close')?.addEventListener('click', () => {
            this.hideAddWidgetModal();
        });
        
        // Close modal on background click
        document.getElementById('add-widget-modal')?.addEventListener('click', (e) => {
            if (e.target.id === 'add-widget-modal') {
                this.hideAddWidgetModal();
            }
        });
        
        // Widget options
        document.querySelectorAll('.widget-option').forEach(option => {
            option.addEventListener('click', () => {
                const widgetType = option.dataset.widgetType;
                this.addWidget(widgetType);
                this.hideAddWidgetModal();
            });
        });
    }
    
    toggleEditMode() {
        this.editMode = !this.editMode;
        
        document.getElementById('edit-layout-btn').style.display = this.editMode ? 'none' : 'flex';
        document.getElementById('save-layout-btn').style.display = this.editMode ? 'flex' : 'none';
        document.getElementById('reset-layout-btn').style.display = this.editMode ? 'flex' : 'none';
        
        // Toggle remove buttons
        document.querySelectorAll('.widget-remove-btn').forEach(btn => {
            btn.style.display = this.editMode ? 'block' : 'none';
        });
        
        // Toggle draggable
        document.querySelectorAll('.widget').forEach(widget => {
            widget.draggable = this.editMode;
            if (this.editMode) {
                widget.classList.add('draggable');
            } else {
                widget.classList.remove('draggable');
            }
        });
    }
    
    loadDashboard() {
        // Try to load from server first, then localStorage, then default
        this.loadFromServer()
            .catch(() => {
                const savedLayout = localStorage.getItem('dashboard_layout');
                if (savedLayout) {
                    this.widgets = JSON.parse(savedLayout);
                } else {
                    this.widgets = this.getDefaultLayout();
                }
            })
            .finally(() => {
                this.renderDashboard();
            });
    }
    
    async loadFromServer() {
        if (!this.currentDashboardId) {
            throw new Error('No dashboard ID');
        }
        const response = await fetch(`/api/dashboards/${this.currentDashboardId}/layout/`);
        if (!response.ok) throw new Error('Failed to load layout');
        const data = await response.json();
        this.widgets = data.widgets || this.getDefaultLayout();
    }
    
    getDefaultLayout() {
        return [
            { id: 'lights-1', type: 'lights', size: 'medium' },
            { id: 'climate-1', type: 'climate', size: 'medium' },
            { id: 'printer-status-1', type: 'printer-status', size: 'medium' },
            { id: 'print-progress-1', type: 'print-progress', size: 'large' },
            { id: 'recent-projects-1', type: 'recent-projects', size: 'medium' }
        ];
    }
    
    resetLayout() {
        this.widgets = this.getDefaultLayout();
        this.renderDashboard();
        this.saveLayout();
    }
    
    renderDashboard() {
        const grid = document.getElementById('dashboard-grid');
        if (!grid) return;
        
        grid.innerHTML = '';
        
        this.widgets.forEach(widgetData => {
            const widgetElement = this.createWidget(widgetData);
            grid.appendChild(widgetElement);
        });
    }
    
    createWidget(widgetData) {
        const template = document.getElementById('widget-template');
        const widget = template.content.cloneNode(true);
        const widgetElement = widget.querySelector('.widget');
        
        widgetElement.dataset.widgetId = widgetData.id;
        widgetElement.dataset.widgetType = widgetData.type;
        
        // Set widget size
        if (widgetData.size) {
            widgetElement.classList.add(`widget-${widgetData.size}`);
        }
        
        widget.querySelector('.widget-title').textContent = this.getWidgetTitle(widgetData.type);
        widget.querySelector('.widget-content').innerHTML = this.getWidgetContent(widgetData.type);
        
        // Add event listeners
        const removeBtn = widget.querySelector('[data-action="remove"]');
        removeBtn.addEventListener('click', () => {
            this.removeWidget(widgetData.id);
        });
        
        const refreshBtn = widget.querySelector('[data-action="refresh"]');
        refreshBtn.addEventListener('click', () => {
            this.refreshWidget(widgetData.id);
        });
        
        // Drag and drop
        widgetElement.addEventListener('dragstart', (e) => this.handleDragStart(e));
        widgetElement.addEventListener('dragend', (e) => this.handleDragEnd(e));
        widgetElement.addEventListener('dragover', (e) => this.handleDragOver(e));
        widgetElement.addEventListener('drop', (e) => this.handleDrop(e));
        widgetElement.addEventListener('dragleave', (e) => this.handleDragLeave(e));
        
        return widget;
    }
    
    handleDragStart(e) {
        if (!this.editMode) return;
        
        this.draggedWidget = e.currentTarget;
        e.currentTarget.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
        e.dataTransfer.setData('text/html', e.currentTarget.innerHTML);
    }
    
    handleDragEnd(e) {
        e.currentTarget.classList.remove('dragging');
        
        document.querySelectorAll('.widget').forEach(widget => {
            widget.classList.remove('drag-over');
        });
        
        this.draggedWidget = null;
        this.draggedOverWidget = null;
    }
    
    handleDragOver(e) {
        if (!this.editMode) return;
        if (e.preventDefault) e.preventDefault();
        
        e.dataTransfer.dropEffect = 'move';
        
        const widget = e.currentTarget;
        if (widget !== this.draggedWidget) {
            widget.classList.add('drag-over');
            this.draggedOverWidget = widget;
        }
        
        return false;
    }
    
    handleDragLeave(e) {
        e.currentTarget.classList.remove('drag-over');
    }
    
    handleDrop(e) {
        if (!this.editMode) return;
        if (e.stopPropagation) e.stopPropagation();
        
        if (this.draggedWidget !== e.currentTarget) {
            // Swap widgets in array
            const draggedId = this.draggedWidget.dataset.widgetId;
            const targetId = e.currentTarget.dataset.widgetId;
            
            const draggedIndex = this.widgets.findIndex(w => w.id === draggedId);
            const targetIndex = this.widgets.findIndex(w => w.id === targetId);
            
            if (draggedIndex !== -1 && targetIndex !== -1) {
                [this.widgets[draggedIndex], this.widgets[targetIndex]] = 
                [this.widgets[targetIndex], this.widgets[draggedIndex]];
                
                this.renderDashboard();
            }
        }
        
        e.currentTarget.classList.remove('drag-over');
        return false;
    }
    
    getWidgetTitle(type) {
        const titles = {
            'lights': '💡 Lights',
            'climate': '🌡️ Climate',
            'devices': '📱 Devices',
            'printer-status': '📊 Printer Status',
            'print-progress': '⏱️ Print Progress',
            'printer-camera': '📹 Camera Feed',
            'recent-projects': '📝 Recent Projects',
            'quick-design': '✨ Quick Design'
        };
        return titles[type] || 'Widget';
    }
    
    getWidgetContent(type) {
        // This will be replaced with real data from API calls
        const content = {
            'lights': this.getLightsWidget(),
            'climate': this.getClimateWidget(),
            'devices': this.getDevicesWidget(),
            'printer-status': this.getPrinterStatusWidget(),
            'print-progress': this.getPrintProgressWidget(),
            'printer-camera': this.getPrinterCameraWidget(),
            'recent-projects': this.getRecentProjectsWidget(),
            'quick-design': this.getQuickDesignWidget()
        };
        return content[type] || '<p>Widget content</p>';
    }
    
    getLightsWidget() {
        return `
            <div class="widget-list">
                <div class="widget-list-item">
                    <span>Living Room</span>
                    <span class="status-on">ON</span>
                </div>
                <div class="widget-list-item">
                    <span>Kitchen</span>
                    <span class="status-on">ON</span>
                </div>
                <div class="widget-list-item">
                    <span>Bedroom</span>
                    <span class="status-off">OFF</span>
                </div>
                <div class="widget-list-item">
                    <span>Office</span>
                    <span class="status-on">ON</span>
                </div>
            </div>
        `;
    }
    
    getClimateWidget() {
        return `
            <div class="climate-widget">
                <div class="climate-temp">22°C</div>
                <div class="climate-details">
                    <div class="widget-list-item">
                        <span>Humidity</span>
                        <span>45%</span>
                    </div>
                    <div class="widget-list-item">
                        <span>Target</span>
                        <span>21°C</span>
                    </div>
                    <div class="widget-list-item">
                        <span>Mode</span>
                        <span>Auto</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    getDevicesWidget() {
        return `
            <div class="widget-list">
                <div class="widget-list-item">
                    <span>Router</span>
                    <span class="status-indicator status-on">●</span>
                </div>
                <div class="widget-list-item">
                    <span>NAS</span>
                    <span class="status-indicator status-on">●</span>
                </div>
                <div class="widget-list-item">
                    <span>Camera</span>
                    <span class="status-indicator status-off">●</span>
                </div>
                <div class="widget-list-item">
                    <span>Smart Speaker</span>
                    <span class="status-indicator status-on">●</span>
                </div>
            </div>
        `;
    }
    
    getPrinterStatusWidget() {
        return `
            <div class="printer-status">
                <div class="printer-name">Prusa i3 MK3S</div>
                <div class="widget-list">
                    <div class="widget-list-item">
                        <span>Status</span>
                        <span class="status-on">Ready</span>
                    </div>
                    <div class="widget-list-item">
                        <span>Nozzle Temp</span>
                        <span>25°C</span>
                    </div>
                    <div class="widget-list-item">
                        <span>Bed Temp</span>
                        <span>23°C</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    getPrintProgressWidget() {
        return `
            <div class="print-progress">
                <div class="print-filename">gear_housing.gcode</div>
                <div class="progress-bar-container">
                    <div class="progress-bar" style="width: 47%;"></div>
                </div>
                <div class="print-details">
                    <div class="widget-list-item">
                        <span>Time Elapsed</span>
                        <span>2h 15m</span>
                    </div>
                    <div class="widget-list-item">
                        <span>Time Remaining</span>
                        <span>2h 15m</span>
                    </div>
                    <div class="widget-list-item">
                        <span>Progress</span>
                        <span>47%</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    getPrinterCameraWidget() {
        return `
            <div class="camera-feed">
                <div class="camera-placeholder">
                    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path>
                        <circle cx="12" cy="13" r="4"></circle>
                    </svg>
                    <p>Camera feed placeholder</p>
                </div>
            </div>
        `;
    }
    
    getRecentProjectsWidget() {
        return `
            <div class="widget-list">
                <a href="/design/projects/" class="widget-link">
                    <span>Sphere 50mm</span>
                    <span style="color: #6b7280;">2 hours ago</span>
                </a>
                <a href="/design/projects/" class="widget-link">
                    <span>Cylinder 30mm</span>
                    <span style="color: #6b7280;">5 hours ago</span>
                </a>
                <a href="/design/projects/" class="widget-link">
                    <span>Box 25x25x25</span>
                    <span style="color: #6b7280;">1 day ago</span>
                </a>
            </div>
        `;
    }
    
    getQuickDesignWidget() {
        return `
            <a href="/design/projects/" class="btn-primary-large">
                Start New Design
            </a>
        `;
    }
    
    addWidget(type) {
        const id = type + '-' + Date.now();
        this.widgets.push({ id, type, size: 'medium' });
        this.renderDashboard();
    }
    
    removeWidget(id) {
        this.widgets = this.widgets.filter(w => w.id !== id);
        this.renderDashboard();
    }
    
    refreshWidget(id) {
        // Placeholder for refresh functionality
        console.log('Refreshing widget:', id);
        // In the future, this will make API calls to update widget data
    }
    
    showAddWidgetModal() {
        document.getElementById('add-widget-modal')?.classList.add('active');
    }
    
    hideAddWidgetModal() {
        document.getElementById('add-widget-modal')?.classList.remove('active');
    }
    
    async saveLayout() {
        // Save to localStorage (per dashboard)
        if (this.currentDashboardId) {
            localStorage.setItem(`dashboard_layout_${this.currentDashboardId}`, JSON.stringify(this.widgets));
        }
        
        // Try to save to server
        try {
            if (!this.currentDashboardId) {
                throw new Error('No dashboard ID');
            }
            
            const formData = new FormData();
            formData.append('widgets', JSON.stringify(this.widgets));
            
            const response = await fetch(`/api/dashboards/${this.currentDashboardId}/save-layout/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: formData
            });
            
            if (response.ok) {
                this.showNotification('Layout saved successfully!', 'success');
            } else {
                this.showNotification('Layout saved locally only', 'warning');
            }
        } catch (error) {
            console.error('Failed to save layout to server:', error);
            this.showNotification('Layout saved locally only', 'warning');
        }
    }
    
    getCsrfToken() {
        const name = 'csrftoken';
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
    showNotification(message, type = 'info') {
        // Simple notification system
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        document.body.appendChild(notification);
        
        setTimeout(() => {
            notification.classList.add('show');
        }, 10);
        
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Initialize dashboard when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardManager = new DashboardManager();
});

    // Dashboard Management Methods
    async loadDashboards() {
        try {
            const response = await fetch('/api/dashboards/');
            if (!response.ok) throw new Error('Failed to load dashboards');
            const data = await response.json();
            this.dashboards = data.dashboards || [];
        } catch (error) {
            console.error('Failed to load dashboards:', error);
            this.dashboards = [];
        }
    }
    
    showDashboardSwitcher() {
        const modal = document.getElementById('dashboard-switcher-modal');
        const listContainer = document.getElementById('dashboard-list');
        
        listContainer.innerHTML = '';
        
        this.dashboards.forEach(dashboard => {
            const card = document.createElement('div');
            card.className = `dashboard-card ${dashboard.id === this.currentDashboardId ? 'active' : ''}`;
            card.innerHTML = `
                <div class="dashboard-card-header">
                    <div class="dashboard-card-title">
                        <span>${dashboard.icon}</span>
                        <span>${dashboard.name}</span>
                        ${dashboard.is_default ? '<span style="font-size: 0.75rem; color: var(--color-accent);">★</span>' : ''}
                    </div>
                    <div class="dashboard-card-actions">
                        <button class="dashboard-card-btn" onclick="dashboardManager.editDashboard('${dashboard.id}')" title="Edit">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path>
                                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path>
                            </svg>
                        </button>
                        ${!dashboard.is_default ? `
                            <button class="dashboard-card-btn" onclick="dashboardManager.setDefaultDashboard('${dashboard.id}')" title="Set as Default">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"></polygon>
                                </svg>
                            </button>
                            <button class="dashboard-card-btn" onclick="dashboardManager.deleteDashboard('${dashboard.id}')" title="Delete">
                                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <polyline points="3 6 5 6 21 6"></polyline>
                                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                                </svg>
                            </button>
                        ` : ''}
                    </div>
                </div>
                <div style="color: var(--color-text-muted); font-size: 0.875rem; margin-top: 0.5rem;">
                    ${dashboard.room ? dashboard.room + ' • ' : ''}${dashboard.widget_count} widgets
                </div>
            `;
            
            card.addEventListener('click', (e) => {
                if (!e.target.closest('.dashboard-card-btn')) {
                    this.switchDashboard(dashboard.id);
                }
            });
            
            listContainer.appendChild(card);
        });
        
        modal.classList.add('active');
    }
    
    switchDashboard(dashboardId) {
        if (dashboardId === this.currentDashboardId) {
            this.closeDashboardSwitcher();
            return;
        }
        
        window.location.href = `/dashboard/${dashboardId}/`;
    }
    
    showCreateDashboard() {
        document.getElementById('dashboard-switcher-modal').classList.remove('active');
        document.getElementById('dashboard-edit-title').textContent = 'Create Dashboard';
        document.getElementById('edit-dashboard-id').value = '';
        document.getElementById('dashboard-name').value = '';
        document.getElementById('dashboard-room').value = '';
        document.getElementById('dashboard-icon').value = '🏠';
        document.querySelectorAll('.icon-option').forEach(btn => {
            btn.classList.toggle('selected', btn.dataset.icon === '🏠');
        });
        document.getElementById('dashboard-edit-modal').classList.add('active');
    }
    
    async editDashboard(dashboardId) {
        const dashboard = this.dashboards.find(d => d.id === dashboardId);
        if (!dashboard) return;
        
        document.getElementById('dashboard-switcher-modal').classList.remove('active');
        document.getElementById('dashboard-edit-title').textContent = 'Edit Dashboard';
        document.getElementById('edit-dashboard-id').value = dashboard.id;
        document.getElementById('dashboard-name').value = dashboard.name;
        document.getElementById('dashboard-room').value = dashboard.room || '';
        document.getElementById('dashboard-icon').value = dashboard.icon;
        document.querySelectorAll('.icon-option').forEach(btn => {
            btn.classList.toggle('selected', btn.dataset.icon === dashboard.icon);
        });
        document.getElementById('dashboard-edit-modal').classList.add('active');
    }
    
    async saveDashboard() {
        const dashboardId = document.getElementById('edit-dashboard-id').value;
        const name = document.getElementById('dashboard-name').value.trim();
        const room = document.getElementById('dashboard-room').value.trim();
        const icon = document.getElementById('dashboard-icon').value;
        
        if (!name) {
            this.showNotification('Dashboard name is required', 'error');
            return;
        }
        
        const formData = new FormData();
        formData.append('name', name);
        formData.append('room', room);
        formData.append('icon', icon);
        
        try {
            const url = dashboardId 
                ? `/api/dashboards/${dashboardId}/update/`
                : '/api/dashboards/create/';
            
            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(dashboardId ? 'Dashboard updated!' : 'Dashboard created!', 'success');
                this.closeDashboardEdit();
                
                if (!dashboardId && data.dashboard) {
                    // Switch to new dashboard
                    window.location.href = `/dashboard/${data.dashboard.id}/`;
                } else {
                    // Reload dashboards list
                    await this.loadDashboards();
                    if (dashboardId === this.currentDashboardId) {
                        // Update current dashboard title
                        document.getElementById('dashboard-title').textContent = `${icon} ${name}`;
                    }
                }
            } else {
                this.showNotification(data.error || 'Failed to save dashboard', 'error');
            }
        } catch (error) {
            console.error('Failed to save dashboard:', error);
            this.showNotification('Failed to save dashboard', 'error');
        }
    }
    
    async setDefaultDashboard(dashboardId) {
        try {
            const response = await fetch(`/api/dashboards/${dashboardId}/set-default/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Default dashboard updated!', 'success');
                await this.loadDashboards();
                this.showDashboardSwitcher();
            } else {
                this.showNotification(data.error || 'Failed to set default', 'error');
            }
        } catch (error) {
            console.error('Failed to set default dashboard:', error);
            this.showNotification('Failed to set default dashboard', 'error');
        }
    }
    
    async deleteDashboard(dashboardId) {
        if (!confirm('Are you sure you want to delete this dashboard?')) {
            return;
        }
        
        try {
            const response = await fetch(`/api/dashboards/${dashboardId}/delete/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Dashboard deleted!', 'success');
                await this.loadDashboards();
                
                if (dashboardId === this.currentDashboardId) {
                    // Redirect to default dashboard
                    window.location.href = '/dashboard/';
                } else {
                    this.showDashboardSwitcher();
                }
            } else {
                this.showNotification(data.error || 'Failed to delete dashboard', 'error');
            }
        } catch (error) {
            console.error('Failed to delete dashboard:', error);
            this.showNotification('Failed to delete dashboard', 'error');
        }
    }
}

// Global functions for modal controls
function closeDashboardSwitcher() {
    document.getElementById('dashboard-switcher-modal').classList.remove('active');
}

function closeDashboardEdit() {
    document.getElementById('dashboard-edit-modal').classList.remove('active');
}

function showCreateDashboard() {
    dashboardManager.showCreateDashboard();
}

function saveDashboard() {
    dashboardManager.saveDashboard();
}

// Initialize dashboard manager
const dashboardManager = new DashboardManager();
