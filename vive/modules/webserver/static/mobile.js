document.addEventListener('DOMContentLoaded', () => {
    const connectionStatus = document.getElementById('connectionStatus');
    const statusText = document.getElementById('statusText');
    const indicatorDot = document.querySelector('.indicator-dot');
    const uploadButton = document.getElementById('uploadButton');
    const fileInput = document.getElementById('fileInput');
    const uploadStatus = document.getElementById('uploadStatus');

    // 1. Health Check
    async function checkServerHealth() {
        try {
            const response = await fetch('/api/health');
            if (response.ok) {
                statusText.textContent = 'Connected';
                indicatorDot.classList.add('connected');
            } else {
                throw new Error('Server not healthy');
            }
        } catch (error) {
            statusText.textContent = 'Offline';
            indicatorDot.classList.remove('connected');
        }
    }

    // Check health immediately and then every 3 seconds
    checkServerHealth();
    setInterval(checkServerHealth, 3000);

    // 2. Upload Logic
    uploadButton.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', async (event) => {
        const file = event.target.files[0];
        if (!file) {
            return;
        }

        uploadStatus.textContent = 'Uploading...';
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (response.ok && result.success) {
                uploadStatus.textContent = 'Upload successful! Processing on PC.';
            } else {
                uploadStatus.textContent = `Upload failed: ${result.error || 'Unknown error'}`;
            }
        } catch (error) {
            uploadStatus.textContent = 'Upload failed: Could not connect to server.';
        }
        
        // Clear the input value to allow re-uploading the same file
        fileInput.value = ''; 
        
        // Hide the status message after a few seconds
        setTimeout(() => {
            uploadStatus.textContent = '';
        }, 5000);
    });
});