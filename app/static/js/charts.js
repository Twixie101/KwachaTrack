// app/static/js/charts.js

document.addEventListener('DOMContentLoaded', function () {
    // 1. Structural Distribution Doughnut Chart Setup
    const statusCtx = document.getElementById('statusChart');
    if (statusCtx) {
        // Data parameters injected via DOM context variables parsed safely from Jinja
        const completed = parseInt(statusCtx.getAttribute('data-completed')) || 0;
        const inProgress = parseInt(statusCtx.getAttribute('data-inprogress')) || 0;
        const abandoned = parseInt(statusCtx.getAttribute('data-abandoned')) || 0;

        new Chart(statusCtx, {
            type: 'doughnut',
            data: {
                labels: ['Completed', 'In Progress', 'Abandoned'],
                datasets: [{
                    data: [completed, inProgress, abandoned],
                    backgroundColor: ['#009e49', '#ef7d12', '#de2010'],
                    borderWidth: 0,
                    hoverOffset: 4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { color: '#e0e0e0', font: { family: 'Inter', size: 12 } }
                    }
                }
            }
        });
    }

    // 2. "Follow the Money" Mixed Variable Timeline Chart
    const moneyTrackerCtx = document.getElementById('followMoneyChart');
    if (moneyTrackerCtx) {
        // Extract evaluation data vectors parsed from data attributes
        const dates = JSON.parse(moneyTrackerCtx.getAttribute('data-dates') || '[]');
        const disbursements = JSON.parse(moneyTrackerCtx.getAttribute('data-disbursements') || '[]');
        const progressMilestones = JSON.parse(moneyTrackerCtx.getAttribute('data-progress') || '[]');

        new Chart(moneyTrackerCtx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [{
                    label: 'Cumulative Disbursals (ZMW)',
                    data: disbursements,
                    borderColor: '#009e49',
                    backgroundColor: 'rgba(0, 184, 148, 0.1)',
                    fill: true,
                    yAxisID: 'yFinancials',
                    tension: 0.2
                }, {
                    label: 'Physical Infrastructure Milestones (%)',
                    data: progressMilestones,
                    borderColor: '#ef7d12',
                    backgroundColor: 'rgba(239, 125, 18, 0.2)',
                    type: 'bar',
                    yAxisID: 'yPercentage',
                    barThickness: 15
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { ticks: { color: '#c5c6c7' }, grid: { color: 'rgba(255,255,255,0.05)' } },
                    yFinancials: {
                        type: 'linear',
                        position: 'left',
                        ticks: { color: '#009e49' },
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        title: { display: true, text: 'Kwacha Transactions', color: '#009e49' }
                    },
                    yPercentage: {
                        type: 'linear',
                        position: 'right',
                        min: 0,
                        max: 100,
                        ticks: { color: '#ef7d12' },
                        grid: { drawOnChartArea: false }, // Prevent gridline overlapping
                        title: { display: true, text: 'Physical Execution %', color: '#ef7d12' }
                    }
                },
                plugins: {
                    legend: { labels: { color: '#e0e0e0', font: { family: 'Inter' } } }
                }
            }
        });
    }
});