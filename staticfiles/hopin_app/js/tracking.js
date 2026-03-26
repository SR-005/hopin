// tracking.js

document.addEventListener("DOMContentLoaded", function () {

    // Grab the Django variables we passed from the HTML
    const reqId = window.TRACKING_VARS.requestId;
    const rideId = window.TRACKING_VARS.rideId;
    const rLat = window.TRACKING_VARS.riderLat;
    const rLng = window.TRACKING_VARS.riderLng;

    let hasRideEnded = false; // Flag to prevent multiple alerts/redirects
    let lastETA = null;       // For ETA smoothing logic

    /* --- 1. CSRF Token Setup --- */
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== "") {
            const cookies = document.cookie.split(";");
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + "=")) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie("csrftoken");

    /* --- 2. Button & Ride End Logic --- */
    const confirmBtn = document.getElementById("confirmbutton");

    function handleRideEnded(message = "Ride completed successfully") {
        if (hasRideEnded) return;
        hasRideEnded = true;
        clearInterval(statusInterval);
        clearInterval(trackingInterval);
        alert(message);
        window.location.href = "/";
    }

    function checkPickup() {
        if (hasRideEnded) return;

        fetch(`/fetchstatus/${reqId}/`)
            .then(response => response.json())
            .then(data => {
                // Test code logic: End ride if these statuses occur
                if (["DROPPED", "DROPPEDNOTCONFIRMED", "NOTBOARDED"].includes(data.status)) {
                    handleRideEnded();
                    return;
                }

                // Confirm button behavior
                if (data.status === "HALFCONFIRM") {
                    confirmBtn.disabled = false;
                    confirmBtn.innerText = "Confirm Pickup Now";
                } else {
                    confirmBtn.disabled = true;
                    confirmBtn.innerText = "Confirm Pickup ";
                }
            })
            .catch(err => console.error("Status fetch error:", err));
    }
    const statusInterval = setInterval(checkPickup, 2000);

    /* --- 3. Map Initialization --- */
    const map = L.map("map").setView([10.050272, 76.329273], 15);
    map.eachLayer(function (layer) {
        if (layer instanceof L.Polyline) {
            map.removeLayer(layer);
        }
    });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors"
    }).addTo(map);

    setTimeout(() => { map.invalidateSize(); }, 500);

    /* --- 4. Tracking & ETA Logic --- */
    const driverMarker = L.marker([10.050272, 76.329273]).addTo(map).bindPopup("Driver");
    const riderMarker = L.marker([rLat, rLng]).addTo(map).bindPopup("Rider Destination");



    function getDriverLocation() {
        if (hasRideEnded) return;

        fetch(`/fetchtracking/${rideId}/?requestid=${reqId}`)
            .then(res => res.json())
            .then(data => {
                if (data.route) {
                    console.log("Route ignored");
                    data.route = null;
                }
                // Test code logic: Handle redirect flag
                if (data.redirect || data.status === "COMPLETED") {
                    handleRideEnded(data.message || "Ride completed successfully");
                    return;
                }

                // --- ETA Smoothing Logic from test page ---
                if (data.eta !== undefined) {
                    if (lastETA === null) {
                        lastETA = data.eta;
                    } else {
                        // Weighted average to prevent jumping
                        lastETA = 0.7 * lastETA + 0.3 * data.eta;
                    }
                    // Updating text (you can add a <p id="etaText"> to your HTML if you want to show it)
                    const etaEl = document.getElementById("etaText");
                    if (etaEl) {
                        etaEl.innerText = `Driver arrives in ${Math.round(lastETA)} min`;
                    }
                }

                const lat = parseFloat(data.lat);
                const lng = parseFloat(data.lng);
                driverMarker.setLatLng([lat, lng]);

                // Initialize Route


                // Split route calculation (Remaining vs Travelled)

            })
            .catch(err => console.error("Tracking fetch error:", err));
    }

    const trackingInterval = setInterval(getDriverLocation, 3000);

    /* --- 5. Recenter Button Logic --- */
    const recenterBtn = document.getElementById("recenterBtn");
    map.on("dragstart zoomstart", () => recenterBtn.classList.remove("hidden"));

    if (recenterBtn) {
        recenterBtn.addEventListener("click", function () {
            map.setView(driverMarker.getLatLng(), 15);
            recenterBtn.classList.add("hidden");
        });
    }
});
