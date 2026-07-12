// app/static/js/map.js

document.addEventListener('DOMContentLoaded', function () {
    const mapContainer = document.getElementById('zambiaCdfMap');

    if (!mapContainer) return;

    // 1. DEFINE ZAMBIA'S GEOGRAPHIC BOUNDARIES (South-West and North-East corners)
    // These coordinates form a bounding box around Zambia's borders
    const southWest = L.latLng([-18.3, 21.8]);
    const northEast = L.latLng([-8.2, 33.9]);
    const zambiaBounds = L.latLngBounds(southWest, northEast);

    // 2. INITIALIZE MAP WITH RESTRICTIONS
    const map = L.map('zambiaCdfMap', {
        center: [-13.1339, 27.8493], // Centers on Zambia
        zoom: 6,                      // Optimal starting view for Zambia
        minZoom: 6,                   // Prevents zooming out past country level
        maxZoom: 16,                  // Allows deep zoom into constituencies
        maxBounds: zambiaBounds,      // Locks the map view inside this box
        maxBoundsViscosity: 1.0       // 1.0 means the map hard-bounces back if they try to pan out
    });

    // Apply high-impact, dark-mode geospatial tile layer
    L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>',
        subdomains: 'abcd',
        maxZoom: 20
    }).addTo(map);

    // Fetch dynamic constituency spatial tracking payloads from the REST API
    fetch('/api/v1/constituencies')
        .then(response => response.json())
        .then(payload => {
            if (!payload.success) {
                console.error("Failed to extract geographic structural metrics.");
                return;
            }

            payload.data.forEach(constituency => {
                if (constituency.latitude && constituency.longitude) {
                    
                    const markerOptions = {
                        radius: 8,
                        fillColor: '#009e49',
                        color: '#ffffff',
                        weight: 1.5,
                        opacity: 1,
                        fillOpacity: 0.85
                    };

                    const marker = L.circleMarker(
                        [constituency.latitude, constituency.longitude], 
                        markerOptions
                    ).addTo(map);

                    const budgetValue = constituency.total_project_budget 
                        ? constituency.total_project_budget.toLocaleString(undefined, {minimumFractionDigits: 2}) 
                        : '0.00';

                    const popupContent = `
                        <div style="color: #111; font-family: 'Inter', sans-serif; padding: 5px; min-width: 160px;">
                            <h6 style="margin: 0 0 5px 0; font-weight: 800; text-transform: uppercase; color: #009e49; font-size: 0.9rem;">
                                ${constituency.name}
                            </h6>
                            <p style="margin: 0; font-size: 0.85rem; color: #333;">
                                <strong>Committed Budget:</strong><br>
                                ZMW ${budgetValue}
                            </p>
                            <hr style="margin: 8px 0; border: 0; border-top: 1px solid #eee;">
                            <a href="/projects?constituency_id=${constituency.id}" 
                               style="display: block; text-align: center; background: #009e49; color: #fff; text-decoration: none; padding: 6px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;">
                                View Constituency Projects
                            </a>
                        </div>
                    `;
                    marker.bindPopup(popupContent);
                }
            });
        })
        .catch(error => console.error("Error executing API spatial handshake:", error));
});