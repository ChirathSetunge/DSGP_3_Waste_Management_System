from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify
import networkx as nx

driver_bp = Blueprint('driver', __name__, template_folder='templates', static_folder='static')

# Waste Collection Points
points = {
    "A": {"lat": 6.837101, "lon": 79.869292},
    "B": {"lat": 6.835698, "lon": 79.867392},
    "C": {"lat": 6.832870, "lon": 79.868815},
    "D": {"lat": 6.830379, "lon": 79.867886},
    "E": {"lat": 6.828325, "lon": 79.871037},
    "F": {"lat": 6.826814, "lon": 79.871954},
}

# Example Road Network (Replace with actual road data from OpenStreetMap)
road_network = {
    ("A", "B"): {"distance": 0.5, "road_type": "residential"},
    ("B", "C"): {"distance": 1.2, "road_type": "primary"},
    ("C", "D"): {"distance": 0.8, "road_type": "secondary"},
    ("D", "E"): {"distance": 1.0, "road_type": "residential"},
    ("E", "F"): {"distance": 1.5, "road_type": "service"},
}

# Road Type Weights
road_type_weights = {
    "motorway": 1.0,
    "primary": 1.2,
    "secondary": 1.5,
    "tertiary": 1.8,
    "residential": 2.0,
    "service": 2.5,
}

# Build Weighted Graph
def build_weighted_graph():
    G = nx.DiGraph()
    for (start, end), info in road_network.items():
        distance = info["distance"]
        weight_factor = road_type_weights.get(info["road_type"], 2.0)
        weighted_distance = distance * weight_factor

        G.add_edge(start, end, weight=weighted_distance)
        G.add_edge(end, start, weight=weighted_distance)  # Bidirectional road

    return G

# Find Shortest Path Using Bidirectional Dijkstra
def find_shortest_path(graph, start, end):
    try:
        path = nx.bidirectional_dijkstra(graph, start, end, weight="weight")
        return path[1]
    except nx.NetworkXNoPath:
        return None

@driver_bp.route('/waste-collection-map')
def waste_collection_map():
    if 'driver_vehicle_no' not in session:
        flash('You must log in first.', 'danger')
        return redirect(url_for('shared.driver_login'))

    G = build_weighted_graph()
    point_order = ["A", "B", "C", "D", "E", "F"]

    full_route = []
    for i in range(len(point_order) - 1):
        sub_path = find_shortest_path(G, point_order[i], point_order[i + 1])
        if sub_path:
            full_route.extend(sub_path[:-1])

    full_route.append("F")
    return_path = find_shortest_path(G, "F", "A")

    route_data = [{"id": node, "lat": points[node]["lat"], "lon": points[node]["lon"]} for node in full_route]
    return_route = [{"id": node, "lat": points[node]["lat"], "lon": points[node]["lon"]} for node in return_path]

    return render_template(
        'driver_map.html',
        route_data=route_data,
        return_route=return_route,
        vehicle_no=session['driver_vehicle_no']
    )
