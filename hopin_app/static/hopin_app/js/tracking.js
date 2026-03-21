// tracking.js

document.addEventListener("DOMContentLoaded", function () {

    // Grab the Django variables we passed from the HTML
    const reqId=window.TRACKING_VARS.requestId;
    const rideId=window.TRACKING_VARS.rideId;
    const rLat=window.TRACKING_VARS.riderLat;
    const rLng=window.TRACKING_VARS.riderLng;

    /* --- 1. CSRF Token Setup --- */
    function getCookie(name) {
        let cookieValue=null;
        if (document.cookie && document.cookie !== "") {
            const cookies=document.cookie.split(";");
            for (let i=0; i < cookies.length; i++) {
                const cookie=cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + "=")) {
                    cookieValue=decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken=getCookie("csrftoken");

    /* --- 2. Button State Polling --- */
    const confirmBtn=document.getElementById("confirmbutton");

    function checkPickup() {
        // Use the JavaScript variable instead of the Django tag
        fetch(`/fetchstatus/${reqId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.status === "HALFCONFIRM") {
                    confirmBtn.disabled=false;
                    confirmBtn.innerText="Confirm Pickup Now";
                } else {
                    confirmBtn.disabled=true;
                    confirmBtn.innerText="Confirm Pickup (Waiting for Driver...)";
                }
            })
            .catch(err => console.error("Status fetch error:", err));
    }
    setInterval(checkPickup, 3000);

    /* --- 3. Map Initialization --- */
    const map=L.map("map").setView([10.0469, 76.3467], 15);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);

    setTimeout(() => { map.invalidateSize(); }, 500);

    /* --- 4. Tracking Logic --- */
    const driverMarker=L.marker([10.0469, 76.3467]).addTo(map).bindPopup("Driver");
    const riderMarker=L.marker([rLat, rLng]).addTo(map).bindPopup("You are here");

    let routeLine=null;
    let routeCoords=[];
    let remainingRouteLine=null;
    let travelledRouteLine=null;

    function getDriverLocation() {
        // Use the JavaScript variables for the fetch URL
        fetch(`/fetchtracking/${rideId}/?requestid=${reqId}`)
            .then(res => res.json())
            .then(data => {

                if (data.status === "COMPLETED") {
                    clearInterval(trackingInterval);
                    alert(data.message);
                    window.location.href="/";
                    return;
                }

                const lat=parseFloat(data.lat);
                const lng=parseFloat(data.lng);
                driverMarker.setLatLng([lat, lng]);

                // Initialize Route if not drawn yet
                if (routeCoords.length === 0 && data.route) {
                    const routeGeoJSON=JSON.parse(data.route);
                    routeCoords=routeGeoJSON.coordinates.map(coord => [coord[1], coord[0]]);

                    remainingRouteLine=L.polyline(routeCoords, {
                        color: "#2563eb",
                        weight: 5,
                        opacity: 0.8
                    }).addTo(map);

                    map.fitBounds(remainingRouteLine.getBounds());

                    const coords=routeGeoJSON.coordinates;
                    const start=coords[0];
                    const end=coords[coords.length - 1];

                    L.marker([start[1], start[0]]).addTo(map).bindPopup("Start");
                    L.marker([end[1], end[0]]).addTo(map).bindPopup("Destination");
                }

                // Split route calculation
                if (routeCoords.length > 0) {
                    const driverPos=[lat, lng];
                    let closestIndex=0;
                    let minDist=Infinity;

                    routeCoords.forEach((point, i) => {
                        const dist=map.distance(driverPos, point);
                        if (dist < minDist) {
                            minDist=dist;
                            closestIndex=i;
                        }
                    });

                    const travelled=routeCoords.slice(0, closestIndex + 1);
                    const remaining=routeCoords.slice(closestIndex);

                    if (remainingRouteLine) map.removeLayer(remainingRouteLine);
                    if (travelledRouteLine) map.removeLayer(travelledRouteLine);

                    // Draw remaining route
                    remainingRouteLine=L.polyline(remaining, {
                        color: "#2563eb",
                        weight: 6
                    }).addTo(map);

                    // Draw travelled route
                    travelledRouteLine=L.polyline(travelled, {
                        color: "#9ca3af",
                        weight: 4,
                        dashArray: "5, 10"
                    }).addTo(map);
                }
            })
            .catch(err => console.error("Tracking fetch error:", err));
    }

    const trackingInterval=setInterval(getDriverLocation, 3000);

    /* --- 5. Recenter Button Logic --- */
    const recenterBtn=document.getElementById("recenterBtn");

    map.on("dragstart zoomstart", () => {
        recenterBtn.classList.remove("hidden");
    });

    recenterBtn.addEventListener("click", function () {
        if (remainingRouteLine && routeCoords.length > 0) {
            map.fitBounds(remainingRouteLine.getBounds(), { padding: [20, 20] });
        } else if (driverMarker) {
            map.setView(driverMarker.getLatLng(), 15);
        }
        recenterBtn.classList.add("hidden");
    });
});