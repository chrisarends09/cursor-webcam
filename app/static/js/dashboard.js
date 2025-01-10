let snapshotChart = null;

async function updateSnapshotChart() {
    try {
        const stats = await SystemAPI.getSnapshotStats();
        const dates = Object.keys(stats.by_date).sort();
        const counts = dates.map(date => stats.by_date[date].count);
        
        if (!snapshotChart) {
            const ctx = document.getElementById('snapshot-chart').getContext('2d');
            snapshotChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: dates,
                    datasets: [{
                        label: 'Snapshots per Day',
                        data: counts,
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            }
                        }
                    }
                }
            });
        } else {
            snapshotChart.data.labels = dates;
            snapshotChart.data.datasets[0].data = counts;
            snapshotChart.update();
        }
    } catch (error) {
        console.error('Failed to update snapshot chart:', error);
    }
}

// Update chart periodically
document.addEventListener('DOMContentLoaded', function() {
    updateSnapshotChart();
    setInterval(updateSnapshotChart, 300000); // Update every 5 minutes
}); 