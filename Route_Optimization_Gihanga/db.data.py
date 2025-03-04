from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# Configure the Flask application and the SQLite database location.
app = Flask(__name__)
app.config[
    'SQLALCHEMY_DATABASE_URI'] = r"sqlite:///D:/Uni Modules/Year 2/DSGP/Componant Implementation/DSGP-Git/instance/database.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# Define the Citizen model.
class Citizen(db.Model):
    __tablename__ = 'citizens'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(100), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Define the DriverStart model.
class DriverStart(db.Model):
    __tablename__ = 'driver_start'
    id = db.Column(db.Integer, primary_key=True)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)


# Data for citizens and driver's starting point.
citizens_data = [
    {"name": "Kumara Perera", "username": "kumara_perera", "password": "pass1", "latitude": 6.860520,
     "longitude": 79.864030},
    {"name": "Nimal Fernando", "username": "nimal_fernando", "password": "pass2", "latitude": 6.859603,
     "longitude": 79.864307},
    {"name": "Saman Wijesinghe", "username": "saman_wijesinghe", "password": "pass3", "latitude": 6.859521,
     "longitude": 79.864001},
    {"name": "Lakmal Silva", "username": "lakmal_silva", "password": "pass4", "latitude": 6.859508,
     "longitude": 79.863697},
    {"name": "Ruwan Jayawardena", "username": "ruwan_jayawardena", "password": "pass5", "latitude": 6.859397,
     "longitude": 79.862923},
    {"name": "Chandani De Silva", "username": "chandani_desilva", "password": "pass6", "latitude": 6.858234,
     "longitude": 79.864928},
    {"name": "Sujatha Bandara", "username": "sujatha_bandara", "password": "pass7", "latitude": 6.857815,
     "longitude": 79.865030},
    {"name": "Amarasinghe Senanayake", "username": "amarasinghe_senanayake", "password": "pass8", "latitude": 6.857400,
     "longitude": 79.865426},
    {"name": "Dilani Herath", "username": "dilani_herath", "password": "pass9", "latitude": 6.857449,
     "longitude": 79.866452},
    {"name": "Kasun Weerasinghe", "username": "kasun_weerasinghe", "password": "pass10", "latitude": 6.857283,
     "longitude": 79.866835},
    {"name": "Manoj Samarasinghe", "username": "manoj_samarasinghe", "password": "pass11", "latitude": 6.856900,
     "longitude": 79.866770},
    {"name": "Nadeesha Rajapaksha", "username": "nadeesha_rajapaksha", "password": "pass12", "latitude": 6.856251,
     "longitude": 79.866634},
    {"name": "Pasindu Abeywardena", "username": "pasindu_abeywardena", "password": "pass13", "latitude": 6.855554,
     "longitude": 79.865544},
    {"name": "Tharindu Perera", "username": "tharindu_perera", "password": "pass14", "latitude": 6.854615,
     "longitude": 79.866007},
    {"name": "Vimukthi Gunasekara", "username": "vimukthi_gunasekara", "password": "pass15", "latitude": 6.854479,
     "longitude": 79.866838},
    {"name": "Shashika Fernando", "username": "shashika_fernando", "password": "pass16", "latitude": 6.853883,
     "longitude": 79.867302},
    {"name": "Upeksha Wijeratne", "username": "upeksha_wijeratne", "password": "pass17", "latitude": 6.853150,
     "longitude": 79.866042},
    {"name": "Sahan Silva", "username": "sahan_silva", "password": "pass18", "latitude": 6.852966,
     "longitude": 79.865293},
    {"name": "Rashmi Jayakody", "username": "rashmi_jayakody", "password": "pass19", "latitude": 6.850315,
     "longitude": 79.866237},
    {"name": "Asela Kumara", "username": "asela_kumara", "password": "pass20", "latitude": 6.849501,
     "longitude": 79.866201},
    {"name": "Dileesha Chandrasekara", "username": "dileesha_chandrasekara", "password": "pass21", "latitude": 6.849023,
     "longitude": 79.866273},
    {"name": "Madhusha Rathnayake", "username": "madhusha_rathnayake", "password": "pass22", "latitude": 6.848855,
     "longitude": 79.867181},
    {"name": "Nirosha Kuruppu", "username": "nirosha_kuruppu", "password": "pass23", "latitude": 6.848453,
     "longitude": 79.867778},
    {"name": "Prasanna De Alwis", "username": "prasanna_dealwis", "password": "pass24", "latitude": 6.847886,
     "longitude": 79.867916},
    {"name": "Sajith Gunawardena", "username": "sajith_gunawardena", "password": "pass25", "latitude": 6.847471,
     "longitude": 79.868282},
    {"name": "Nalin Wickramasinghe", "username": "nalin_wickramasinghe", "password": "pass26", "latitude": 6.846422,
     "longitude": 79.868545},
    {"name": "Hiran Peris", "username": "hiran_peris", "password": "pass27", "latitude": 6.845927,
     "longitude": 79.867529},
    {"name": "Gemunu Gamage", "username": "gemunu_gamage", "password": "pass28", "latitude": 6.845839,
     "longitude": 79.866905},
    {"name": "Kavinda Samarasinghe", "username": "kavinda_samarasinghe", "password": "pass29", "latitude": 6.845635,
     "longitude": 79.866482},
    {"name": "Vindya Fernando", "username": "vindya_fernando", "password": "pass30", "latitude": 6.844720,
     "longitude": 79.867021},
    {"name": "Rohan Silva", "username": "rohan_silva", "password": "pass31", "latitude": 6.844569,
     "longitude": 79.867698},
    {"name": "Gayantha Jayasena", "username": "gayantha_jayasena", "password": "pass32", "latitude": 6.843296,
     "longitude": 79.869489},
    {"name": "Hemalatha Kumari", "username": "hemalatha_kumari", "password": "pass33", "latitude": 6.843059,
     "longitude": 79.868251}
]

driver_start_data = {"latitude": 6.861267, "longitude": 79.864307}

# API ROUTES
@app.route("/api/citizen-locations")
def get_citizen_locations():
    """
    Returns all citizens' lat/lon (plus optional name) as JSON:
    [
      { "lat": 6.859603, "lon": 79.864307, "name": "Nimal Fernando" },
      ...
    ]
    """
    citizens = Citizen.query.all()
    data = []
    for c in citizens:
        data.append({
            "lat": c.latitude,
            "lon": c.longitude,
            "name": c.name
        })
    return jsonify(data)

@app.route("/api/driver-start")
def get_driver_start():
    """
    Returns the first driver_start record as JSON:
    { "lat": 6.861267, "lon": 79.864307 }
    """
    driver_start = DriverStart.query.first()
    if driver_start:
        return jsonify({
            "lat": driver_start.latitude,
            "lon": driver_start.longitude
        })
    else:
        return jsonify({"error": "No driver start found"}), 404

@app.route("/")
def index():
    return "Hello from the Combined Flask App!"

# UTILITY: CREATE/POPULATE TABLES IF EMPTY
def initialize_database():
    """
    Creates the tables (if they don't exist) and
    populates them with sample data if they're empty.
    """
    db.create_all()

    # Check if any Citizen records exist
    if Citizen.query.count() == 0:
        for citizen in citizens_data:
            new_citizen = Citizen(
                name=citizen['name'],
                username=citizen['username'],
                latitude=citizen['latitude'],
                longitude=citizen['longitude']
            )
            new_citizen.set_password(citizen['password'])
            db.session.add(new_citizen)
        print("Populated 'citizens' table with sample data.")

    # Check if any DriverStart records exist
    if DriverStart.query.count() == 0:
        driver_start = DriverStart(
            latitude=driver_start_data['latitude'],
            longitude=driver_start_data['longitude']
        )
        db.session.add(driver_start)
        print("Populated 'driver_start' table with sample data.")

    db.session.commit()

#  MAIN ENTRY POINT
if __name__ == "__main__":
    with app.app_context():
        initialize_database()
    app.run(debug=True)