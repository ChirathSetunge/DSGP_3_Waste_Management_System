// 🗺️ Map Initialization
const map = L.map("map").setView([6.8330, 79.8690], 15);

L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "© OpenStreetMap contributors",
}).addTo(map);

// 📍 Waste Collection Points
const points = {
    A: { lat: 6.837101, lon: 79.869292 },
    B: { lat: 6.835698, lon: 79.867392 },
    C: { lat: 6.832870, lon: 79.868815 },
    D: { lat: 6.830379, lon: 79.867886 },
    E: { lat: 6.828325, lon: 79.871037 },
    F: { lat: 6.826814, lon: 79.871954 },
};

// 🌍 Overpass API URL for road network data
const OVERPASS_API_URL =
    "https://overpass-api.de/api/interpreter?data=[out:json];way[highway](6.82,79.85,6.85,79.88);out geom;";

// 🚀 Fetch road data from Overpass API
async function fetchRoadData() {
    try {
        const response = await fetch(OVERPASS_API_URL);
        if (!response.ok) throw new Error(`Error fetching road data: ${response.statusText}`);
        const data = await response.json();
        console.log("✅ Road data fetched successfully:", data);
        return data;
    } catch (error) {
        console.error("❌ Road data fetch failed:", error);
        return null;
    }
}

// 📊 Build a weighted graph from Overpass API road data
function buildWeightedGraph(roadData) {
    const graph = {};
    roadData.elements.forEach((way) => {
        if (way.type === "way" && way.geometry) {
            for (let i = 0; i < way.geometry.length - 1; i++) {
                const start = way.geometry[i];
                const end = way.geometry[i + 1];

                // 🚀 Use actual road segment distances
                const distance = Math.sqrt(
                    Math.pow(end.lat - start.lat, 2) +
                    Math.pow(end.lon - start.lon, 2)
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

// 🔍 Find the closest node in the graph to a given coordinate
function findClosestNode(graph, lat, lon) {
    let closestNode = null;
    let smallestDistance = Infinity;

    for (const node in graph) {
        const [nodeLat, nodeLon] = node.split(",").map(Number);
        const distance = Math.sqrt(
            Math.pow(lat - nodeLat, 2) + Math.pow(lon - nodeLon, 2)
        );
        if (distance < smallestDistance) {
            closestNode = node;
            smallestDistance = distance;
        }
    }

    return closestNode;
}

// 🔄 Bidirectional Dijkstra Algorithm for Shortest Path
function bidirectionalDijkstra(graph, start, end) {
    const forwardDistances = {}; // Distance from start
    const backwardDistances = {}; // Distance from end
    const forwardPrevious = {};
    const backwardPrevious = {};
    const forwardQueue = [];
    const backwardQueue = [];
    const visitedForward = new Set();
    const visitedBackward = new Set();

    // Initialize distances
    for (const node in graph) {
        forwardDistances[node] = Infinity;
        backwardDistances[node] = Infinity;
        forwardPrevious[node] = null;
        backwardPrevious[node] = null;
    }

    forwardDistances[start] = 0;
    backwardDistances[end] = 0;
    forwardQueue.push(start);
    backwardQueue.push(end);

    let mu = Infinity; // Best known shortest path
    let meetingNode = null;

    while (forwardQueue.length > 0 && backwardQueue.length > 0) {
        // 🏎️ Forward search
        let u = forwardQueue.reduce((a, b) => forwardDistances[a] < forwardDistances[b] ? a : b);
        forwardQueue.splice(forwardQueue.indexOf(u), 1);
        visitedForward.add(u);

        for (const neighbor in graph[u]) {
            if (!visitedForward.has(neighbor)) {
                let newDist = forwardDistances[u] + graph[u][neighbor];
                if (newDist < forwardDistances[neighbor]) {
                    forwardDistances[neighbor] = newDist;
                    forwardPrevious[neighbor] = u;
                    forwardQueue.push(neighbor);
                }
                // Check for meeting point
                if (visitedBackward.has(neighbor)) {
                    let totalDistance = forwardDistances[neighbor] + backwardDistances[neighbor];
                    if (totalDistance < mu) {
                        mu = totalDistance;
                        meetingNode = neighbor;
                    }
                }
            }
        }

        // 🏎️ Backward search
        let v = backwardQueue.reduce((a, b) => backwardDistances[a] < backwardDistances[b] ? a : b);
        backwardQueue.splice(backwardQueue.indexOf(v), 1);
        visitedBackward.add(v);

        for (const neighbor in graph[v]) {
            if (!visitedBackward.has(neighbor)) {
                let newDist = backwardDistances[v] + graph[v][neighbor];
                if (newDist < backwardDistances[neighbor]) {
                    backwardDistances[neighbor] = newDist;
                    backwardPrevious[neighbor] = v;
                    backwardQueue.push(neighbor);
                }
                // Check for meeting point
                if (visitedForward.has(neighbor)) {
                    let totalDistance = forwardDistances[neighbor] + backwardDistances[neighbor];
                    if (totalDistance < mu) {
                        mu = totalDistance;
                        meetingNode = neighbor;
                    }
                }
            }
        }

        // Termination condition
        if (forwardDistances[u] + backwardDistances[v] >= mu) {
            break;
        }
    }

    // 🚀 Reconstruct path from start to meetingNode
    let forwardPath = [];
    let current = meetingNode;
    while (current) {
        forwardPath.unshift(current);
        current = forwardPrevious[current];
    }

    // 🚀 Reconstruct path from meetingNode to end
    let backwardPath = [];
    current = backwardPrevious[meetingNode];
    while (current) {
        backwardPath.push(current);
        current = backwardPrevious[current];
    }

    return forwardPath.concat(backwardPath);
}

// 🗺️ Visualize the optimized route on the map
async function visualizeRoute() {
    const roadData = await fetchRoadData();
    if (!roadData || !roadData.elements) return;

    const graph = buildWeightedGraph(roadData);

    const pointNodes = {};
    for (const point in points) {
        const { lat, lon } = points[point];
        pointNodes[point] = findClosestNode(graph, lat, lon);
        L.marker([lat, lon]).addTo(map).bindPopup(`Point: ${point}`);
    }

    // 📍 Create a route visiting all points
    const pointOrder = ["A", "B", "C", "D", "E", "F"];
    let fullPath = [];
    for (let i = 0; i < pointOrder.length - 1; i++) {
        const startNode = pointNodes[pointOrder[i]];
        const endNode = pointNodes[pointOrder[i + 1]];
        const path = bidirectionalDijkstra(graph, startNode, endNode);
        fullPath = fullPath.concat(path.slice(0, -1));
    }
    fullPath.push(pointNodes["F"]);

    // 🎯 Add return path (F to A)
    const returnPath = bidirectionalDijkstra(graph, pointNodes["F"], pointNodes["A"]);

    // 🛣️ Draw "going" path in **blue**
    L.polyline(fullPath.map(node => node.split(",").map(Number)), { color: "blue", weight: 4 }).addTo(map);

    // 🔄 Draw "returning" path in **red**
    L.polyline(returnPath.map(node => node.split(",").map(Number)), { color: "red", weight: 4 }).addTo(map);
}

// ✅ Run visualization after page load
window.onload = function() {
    visualizeRoute();
};
