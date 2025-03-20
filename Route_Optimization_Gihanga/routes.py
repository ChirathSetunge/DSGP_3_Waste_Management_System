from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify, request
import networkx as nx
from datetime import datetime, timedelta
import pytz
import math

from Route_Optimization_Gihanga import route_optimization_bp
from shared.models import db, Citizen, Driver, DriverRoute, WasteAvailability
#from Route_Optimization_Gihanga.models import db, Citizen, Driver, DriverRoute
from shared.forms import CitizenLoginForm

@route_optimization_bp.route('/waste-collection-map-admin')
def waste_collection_map_admin():
    now = datetime.utcnow()
    fourteen_hours_ago = datetime.utcnow() - timedelta(hours=14)
    waste_entries = WasteAvailability.query.filter(
        WasteAvailability.date >= fourteen_hours_ago
    ).all()
    citizen_points = [{
        "lat": w.latitude,
        "lon": w.longitude,
        "username": w.username,
        "date": w.date
    } for w in waste_entries]

    drivers = Driver.query.all()
    driver_numbers = [driver.vehicle_no for driver in drivers]

    return render_template('admin_map.html', citizen_points=citizen_points, driver_numbers=driver_numbers)

@route_optimization_bp.route('/waste-collection-map')
def waste_collection_map():
    """
    Driver page that displays the route assigned to the logged-in driver.
    """
    vehicle_no = session.get('driver_vehicle_no')
    if not vehicle_no:
        flash('You must log in to access this page.', 'danger')
        return redirect(url_for('shared.driver_login'))

    # We won't do any citizen matching. We'll just pass an empty list.
    citizen_points = []

    return render_template(
        'driver_map.html',
        vehicle_no=vehicle_no,
        citizen_points=citizen_points
    )

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


@route_optimization_bp.route('/citizen/waste_availability', methods=['GET', 'POST'])
def citizen_waste_availability():
    if 'citizen_username' not in session:
        flash('Please login to access this page.', 'danger')
        return redirect(url_for('shared.citizen_login'))

    note = "You can submit your waste availability between 7:00 PM and 6:00 AM (IST)."
    message = None

    # Convert current UTC time to IST
    tz_ist = pytz.timezone("Asia/Kolkata")
    now_utc = datetime.utcnow()
    now_ist = now_utc.replace(tzinfo=pytz.utc).astimezone(tz_ist)
    current_hour_ist = now_ist.hour

    # Allowed if hour >= 19 (7 PM) or hour < 6
    in_allowed_window = (current_hour_ist >= 19) or (current_hour_ist < 6)

    if request.method == 'POST':
        if not in_allowed_window:
            message = "You can only submit your waste availability between 7 PM and 6 AM (IST)."
        else:
            # Ensure session['waste_submitted'] is a dictionary
            if 'waste_submitted' not in session or not isinstance(session.get('waste_submitted'), dict):
                session['waste_submitted'] = {}

            username = session['citizen_username']

            # Determine window start and end in IST
            if current_hour_ist >= 19:
                # Window start = today 19:00, end = tomorrow 06:00
                window_start_ist = now_ist.replace(hour=19, minute=0, second=0, microsecond=0)
                window_end_ist = (window_start_ist + timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
            else:
                # current_hour_ist < 6: Window start = yesterday 19:00, end = today 06:00
                window_end_ist = now_ist.replace(hour=6, minute=0, second=0, microsecond=0)
                window_start_ist = (window_end_ist - timedelta(days=1)).replace(hour=19, minute=0, second=0, microsecond=0)

            # Check if user already submitted in this window
            # 1) Check DB entry ("I Have Waste")
            last_entry = (WasteAvailability.query
                          .filter_by(username=username)
                          .order_by(WasteAvailability.id.desc())
                          .first())


            already_submitted = False

            if last_entry:
                try:
                    last_time_utc = datetime.strptime(last_entry.date, "%Y-%m-%d %H:%M:%S")
                    last_time_ist = last_time_utc.replace(tzinfo=pytz.utc).astimezone(tz_ist)
                    if last_time_ist >= window_start_ist:
                        already_submitted = True
                except ValueError:
                    pass

            if already_submitted:
                message = "You have already submitted your selection in this time window."
            else:
                if request.form.get('has_waste') == 'true':
                    # "I Have Waste": record in DB
                    citizen = Citizen.query.filter_by(username=username).first()
                    if citizen:
                        new_entry = WasteAvailability(
                            username=citizen.username,
                            latitude=citizen.latitude,
                            longitude=citizen.longitude,
                            date=datetime.utcnow()  # store as a proper DateTime
                        )
                        db.session.add(new_entry)
                        db.session.commit()
                        message = "Waste availability recorded successfully!"
                    else:
                        message = "Error: Citizen record not found."
                else:
                    # "I Don't Have Waste": record submission in session (as IST)
                    now_ist_str = now_ist.strftime("%Y-%m-%d %H:%M:%S")
                    session['waste_submitted'][username] = now_ist_str
                    message = "You indicated that you don't have waste. Your choice is recorded."

    return render_template(
        'waste_availability.html',
        message=message,
        waste_date=now_utc.strftime("%Y-%m-%d"),
        waste_type="Household Waste",
        note=note
    )

@route_optimization_bp.route('/citizen-map')
def citizen_map():
    if 'citizen_username' not in session:
        flash("Please log in as a citizen first.", "danger")
        return redirect(url_for('shared.citizen_login'))

    # 1) Fetch the citizen record
    citizen = Citizen.query.filter_by(username=session['citizen_username']).first()
    if not citizen:
        flash("Citizen record not found.", "danger")
        return redirect(url_for('shared.citizen_login'))

    citizen_lat = citizen.latitude
    citizen_lon = citizen.longitude

    # ---------------------------------------------------------------------
    # 2) Check if the citizen has waste availability in the last 24 hours
    #    (Adjust the time window as needed, e.g. 14 hours, 12 hours, etc.)
    # ---------------------------------------------------------------------
    time_window_hours = 24
    cutoff = datetime.utcnow() - timedelta(hours=time_window_hours)

    recent_waste = (WasteAvailability.query
                    .filter_by(username=citizen.username)
                    .filter(WasteAvailability.date >= cutoff.strftime("%Y-%m-%d %H:%M:%S"))
                    .order_by(WasteAvailability.id.desc())
                    .first())

    if not recent_waste:
        # The citizen has no waste record in the last 24 hours
        # => Show only their house, no route
        flash("You have not indicated any waste availability recently. No pickup route assigned.", "info")

        assigned_driver_no = "N/A"
        assigned_route = []
        driver_start = [citizen_lat, citizen_lon]  # fallback
    else:
        # Citizen does have a recent waste availability
        # => We proceed to find which driver route includes them
        assigned_driver_no = None
        assigned_route = None
        TOLERANCE = 0.001
        found_match = False

        all_driver_routes = DriverRoute.query.order_by(DriverRoute.assigned_at.desc()).all()

        for dr in all_driver_routes:
            raw_points = dr.get_route()  # e.g. ["6.861,79.864","6.862,79.865"] or [[6.861,79.864], ...]
            if not raw_points:
                continue

            parsed_points = []
            for p in raw_points:
                if isinstance(p, str):
                    lat_str, lon_str = p.split(',')
                    lat = float(lat_str)
                    lon = float(lon_str)
                elif isinstance(p, list) and len(p) == 2:
                    lat = float(p[0])
                    lon = float(p[1])
                else:
                    continue

                parsed_points.append([lat, lon])

                # Check tolerance
                if (abs(lat - citizen_lat) < TOLERANCE and
                    abs(lon - citizen_lon) < TOLERANCE):
                    assigned_driver_no = dr.driver_vehicle_no
                    assigned_route = parsed_points
                    found_match = True
                    break

            if found_match:
                break

        if not assigned_driver_no:
            flash("No assigned driver found for your location yet.", "info")
            assigned_driver_no = "N/A"
            assigned_route = []
            driver_start = [citizen_lat, citizen_lon]
        else:
            # If you want the full route from DB:
            full_raw_points = (DriverRoute.query
                               .filter_by(driver_vehicle_no=assigned_driver_no)
                               .order_by(DriverRoute.assigned_at.desc())
                               .first()
                               .get_route())
            full_parsed = []
            for p in full_raw_points:
                if isinstance(p, str):
                    lat_str, lon_str = p.split(',')
                    lat = float(lat_str)
                    lon = float(lon_str)
                else:
                    lat, lon = p[0], p[1]
                full_parsed.append([lat, lon])

            assigned_route = full_parsed
            driver_start = assigned_route[0]

    # 4) Render the template
    return render_template(
        'citizen_map.html',
        citizen_lat=citizen_lat,
        citizen_lon=citizen_lon,
        driver_vehicle_no=assigned_driver_no,
        driver_start=driver_start,
        driver_route=assigned_route
    )
