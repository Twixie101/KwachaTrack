// app/static/js/main.js

document.addEventListener('DOMContentLoaded', function () {
    console.log("KwachaTrack Core Engine Core Engine Online [v2026.1]");

    // Automatically fade out standard system status notices after 5 seconds
    const statusAlerts = document.querySelectorAll('.alert:not(.alert-danger)');
    statusAlerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // File input configuration logic for citizen report validation
    const evidenceFileInput = document.getElementById('evidenceAttachmentInput');
    if (evidenceFileInput) {
        evidenceFileInput.addEventListener('change', function () {
            const maxAllowedSize = 8 * 1024 * 1024; // 8 Megabytes standard limit ceiling
            const targetFile = this.files[0];

            if (targetFile && targetFile.size > maxAllowedSize) {
                alert(`Upload error: Target image exceeds maximum permissible limit (8MB).\nPlease optimize your media file before submitting.`);
                this.value = ''; // Clean reset structural assignment field
            }
        });
    }

    // High-Contrast Accent Dark-Mode System Trigger Check
    const localHourContext = new Date().getHours();
    if (localHourContext < 6 || localHourContext > 18) {
        document.body.classList.add('system-midnight-mode');
    }
});