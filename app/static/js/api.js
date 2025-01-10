class WebcamAPI {
    static async getWebcams() {
        const response = await fetch('/api/webcams');
        if (!response.ok) throw new Error('Failed to fetch webcams');
        return response.json();
    }

    static async getUserWebcams() {
        const response = await fetch('/api/webcams/user');
        if (!response.ok) throw new Error('Failed to fetch user webcams');
        return response.json();
    }

    static async captureWebcam(webcamId) {
        const response = await fetch(`/api/webcams/${webcamId}/capture`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        if (!response.ok) throw new Error('Failed to capture webcam');
        return response.json();
    }
}

// Update webcam cards with live data
async function updateWebcamStatus() {
    try {
        const userWebcams = await WebcamAPI.getUserWebcams();
        userWebcams.forEach(webcam => {
            const card = document.querySelector(`#webcam-${webcam.id}`);
            if (card) {
                const statusElement = card.querySelector('.webcam-status');
                if (statusElement) {
                    let status = 'Manual capture only';
                    if (webcam.interval_hours) {
                        status = `Next capture: ${new Date(webcam.next_capture).toLocaleString()}`;
                    }
                    statusElement.textContent = status;
                }
            }
        });
    } catch (error) {
        console.error('Failed to update webcam status:', error);
    }
}

// Initialize webcam cards
document.addEventListener('DOMContentLoaded', function() {
    // Set up capture buttons
    document.querySelectorAll('.capture-now').forEach(button => {
        button.addEventListener('click', async function(e) {
            e.preventDefault();
            const webcamId = this.dataset.webcamId;
            try {
                this.disabled = true;
                this.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Capturing...';
                
                await WebcamAPI.captureWebcam(webcamId);
                await updateWebcamStatus();
                
                this.innerHTML = 'Capture Now';
                this.disabled = false;
            } catch (error) {
                console.error('Capture failed:', error);
                this.innerHTML = 'Capture Failed';
                setTimeout(() => {
                    this.innerHTML = 'Capture Now';
                    this.disabled = false;
                }, 2000);
            }
        });
    });

    // Update status periodically
    updateWebcamStatus();
    setInterval(updateWebcamStatus, 60000); // Update every minute
}); 