document.addEventListener('DOMContentLoaded', function () {
    // Initialize all charts on the page
    const charts = document.querySelectorAll('.chart-container canvas');

    charts.forEach(chartElement => {
        const ctx = chartElement.getContext('2d');
        const chartType = chartElement.dataset.chartType || 'line';
        const chartData = JSON.parse(chartElement.dataset.chartData || '{}');

        new Chart(ctx, {
            type: chartType,
            data: chartData,
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    });
});