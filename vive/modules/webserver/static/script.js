document.addEventListener('DOMContentLoaded', () => {
    const statusDiv = document.getElementById('status');
    const restartBtn = document.getElementById('restartBtn');
    const stopBtn = document.getElementById('stopBtn');
    const showIpBtn = document.getElementById('showIpBtn');
    const serverIpDiv = document.getElementById('serverIp');
    const timetableBtn = document.getElementById('timetableBtn');
    const timetableData = document.getElementById('timetableData');

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

    restartBtn.addEventListener('click', async () => {
        const response = await fetch('/api/restart', { method: 'POST' });
        const data = await response.json();
        alert(data.message || 'Restart command sent!');
    });

    stopBtn.addEventListener('click', async () => {
        const response = await fetch('/api/stop', { method: 'POST' });
        const data = await response.json();
        alert(data.message || 'Stop command sent!');
    });

    showIpBtn.addEventListener('click', async () => {
        const response = await fetch('/api/server_ip');
        const data = await response.json();
        serverIpDiv.textContent = data.ip ? `Server IP: ${data.ip}` : 'Could not fetch IP.';
    });

    timetableBtn.addEventListener('click', getTimetable);

    async function getTimetable() {
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
        timetableBtn.textContent = 'Get Timetable';
    }

    function displayTimetable(timetable) {
        timetableData.innerHTML = '';
        if (!Array.isArray(timetable) || timetable.length === 0) {
            timetableData.innerHTML = '<p>No timetable data available.</p>';
            return;
        }
        const table = document.createElement('table');
        table.className = 'timetable-table';
        const thead = document.createElement('thead');
        const headerRow = document.createElement('tr');
        headerRow.innerHTML = '<th>Day</th><th>Lessons</th>';
        thead.appendChild(headerRow);
        table.appendChild(thead);
        const tbody = document.createElement('tbody');
        timetable.forEach(entry => {
            const row = document.createElement('tr');
            row.innerHTML = `<td>${entry.day}</td><td>${entry.lessons.join(', ')}</td>`;
            tbody.appendChild(row);
        });
        table.appendChild(tbody);
        timetableData.appendChild(table);
    }

    document.getElementById('stop-server').addEventListener('click', () => {
        fetch('/api/stop', { method: 'POST' })
            .then(response => response.json())
            .then(data => alert(data.message));
    });

    document.getElementById('open-webcam').addEventListener('click', () => {
        window.open('/webcam', '_blank');
    });
});