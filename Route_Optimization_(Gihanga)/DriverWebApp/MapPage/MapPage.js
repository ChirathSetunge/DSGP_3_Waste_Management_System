const routePoints = [
    { id: "A", lat: 6.837101, lon: 79.869292 }, // Starting point
    { id: "B", lat: 6.835698, lon: 79.867392 },
    { id: "C", lat: 6.832870, lon: 79.868815 },
    { id: "D", lat: 6.830379, lon: 79.867886 },
    { id: "E", lat: 6.828325, lon: 79.871037 },
    { id: "F", lat: 6.826814, lon: 79.871954 } // End point
];

let completedHouses = []; // Track completed houses

function initializeMap() {
    const map = L.map("map").setView([6.8330, 79.8690], 15);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "© OpenStreetMap contributors"
    }).addTo(map);

    const control = L.Routing.control({
        waypoints: routePoints.map((point) => L.latLng(point.lat, point.lon)),
        routeWhileDragging: false,
        showAlternatives: false,
        createMarker: (i, waypoint, n) => {
            // Starting point marker
            if (i === 0) {
                return L.marker(waypoint.latLng, {
                    icon: L.icon({
                        iconUrl: "https://cdn-icons-png.flaticon.com/512/565/565547.png",
                        iconSize: [30, 30],
                        iconAnchor: [15, 30]
                    })
                }).bindPopup("<b>Start Point (A)</b>");
            }

            // End point marker
            if (i === n - 1) {
                return L.marker(waypoint.latLng, {
                    icon: L.icon({
                        iconUrl: "https://cdn-icons-png.flaticon.com/512/3349/3349114.png",
                        iconSize: [30, 30],
                        iconAnchor: [15, 30]
                    })
                }).bindPopup("<b>End Point (F)</b>");
            }

            // Intermediate points
            return L.marker(waypoint.latLng, {
                icon: L.icon({
                    iconUrl: "https://cdn-icons-png.flaticon.com/512/2534/2534094.png",
                    iconSize: [25, 25],
                    iconAnchor: [12, 25]
                })
            }).bindPopup(`<b>Point ${routePoints[i].id}</b>`);
        }
    }).addTo(map);

    // Track driver's current location
    const currentLocationMarker = L.marker([0, 0], {
        icon: L.icon({
            iconUrl: "https://cdn-icons-png.flaticon.com/512/684/684908.png",
            iconSize: [20, 20],
            iconAnchor: [10, 20]
        })
    }).addTo(map);

    if (navigator.geolocation) {
        navigator.geolocation.watchPosition(
            (position) => {
                const { latitude, longitude } = position.coords;
                currentLocationMarker.setLatLng([latitude, longitude]).bindPopup("Your current location");
                map.panTo([latitude, longitude]);
            },
            (error) => console.error("Error getting location:", error),
            { enableHighAccuracy: true }
        );
    }

    // Mark houses as completed
    routePoints.forEach((point) => {
        const marker = L.marker([point.lat, point.lon]).addTo(map);

        marker.on("click", () => {
            if (!completedHouses.includes(point.id)) {
                completedHouses.push(point.id);
                marker.setIcon(
                    L.icon({
                        iconUrl: "https://cdn-icons-png.flaticon.com/512/190/190411.png", // Green icon
                        iconSize: [25, 25],
                        iconAnchor: [12, 25]
                    })
                ).bindPopup(`<b>${point.id}</b><br>Status: Collected`);
            }
        });
    });
}

initializeMap();
