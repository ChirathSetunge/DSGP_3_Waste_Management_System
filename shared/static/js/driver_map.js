const routePoints = routeData; // Use routeData passed from Flask

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
            if (i === 0) {
                return L.marker(waypoint.latLng, {
                    icon: L.icon({
                        iconUrl: "https://cdn-icons-png.flaticon.com/512/565/565547.png",
                        iconSize: [30, 30],
                        iconAnchor: [15, 30]
                    })
                }).bindPopup("<b>Start Point</b>");
            }

            if (i === n - 1) {
                return L.marker(waypoint.latLng, {
                    icon: L.icon({
                        iconUrl: "https://cdn-icons-png.flaticon.com/512/3349/3349114.png",
                        iconSize: [30, 30],
                        iconAnchor: [15, 30]
                    })
                }).bindPopup("<b>End Point</b>");
            }

            return L.marker(waypoint.latLng, {
                icon: L.icon({
                    iconUrl: "https://cdn-icons-png.flaticon.com/512/2534/2534094.png",
                    iconSize: [25, 25],
                    iconAnchor: [12, 25]
                })
            }).bindPopup(`<b>Point ${i + 1}</b>`);
        }
    }).addTo(map);

    routePoints.forEach((point) => {
        const marker = L.marker([point.lat, point.lon]).addTo(map);

        marker.on("click", () => {
            if (!completedHouses.includes(point.id)) {
                completedHouses.push(point.id);
                marker.setIcon(
                    L.icon({
                        iconUrl: "https://cdn-icons-png.flaticon.com/512/190/190411.png",
                        iconSize: [25, 25],
                        iconAnchor: [12, 25]
                    })
                ).bindPopup(`<b>${point.id}</b><br>Status: Collected`);
            }
        });
    });
}

initializeMap();
