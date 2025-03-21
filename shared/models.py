from . import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
from sqlalchemy import DateTime

# Admin Model
class Admin(db.Model):
    __tablename__ = 'admins'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# Driver Model
class Driver(db.Model):
    __tablename__ = 'drivers'
    id = db.Column(db.Integer, primary_key=True)
    vehicle_no = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Citizen(db.Model):
    __tablename__ = 'citizens'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    nic = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class DriverStart(db.Model):
    __tablename__ = 'driver_start'
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

class DriverRoute(db.Model):
    __tablename__ = 'driver_routes'
    id = db.Column(db.Integer, primary_key=True)
    driver_vehicle_no = db.Column(db.String(50), db.ForeignKey('drivers.vehicle_no'))
    route_data = db.Column(db.Text, nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_route(self, route_list):
        """
        Store the route in JSON form. 'route_list' might be an array of node-strings
        like ["6.861,79.864", "6.862,79.865", ...] or an array of [lat, lon] pairs.
        """
        self.route_data = json.dumps(route_list)

    def get_route(self):
        """
        Return the route as a Python list. (Convert from JSON.)
        """
        return json.loads(self.route_data)

class WasteAvailability(db.Model):
    __tablename__ = 'waste_availability'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    date = db.Column(DateTime, nullable=False) # storing the date as a text string
