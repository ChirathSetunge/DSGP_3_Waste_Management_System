from flask import render_template, redirect, url_for, flash, session
from datetime import datetime, timedelta
from . import shared_bp
from .forms import AdminLoginForm, AdminSignupForm, DriverLoginForm, DriverSignupForm
from .models import Admin, Driver, db

# Admin Routes
@shared_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and admin.check_password(form.password.data):
            flash('Admin Login Successful!', 'success')
            return redirect(url_for('shared.admin_options'))
        else:
            flash('Invalid Username or Password', 'danger')
    return render_template('admin_login.html', form=form)


@shared_bp.route('/admin/signup', methods=['GET', 'POST'])
def admin_signup():
    form = AdminSignupForm()
    if form.validate_on_submit():
        existing_admin = Admin.query.filter_by(username=form.username.data).first()
        if existing_admin:
            flash('Username already exists.', 'danger')
        else:
            new_admin = Admin(username=form.username.data)
            new_admin.set_password(form.password.data)
            db.session.add(new_admin)
            db.session.commit()
            flash('Signup Successful!', 'success')
            return redirect(url_for('shared.admin_login'))
    return render_template('admin_signup.html', form=form)


@shared_bp.route('/admin/options')
def admin_options():
    return render_template('admin_options.html')


# Driver Routes
@shared_bp.route('/driver/login', methods=['GET', 'POST'])
def driver_login():
    form = DriverLoginForm()
    if form.validate_on_submit():
        driver = Driver.query.filter_by(vehicle_no=form.vehicle_no.data).first()
        if driver and driver.check_password(form.password.data):
            # Store the driver's vehicle number in the session
            session['driver_vehicle_no'] = driver.vehicle_no
            flash('Driver Login Successful!', 'success')
            return redirect(url_for('shared.driver_dashboard'))
        else:
            flash('Invalid Vehicle Number or Password', 'danger')
    return render_template('driver_login.html', form=form)


@shared_bp.route('/driver/signup', methods=['GET', 'POST'])
def driver_signup():
    form = DriverSignupForm()
    if form.validate_on_submit():
        existing_driver = Driver.query.filter_by(vehicle_no=form.vehicle_no.data).first()
        if existing_driver:
            flash('Vehicle Number already exists.', 'danger')
        else:
            new_driver = Driver(vehicle_no=form.vehicle_no.data)
            new_driver.set_password(form.password.data)
            db.session.add(new_driver)
            db.session.commit()
            flash('Signup Successful!', 'success')
            return redirect(url_for('shared.driver_login'))
    return render_template('driver_signup.html', form=form)


@shared_bp.route('/driver/dashboard')
def driver_dashboard():
    # Example data for the dashboard
    start_time = datetime.now()
    eta = start_time + timedelta(hours=2)
    total_houses = 25
    return render_template(
        'driver_dashboard.html',
        start_time=start_time,
        eta=eta,
        total_houses=total_houses
    )


@shared_bp.route('/driver/waste-collection-map')
def waste_collection_map():
    # Ensure the driver is logged in
    vehicle_no = session.get('driver_vehicle_no')
    if not vehicle_no:
        flash('You must log in to access this page.', 'danger')
        return redirect(url_for('shared.driver_login'))

    # Example route data
    route_data = [
        {"id": "A", "lat": 6.837101, "lon": 79.869292},
        {"id": "B", "lat": 6.835698, "lon": 79.867392},
        {"id": "C", "lat": 6.832870, "lon": 79.868815},
        {"id": "D", "lat": 6.830379, "lon": 79.867886},
        {"id": "E", "lat": 6.828325, "lon": 79.871037},
        {"id": "F", "lat": 6.826814, "lon": 79.871954},
    ]

    return render_template(
        'driver_map.html',
        route_data=route_data,
        vehicle_no=vehicle_no
    )



@shared_bp.route('/driver/chatbot')
def driver_chatbot():
    # Placeholder for the chatbot page
    return "<h1>Chatbot is under construction. Please check back later!</h1>"
