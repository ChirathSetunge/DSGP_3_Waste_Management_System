from flask import render_template, redirect, url_for, flash
from werkzeug.security import check_password_hash
from . import shared_bp
from .forms import AdminLoginForm, AdminSignupForm
from .models import Admin, db


@shared_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(username=form.username.data).first()
        if admin and check_password_hash(admin.password_hash, form.password.data):
            flash('Login successful!', 'success')
            return redirect(url_for('shared.admin_options'))
        else:
            flash('Invalid username or password.', 'danger')
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
            flash('Signup successful! You can now log in.', 'success')
            return redirect(url_for('shared.admin_login'))
    return render_template('admin_signup.html', form=form)


@shared_bp.route('/admin/options')
def admin_options():
    return render_template('admin_options.html')
