// static/script.js
const API_URL = "https://clouddrive-secure-file-storage-system.onrender.com/api";


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

    try {
        const response = await fetch(`${API_URL}/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            showNotification('File uploaded successfully!', 'success');
        } else {
            showNotification(data.error || 'Upload failed', 'error');
        }
    } catch (error) {
        showNotification('Network error: ' + error.message, 'error');
    }
}

async function loadFiles() {
    try {
        const response = await fetch(`${API_URL}/files`);
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
    if (files.length === 0) {
        filesList.innerHTML = '<p class="loading">No files uploaded yet</p>';
        return;
    }

    filesList.innerHTML = files.map(file => `
        <div class="file-item">
            <div class="file-info">
                <div class="file-icon">📄</div>
                <div class="file-details">
                    <h4>${file.filename}</h4>
                    <p>${formatFileSize(file.size)} • ${formatDate(file.last_modified)}</p>
                </div>
            </div>
            <div class="file-actions">
                <button class="btn-icon" onclick="downloadFile('${file.key}', '${file.filename}')" title="Download">
                    ⬇️
                </button>
                <button class="btn-icon" onclick="deleteFile('${file.key}')" title="Delete">
                    🗑️
                </button>
            </div>
        </div>
    `).join('');
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
            method: 'DELETE'
        });

        if (response.ok) {
            showNotification('File deleted successfully', 'success');
            loadFiles();
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