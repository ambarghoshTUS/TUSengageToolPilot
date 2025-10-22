/**
 * TUS Data Submission Portal - Upload JavaScript
 * Handles file upload, drag & drop, and UI interactions
 */

class UploadManager {
    constructor() {
        this.init();
        this.loadInitialData();
    }

    init() {
        this.setupDropZone();
        this.setupFileInput();
        this.setupForm();
        this.setupEventListeners();
    }

    setupDropZone() {
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');

        // Click to browse
        dropZone.addEventListener('click', () => {
            fileInput.click();
        });

        // Drag and drop events
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.add('drag-over');
            });
        });

        ['dragleave', 'drop'].forEach(eventName => {
            dropZone.addEventListener(eventName, () => {
                dropZone.classList.remove('drag-over');
            });
        });

        dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFileSelect(files[0]);
            }
        });
    }

    setupFileInput() {
        const fileInput = document.getElementById('fileInput');
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelect(e.target.files[0]);
            }
        });
    }

    setupForm() {
        const form = document.getElementById('uploadForm');
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitForm();
        });
    }

    setupEventListeners() {
        // Template selection
        const templateSelect = document.getElementById('templateSelect');
        templateSelect.addEventListener('change', (e) => {
            this.onTemplateChange(e.target.value);
        });
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    handleFileSelect(file) {
        const fileInput = document.getElementById('fileInput');
        const dropZone = document.getElementById('dropZone');
        const fileInfoCard = document.getElementById('fileInfoCard');
        
        // Validate file type
        const allowedTypes = ['.xlsx', '.xls', '.csv', '.tsv'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!allowedTypes.includes(fileExtension)) {
            this.showError('Invalid file type. Please select an Excel, CSV, or TSV file.');
            return;
        }

        // Update file input
        const dt = new DataTransfer();
        dt.items.add(file);
        fileInput.files = dt.files;

        // Update drop zone appearance
        dropZone.classList.add('file-selected');
        dropZone.innerHTML = `
            <div class="drop-zone-content">
                <i class="fas fa-file-${this.getFileIcon(fileExtension)} fa-3x text-success mb-3"></i>
                <p class="mb-2"><strong>${file.name}</strong></p>
                <p class="text-muted">${this.formatFileSize(file.size)}</p>
                <small class="text-success">File selected - Click to change</small>
            </div>
        `;

        // Show file information
        this.displayFileInfo(file);
        fileInfoCard.classList.remove('d-none');
        fileInfoCard.classList.add('fade-in');
    }

    displayFileInfo(file) {
        const fileInfo = document.getElementById('fileInfo');
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        fileInfo.innerHTML = `
            <div class="file-info-item">
                <span class="file-info-label">
                    <i class="fas fa-file-${this.getFileIcon(fileExtension)} file-icon ${fileExtension.replace('.', '')} me-2"></i>
                    Filename:
                </span>
                <span class="file-info-value">${file.name}</span>
            </div>
            <div class="file-info-item">
                <span class="file-info-label">
                    <i class="fas fa-weight-hanging me-2"></i>
                    File Size:
                </span>
                <span class="file-info-value">${this.formatFileSize(file.size)}</span>
            </div>
            <div class="file-info-item">
                <span class="file-info-label">
                    <i class="fas fa-calendar me-2"></i>
                    Last Modified:
                </span>
                <span class="file-info-value">${new Date(file.lastModified).toLocaleString()}</span>
            </div>
            <div class="file-info-item">
                <span class="file-info-label">
                    <i class="fas fa-tag me-2"></i>
                    Type:
                </span>
                <span class="file-info-value">${this.getFileTypeDescription(fileExtension)}</span>
            </div>
        `;
    }

    getFileIcon(extension) {
        switch (extension) {
            case '.xlsx':
            case '.xls':
                return 'excel';
            case '.csv':
                return 'csv';
            case '.tsv':
                return 'alt';
            default:
                return 'alt';
        }
    }

    getFileTypeDescription(extension) {
        switch (extension) {
            case '.xlsx':
                return 'Excel Workbook (XLSX)';
            case '.xls':
                return 'Excel Workbook (XLS)';
            case '.csv':
                return 'Comma Separated Values (CSV)';
            case '.tsv':
                return 'Tab Separated Values (TSV)';
            default:
                return 'Unknown';
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    async submitForm() {
        const form = document.getElementById('uploadForm');
        const submitBtn = document.getElementById('submitBtn');
        const progressContainer = document.getElementById('progressContainer');
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        const resultArea = document.getElementById('resultArea');

        // Validate form
        if (!form.checkValidity()) {
            form.reportValidity();
            return;
        }

        const fileInput = document.getElementById('fileInput');
        if (!fileInput.files || fileInput.files.length === 0) {
            this.showError('Please select a file to upload.');
            return;
        }

        // Prepare form data
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        const templateId = document.getElementById('templateSelect').value;
        if (templateId) {
            formData.append('template_id', templateId);
        }

        // Update UI
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Uploading...';
        progressContainer.classList.remove('d-none');
        resultArea.innerHTML = '';

        try {
            const response = await fetch('/api/submission/upload', {
                method: 'POST',
                body: formData,
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });

            progressBar.style.width = '100%';
            progressText.textContent = 'Processing...';

            const result = await response.json();

            if (response.ok) {
                this.showSuccess(result);
                this.resetForm();
                this.loadRecentUploads(); // Refresh the list
            } else {
                this.showError(result.error || 'Upload failed', result.details);
            }

        } catch (error) {
            console.error('Upload error:', error);
            this.showError('Network error. Please check your connection and try again.');
        } finally {
            // Reset UI
            submitBtn.disabled = false;
            submitBtn.innerHTML = '<i class="fas fa-upload me-2"></i>Upload File';
            progressContainer.classList.add('d-none');
            progressBar.style.width = '0%';
        }
    }

    showSuccess(result) {
        const successModal = new bootstrap.Modal(document.getElementById('successModal'));
        const successContent = document.getElementById('successContent');
        
        successContent.innerHTML = `
            <div class="mb-3">
                <strong>File uploaded successfully!</strong>
            </div>
            <div class="row">
                <div class="col-6">
                    <strong>File:</strong><br>
                    <span class="text-muted">${result.file?.original_filename || 'Unknown'}</span>
                </div>
                <div class="col-6">
                    <strong>Status:</strong><br>
                    <span class="badge bg-success">${result.file?.upload_status || 'Completed'}</span>
                </div>
            </div>
            ${result.processing ? `
                <div class="mt-3">
                    <strong>Processing Results:</strong><br>
                    <div class="row">
                        <div class="col-6">
                            <small class="text-muted">Rows Processed:</small><br>
                            <span class="text-success">${result.processing.rows_processed || 0}</span>
                        </div>
                        <div class="col-6">
                            <small class="text-muted">Rows Failed:</small><br>
                            <span class="text-danger">${result.processing.rows_failed || 0}</span>
                        </div>
                    </div>
                </div>
            ` : ''}
        `;
        
        successModal.show();
    }

    showError(message, details = null) {
        const errorModal = new bootstrap.Modal(document.getElementById('errorModal'));
        const errorContent = document.getElementById('errorContent');
        
        errorContent.innerHTML = `
            <div class="mb-2">
                <strong>${message}</strong>
            </div>
            ${details ? `
                <div class="mt-2">
                    <strong>Details:</strong><br>
                    <small class="text-muted">${details}</small>
                </div>
            ` : ''}
        `;
        
        errorModal.show();
    }

    resetForm() {
        const form = document.getElementById('uploadForm');
        const dropZone = document.getElementById('dropZone');
        const fileInfoCard = document.getElementById('fileInfoCard');
        
        form.reset();
        dropZone.classList.remove('file-selected');
        dropZone.innerHTML = `
            <div class="drop-zone-content">
                <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
                <p class="mb-2"><strong>Drop your file here</strong></p>
                <p class="text-muted">or click to browse</p>
            </div>
        `;
        fileInfoCard.classList.add('d-none');
    }

    async loadInitialData() {
        await Promise.all([
            this.loadTemplates(),
            this.loadStats(),
            this.loadRecentUploads()
        ]);
    }

    async loadTemplates() {
        try {
            const response = await fetch('/api/submission/templates', {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.populateTemplates(data.templates || []);
            }
        } catch (error) {
            console.error('Error loading templates:', error);
        }
    }

    populateTemplates(templates) {
        const templateSelect = document.getElementById('templateSelect');
        const templatesList = document.getElementById('templatesList');
        
        // Populate select dropdown
        templateSelect.innerHTML = '<option value="">Choose a template...</option>';
        templates.forEach(template => {
            const option = document.createElement('option');
            option.value = template.template_id;
            option.textContent = `${template.template_name} (v${template.template_version})`;
            templateSelect.appendChild(option);
        });
        
        // Populate templates list
        if (templates.length === 0) {
            templatesList.innerHTML = '<p class="text-muted mb-0">No templates available</p>';
        } else {
            templatesList.innerHTML = templates.map(template => `
                <div class="template-item">
                    <div class="template-info">
                        <div class="template-name">${template.template_name}</div>
                        <div class="template-version">Version ${template.template_version}</div>
                    </div>
                    <a href="/api/submission/templates/download/${template.template_id}" 
                       class="btn btn-sm btn-outline-primary">
                        <i class="fas fa-download"></i>
                    </a>
                </div>
            `).join('');
        }
    }

    async loadStats() {
        try {
            const response = await fetch('/api/submission/uploads?limit=1000', {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.updateStats(data);
            }
        } catch (error) {
            console.error('Error loading stats:', error);
        }
    }

    updateStats(data) {
        const totalUploads = document.getElementById('totalUploads');
        const recentUploads = document.getElementById('recentUploads');
        
        const total = data.total || 0;
        const currentMonth = new Date().getMonth();
        const currentYear = new Date().getFullYear();
        
        const recent = (data.uploads || []).filter(upload => {
            const uploadDate = new Date(upload.uploaded_at);
            return uploadDate.getMonth() === currentMonth && 
                   uploadDate.getFullYear() === currentYear;
        }).length;
        
        totalUploads.textContent = total.toLocaleString();
        recentUploads.textContent = recent.toLocaleString();
    }

    async loadRecentUploads() {
        try {
            const response = await fetch('/api/submission/uploads?limit=5', {
                headers: {
                    'Authorization': `Bearer ${this.getAuthToken()}`
                }
            });
            
            if (response.ok) {
                const data = await response.json();
                this.populateRecentUploads(data.uploads || []);
            }
        } catch (error) {
            console.error('Error loading recent uploads:', error);
        }
    }

    populateRecentUploads(uploads) {
        const recentUploadsList = document.getElementById('recentUploadsList');
        
        if (uploads.length === 0) {
            recentUploadsList.innerHTML = '<p class="text-muted mb-0">No uploads yet</p>';
        } else {
            recentUploadsList.innerHTML = uploads.map(upload => `
                <div class="upload-item">
                    <div class="upload-info">
                        <div class="upload-filename">${upload.original_filename}</div>
                        <div class="upload-date">${new Date(upload.uploaded_at).toLocaleDateString()}</div>
                    </div>
                    <span class="upload-status ${upload.upload_status}">${upload.upload_status}</span>
                </div>
            `).join('');
        }
    }

    onTemplateChange(templateId) {
        // Could add template-specific validation or help text here
        console.log('Template selected:', templateId);
    }

    getAuthToken() {
        // In a real implementation, this would get the JWT token from localStorage, cookies, or session
        // For now, we'll need to implement proper authentication
        return localStorage.getItem('jwt_token') || 'demo_token';
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new UploadManager();
});

// Add some utility functions for better UX
window.addEventListener('beforeunload', (e) => {
    const form = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    
    if (fileInput && fileInput.files && fileInput.files.length > 0) {
        const confirmationMessage = 'You have selected a file but haven\'t uploaded it. Are you sure you want to leave?';
        e.returnValue = confirmationMessage;
        return confirmationMessage;
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + U for upload
    if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
        e.preventDefault();
        document.getElementById('fileInput').click();
    }
});