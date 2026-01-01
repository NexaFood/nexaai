/**
 * Printers Page JavaScript
 * Handles printer management, file uploads, and print control
 */

// State
let currentPrinterId = null;
let currentPrinterName = null;
let selectedFile = null;

// ==================== Initialization ====================

document.addEventListener('DOMContentLoaded', function() {
    initDropzone();
    initFileInput();
    initUploadForm();
});

// ==================== Dropzone ====================

function initDropzone() {
    const dropzone = document.getElementById('dropzone');
    if (!dropzone) return;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, preventDefaults, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropzone.addEventListener(eventName, () => dropzone.classList.remove('dragover'), false);
    });

    dropzone.addEventListener('drop', handleDrop, false);
    dropzone.addEventListener('click', () => document.getElementById('file-input').click());
}

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
}

// ==================== File Input ====================

function initFileInput() {
    const fileInput = document.getElementById('file-input');
    if (!fileInput) return;

    fileInput.addEventListener('change', function(e) {
        if (this.files.length > 0) {
            handleFileSelect(this.files[0]);
        }
    });
}

function handleFileSelect(file) {
    // Validate file type
    const validExtensions = ['.gcode', '.stl'];
    const fileName = file.name.toLowerCase();
    const isValid = validExtensions.some(ext => fileName.endsWith(ext));

    if (!isValid) {
        showNotification('Please select a .gcode or .stl file', 'error');
        return;
    }

    selectedFile = file;
    
    // Update UI
    document.getElementById('dropzone').style.display = 'none';
    document.getElementById('selected-file').style.display = 'flex';
    document.getElementById('selected-file-name').textContent = file.name;
}

function clearSelectedFile() {
    selectedFile = null;
    document.getElementById('file-input').value = '';
    document.getElementById('dropzone').style.display = 'block';
    document.getElementById('selected-file').style.display = 'none';
}

// ==================== Upload Form ====================

function initUploadForm() {
    const form = document.getElementById('upload-form');
    if (!form) return;

    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        if (!selectedFile) {
            showNotification('Please select a file to upload', 'error');
            return;
        }

        const printerId = document.getElementById('upload-printer-id').value;
        const printAfterUpload = document.getElementById('print-after-upload').checked;

        // Show progress
        document.getElementById('upload-progress').style.display = 'flex';
        document.getElementById('upload-btn').disabled = true;

        try {
            await uploadFile(printerId, selectedFile, printAfterUpload);
            showNotification('File uploaded successfully!', 'success');
            closeUploadModal();
            refreshPrinters();
        } catch (error) {
            showNotification('Upload failed: ' + error.message, 'error');
        } finally {
            document.getElementById('upload-progress').style.display = 'none';
            document.getElementById('upload-btn').disabled = false;
        }
    });
}

async function uploadFile(printerId, file, printAfterUpload) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('print_after_upload', printAfterUpload);

    const response = await fetch(`/api/printers/${printerId}/upload/`, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': getCSRFToken()
        }
    });

    if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Upload failed');
    }

    return await response.json();
}

// ==================== Modal Functions ====================

function openUploadModal(printerId) {
    currentPrinterId = printerId;
    document.getElementById('upload-printer-id').value = printerId;
    clearSelectedFile();
    document.getElementById('upload-modal').style.display = 'flex';
}

function closeUploadModal() {
    document.getElementById('upload-modal').style.display = 'none';
    clearSelectedFile();
}

function openModeModal(printerId, currentMode) {
    currentPrinterId = printerId;
    document.getElementById('mode-modal').style.display = 'flex';
    
    // Highlight current mode
    document.querySelectorAll('.mode-option').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.mode === currentMode) {
            btn.classList.add('active');
        }
    });
}

function closeModeModal() {
    document.getElementById('mode-modal').style.display = 'none';
}

function openDeleteModal(printerId, printerName) {
    currentPrinterId = printerId;
    currentPrinterName = printerName;
    document.getElementById('delete-printer-name').textContent = printerName;
    document.getElementById('delete-modal').style.display = 'flex';
}

function closeDeleteModal() {
    document.getElementById('delete-modal').style.display = 'none';
}

function openPrinterDetail(printerId) {
    // Fetch printer details and show modal
    fetch(`/api/printers/${printerId}/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showPrinterDetailModal(data.printer);
            }
        })
        .catch(error => {
            showNotification('Failed to load printer details', 'error');
        });
}

function showPrinterDetailModal(printer) {
    document.getElementById('modal-printer-name').textContent = printer.name;
    
    const content = `
        <div class="detail-section">
            <h4 class="detail-section-title">Connection</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <span class="detail-label">IP Address</span>
                    <span class="detail-value">${printer.ip_address || 'Not configured'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Status</span>
                    <span class="detail-value">${printer.status_display}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">API Key</span>
                    <span class="detail-value">${printer.api_key ? '••••••••' : 'Not configured'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Last Seen</span>
                    <span class="detail-value">${printer.last_seen || 'Never'}</span>
                </div>
            </div>
        </div>
        
        <div class="detail-section">
            <h4 class="detail-section-title">Specifications</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <span class="detail-label">Model</span>
                    <span class="detail-value">${printer.model}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Type</span>
                    <span class="detail-value">${printer.printer_type_display}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Build Volume</span>
                    <span class="detail-value">${printer.build_volume_x}×${printer.build_volume_y}×${printer.build_volume_z}mm</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Serial Number</span>
                    <span class="detail-value">${printer.serial_number || 'N/A'}</span>
                </div>
            </div>
        </div>
        
        ${printer.status === 'printing' || printer.status === 'paused' ? `
        <div class="detail-section">
            <h4 class="detail-section-title">Current Print</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <span class="detail-label">File</span>
                    <span class="detail-value">${printer.current_file || 'Unknown'}</span>
                </div>
                <div class="detail-item">
                    <span class="detail-label">Progress</span>
                    <span class="detail-value">${printer.progress || 0}%</span>
                </div>
            </div>
            <div class="control-buttons" style="margin-top: 1rem;">
                ${printer.status === 'printing' ? `
                    <button onclick="pausePrint('${printer.id}')" class="control-btn pause">
                        <i class="bi bi-pause-fill"></i> Pause
                    </button>
                ` : `
                    <button onclick="resumePrint('${printer.id}')" class="control-btn resume">
                        <i class="bi bi-play-fill"></i> Resume
                    </button>
                `}
                <button onclick="cancelPrint('${printer.id}')" class="control-btn stop">
                    <i class="bi bi-stop-fill"></i> Cancel Print
                </button>
            </div>
        </div>
        ` : ''}
    `;
    
    document.getElementById('modal-printer-content').innerHTML = content;
    document.getElementById('printer-detail-modal').style.display = 'flex';
}

function closePrinterModal() {
    document.getElementById('printer-detail-modal').style.display = 'none';
}

// ==================== Printer Actions ====================

async function setMode(mode) {
    if (!currentPrinterId) return;

    try {
        const response = await fetch(`/api/printers/${currentPrinterId}/mode/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCSRFToken()
            },
            body: JSON.stringify({ mode: mode })
        });

        const data = await response.json();
        
        if (data.success) {
            showNotification('Mode changed successfully', 'success');
            closeModeModal();
            refreshPrinters();
        } else {
            showNotification(data.error || 'Failed to change mode', 'error');
        }
    } catch (error) {
        showNotification('Failed to change mode', 'error');
    }
}

async function confirmDelete() {
    if (!currentPrinterId) return;

    try {
        const response = await fetch(`/api/printers/${currentPrinterId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });

        const data = await response.json();
        
        if (data.success) {
            showNotification('Printer deleted successfully', 'success');
            closeDeleteModal();
            refreshPrinters();
        } else {
            showNotification(data.error || 'Failed to delete printer', 'error');
        }
    } catch (error) {
        showNotification('Failed to delete printer', 'error');
    }
}

async function pausePrint(printerId) {
    await controlPrint(printerId, 'pause');
}

async function resumePrint(printerId) {
    await controlPrint(printerId, 'resume');
}

async function cancelPrint(printerId) {
    if (!confirm('Are you sure you want to cancel this print?')) return;
    await controlPrint(printerId, 'cancel');
}

async function controlPrint(printerId, action) {
    try {
        const response = await fetch(`/api/printers/${printerId}/${action}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCSRFToken()
            }
        });

        const data = await response.json();
        
        if (data.success) {
            showNotification(`Print ${action}d successfully`, 'success');
            refreshPrinters();
            closePrinterModal();
        } else {
            showNotification(data.error || `Failed to ${action} print`, 'error');
        }
    } catch (error) {
        showNotification(`Failed to ${action} print`, 'error');
    }
}

// ==================== Utility Functions ====================

function refreshPrinters() {
    htmx.trigger('#printers-grid', 'load');
}

function getCSRFToken() {
    const cookie = document.cookie.split(';').find(c => c.trim().startsWith('csrftoken='));
    return cookie ? cookie.split('=')[1] : '';
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="bi bi-${type === 'success' ? 'check-circle' : type === 'error' ? 'x-circle' : 'info-circle'}"></i>
        <span>${message}</span>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => notification.classList.add('show'), 10);
    
    // Remove after delay
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, 3000);
}

// Close modals on escape key
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeUploadModal();
        closeModeModal();
        closeDeleteModal();
        closePrinterModal();
    }
});

// Close modals on overlay click
document.querySelectorAll('.modal-overlay').forEach(overlay => {
    overlay.addEventListener('click', function(e) {
        if (e.target === this) {
            this.style.display = 'none';
        }
    });
});
