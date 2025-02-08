const map = L.map('map').setView([6.8330, 79.8690], 15); // Mount Lavinia

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    maxZoom: 19,
    attribution: '© OpenStreetMap contributors'
}).addTo(map);

// Overpass API URL to fetch road data for the area
const overpassApiUrl =
    "https://overpass-api.de/api/interpreter?data=[out:json];way[highway](6.82,79.85,6.85,79.88);out geom;";

const points = {
    A: { lat: 6.837101, lon: 79.869292 },
    B: { lat: 6.835698, lon: 79.867392 },
    C: { lat: 6.832870, lon: 79.868815 },
    D: { lat: 6.830379, lon: 79.867886 },
    E: { lat: 6.828325, lon: 79.871037 },
    F: { lat: 6.826814, lon: 79.871954 }
};

const TOMORROW_API_KEY = "ANdww0OIEYNM3xLd1xsdiPE5XC34xLDd";
const HERE_API_KEY = "4R4FFSiF3U8w3c-CMftieXcn1UbATthLqeJU5ppza-I";

// Fetch road data from Overpass API
async function fetchRoadData() {
    try {
        console.log("Fetching road data from Overpass API...");
        const response = await fetch(overpassApiUrl);
        if (!response.ok) {
            throw new Error(`Failed to fetch road data: ${response.statusText}`);
        }
        const data = await response.json();
        console.log("Road data fetched successfully:", data);
        return data;
    } catch (error) {
        console.error("Error fetching road data:", error);
    }
}

// Fetch weather and traffic data for a specific point
async function fetchWeatherAndTraffic(lat, lon) {
    try {
        const weatherResponse = await fetch(
            `https://api.tomorrow.io/v4/timelines?location=${lat},${lon}&fields=temperature,precipitationIntensity&timesteps=1h&units=metric&apikey=${TOMORROW_API_KEY}`
        );
        const weatherData = await weatherResponse.json();
        const weather = weatherData.data?.timelines?.[0]?.intervals?.[0]?.values || {};
        const temperature = weather.temperature || "N/A";
        const rain = weather.precipitationIntensity || "N/A";

        const trafficResponse = await fetch(
            `https://traffic.ls.hereapi.com/traffic/6.3/flow.json?prox=${lat},${lon},500&apikey=${HERE_API_KEY}`
        );
        const trafficData = await trafficResponse.json();
        const traffic = trafficData.RWS?.[0]?.RW?.[0]?.FIS?.[0]?.FI?.[0]?.CF?.[0] || {};
        const jamFactor = traffic.JF || "N/A";

        return {
            temperature: `${temperature}°C`,
            rain: `${rain} mm/h`,
            jamFactor: jamFactor === "N/A" ? "N/A" : jamFactor.toString()
        };
    } catch (error) {
        console.error("Error fetching weather or traffic data:", error);
        return { temperature: "Unavailable", rain: "Unavailable", jamFactor: "Unavailable" };
    }
}

// Calculate distance between two geographical points (Haversine formula)
function calculateDistance(point1, point2) {
    const R = 6371; // Earth's radius in km
    const dLat = (point2.lat - point1.lat) * (Math.PI / 180);
    const dLon = (point2.lon - point1.lon) * (Math.PI / 180);
    const a =
        Math.sin(dLat / 2) * Math.sin(dLat / 2) +
        Math.cos(point1.lat * (Math.PI / 180)) *
        Math.cos(point2.lat * (Math.PI / 180)) *
        Math.sin(dLon / 2) * Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c; // Distance in km
}

// Build a graph from road data
function buildGraph(roadData) {
    const graph = {};

    roadData.elements.forEach((way) => {
        if (way.type === "way" && way.geometry) {
            for (let i = 0; i < way.geometry.length - 1; i++) {
                const start = way.geometry[i];
                const end = way.geometry[i + 1];

                const distance = calculateDistance(
                    { lat: start.lat, lon: start.lon },
                    { lat: end.lat, lon: end.lon }
                );

                const startNode = `${start.lat},${start.lon}`;
                const endNode = `${end.lat},${end.lon}`;

                if (!graph[startNode]) graph[startNode] = {};
                if (!graph[endNode]) graph[endNode] = {};

                graph[startNode][endNode] = distance;
                graph[endNode][startNode] = distance; // Bidirectional edge
            }
        }
    });

    return graph;
}

// Find the closest node in the graph to a given coordinate
function findClosestNode(graph, lat, lon) {
    let closestNode = null;
    let smallestDistance = Infinity;

    for (const node in graph) {
        const [nodeLat, nodeLon] = node.split(",").map(Number);
        const distance = calculateDistance({ lat, lon }, { lat: nodeLat, lon: nodeLon });

        if (distance < smallestDistance) {
            closestNode = node;
            smallestDistance = distance;
        }
    }

    return closestNode;
}

// Dijkstra's algorithm for shortest path
function dijkstra(graph, start, end) {
    const distances = {};
    const previous = {};
    const queue = [];

    for (const node in graph) {
        distances[node] = Infinity;
        previous[node] = null;
        queue.push(node);
    }
    distances[start] = 0;

    while (queue.length > 0) {
        const current = queue.reduce((a, b) => (distances[a] < distances[b] ? a : b));
        queue.splice(queue.indexOf(current), 1);

        if (current === end) break;

        for (const neighbor in graph[current]) {
            const distance = distances[current] + graph[current][neighbor];
            if (distance < distances[neighbor]) {
                distances[neighbor] = distance;
                previous[neighbor] = current;
            }
        }
    }

    const path = [];
    let current = end;
    while (current) {
        path.unshift(current);
        current = previous[current];
    }
    return path;
}

// Visualize the full path covering all points and returning to A
async function visualizeRoundTripPath() {
    const roadData = await fetchRoadData();
    if (!roadData || !roadData.elements) {
        console.error("No road data available. Cannot visualize shortest path.");
        return;
    }

    const graph = buildGraph(roadData);

    // Map each point to the closest node in the graph
    const pointNodes = {};
    for (const point in points) {
        const { lat, lon } = points[point];
        const closestNode = findClosestNode(graph, lat, lon);
        pointNodes[point] = closestNode;

        // Fetch weather and traffic data for the point
        const weather = await fetchWeatherAndTraffic(lat, lon);

        // Add a marker for the point
        const marker = L.marker([lat, lon]).addTo(map);
        marker.bindPopup(`
            <b>Point: ${point}</b><br>
            Temperature: ${weather.temperature}<br>
            Rain: ${weather.rain}<br>
            Traffic Jam Factor: ${weather.jamFactor}
        `);
    }

    // Build the A to F path
    const pointOrderAtoF = ["A", "B", "C", "D", "E", "F"];
    let pathAtoF = [];
    for (let i = 0; i < pointOrderAtoF.length - 1; i++) {
        const startNode = pointNodes[pointOrderAtoF[i]];
        const endNode = pointNodes[pointOrderAtoF[i + 1]];
        const path = dijkstra(graph, startNode, endNode);
        pathAtoF = pathAtoF.concat(path.slice(0, -1)); // Avoid duplicate nodes
    }
    pathAtoF.push(pointNodes["F"]);

    // Convert path A to F nodes into coordinates
    const routeCoordsAtoF = pathAtoF.map((node) => {
        const [lat, lon] = node.split(",");
        return [parseFloat(lat), parseFloat(lon)];
    });

    L.polyline(routeCoordsAtoF, { color: "blue", weight: 4, opacity: 0.7 }).addTo(map);

    // Build the F to A path
    const pathFtoA = dijkstra(graph, pointNodes["F"], pointNodes["A"]);

    // Convert path F to A nodes into coordinates
    const routeCoordsFtoA = pathFtoA.map((node) => {
        const [lat, lon] = node.split(",");
        return [parseFloat(lat), parseFloat(lon)];
    });

    L.polyline(routeCoordsFtoA, { color: "red", weight: 4, opacity: 0.7 }).addTo(map);

    // Adjust map bounds to fit both paths
    const fullCoords = routeCoordsAtoF.concat(routeCoordsFtoA);
    map.fitBounds(L.polyline(fullCoords).getBounds());
}

visualizeRoundTripPath();
