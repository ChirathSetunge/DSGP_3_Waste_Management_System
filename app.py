from flask import Flask, render_template
from shared import shared_bp, db
from Route_Optimization_Gihanga import route_optimization_bp
from HouseHold_Waste_Prediction_Chirath import household_bp
from Hospital_Waste_Prediction_Dharani import hospital_bp
from Feedback_Complaints_Chatbot_Himan import chatbot_bp, init_chatbot_db
app = Flask(__name__)

# Application Configuration
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database
db.init_app(app)

# Register the shared blueprint
app.register_blueprint(shared_bp, url_prefix='/shared')
app.register_blueprint(route_optimization_bp, url_prefix='/routeOptimization')
app.register_blueprint(household_bp, url_prefix='/household')
app.register_blueprint(hospital_bp, url_prefix='/hospital')
app.register_blueprint(chatbot_bp, url_prefix='/chat')
# Home Route
@app.route('/')
def home():
    return render_template('home.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)