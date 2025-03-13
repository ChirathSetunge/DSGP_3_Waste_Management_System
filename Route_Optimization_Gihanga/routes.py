from flask import Blueprint, render_template, session, redirect, url_for, flash, jsonify, request
import networkx as nx
from datetime import datetime, timedelta
import pytz

from Route_Optimization_Gihanga import route_optimization_bp
from shared.models import db, Citizen, Driver, DriverRoute, WasteAvailability
#from Route_Optimization_Gihanga.models import db, Citizen, Driver, DriverRoute
from shared.forms import CitizenLoginForm

@route_optimization_bp.route('/waste-collection-map-admin')
def waste_collection_map_admin():
    now = datetime.utcnow()
    fourteen_hours_ago = now - timedelta(hours=14)
    threshold_str = fourteen_hours_ago.strftime("%Y-%m-%d %H:%M:%S")
    waste_entries = WasteAvailability.query.filter(WasteAvailability.date >= threshold_str).all()

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

            # 2) Check session entry ("I Don't Have Waste")
            session_submitted_time = session['waste_submitted'].get(username)

            already_submitted = False

            if last_entry:
                try:
                    last_time_utc = datetime.strptime(last_entry.date, "%Y-%m-%d %H:%M:%S")
                    last_time_ist = last_time_utc.replace(tzinfo=pytz.utc).astimezone(tz_ist)
                    if last_time_ist >= window_start_ist:
                        already_submitted = True
                except ValueError:
                    pass

            if session_submitted_time:
                try:
                    # Parse the session time (stored as IST string) and localize it to IST
                    naive_ist = datetime.strptime(session_submitted_time, "%Y-%m-%d %H:%M:%S")
                    session_time_ist = tz_ist.localize(naive_ist)
                    if session_time_ist >= window_start_ist:
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
                            date=now_utc.strftime("%Y-%m-%d %H:%M:%S")  # stored in UTC
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
