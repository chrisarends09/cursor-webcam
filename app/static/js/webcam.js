document.addEventListener('DOMContentLoaded', function() {
    // Confirm webcam deletion
    document.querySelectorAll('.delete-webcam').forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to remove this webcam?')) {
                e.preventDefault();
            }
        });
    });

    // Interval selection handling
    document.querySelectorAll('.interval-select').forEach(select => {
        select.addEventListener('change', function() {
            const nextCapture = this.closest('.webcam-card').querySelector('.next-capture');
            if (this.value) {
                const hours = parseInt(this.value);
                const next = new Date(Date.now() + hours * 60 * 60 * 1000);
                nextCapture.textContent = `Next capture: ${next.toLocaleString()}`;
            } else {
                nextCapture.textContent = 'Manual capture only';
            }
        });
    });

    // Add loading state to capture buttons
    document.querySelectorAll('.capture-now').forEach(button => {
        button.addEventListener('click', function() {
            this.disabled = true;
            this.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Capturing...';
        });
    });
}); 