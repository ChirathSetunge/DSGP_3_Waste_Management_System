from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify
import networkx as nx

from Route_Optimization_Gihanga import route_optimization_bp
from shared.models import db, Citizen

@route_optimization_bp.route('/waste-collection-map')
def waste_collection_map():
    # Ensure the driver is logged in
    vehicle_no = session.get('driver_vehicle_no')
    if not vehicle_no:
        flash('You must log in to access this page.', 'danger')
        return redirect(url_for('shared.driver_login'))

    return render_template('driver_map.html', vehicle_no=vehicle_no)


@route_optimization_bp.route('/waste-collection-map-admin')
def waste_collection_map_admin():
    """
    Renders admin_map.html, injecting real citizen locations from the DB
    so the front-end can run TSP logic on actual data.
    """

    # 1) Fetch citizen data from DB
    citizens = Citizen.query.all()

    # 2) Convert to a list of dicts with lat/lon
    citizen_points = [
        {
            "lat": c.latitude,
            "lon": c.longitude,
            "name": c.name  # optional if you want the name on the front-end
        }
        for c in citizens
    ]

    # 3) Render the template, passing citizen_points
    return render_template('admin_map.html', citizen_points=citizen_points)