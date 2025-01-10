class SystemAPI {
    static async getStatus() {
        const response = await fetch('/api/system/status', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('api_token')}`
            }
        });
        if (!response.ok) throw new Error('Failed to fetch system status');
        return response.json();
    }

    static async getSnapshotStats() {
        const response = await fetch('/api/system/snapshots', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('api_token')}`
            }
        });
        if (!response.ok) throw new Error('Failed to fetch snapshot stats');
        return response.json();
    }
}

function formatBytes(bytes) {
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 Byte';
    const i = parseInt(Math.floor(Math.log(bytes) / Math.log(1024)));
    return Math.round(bytes / Math.pow(1024, i), 2) + ' ' + sizes[i];
}

function updateSystemStatus() {
    SystemAPI.getStatus().then(status => {
        // Update CPU gauge
        const cpuGauge = document.getElementById('cpu-gauge');
        if (cpuGauge) {
            cpuGauge.style.width = `${status.system.cpu_percent}%`;
            cpuGauge.textContent = `${status.system.cpu_percent}%`;
        }

        // Update memory usage
        const memoryUsage = document.getElementById('memory-usage');
        if (memoryUsage) {
            memoryUsage.innerHTML = `
                <div class="progress">
                    <div class="progress-bar" style="width: ${status.system.memory.percent}%">
                        ${status.system.memory.percent}%
                    </div>
                </div>
                <small class="text-muted">
                    ${formatBytes(status.system.memory.available)} available of 
                    ${formatBytes(status.system.memory.total)}
                </small>
            `;
        }

        // Update application stats
        document.getElementById('total-snapshots').textContent = status.application.snapshots.count;
        document.getElementById('total-storage').textContent = formatBytes(status.application.snapshots.size);
        document.getElementById('active-users').textContent = status.application.users.active;
        document.getElementById('active-webcams').textContent = status.application.webcams.active;
    }).catch(error => {
        console.error('Failed to update system status:', error);
    });
}

// Initialize system monitoring
document.addEventListener('DOMContentLoaded', function() {
    // Get API token if not present
    if (!localStorage.getItem('api_token')) {
        fetch('/api/auth/token', {
            method: 'POST',
            credentials: 'same-origin'
        })
        .then(response => response.json())
        .then(data => {
            localStorage.setItem('api_token', data.token);
        })
        .catch(error => {
            console.error('Failed to get API token:', error);
        });
    }

    // Start monitoring
    updateSystemStatus();
    setInterval(updateSystemStatus, 30000); // Update every 30 seconds
}); 