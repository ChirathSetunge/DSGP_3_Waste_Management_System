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

// 📊 **Build a Weighted Graph Using Real-World Road Distance**
// 🚛 Adjusted Road Weights for Garbage Collection
const roadTypeWeights = {
    motorway: 1,       // Highways - Least weight (fastest)
    primary: 1.2,      // Major roads
    secondary: 1.5,    // Secondary roads
    tertiary: 1.8,     // Tertiary roads
    residential: 2,    // Residential roads - Normal weight (since we must cover them)
    service: 2.5,      // Service roads - More weight but still usable
    path: 4            // Least preferred (walking paths)
};

// 🔄 Dummy Data: Roads with Garbage Presence (This should come from your database or API)
const roadsWithGarbage = new Set([
    "6.832870,79.868815",  // Example roads with waste
    "6.830379,79.867886",
    "6.828325,79.871037",
    "6.826814,79.871954"
]);

// 🏗️ Build Weighted Graph Considering Garbage Collection
function buildWeightedGraph(roadData) {
    const graph = {};

    roadData.elements.forEach((way) => {
        if (way.type === "way" && way.geometry) {
            const roadType = way.tags.highway || "unknown";
            let weightFactor = roadTypeWeights[roadType] || 2;

            for (let i = 0; i < way.geometry.length - 1; i++) {
                const start = way.geometry[i];
                const end = way.geometry[i + 1];

                // ✅ Compute real-world distance using Turf.js
                const distance = turf.distance(
                    [start.lon, start.lat],
                    [end.lon, end.lat],
                    { units: "kilometers" }
                );

                const startNode = `${start.lat},${start.lon}`;
                const endNode = `${end.lat},${end.lon}`;

                // 📌 **Check if the road has garbage**
                if (roadsWithGarbage.has(startNode) || roadsWithGarbage.has(endNode)) {
                    weightFactor *= 0.5;  // Reduce weight to prioritize this road
                }

                const weightedDistance = distance * weightFactor;

                if (!graph[startNode]) graph[startNode] = {};
                if (!graph[endNode]) graph[endNode] = {};

                graph[startNode][endNode] = weightedDistance;
                graph[endNode][startNode] = weightedDistance; // Bidirectional edge
            }
        }
    });

    console.log("✅ Weighted Graph Built with Garbage Collection Considerations:", graph);
    return graph;
}

// 🔍 **Find the Closest Node Using Real-World Distance**
function findClosestNode(graph, lat, lon) {
    let closestNode = null;
    let smallestDistance = Infinity;

    for (const node in graph) {
        const [nodeLat, nodeLon] = node.split(",").map(Number);

        // ✅ **Use Turf.js instead of Euclidean distance**
        const distance = turf.distance(
            turf.point([lon, lat]),
            turf.point([nodeLon, nodeLat]),
            { units: "kilometers" }
        );

        if (distance < smallestDistance) {
            closestNode = node;
            smallestDistance = distance;
        }
    }

    return closestNode;
}

// 🔄 **Bidirectional Dijkstra Algorithm for Shortest Path**
function bidirectionalDijkstra(graph, start, end) {
    if (!graph[start] || !graph[end]) {
        console.error(`❌ Start or End node missing in graph: start(${start}), end(${end})`);
        return [];
    }

    const forwardDistances = { [start]: 0 };
    const backwardDistances = { [end]: 0 };
    const forwardPrevious = {};
    const backwardPrevious = {};
    const forwardQueue = [start];
    const backwardQueue = [end];
    const visitedForward = new Set();
    const visitedBackward = new Set();

    let mu = Infinity;
    let meetingNode = null;

    while (forwardQueue.length > 0 && backwardQueue.length > 0) {
        let u = forwardQueue.reduce((a, b) => forwardDistances[a] < forwardDistances[b] ? a : b);
        forwardQueue.splice(forwardQueue.indexOf(u), 1);
        visitedForward.add(u);

        for (const neighbor in graph[u]) {
            if (!visitedForward.has(neighbor)) {
                let newDist = forwardDistances[u] + graph[u][neighbor];
                if (newDist < (forwardDistances[neighbor] || Infinity)) {
                    forwardDistances[neighbor] = newDist;
                    forwardPrevious[neighbor] = u;
                    forwardQueue.push(neighbor);
                }
                if (visitedBackward.has(neighbor)) {
                    let totalDistance = forwardDistances[neighbor] + backwardDistances[neighbor];
                    if (totalDistance < mu) {
                        mu = totalDistance;
                        meetingNode = neighbor;
                    }
                }
            }
        }

        let v = backwardQueue.reduce((a, b) => backwardDistances[a] < backwardDistances[b] ? a : b);
        backwardQueue.splice(backwardQueue.indexOf(v), 1);
        visitedBackward.add(v);

        for (const neighbor in graph[v]) {
            if (!visitedBackward.has(neighbor)) {
                let newDist = backwardDistances[v] + graph[v][neighbor];
                if (newDist < (backwardDistances[neighbor] || Infinity)) {
                    backwardDistances[neighbor] = newDist;
                    backwardPrevious[neighbor] = v;
                    backwardQueue.push(neighbor);
                }
                if (visitedForward.has(neighbor)) {
                    let totalDistance = forwardDistances[neighbor] + backwardDistances[neighbor];
                    if (totalDistance < mu) {
                        mu = totalDistance;
                        meetingNode = neighbor;
                    }
                }
            }
        }

        if (forwardDistances[u] + backwardDistances[v] >= mu) break;
    }

    let forwardPath = [];
    let current = meetingNode;
    while (current) {
        forwardPath.unshift(current);
        current = forwardPrevious[current];
    }

    let backwardPath = [];
    current = backwardPrevious[meetingNode];
    while (current) {
        backwardPath.push(current);
        current = backwardPrevious[current];
    }

    return forwardPath.concat(backwardPath);
}

// 🗺️ **Visualize the Optimized Route on the Map**
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

    // 🎯 Compute Direct Return Path (F to A)
    const returnPath = bidirectionalDijkstra(graph, pointNodes["F"], pointNodes["A"]);

    // 🛣️ Draw the collection route in **red**
    L.polyline(fullPath.map(node => node.split(",").map(Number)), { color: "red", weight: 4 }).addTo(map);

    // 🔄 Draw the **returning** path in **blue**
    L.polyline(returnPath.map(node => node.split(",").map(Number)), { color: "blue", weight: 4 }).addTo(map);
}

// ✅ Run visualization after page load
window.onload = function() {
    visualizeRoute();
};

