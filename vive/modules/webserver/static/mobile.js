document.addEventListener('DOMContentLoaded', () => {
    const connectionStatus = document.getElementById('connectionStatus');
    const statusText = document.getElementById('statusText');
    const indicatorDot = document.querySelector('.indicator-dot');
    const uploadButton = document.getElementById('uploadButton');
    const fileInput = document.getElementById('fileInput');
    const uploadStatus = document.getElementById('uploadStatus');
    const deviceStatus = document.getElementById('deviceStatus'); // New element for device status

    let deviceId = localStorage.getItem('deviceId');
    let deviceStatusInterval = null;

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

    // 2. Device Registration and Status Checking
    async function registerDevice() {
        try {
            const response = await fetch('/api/register_device', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ name: 'Mobile Device' }) // You can make this name dynamic later
            });
            const result = await response.json();
            if (result.success && result.device_id) {
                deviceId = result.device_id;
                localStorage.setItem('deviceId', deviceId);
                console.log('Device registered with ID:', deviceId);
                startDeviceStatusPolling();
            } else {
                deviceStatus.textContent = 'Error: Could not register device.';
            }
        } catch (error) {
            deviceStatus.textContent = 'Error: Could not connect to server to register.';
        }
    }

    async function checkDeviceStatus() {
        if (!deviceId) return;

        try {
            const response = await fetch(`/api/device_status/${deviceId}`);
            const result = await response.json();

            if (result.status === 'approved') {
                deviceStatus.textContent = 'Device Approved';
                deviceStatus.classList.add('approved');
                uploadButton.style.display = 'block'; // Show upload button
                stopDeviceStatusPolling(); // Stop checking once approved
            } else {
                deviceStatus.textContent = 'Waiting for Admin Approval...';
                deviceStatus.classList.remove('approved');
                uploadButton.style.display = 'none'; // Hide upload button
            }
        } catch (error) {
            console.error('Error checking device status:', error);
            deviceStatus.textContent = 'Could not verify device status.';
        }
    }

    function startDeviceStatusPolling() {
        if (deviceStatusInterval) return; // Prevent multiple intervals
        checkDeviceStatus(); // Check immediately
        deviceStatusInterval = setInterval(checkDeviceStatus, 3000); // Then every 3 seconds
    }

    function stopDeviceStatusPolling() {
        clearInterval(deviceStatusInterval);
        deviceStatusInterval = null;
    }

    // Initial setup
    if (!deviceId) {
        registerDevice();
    } else {
        startDeviceStatusPolling();
    }

    // 3. Upload Logic
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
        formData.append('device_id', deviceId); // Add device ID to the form data

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