from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify, request
import networkx as nx
from datetime import datetime

from Route_Optimization_Gihanga import route_optimization_bp
from shared.models import db, Citizen, Driver, DriverRoute
#from Route_Optimization_Gihanga.models import db, Citizen, Driver, DriverRoute


@route_optimization_bp.route('/waste-collection-map-admin')
def waste_collection_map_admin():
    """
    Renders admin_map.html, injecting real citizen locations from the DB
    so the front-end can run TSP logic on actual data.
    """

    # Fetch citizen data from DB
    citizens = Citizen.query.all()

    # Convert to a list of dicts with lat/lon
    citizen_points = [
        {
            "lat": c.latitude,
            "lon": c.longitude,
            "name": c.name  # optional if you want the name on the front-end
        }
        for c in citizens
    ]
    # Fetch all registered drivers (assumes at least 3 exist)
    drivers = Driver.query.all()
    driver_numbers = [driver.vehicle_no for driver in drivers]

    # Render the template, passing both citizen_points and driver_numbers
    return render_template(
        'admin_map.html',
        citizen_points=citizen_points,
        driver_numbers=driver_numbers
    )

@route_optimization_bp.route('/waste-collection-map')
def waste_collection_map():
    # Ensure the driver is logged in
    vehicle_no = session.get('driver_vehicle_no')
    if not vehicle_no:
        flash('You must log in to access this page.', 'danger')
        return redirect(url_for('shared.driver_login'))

    return render_template('driver_map.html', vehicle_no=vehicle_no)


# API: Assign Routes
@route_optimization_bp.route('/api/assign-routes', methods=['POST'])
def assign_routes():
    """
    Receives an array of route assignments from admin_map.html and
    stores/updates them in the driver_routes table.
    """
    data = request.get_json()
    assignments = data.get('assignments', [])

    for assignment in assignments:
        vehicle_no = assignment.get('vehicle_no')
        route = assignment.get('route')
        if vehicle_no and route:
            # Check if a route already exists for this driver
            driver_route = DriverRoute.query.filter_by(driver_vehicle_no=vehicle_no).first()
            if driver_route:
                # Update existing route
                driver_route.set_route(route)
                driver_route.assigned_at = datetime.utcnow()
            else:
                # Create a new record
                new_route = DriverRoute(driver_vehicle_no=vehicle_no)
                new_route.set_route(route)
                db.session.add(new_route)

    db.session.commit()
    return jsonify({"status": "success"}), 200

# API: Get Driver Route
@route_optimization_bp.route('/api/driver-route', methods=['GET'])
def get_driver_route():
    """
    Returns the assigned route (array of node-strings) for the currently
    logged-in driver, or 404 if no route was assigned.
    """
    vehicle_no = session.get('driver_vehicle_no')
    if not vehicle_no:
        return jsonify({"error": "Not logged in"}), 401

    driver_route = (
        DriverRoute.query
        .filter_by(driver_vehicle_no=vehicle_no)
        .order_by(DriverRoute.assigned_at.desc())
        .first()
    )
    if not driver_route:
        return jsonify({"error": "No route assigned"}), 404

    # Return the stored route as JSON
    return jsonify({
        "route": driver_route.get_route(),
        "assigned_at": driver_route.assigned_at.isoformat()
    })

