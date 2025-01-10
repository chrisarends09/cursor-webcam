class UserAPI {
    static async getProfile() {
        const response = await fetch('/api/user/profile');
        if (!response.ok) throw new Error('Failed to fetch profile');
        return response.json();
    }

    static async updateProfile(data) {
        const response = await fetch('/api/user/profile', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to update profile');
        return response.json();
    }

    static async getWebcamStats() {
        const response = await fetch('/api/user/webcams/stats');
        if (!response.ok) throw new Error('Failed to fetch webcam stats');
        return response.json();
    }
}

document.addEventListener('DOMContentLoaded', function() {
    // Update profile form
    const profileForm = document.getElementById('profile-form');
    if (profileForm) {
        profileForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const submitButton = this.querySelector('button[type="submit"]');
            submitButton.disabled = true;
            
            try {
                const formData = new FormData(this);
                const data = {
                    email: formData.get('email')
                };
                
                if (formData.get('password')) {
                    data.password = formData.get('password');
                }
                
                await UserAPI.updateProfile(data);
                showAlert('Profile updated successfully', 'success');
            } catch (error) {
                showAlert('Failed to update profile', 'danger');
            } finally {
                submitButton.disabled = false;
            }
        });
    }

    // Update webcam statistics
    async function updateStats() {
        try {
            const stats = await UserAPI.getWebcamStats();
            document.getElementById('total-webcams').textContent = stats.total_webcams;
            document.getElementById('active-schedules').textContent = stats.active_schedules;
            document.getElementById('captures-today').textContent = stats.captures_today;
            
            const nextCapturesList = document.getElementById('next-captures');
            if (nextCapturesList) {
                nextCapturesList.innerHTML = stats.next_captures
                    .map(capture => `
                        <li class="list-group-item">
                            ${capture.webcam_name}: 
                            ${new Date(capture.next_capture).toLocaleString()}
                        </li>
                    `)
                    .join('');
            }
        } catch (error) {
            console.error('Failed to update stats:', error);
        }
    }

    // Update stats periodically
    updateStats();
    setInterval(updateStats, 60000);
});

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    setTimeout(() => {
        alertDiv.remove();
    }, 5000);
} 