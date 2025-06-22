document.addEventListener('DOMContentLoaded', () => {
    const loginBtn = document.getElementById('loginBtn');
    const authSection = document.getElementById('auth-section');
    const timetableSection = document.getElementById('timetable-section');
    const statusDiv = document.getElementById('status');

    // Check server health on load
    checkHealth();

    async function checkHealth() {
        try {
            const response = await fetch('/api/health');
            if (response.ok) {
                const data = await response.json();
                if (data.status === 'healthy') {
                    statusDiv.textContent = 'Connected';
                    statusDiv.className = 'status connected';
                } else {
                    throw new Error('Not healthy');
                }
            } else {
                 throw new Error(`HTTP error! status: ${response.status}`);
            }
        } catch (error) {
            statusDiv.textContent = 'Disconnected';
            statusDiv.className = 'status disconnected';
        }
    }

    // Placeholder login
    loginBtn.addEventListener('click', async () => {
        // Simulate an API call
        try {
            const response = await fetch('/api/auth', { method: 'POST' });
            if(response.ok) {
                const data = await response.json();
                if (data.authenticated) {
                    authSection.style.display = 'none';
                    timetableSection.style.display = 'block';
                } else {
                    alert('Authentication failed!');
                }
            } else {
                alert('Authentication request failed!');
            }
        } catch (e) {
            alert('Error during authentication!');
        }
    });
});

async function getTimetable() {
    const timetableBtn = document.getElementById('timetableBtn');
    const timetableData = document.getElementById('timetableData');
    
    timetableBtn.disabled = true;
    timetableBtn.textContent = 'Loading...';
    timetableData.innerHTML = '';

    try {
        const response = await fetch('/api/untis/timetable');
        const data = await response.json();
        
        if (data.status === 'success') {
            displayTimetable(data.data);
        } else {
            timetableData.innerHTML = `<p style="color: #ff3b30;">Error: ${data.message}</p>`;
        }
    } catch (error) {
        timetableData.innerHTML = `<p style="color: #ff3b30;">Connection error: ${error.message}</p>`;
    }
    
    timetableBtn.disabled = false;
    timetableBtn.textContent = 'Get Timetable (Auto-Login)';
}

function displayTimetable(timetable) {
    const timetableData = document.getElementById('timetableData');
    timetableData.innerHTML = ''; // Clear previous data

    if (!timetable || timetable.length === 0) {
        timetableData.innerHTML = '<p>No lessons found for tomorrow.</p>';
        return;
    }

    timetable.forEach(entry => {
        const entryDiv = document.createElement('div');
        entryDiv.className = 'timetable-entry';
        
        let content = `
            <p><strong>${entry.start_time} - ${entry.end_time}</strong></p>
            <p><strong>Subject:</strong> ${entry.subject}</p>
        `;
        if(entry.teacher_id) content += `<p><strong>Teacher:</strong> ${entry.teacher_id}</p>`;
        if(entry.room_id) content += `<p><strong>Room:</strong> ${entry.room_id}</p>`;
        if(entry.is_cancelled) content += `<p style="color: #ff3b30; font-weight: bold;">CANCELLED</p>`;

        entryDiv.innerHTML = content;
        timetableData.appendChild(entryDiv);
    });
}