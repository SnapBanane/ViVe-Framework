let isLoggedIn = false;

// Check server health on load
window.onload = function() {
    checkHealth();
    listFiles();
};

async function checkHealth() {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        
        if (data.status === 'healthy') {
            document.getElementById('status').textContent = 'Connected';
            document.getElementById('status').className = 'status connected';
        }
    } catch (error) {
        document.getElementById('status').textContent = 'Disconnected';
        document.getElementById('status').className = 'status disconnected';
    }
}

async function untisLogin() {
    const loginBtn = document.getElementById('loginBtn');
    const loginStatus = document.getElementById('loginStatus');
    
    loginBtn.disabled = true;
    loginBtn.textContent = 'Logging in...';
    loginStatus.innerHTML = '<span class="loading">Connecting to Untis...</span>';
    
    try {
        const response = await fetch('/api/untis/login', {
            method: 'POST'
        });
        const data = await response.json();
        
        if (data.status === 'success') {
            loginStatus.innerHTML = `<span class="success">${data.message}</span>`;
            isLoggedIn = true;
            document.getElementById('timetableBtn').disabled = false;
            loginBtn.textContent = 'Logged In';
        } else {
            loginStatus.innerHTML = `<span class="error">Error: ${data.message}</span>`;
            loginBtn.disabled = false;
            loginBtn.textContent = 'Login to Untis';
        }
    } catch (error) {
        loginStatus.innerHTML = `<span class="error">Connection error: ${error.message}</span>`;
        loginBtn.disabled = false;
        loginBtn.textContent = 'Login to Untis';
    }
}

async function getTimetable() {
    const timetableBtn = document.getElementById('timetableBtn');
    const timetableData = document.getElementById('timetableData');
    
    timetableBtn.disabled = true;
    timetableBtn.textContent = 'Connecting & Loading...';
    timetableData.innerHTML = '<span class="loading">Logging into Untis and loading timetable...</span>';
    
    try {
        const response = await fetch('/api/untis/timetable');
        const data = await response.json();
        
        if (data.status === 'success') {
            displayTimetable(data.data);
            timetableBtn.textContent = 'Refresh Timetable';
            timetableData.innerHTML = `<div class="success-message">✓ ${data.message}</div>` + timetableData.innerHTML;
        } else {
            timetableData.innerHTML = `<span class="error">Error: ${data.message}</span>`;
            timetableBtn.textContent = 'Get Timetable (Auto-Login)';
        }
    } catch (error) {
        timetableData.innerHTML = `<span class="error">Connection error: ${error.message}</span>`;
        timetableBtn.textContent = 'Get Timetable (Auto-Login)';
    }
    
    timetableBtn.disabled = false;
}

function displayTimetable(timetable) {
    const timetableData = document.getElementById('timetableData');
    
    if (timetable.length === 0) {
        timetableData.innerHTML += '<p>No lessons found for tomorrow.</p>';
        return;
    }
    
    let html = '<h3>Tomorrow\'s Timetable:</h3>';
    timetable.forEach(entry => {
        html += `
            <div class="timetable-entry">
                <strong>${entry.start_time} - ${entry.end_time}</strong><br>
                Subject: ${entry.subject}<br>
                ${entry.teacher_id ? `Teacher ID: ${entry.teacher_id}<br>` : ''}
                ${entry.room_id ? `Room ID: ${entry.room_id}` : ''}
                ${entry.is_cancelled ? '<span class="cancelled">CANCELLED</span>' : ''}
            </div>
        `;
    });
    
    timetableData.innerHTML += html;
}

async function uploadFiles() {
    const fileInput = document.getElementById('fileInput');
    const uploadStatus = document.getElementById('uploadStatus');
    
    if (fileInput.files.length === 0) {
        uploadStatus.innerHTML = '<span class="error">Please select files to upload</span>';
        return;
    }
    
    uploadStatus.innerHTML = '<span class="loading">Uploading files...</span>';
    
    for (let file of fileInput.files) {
        const formData = new FormData();
        formData.append('file', file);
        
        try {
            const response = await fetch('/api/upload', {
                method: 'POST',
                body: formData
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                uploadStatus.innerHTML += `<br><span class="success">✓ ${file.name} uploaded</span>`;
            } else {
                uploadStatus.innerHTML += `<br><span class="error">✗ ${file.name}: ${data.message}</span>`;
            }
        } catch (error) {
            uploadStatus.innerHTML += `<br><span class="error">✗ ${file.name}: ${error.message}</span>`;
        }
    }
    
    // Refresh file list after upload
    setTimeout(listFiles, 1000);
}

async function listFiles() {
    const fileList = document.getElementById('fileList');
    fileList.innerHTML = '<span class="loading">Loading files...</span>';
    
    try {
        const response = await fetch('/api/files');
        const data = await response.json();
        
        if (data.status === 'success') {
            if (data.data.length === 0) {
                fileList.innerHTML = '<p>No files uploaded yet.</p>';
            } else {
                let html = '<h4>Uploaded Files:</h4>';
                data.data.forEach(filename => {
                    html += `<div class="file-item">${filename}</div>`;
                });
                fileList.innerHTML = html;
            }
        } else {
            fileList.innerHTML = `<span class="error">Error: ${data.message}</span>`;
        }
    } catch (error) {
        fileList.innerHTML = `<span class="error">Connection error: ${error.message}</span>`;
    }
}