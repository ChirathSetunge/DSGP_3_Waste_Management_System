from flask import render_template, redirect, url_for, flash, session
from datetime import datetime, timedelta
from . import shared_bp
from .forms import AdminLoginForm, AdminSignupForm, DriverLoginForm, DriverSignupForm, CitizenLoginForm
from .models import Admin, Driver, db, Citizen

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

# Citizen routes
@shared_bp.route('/citizen/login', methods=['GET', 'POST'])
def citizen_login():
    form = CitizenLoginForm()
    if form.validate_on_submit():
        citizen = Citizen.query.filter_by(username=form.username.data).first()
        if citizen and citizen.check_password(form.password.data):
            # Store the citizen's username in the session
            session['citizen_username'] = citizen.username
            flash('Citizen Login Successful!', 'success')
            return redirect(url_for('shared.citizen_options'))
        else:
            flash('Invalid Username or Password', 'danger')
    return render_template('citizen_login.html', form=form)

@shared_bp.route('/citizen/options')
def citizen_options():
    return render_template('citizen_options.html')