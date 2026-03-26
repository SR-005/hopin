
document.addEventListener("DOMContentLoaded", function () {

    const ridesCount = window.DJANGO_VARS.ridesCount;
    const collegeLat = 10.050272;
    const collegeLng = 76.329273;
    const collegeName = "AISAT Engineering College";
    const maxLocationLength = 100;

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
    const ridesList = document.getElementById("ridesList");
    const rideCards = ridesList ? Array.from(ridesList.querySelectorAll(".ride-card")) : [];
    const vehicleRadios = Array.from(document.querySelectorAll('input[name="vehicle"]'));
    const helmetFilter = document.getElementById("helmetFilter");
    const helmetFilterLabel = helmetFilter ? helmetFilter.closest("label") : null;
    const sortFilter = document.getElementById("sortFilter");
    const filteredEmptyState = document.getElementById("filteredEmptyState");
    const ridesCountLabel = document.getElementById("ridesCountLabel");

    //TOAST
    function showToast(message, type = "info") {
        const toast = document.createElement("div");

        const colors = {
            success: "bg-green-600",
            error: "bg-red-600",
            info: "bg-blue-600"
        };

        toast.className = `${colors[type]} text-white px-4 py-3 rounded-xl shadow-lg fixed top-5 right-5 z-50`;

        toast.innerText = message;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    const cancelledRequestStorageKey = "rider_cancelled_request_ids";

    function getCancelledRequestIds() {
        try {
            const rawValue = sessionStorage.getItem(cancelledRequestStorageKey);
            const parsedValue = rawValue ? JSON.parse(rawValue) : [];
            return Array.isArray(parsedValue) ? parsedValue.map(String) : [];
        } catch (error) {
            console.warn("Could not read cancelled request ids:", error);
            return [];
        }
    }

    function setCancelledRequestIds(requestIds) {
        sessionStorage.setItem(
            cancelledRequestStorageKey,
            JSON.stringify(Array.from(new Set(requestIds.map(String))))
        );
    }

    function rememberCancelledRequest(requestId) {
        if (!requestId) return;

        const requestIds = getCancelledRequestIds();
        requestIds.push(String(requestId));
        setCancelledRequestIds(requestIds);
    }

    function forgetCancelledRequests(requestIdsToRemove) {
        if (!requestIdsToRemove.length) return;

        const idsToRemove = new Set(requestIdsToRemove.map(String));
        const remainingIds = getCancelledRequestIds().filter(id => !idsToRemove.has(id));
        setCancelledRequestIds(remainingIds);
    }


    function trimLocationLabel(label) {
        if (!label) return "";
        const normalized = label.replace(/\s+/g, " ").trim();
        return normalized.slice(0, maxLocationLength);
    }

    function buildShortLocationLabel(place) {
        const address = place?.address || {};
        const nameParts = [
            place?.name,
            address.road,
            address.neighbourhood,
            address.suburb,
            address.hamlet,
            address.quarter,
            address.village,
            address.town,
            address.city
        ].filter(Boolean);

        const primaryName = nameParts[0] || "";
        const locality = address.city || address.town || address.village || address.suburb || address.state_district || address.state || "";
        const shortLabel = locality && primaryName && locality !== primaryName
            ? `${primaryName}, ${locality}`
            : (primaryName || locality || place?.display_name || "");

        return trimLocationLabel(shortLabel);
    }

    function setSelectedLocation(placeName, isPickup) {
        const safePlaceName = trimLocationLabel(placeName);
        if (isPickup) {
            pickupInput.value = safePlaceName;
        } else {
            destinationInput.value = safePlaceName;
        }

        if (locationHidden) locationHidden.value = safePlaceName;
    }

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
                const placeName = buildShortLocationLabel(data);
                setSelectedLocation(placeName, direction === "to");
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
                    const shortPlaceName = buildShortLocationLabel(place);
                    item.textContent = shortPlaceName;

                    item.onclick = function () {
                        const lat = parseFloat(place.lat);
                        const lon = parseFloat(place.lon);

                        setSelectedLocation(shortPlaceName, isPickup);

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
    if (pickupInput) pickupInput.maxLength = maxLocationLength;
    if (destinationInput) destinationInput.maxLength = maxLocationLength;

    if (searchForm) {
        searchForm.addEventListener("submit", function (e) {
            if (direction === 'to') {
                if (locationHidden) locationHidden.value = trimLocationLabel(pickupInput.value);
                pickupInput.value = trimLocationLabel(pickupInput.value);
            } else {
                if (locationHidden) locationHidden.value = trimLocationLabel(destinationInput.value);
                destinationInput.value = trimLocationLabel(destinationInput.value);
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

    /* ---------------- RESULT FILTERS & SORT ---------------- */
    function updateResultsCount(count) {
        if (!ridesCountLabel) return;
        ridesCountLabel.textContent = `${count} Ride${count === 1 ? "" : "s"} Available`;
    }

    function applyRideCardOrder(cards) {
        cards.forEach((card, index) => {
            card.style.order = String(index);
        });

        if (filteredEmptyState) {
            filteredEmptyState.style.order = String(cards.length);
        }
    }

    function getSelectedVehicle() {
        const selectedRadio = vehicleRadios.find(radio => radio.checked);
        return selectedRadio ? selectedRadio.value : "";
    }

    function parseCardRating(card) {
        const rawRating = (card.dataset.rating || "").trim();
        const parsedRating = Number.parseFloat(rawRating);
        if (Number.isFinite(parsedRating)) {
            return parsedRating;
        }

        const visibleRating = card.querySelector(".driver-rating-value")?.textContent?.trim() || "";
        const parsedVisibleRating = Number.parseFloat(visibleRating);
        return Number.isFinite(parsedVisibleRating) ? parsedVisibleRating : 0;
    }

    function sortRideCards(cards, sortValue) {
        const sortedCards = [...cards];

        if (sortValue === "rating-desc") {
            sortedCards.sort((a, b) => {
                const ratingDiff = parseCardRating(b) - parseCardRating(a);
                if (ratingDiff !== 0) return ratingDiff;
                return parseInt(a.dataset.originalOrder || "0", 10) - parseInt(b.dataset.originalOrder || "0", 10);
            });
        } else {
            sortedCards.sort((a, b) => parseInt(a.dataset.originalOrder || "0", 10) - parseInt(b.dataset.originalOrder || "0", 10));
        }

        return sortedCards;
    }

    function updateHelmetFilterState() {
        if (!helmetFilter) return;

        const selectedVehicle = getSelectedVehicle();
        const shouldDisableHelmet = selectedVehicle === "car";

        if (shouldDisableHelmet) {
            helmetFilter.checked = false;
        }

        helmetFilter.disabled = shouldDisableHelmet;

        if (helmetFilterLabel) {
            helmetFilterLabel.classList.toggle("opacity-50", shouldDisableHelmet);
            helmetFilterLabel.classList.toggle("cursor-not-allowed", shouldDisableHelmet);
        }
    }

    function applyRideFilters() {
        if (!rideCards.length) return;

        const selectedVehicle = getSelectedVehicle();
        const requiresHelmet = helmetFilter ? helmetFilter.checked : false;
        const sortValue = sortFilter ? sortFilter.value : "optimized";
        const sortedCards = sortRideCards(rideCards, sortValue);

        let visibleCount = 0;

        sortedCards.forEach(card => {
            const cardVehicle = (card.dataset.vehicle || "").toLowerCase();
            const cardHelmet = (card.dataset.helmet || "").toLowerCase();
            const matchesVehicle = !selectedVehicle || cardVehicle === selectedVehicle;
            const matchesHelmet = !requiresHelmet || (cardVehicle === "bike" && cardHelmet === "yes");
            const shouldShow = matchesVehicle && matchesHelmet;

            card.classList.toggle("hidden", !shouldShow);
            if (shouldShow) visibleCount += 1;
        });

        applyRideCardOrder(sortedCards);
        updateResultsCount(visibleCount);

        if (filteredEmptyState) {
            filteredEmptyState.classList.toggle("hidden", visibleCount !== 0);
        }
    }

    function clearRideFilters() {
        vehicleRadios.forEach(radio => {
            radio.checked = false;
        });

        if (helmetFilter) {
            helmetFilter.checked = false;
        }

        if (sortFilter) {
            sortFilter.value = "optimized";
        }

        updateHelmetFilterState();
        applyRideFilters();
    }

    if (rideCards.length) {
        vehicleRadios.forEach(radio => {
            radio.addEventListener("change", function () {
                updateHelmetFilterState();
                applyRideFilters();
            });
        });

        if (helmetFilter) {
            helmetFilter.addEventListener("change", applyRideFilters);
        }

        if (sortFilter) {
            sortFilter.addEventListener("change", applyRideFilters);
        }

        updateHelmetFilterState();
        applyRideFilters();
    }

    window.clearFilters = clearRideFilters;

    document.addEventListener("click", function (event) {
        const cancelButton = event.target.closest('#rider-state button[name="action"][value="cancelrequest"]');
        if (!cancelButton) return;

        const form = cancelButton.closest("form");
        const requestId = form?.querySelector('input[name="requestid"]')?.value;
        rememberCancelledRequest(requestId);
    });

    document.addEventListener("submit", function (event) {
        const form = event.target;
        if (!(form instanceof HTMLFormElement)) return;
        if (!form.closest("#rider-state")) return;

        const submitter = event.submitter;
        if (!submitter || submitter.name !== "action" || submitter.value !== "cancelrequest") return;

        const requestId = form.querySelector('input[name="requestid"]')?.value;
        rememberCancelledRequest(requestId);
    });

    let prevAccepted = [];
    let prevPending = [];
    let initialized = false;

    function getNewItems(newArr, oldArr) {
        return newArr.filter(id => !oldArr.includes(id));
    }

    function getRemovedItems(newArr, oldArr) {
        return oldArr.filter(id => !newArr.includes(id));
    }

    function startRiderPollingLegacy() {
        const container = document.getElementById("rider-state");
        if (!container) return;
        return;

        async function poll() {
            if (window.isMapViewing === true) {
                console.log("Polling skipped because map is currently open.");
                return;
            }
            try {
                const res = await fetch("/rider/poll/");
                const contentType = res.headers.get("content-type") || "";

                if (!res.ok || !contentType.includes("application/json")) {
                    const responseText = await res.text();
                    throw new Error(`Polling returned ${res.status}: ${responseText.slice(0, 120)}`);
                }

                const data = await res.json();

                if (initialized) {
                    const newlyAccepted = getNewItems(data.accepted_ids, prevAccepted);
                    const removedPending = getRemovedItems(data.pending_ids, prevPending);
                    const removedAccepted = getRemovedItems(data.accepted_ids, prevAccepted);
                    const rejectedIds = data.rejected_ids || [];
                    const activeRequestIds = data.active_request_ids || [];
                    const deletedPendingRequests = removedPending.filter(id =>
                        !rejectedIds.includes(id) && !activeRequestIds.includes(id)
                    );
                    const deletedAcceptedRequests = removedAccepted.filter(id =>
                        !rejectedIds.includes(id) && !activeRequestIds.includes(id)
                    );

                    if (newlyAccepted.length > 0) {
                        showToast("🎉 Your ride was accepted!", "success");
                    }

                    const actuallyRejected = removedPending.filter(id => rejectedIds.includes(id));

                    if (actuallyRejected.length > 0) {
                        showToast("❌ A driver rejected your request", "error");
                    }

                    if (deletedPendingRequests.length > 0 || deletedAcceptedRequests.length > 0) {
                        showToast("The driver deleted the ride, so your request was removed.", "error");
                    }
                }
                initialized = true;
                prevAccepted = [...data.accepted_ids];
                prevPending = [...data.pending_ids];

                if (data.html) {
                    container.innerHTML = data.html;
                }
            } catch (err) {
                console.error("Polling error:", err);
            }
        }

        // poll every 5 seconds
        setInterval(poll, 5000);
    }

    let riderPollingAcceptedIds = [];
    let riderPollingPendingIds = [];
    let riderPollingInitialized = false;

    function startRiderPolling() {
        const container = document.getElementById("rider-state");
        if (!container) return;

        async function poll() {
            if (typeof isMapViewing !== 'undefined' && isMapViewing) return;
            if (window.isMapViewing === true) {
                console.log("Polling paused because map is open");
                return;
            }
            try {
                const res = await fetch("/rider/poll/");
                const contentType = res.headers.get("content-type") || "";

                if (!res.ok || !contentType.includes("application/json")) {
                    const responseText = await res.text();
                    throw new Error(`Polling returned ${res.status}: ${responseText.slice(0, 120)}`);
                }

                const data = await res.json();
                const acceptedIds = data.accepted_ids || [];
                const pendingIds = data.pending_ids || [];
                const rejectedIds = data.rejected_ids || [];
                const activeRequestIds = data.active_request_ids || [];
                const cancelledRequestIds = getCancelledRequestIds();
                const visibleRequestIds = [...acceptedIds, ...pendingIds, ...activeRequestIds].map(String);
                const staleCancelledIds = cancelledRequestIds.filter(id => !visibleRequestIds.includes(String(id)));

                if (staleCancelledIds.length > 0) {
                    forgetCancelledRequests(staleCancelledIds);
                }

                if (riderPollingInitialized) {
                    const newlyAccepted = getNewItems(acceptedIds, riderPollingAcceptedIds);
                    const removedPending = getRemovedItems(pendingIds, riderPollingPendingIds);
                    const removedAccepted = getRemovedItems(acceptedIds, riderPollingAcceptedIds);
                    const driverDeletedPendingRequests = removedPending.filter(id =>
                        !rejectedIds.includes(id) &&
                        !activeRequestIds.includes(id) &&
                        !cancelledRequestIds.includes(String(id))
                    );
                    const driverDeletedAcceptedRequests = removedAccepted.filter(id =>
                        !rejectedIds.includes(id) &&
                        !activeRequestIds.includes(id) &&
                        !cancelledRequestIds.includes(String(id))
                    );
                    const selfCancelledRequests = [...removedPending, ...removedAccepted].filter(id =>
                        cancelledRequestIds.includes(String(id))
                    );
                    const actuallyRejected = removedPending.filter(id => rejectedIds.includes(id));

                    if (newlyAccepted.length > 0) {
                        showToast("Your ride was accepted!", "success");
                    }

                    if (actuallyRejected.length > 0) {
                        showToast("A driver rejected your request", "error");
                    }

                    if (driverDeletedPendingRequests.length > 0 || driverDeletedAcceptedRequests.length > 0) {
                        showToast("The driver deleted the ride, so your request was removed.", "error");
                    }

                    if (selfCancelledRequests.length > 0) {
                        forgetCancelledRequests(selfCancelledRequests);
                    }
                }

                riderPollingInitialized = true;
                riderPollingAcceptedIds = [...acceptedIds];
                riderPollingPendingIds = [...pendingIds];

                if (data.html) {
                    container.innerHTML = data.html;
                }
            } catch (err) {
                console.error("Polling error:", err);
            }
        }

        setInterval(poll, 5000);
    }

    // start after DOM ready
    startRiderPolling();
});
// Use window. to make it 100% global
window.isMapViewing = false;
let popupMap = null;
let routeLayer = null;
let mapMarkers = [];

function showRoutePopup(sLat, sLng, eLat, eLng) {
    window.isMapViewing = true; // LOCK: Stop background polling
    console.log("Map opened! Polling locked.");

    if (!sLat || !sLng || !eLat || !eLng) {
        alert("Location coordinates are missing for this ride.");
        return;
    }

    const modal = document.getElementById('mapModal');
    modal.classList.remove('hidden');
    modal.classList.add('flex');

    if (!popupMap) {
        popupMap = L.map('popupMap').setView([sLat, sLng], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(popupMap);
    }

    setTimeout(() => {
        popupMap.invalidateSize();

        if (routeLayer) popupMap.removeLayer(routeLayer);
        mapMarkers.forEach(m => popupMap.removeLayer(m));
        mapMarkers = [];

        const url = `https://router.project-osrm.org/route/v1/driving/${sLng},${sLat};${eLng},${eLat}?overview=full&geometries=geojson`;

        fetch(url)
            .then(res => res.json())
            .then(data => {
                if (!data.routes || data.routes.length === 0) return;

                routeLayer = L.geoJSON(data.routes[0].geometry, {
                    style: { color: '#191265', weight: 6, opacity: 0.8 }
                }).addTo(popupMap);

                const startMarker = L.marker([sLat, sLng]).addTo(popupMap).bindPopup("Start");
                const endMarker = L.marker([eLat, eLng]).addTo(popupMap).bindPopup("End");
                mapMarkers.push(startMarker, endMarker);

                popupMap.fitBounds(routeLayer.getBounds(), { padding: [50, 50] });
            })
            .catch(err => console.error("OSRM Fetch Error:", err));
    }, 300);
}

function closeMapPopup() {
    window.isMapViewing = false; // UNLOCK: Resume background polling!
    console.log("Map closed! Polling resumed.");

    const modal = document.getElementById('mapModal');
    if (modal) {
        modal.classList.add('hidden');
        modal.classList.remove('flex');

        if (popupMap) {
            popupMap.stop();
        }
    }
}

document.addEventListener('keydown', function (e) {
    if (e.key === "Escape") {
        closeMapPopup();
    }
});
