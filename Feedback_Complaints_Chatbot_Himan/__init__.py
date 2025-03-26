from flask import Blueprint
from Feedback_Complaints_Chatbot_Himan.chat.intent_database import db

chatbot_bp = Blueprint('chatbot', __name__, template_folder='templates', static_folder='static')

from Feedback_Complaints_Chatbot_Himan import routes


def init_chatbot_db(app):
    with app.app_context():
        db.create_all()
