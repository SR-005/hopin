
document.addEventListener("DOMContentLoaded", function () {
    // 1. SAFE DJANGO INJECTION: Wrapped in quotes to prevent SyntaxErrors!
    const ridesCount = window.DJANGO_VARS.ridesCount;
    const collegeLat = 10.0469;
    const collegeLng = 76.3467;
    const collegeName = "AISAT Engineering College";

    let direction = "to"; // Default direction
    let userLat = null;
    let userLng = null;
    let routeLayer = null;

    // DOM Elements
    const pickupInput = document.getElementById("pickup");
    const destinationInput = document.getElementById("destination");
    const directionHidden = document.getElementById("direction-input");
    const locationHidden = document.getElementById("location-input");
    const latHidden = document.getElementById("lat-input");
    const lngHidden = document.getElementById("lng-input");

    const toBtn = document.getElementById("toCollege");
    const fromBtn = document.getElementById("fromCollege");
    const timeInput = document.getElementById("rideTime");
    const dateInput = document.getElementById("rideDate");
    const searchForm = document.getElementById("searchForm");

    const pickupResults = document.getElementById("pickup-results");
    const destinationResults = document.getElementById("destination-results");

    /* ---------------- DATE SETUP (Today & Tomorrow Only) ---------------- */
    const today = new Date();
    const tomorrow = new Date();
    tomorrow.setDate(today.getDate() + 1);

    function formatDate(d) {
        let month = (d.getMonth() + 1).toString().padStart(2, '0');
        let day = d.getDate().toString().padStart(2, '0');
        return `${d.getFullYear()}-${month}-${day}`;
    }

    if (dateInput) {
        dateInput.min = formatDate(today);
        dateInput.max = formatDate(tomorrow);
        if (!dateInput.value) dateInput.value = formatDate(today);
    }

    /* ---------------- MAP SETUP ---------------- */
    const map = L.map("map").setView([collegeLat, collegeLng], 12);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19 }).addTo(map);
    const marker = L.marker([collegeLat, collegeLng], { draggable: true }).addTo(map);
    L.marker([collegeLat, collegeLng]).addTo(map).bindPopup("College").openPopup();

    // Fix for map tiles not loading fully inside Flexbox containers
    setTimeout(() => { map.invalidateSize(); }, 500);

    /* ---------------- DIRECTION TOGGLE LOGIC ---------------- */
    function setDirection(dir) {
        direction = dir;
        if (directionHidden) directionHidden.value = dir;

        if (dir === "to") {
            // Enforce #191265 text on both buttons
            toBtn.className = "flex-1 bg-white py-3 rounded-xl text-[#191265] font-bold shadow-inner transition";
            fromBtn.className = "flex-1 bg-white/40 hover:bg-white/60 py-3 rounded-xl text-[#191265] font-bold transition";

            // Destination is College (Locked, Solid Color)
            destinationInput.value = collegeName;
            destinationInput.readOnly = true;
            destinationInput.className = "w-full bg-gray-400 rounded-xl p-3 font-semibold text-[#191265] cursor-not-allowed";

            // Pickup is Open
            pickupInput.readOnly = false;
            pickupInput.className = "w-full bg-gray-300 rounded-xl p-3 font-semibold text-[#191265]";
            if (pickupInput.value === collegeName) pickupInput.value = "";

            if (timeInput) timeInput.value = "07:45"; // 7:45 AM

        } else {
            // Enforce #191265 text on both buttons
            fromBtn.className = "flex-1 bg-white py-3 rounded-xl text-[#191265] font-bold shadow-inner transition";
            toBtn.className = "flex-1 bg-white/40 hover:bg-white/60 py-3 rounded-xl text-[#191265] font-bold transition";

            // Pickup is College (Locked, Solid Color)
            pickupInput.value = collegeName;
            pickupInput.readOnly = true;
            pickupInput.className = "w-full bg-gray-400 rounded-xl p-3 font-semibold text-[#191265] cursor-not-allowed";

            // Destination is Open
            destinationInput.readOnly = false;
            destinationInput.className = "w-full bg-gray-300 rounded-xl p-3 font-semibold text-[#191265]";
            if (destinationInput.value === collegeName) destinationInput.value = "";

            if (timeInput) timeInput.value = "13:30"; // 1:30 PM
        }
    }
    // Bind buttons
    if (toBtn && fromBtn) {
        toBtn.addEventListener("click", () => setDirection("to"));
        fromBtn.addEventListener("click", () => setDirection("from"));
        setDirection("to"); // Run once on load
    }

    /* ---------------- MAP MARKER DRAG & CLICK ---------------- */
    function updateCoordinates(lat, lng) {
        userLat = lat;
        userLng = lng;
        if (latHidden) latHidden.value = lat;
        if (lngHidden) lngHidden.value = lng;
        marker.setLatLng([lat, lng]);

        fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`)
            .then(res => res.json())
            .then(data => {
                const placeName = data.display_name;
                if (direction === "to") {
                    pickupInput.value = placeName;
                    if (locationHidden) locationHidden.value = placeName;
                } else {
                    destinationInput.value = placeName;
                    if (locationHidden) locationHidden.value = placeName;
                }
            });
    }

    marker.on("dragend", () => updateCoordinates(marker.getLatLng().lat, marker.getLatLng().lng));
    map.on("click", (e) => updateCoordinates(e.latlng.lat, e.latlng.lng));

    /* ---------------- AUTOCOMPLETE (NOMINATIM) ---------------- */
    function searchLocation(query, resultsBox, isPickup) {
        fetch(`https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(query)}&countrycodes=in&limit=5`)
            .then(res => res.json())
            .then(data => {
                resultsBox.innerHTML = "";
                data.forEach(place => {
                    const item = document.createElement("div");
                    item.className = "p-3 hover:bg-gray-100 cursor-pointer border-b border-gray-100 last:border-0 text-black";
                    item.textContent = place.display_name;

                    item.onclick = function () {
                        const lat = parseFloat(place.lat);
                        const lon = parseFloat(place.lon);

                        if (isPickup) {
                            pickupInput.value = place.display_name;
                            if (locationHidden) locationHidden.value = place.display_name;
                        } else {
                            destinationInput.value = place.display_name;
                            if (locationHidden) locationHidden.value = place.display_name;
                        }

                        if (latHidden) latHidden.value = lat;
                        if (lngHidden) lngHidden.value = lon;
                        userLat = lat;
                        userLng = lon;

                        map.setView([lat, lon], 15);
                        marker.setLatLng([lat, lon]);
                        resultsBox.innerHTML = "";
                    };
                    resultsBox.appendChild(item);
                });
            });
    }

    let timeout;
    if (pickupInput) {
        pickupInput.addEventListener("input", function () {
            if (direction === "from") return;
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                if (this.value.length >= 3) searchLocation(this.value, pickupResults, true);
                else pickupResults.innerHTML = "";
            }, 400);
        });
    }

    if (destinationInput) {
        destinationInput.addEventListener("input", function () {
            if (direction === "to") return;
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                if (this.value.length >= 3) searchLocation(this.value, destinationResults, false);
                else destinationResults.innerHTML = "";
            }, 400);
        });
    }

    document.addEventListener("click", function (e) {
        if (pickupInput && !pickupInput.contains(e.target)) pickupResults.innerHTML = "";
        if (destinationInput && !destinationInput.contains(e.target)) destinationResults.innerHTML = "";
    });

    /* ---------------- ROUTE DRAWING ON MAP ---------------- */
    const mapSubmitBtn = document.getElementById("mapSubmit");
    if (mapSubmitBtn) {
        mapSubmitBtn.addEventListener("click", function () {
            if (!userLat || !userLng) {
                alert("Please select a location on the map or type in a location first.");
                return;
            }

            let startLat, startLng, endLat, endLng;
            if (direction === "to") {
                startLat = userLat; startLng = userLng;
                endLat = collegeLat; endLng = collegeLng;
            } else {
                startLat = collegeLat; startLng = collegeLng;
                endLat = userLat; endLng = userLng;
            }

            const url = `https://router.project-osrm.org/route/v1/driving/${startLng},${startLat};${endLng},${endLat}?overview=full&geometries=geojson`;

            fetch(url)
                .then(res => res.json())
                .then(data => {
                    if (routeLayer) map.removeLayer(routeLayer);
                    routeLayer = L.geoJSON(data.routes[0].geometry, {
                        style: { color: "blue", weight: 5 }
                    }).addTo(map);
                    map.fitBounds(routeLayer.getBounds());
                });
        });
    }

    /* ---------------- FORM SUBMIT HANDLER ---------------- */
    if (searchForm) {
        searchForm.addEventListener("submit", function (e) {
            if (direction === 'to') {
                if (locationHidden) locationHidden.value = pickupInput.value;
            } else {
                if (locationHidden) locationHidden.value = destinationInput.value;
            }

            if (!latHidden.value || !lngHidden.value) {
                e.preventDefault();
                alert("Please select a specific location from the dropdown suggestions or click on the map.");
            }
        });
    }

    /* ---------------- AUTO-SCROLL IF RIDES EXIST ---------------- */
    if (ridesCount > 0) {
        const resultsSection = document.getElementById("search-results");
        if (resultsSection) resultsSection.scrollIntoView({ behavior: "smooth" });
    }
});

function clearFilters() {
    const radios = document.querySelectorAll('input[name="vehicle"]');
    radios.forEach(radio => radio.checked = false);
}
