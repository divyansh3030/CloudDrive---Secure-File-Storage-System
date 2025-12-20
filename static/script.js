// static/script.js
const API_URL = "https://clouddrive-secure-file-storage-system.onrender.com/api";

// ADD THESE 3 LINES HERE ⬇️
// Search and filter variables
let allFiles = [];
let filteredFiles = [];
// Upload functionality
const fileInput = document.getElementById('fileInput');
const dropZone = document.getElementById('dropZone');
const filesList = document.getElementById('filesList');

dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    handleFiles(files);
});

fileInput.addEventListener('change', (e) => {
    handleFiles(e.target.files);
});

async function handleFiles(files) {
    for (let file of files) {
        await uploadFile(file);
    }
    loadFiles();
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    // Create progress indicator
    const progressId = 'progress-' + Date.now();
    showUploadProgress(file.name, progressId);

    try {
        const xhr = new XMLHttpRequest();
        
        // Track upload progress
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                updateUploadProgress(progressId, percentComplete);
            }
        });
        
        xhr.addEventListener('load', () => {
            if (xhr.status === 200) {
                completeUploadProgress(progressId);
                showNotification('File uploaded successfully!', 'success');
                setTimeout(() => loadFiles(), 1000);
            } else {
                failUploadProgress(progressId);
                const data = JSON.parse(xhr.responseText);
                showNotification(data.error || 'Upload failed', 'error');
            }
        });
        
        xhr.addEventListener('error', () => {
            failUploadProgress(progressId);
            showNotification('Network error during upload', 'error');
        });
        
        xhr.open('POST', `${API_URL}/upload`);
        xhr.withCredentials = true;
        xhr.send(formData);
        
    } catch (error) {
        failUploadProgress(progressId);
        showNotification('Network error: ' + error.message, 'error');
    }
}
async function loadFiles() {
    try {
        const response = await fetch(`${API_URL}/files`, {
            credentials: 'include'  // Important for sessions
        });

        if (response.status === 401) {
            window.location.href = '/login';
            return;
        }

        const data = await response.json();

        if (response.ok) {
            displayFiles(data.files);
        } else {
            filesList.innerHTML = '<p class="loading">Error loading files</p>';
        }
    } catch (error) {
        filesList.innerHTML = '<p class="loading">Network error</p>';
    }
}

function displayFiles(files) {
    allFiles = files; // Store all files globally
    
    if (files.length === 0) {
        filesList.innerHTML = '<p class="loading">No files uploaded yet</p>';
        return;
    }

    filesList.innerHTML = files.map(file => `
        <div class="file-item" data-filename="${file.filename.toLowerCase()}" data-type="${getFileType(file.filename)}">
            <div class="file-info">
                <div class="file-icon">${getFileIcon(file.filename)}</div>
                <div class="file-details">
                    <h4>${file.filename}</h4>
                    <p>${formatFileSize(file.size)} • ${formatDate(file.last_modified)}</p>
                </div>
            </div>
            <div class="file-actions">
                <button class="btn-icon" onclick="previewFile('${file.key}', '${file.filename}')" title="Preview">
                    👁️
                </button>
                <button class="btn-icon" onclick="downloadFile('${file.key}', '${file.filename}')" title="Download">
                    ⬇️
                </button>
                <button class="btn-icon" onclick="shareFile('${file.key}', '${file.filename}')" title="Share">
                    🔗
                </button>
                <button class="btn-icon" onclick="deleteFile('${file.key}')" title="Delete">
                    🗑️
                </button>
            </div>
        </div>
    `).join('');
    
    updateStorageDisplay();
}

async function downloadFile(key, filename) {
    try {
        window.location.href = `${API_URL}/download/${key}`;
        showNotification('Downloading ' + filename, 'success');
    } catch (error) {
        showNotification('Download failed', 'error');
    }
}

async function deleteFile(key) {
    if (!confirm('Are you sure you want to delete this file?')) return;

    try {
        const response = await fetch(`${API_URL}/delete/${key}`, {
            method: 'DELETE',
            credentials: 'include'  // Important for sessions
        });

        if (response.ok) {
            showNotification('File deleted successfully', 'success');
            loadFiles();
        } else if (response.status === 401) {
            showNotification('Session expired. Please login again.', 'error');
            setTimeout(() => window.location.href = '/login', 2000);
        } else {
            showNotification('Delete failed', 'error');
        }
    } catch (error) {
        showNotification('Network error', 'error');
    }
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
}

function showNotification(message, type) {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification show ${type}`;
    setTimeout(() => {
        notification.classList.remove('show');
    }, 3000);
}

// Load files on page load
loadFiles();
// Helper functions for file types and icons
function getFileType(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    if (['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp'].includes(ext)) return 'image';
    if (['pdf'].includes(ext)) return 'pdf';
    if (['doc', 'docx'].includes(ext)) return 'document';
    if (['zip', 'rar', '7z'].includes(ext)) return 'archive';
    if (['txt'].includes(ext)) return 'text';
    return 'other';
}

function getFileIcon(filename) {
    const type = getFileType(filename);
    const icons = {
        'image': '🖼️',
        'pdf': '📄',
        'document': '📝',
        'archive': '📦',
        'text': '📃',
        'other': '📄'
    };
    return icons[type];
}

// Search functionality
function searchFiles() {
    const searchTerm = document.getElementById('searchInput').value.toLowerCase();
    const fileItems = document.querySelectorAll('.file-item');
    
    fileItems.forEach(item => {
        const filename = item.dataset.filename;
        if (filename.includes(searchTerm)) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}

// Filter functionality
let currentFilter = 'all';
function filterFiles(type) {
    currentFilter = type;
    const fileItems = document.querySelectorAll('.file-item');
    const filterBtns = document.querySelectorAll('.filter-btn');
    
    // Update active button
    filterBtns.forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');
    
    fileItems.forEach(item => {
        const fileType = item.dataset.type;
        if (type === 'all' || fileType === type) {
            item.style.display = 'flex';
        } else {
            item.style.display = 'none';
        }
    });
}

// Update storage display
function updateStorageDisplay() {
    const totalSize = allFiles.reduce((sum, file) => sum + file.size, 0);
    const totalSizeMB = (totalSize / (1024 * 1024)).toFixed(2);
    const fileCount = allFiles.length;
    const limitMB = 200;
    const percentage = Math.min((totalSizeMB / limitMB) * 100, 100);
    
    document.getElementById('storageUsed').textContent = `${totalSizeMB} MB`;
    document.getElementById('fileCount').textContent = fileCount;
    document.getElementById('storageProgress').style.width = `${percentage}%`;
    
    // Change color based on usage
    const progressBar = document.getElementById('storageProgress');
    if (percentage > 80) {
        progressBar.style.background = 'linear-gradient(90deg, #ff6b6b, #ee5a6f)';
    } else if (percentage > 50) {
        progressBar.style.background = 'linear-gradient(90deg, #ffd93d, #f39c12)';
    } else {
        progressBar.style.background = 'linear-gradient(90deg, #667eea, #764ba2)';
    }
}

// File Preview functionality
async function previewFile(key, filename) {
    const fileType = getFileType(filename);
    const modal = document.getElementById('previewModal');
    const container = document.getElementById('previewContainer');
    const title = document.getElementById('previewTitle');
    
    title.textContent = filename;
    modal.style.display = 'flex';
    
    if (fileType === 'image') {
        container.innerHTML = `<img src="${API_URL}/download/${key}" alt="${filename}" style="max-width: 100%; max-height: 70vh; border-radius: 12px;">`;
    } else if (fileType === 'pdf') {
        container.innerHTML = `<iframe src="${API_URL}/download/${key}" style="width: 100%; height: 70vh; border: none; border-radius: 12px;"></iframe>`;
    } else {
        container.innerHTML = `<div style="text-align: center; padding: 40px;">
            <p style="font-size: 3rem; margin-bottom: 20px;">${getFileIcon(filename)}</p>
            <p style="color: #666;">Preview not available for this file type</p>
            <button class="btn-primary" onclick="downloadFile('${key}', '${filename}')" style="margin-top: 20px;">Download File</button>
        </div>`;
    }
}

function closePreview() {
    document.getElementById('previewModal').style.display = 'none';
    document.getElementById('previewContainer').innerHTML = '';
}

// Upload progress functions
function showUploadProgress(filename, progressId) {
    const uploadSection = document.querySelector('.upload-section');
    const progressHtml = `
        <div class="upload-progress" id="${progressId}">
            <div class="progress-info">
                <span class="progress-filename">📤 ${filename}</span>
                <span class="progress-percent">0%</span>
            </div>
            <div class="progress-bar-container">
                <div class="progress-bar" style="width: 0%"></div>
            </div>
        </div>
    `;
    uploadSection.insertAdjacentHTML('beforeend', progressHtml);
}

function updateUploadProgress(progressId, percent) {
    const progressElement = document.getElementById(progressId);
    if (progressElement) {
        const bar = progressElement.querySelector('.progress-bar');
        const percentText = progressElement.querySelector('.progress-percent');
        bar.style.width = percent + '%';
        percentText.textContent = Math.round(percent) + '%';
    }
}

function completeUploadProgress(progressId) {
    const progressElement = document.getElementById(progressId);
    if (progressElement) {
        progressElement.style.background = 'linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%)';
        setTimeout(() => progressElement.remove(), 2000);
    }
}

function failUploadProgress(progressId) {
    const progressElement = document.getElementById(progressId);
    if (progressElement) {
        progressElement.style.background = 'linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%)';
        setTimeout(() => progressElement.remove(), 3000);
    }
}

// File Sharing functionality
async function shareFile(key, filename) {
    const hours = prompt('Enter link expiry time in hours (default: 24):', '24');
    if (!hours) return;
    
    try {
        const response = await fetch(`${API_URL}/share/${key}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ expiry_hours: parseInt(hours) })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            const modal = document.getElementById('previewModal');
            const container = document.getElementById('previewContainer');
            const title = document.getElementById('previewTitle');
            
            title.textContent = '🔗 Share Link Generated';
            container.innerHTML = `
                <div style="padding: 20px; text-align: center;">
                    <p style="margin-bottom: 15px; color: #666;">Share this link with anyone:</p>
                    <div style="background: #f8f9fa; padding: 15px; border-radius: 10px; margin-bottom: 15px; word-break: break-all;">
                        <code style="color: #667eea; font-size: 0.9rem;">${data.share_link}</code>
                    </div>
                    <p style="font-size: 0.85rem; color: #999; margin-bottom: 20px;">Expires: ${new Date(data.expiry).toLocaleString()}</p>
                    <button class="btn-primary" onclick="copyToClipboard('${data.share_link}')">📋 Copy Link</button>
                </div>
            `;
            modal.style.display = 'flex';
        } else {
            showNotification(data.error || 'Failed to generate share link', 'error');
        }
    } catch (error) {
        showNotification('Error: ' + error.message, 'error');
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(() => {
        showNotification('Link copied to clipboard!', 'success');
    }).catch(() => {
        showNotification('Failed to copy link', 'error');
    });
}