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
        this.updateDashboardTitleIcon();
    }
    
    updateDashboardTitleIcon() {
        // Convert emoji icon in title to Bootstrap Icon
        const titleElement = document.getElementById('dashboard-title');
        if (titleElement) {
            const text = titleElement.textContent.trim();
            const parts = text.split(' ');
            if (parts.length > 0) {
                const icon = parts[0];
                const name = parts.slice(1).join(' ');
                titleElement.innerHTML = `${this.getIconHTML(icon)} ${name}`;
            }
        }
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
            option.addEventListener('click', async () => {
                const widgetType = option.dataset.widgetType;
                
                // For lights widget, show group selection
                if (widgetType === 'lights') {
                    this.hideAddWidgetModal();
                    await this.showLightsWidgetConfig();
                } else {
                    this.addWidget(widgetType);
                    this.hideAddWidgetModal();
                }
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
        
        widget.querySelector('.widget-title').innerHTML = this.getWidgetTitle(widgetData.type);
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
            'lights': '<i class="bi bi-lightbulb" style="color: #e600a5;"></i> Lights',
            'climate': '<i class="bi bi-thermometer-half" style="color: #8400ff;"></i> Climate',
            'devices': '<i class="bi bi-phone" style="color: #e600a5;"></i> Devices',
            'printer-status': '<i class="bi bi-bar-chart" style="color: #8400ff;"></i> Printer Status',
            'print-progress': '<i class="bi bi-clock-history" style="color: #e600a5;"></i> Print Progress',
            'printer-camera': '<i class="bi bi-camera-video" style="color: #8400ff;"></i> Camera Feed',
            'recent-projects': '<i class="bi bi-file-earmark-text" style="color: #e600a5;"></i> Recent Projects',
            'quick-design': '<i class="bi bi-stars" style="color: #8400ff;"></i> Quick Design'
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
        // Return loading state initially
        const loadingHtml = `
            <div class="widget-list">
                <div class="widget-list-item">
                    <span>Loading lights...</span>
                </div>
            </div>
        `;
        
        // Fetch real lights data
        setTimeout(() => this.loadRealLightsData(), 100);
        
        return loadingHtml;
    }
    
    async loadRealLightsData() {
        try {
            const response = await fetch('/api/ledvance/groups/');
            const data = await response.json();
            
            if (data.success && data.groups.length > 0) {
                // Find all lights widgets and update them with their specific config
                document.querySelectorAll('[data-widget-type="lights"]').forEach(widgetElement => {
                    const widgetId = widgetElement.dataset.widgetId;
                    const widgetData = this.widgets.find(w => w.id === widgetId);
                    
                    // Filter groups based on widget config
                    let groupsToShow = data.groups;
                    if (widgetData && widgetData.config && widgetData.config.groups) {
                        groupsToShow = data.groups.filter(g => widgetData.config.groups.includes(g.id));
                    }
                    
                    const container = widgetElement.querySelector('.widget-content');
                    if (container) {
                        container.innerHTML = this.renderLightsWidget(groupsToShow, data.groups.length);
                    }
                });
            } else {
                // No groups configured
                document.querySelectorAll('[data-widget-type="lights"] .widget-content').forEach(container => {
                    container.innerHTML = `
                        <div class="widget-list">
                            <div class="widget-list-item" style="flex-direction: column; align-items: flex-start; gap: 0.5rem;">
                                <span style="color: #8a8694;">No light groups configured</span>
                                <a href="/lights/" style="color: #8400ff; text-decoration: none; font-size: 0.875rem;">Create groups →</a>
                            </div>
                        </div>
                    `;
                });
            }
        } catch (error) {
            console.error('Failed to load light groups:', error);
            document.querySelectorAll('[data-widget-type="lights"] .widget-content').forEach(container => {
                container.innerHTML = `
                    <div class="widget-list">
                        <div class="widget-list-item">
                            <span style="color: #ef4444;">Failed to load groups</span>
                        </div>
                    </div>
                `;
            });
        }
    }
    
    renderLightsWidget(groups, totalGroups = null) {
        // Show max 4 groups in widget
        const displayGroups = groups.slice(0, 4);
        const hasMore = groups.length > 4;
        const showTotalCount = totalGroups !== null && totalGroups !== groups.length;
        
        // Get all group IDs for bulk control
        const groupIds = groups.map(g => g.id).join(',');
        
        let html = '<div class="widget-list">';
        
        // Add All On/Off buttons at the top
        if (groups.length > 0) {
            html += `
                <div style="display: flex; gap: 0.5rem; padding: 0.5rem; border-bottom: 1px solid rgba(255,255,255,0.1);">
                    <button onclick="window.dashboardManager.toggleAllGroupsInWidget('${groupIds}', true); event.stopPropagation();" 
                            style="flex: 1; padding: 0.5rem; border-radius: 0.375rem; border: none; background: linear-gradient(135deg, #8400ff, #e600a5); color: white; cursor: pointer; font-weight: 600; transition: all 0.3s;">
                        <i class="bi bi-lightbulb"></i> All On
                    </button>
                    <button onclick="window.dashboardManager.toggleAllGroupsInWidget('${groupIds}', false); event.stopPropagation();"
                            style="flex: 1; padding: 0.5rem; border-radius: 0.375rem; border: 1px solid rgba(255,255,255,0.2); background: rgba(255,255,255,0.05); color: white; cursor: pointer; font-weight: 600; transition: all 0.3s;">
                        <i class="bi bi-lightbulb-off"></i> All Off
                    </button>
                </div>
            `;
        }
        
        displayGroups.forEach(group => {
            // Group is ON if any light is on
            const isOn = group.lights_on > 0;
            const statusClass = isOn ? 'status-on' : 'status-off';
            const statusText = isOn ? 'ON' : 'OFF';
            const lightCount = group.light_count || 0;
            
            html += `
                <div class="widget-list-item" style="cursor: pointer;" onclick="window.dashboardManager.toggleGroupFromWidget('${group.id}')">
                    <div style="display: flex; flex-direction: column; gap: 0.25rem;">
                        <span>${group.name}</span>
                        <span style="font-size: 0.75rem; color: #8a8694;">${lightCount} light${lightCount !== 1 ? 's' : ''}</span>
                    </div>
                    <span class="${statusClass}">${statusText}</span>
                </div>
            `;
        });
        
        if (hasMore || showTotalCount) {
            const linkText = showTotalCount 
                ? `View ${groups.length} selected of ${totalGroups} groups →`
                : `View all ${groups.length} groups →`;
            html += `
                <div class="widget-list-item">
                    <a href="/lights/" style="color: #8400ff; text-decoration: none; font-size: 0.875rem;">${linkText}</a>
                </div>
            `;
        }
        
        html += '</div>';
        return html;
    }
    
    async toggleGroupFromWidget(groupId) {
        try {
            const response = await fetch(`/api/ledvance/groups/${groupId}/toggle/`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': this.getCsrfToken()
                }
            });
            
            const data = await response.json();
            
            if (data.success) {
                // Reload groups data to update UI
                this.loadRealLightsData();
            } else {
                alert('Failed to toggle group: ' + data.error);
            }
        } catch (error) {
            console.error('Error toggling group:', error);
            alert('Error toggling group');
        }
    }
    
    async toggleAllGroupsInWidget(groupIdsStr, turnOn) {
        try {
            const groupIds = groupIdsStr.split(',');
            
            // Toggle all groups in parallel
            const promises = groupIds.map(groupId => 
                fetch(`/api/ledvance/groups/${groupId}/brightness/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCsrfToken()
                    },
                    body: JSON.stringify({
                        brightness: turnOn ? 100 : 0
                    })
                })
            );
            
            await Promise.all(promises);
            
            // Reload groups data to update UI
            this.loadRealLightsData();
        } catch (error) {
            console.error('Error toggling all groups:', error);
            alert('Error toggling all groups');
        }
    }
    
    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
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
    
    addWidget(type, config = {}) {
        const id = type + '-' + Date.now();
        this.widgets.push({ id, type, size: 'medium', config });
        this.renderDashboard();
    }
    
    removeWidget(id) {
        this.widgets = this.widgets.filter(w => w.id !== id);
        this.renderDashboard();
    }
    
    async showLightsWidgetConfig() {
        try {
            // Fetch available groups
            const response = await fetch('/api/ledvance/groups/');
            const data = await response.json();
            
            if (!data.success || !data.groups || data.groups.length === 0) {
                alert('No light groups found. Please create groups first.');
                return;
            }
            
            // Create modal
            const modal = document.createElement('div');
            modal.className = 'modal active';
            modal.innerHTML = `
                <div class="modal-content" style="max-width: 500px;">
                    <div class="modal-header">
                        <h2>Configure Lights Widget</h2>
                        <button class="modal-close" onclick="this.closest('.modal').remove()">
                            <i class="bi bi-x-lg"></i>
                        </button>
                    </div>
                    <div class="modal-body">
                        <p style="color: #b8b4c5; margin-bottom: 1rem;">Select which groups to show in this widget:</p>
                        <div id="group-selector" style="max-height: 300px; overflow-y: auto;">
                            ${data.groups.map(group => `
                                <div style="padding: 0.75rem; display: flex; align-items: center; gap: 0.75rem; background: rgba(26, 23, 34, 0.4); border-radius: 8px; margin-bottom: 0.5rem;">
                                    <input type="checkbox" id="group-${group.id}" value="${group.id}" checked style="width: auto; margin: 0;">
                                    <label for="group-${group.id}" style="margin: 0; cursor: pointer; flex: 1; color: #ffffff;">
                                        ${group.name} <span style="color: #8a8694;">(${group.light_count} lights)</span>
                                    </label>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                    <div class="modal-footer" style="display: flex; gap: 1rem; justify-content: flex-end;">
                        <button onclick="this.closest('.modal').remove()" style="padding: 0.75rem 1.5rem; border-radius: 8px; border: 1px solid rgba(132, 0, 255, 0.3); background: rgba(26, 23, 34, 0.6); color: #ffffff; cursor: pointer; transition: all 0.3s ease;">Cancel</button>
                        <button id="add-lights-widget-btn" style="padding: 0.75rem 1.5rem; border-radius: 8px; border: none; background: linear-gradient(135deg, #8400ff, #e600a5); color: white; cursor: pointer; transition: all 0.3s ease;">Add Widget</button>
                    </div>
                </div>
            `;
            
            document.body.appendChild(modal);
            
            // Handle add button
            document.getElementById('add-lights-widget-btn').addEventListener('click', () => {
                const selectedGroups = [];
                document.querySelectorAll('#group-selector input[type="checkbox"]:checked').forEach(cb => {
                    selectedGroups.push(cb.value);
                });
                
                if (selectedGroups.length === 0) {
                    alert('Please select at least one group');
                    return;
                }
                
                this.addWidget('lights', { groups: selectedGroups });
                modal.remove();
            });
            
        } catch (error) {
            console.error('Failed to load groups:', error);
            alert('Failed to load groups');
        }
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
    
    // Dashboard Management Methods
    getIconHTML(iconName) {
        // Map emoji to icon names (for backward compatibility)
        const emojiToName = {
            '🏠': 'house',
            '🛋️': 'sofa',
            '🛋': 'sofa',
            '🍳': 'kitchen',
            '🛌️': 'bed',
            '🛌': 'bed',
            '🛠️': 'tools',
            '🛠': 'tools',
            '🏋️': 'gym',
            '🏋': 'gym',
            '🎮': 'game',
            '📚': 'book',
            '🎵': 'music',
            '🎨': 'palette',
            '👾': 'tv',
            '⚙️': 'gear',
            '⚙': 'gear'
        };
        
        // Convert emoji to icon name if needed
        const name = emojiToName[iconName] || iconName;
        
        // Map icon names to Bootstrap Icons HTML
        const iconMap = {
            'house': '<i class="bi bi-house" style="color: #8400ff;"></i>',
            'sofa': '<i class="bi bi-lamp" style="color: #e600a5;"></i>',
            'kitchen': '<i class="bi bi-cup-hot" style="color: #8400ff;"></i>',
            'bed': '<i class="bi bi-moon" style="color: #e600a5;"></i>',
            'tools': '<i class="bi bi-tools" style="color: #8400ff;"></i>',
            'gym': '<i class="bi bi-heart-pulse" style="color: #e600a5;"></i>',
            'game': '<i class="bi bi-controller" style="color: #8400ff;"></i>',
            'book': '<i class="bi bi-book" style="color: #e600a5;"></i>',
            'music': '<i class="bi bi-music-note-beamed" style="color: #8400ff;"></i>',
            'palette': '<i class="bi bi-palette" style="color: #e600a5;"></i>',
            'tv': '<i class="bi bi-tv" style="color: #8400ff;"></i>',
            'gear': '<i class="bi bi-gear" style="color: #e600a5;"></i>'
        };
        
        return iconMap[name] || name;
    }
    
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
                        <span>${this.getIconHTML(dashboard.icon)}</span>
                        <span>${dashboard.name}</span>
                        ${dashboard.is_default ? '<span style="font-size: 0.75rem; color: var(--color-accent);">★</span>' : ''}
                    </div>
                    <div class="dashboard-card-actions">
                        <button class="dashboard-card-btn" onclick="dashboardManager.editDashboard('${dashboard.id}')" title="Edit">
                            <i class="bi bi-pencil-square"></i>
                        </button>
                        ${!dashboard.is_default ? `
                            <button class="dashboard-card-btn" onclick="dashboardManager.setDefaultDashboard('${dashboard.id}')" title="Set as Default">
                                <i class="bi bi-star"></i>
                            </button>
                            <button class="dashboard-card-btn" onclick="dashboardManager.deleteDashboard('${dashboard.id}')" title="Delete">
                                <i class="bi bi-trash"></i>
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
            closeDashboardSwitcher();
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
                closeDashboardEdit();
                
                if (!dashboardId && data.dashboard) {
                    // Switch to new dashboard
                    window.location.href = `/dashboard/${data.dashboard.id}/`;
                } else {
                    // Reload dashboards list
                    await this.loadDashboards();
                    if (dashboardId === this.currentDashboardId) {
                        // Update current dashboard title
                        document.getElementById('dashboard-title').innerHTML = `${this.getIconHTML(icon)} ${name}`;
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
    window.dashboardManager.showCreateDashboard();
}

function saveDashboard() {
    window.dashboardManager.saveDashboard();
}

// Initialize dashboard manager when DOM is ready
let dashboardManager;
document.addEventListener('DOMContentLoaded', () => {
    dashboardManager = new DashboardManager();
    window.dashboardManager = dashboardManager;
});
