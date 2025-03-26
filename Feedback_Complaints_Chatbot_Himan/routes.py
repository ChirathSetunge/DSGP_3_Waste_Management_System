from flask import Flask, render_template, request, jsonify, session
import uuid
from Feedback_Complaints_Chatbot_Himan.chat.processor import ChatProcessor
from Feedback_Complaints_Chatbot_Himan.chat.intent_database import db, UserIntent
from Feedback_Complaints_Chatbot_Himan.chat.suggestions_generator import SuggestionsGenerator
from Feedback_Complaints_Chatbot_Himan import chatbot_bp

chat_processor = ChatProcessor()
suggestions_generator = SuggestionsGenerator()

@chatbot_bp.route('/chat/user')
def user_dashboard():
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
    return render_template('chat.html')


@chatbot_bp.route('/chat/admin')
def admin_dashboard():
    return render_template('chat_admin.html')


@chatbot_bp.route('/chat', methods=['POST'])
def chat():
    data = request.json
    user_message = data.get('message')
    action = data.get('action')
    session_id = session.get('session_id', str(uuid.uuid4()))

    result = {
        'response': '',
        'suggestions': []
    }

    try:
        if action:
            if action == 'schedule':
                result['response'] = chat_processor.process_message(
                    "Show me my waste collection schedule", session_id)
            elif action == 'recycle-guide':
                result['response'] = chat_processor.process_message(
                    "What's the guide for recycling different materials?", session_id)
            elif action == 'report-issue':
                result['response'] = chat_processor.process_message(
                    "I want to report an issue with waste collection", session_id)
            elif action == 'tips':
                result['response'] = chat_processor.process_message(
                    "Share some eco-friendly waste management tips", session_id)
        elif user_message:
            result['response'] = chat_processor.process_message(user_message, session_id)
        else:
            return jsonify({'error': 'No message or action provided'}), 400

        result['suggestions'] = suggestions_generator.generate_suggestions(
            user_message if user_message else action,
            result['response']
        )

        return jsonify(result)

    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({'error': 'An error occurred processing your request'}), 500


@chatbot_bp.route('/admin/intents')
def get_intents():
    try:
        days = int(request.args.get('days', 30))
        return jsonify(UserIntent.get_intent_counts(days))
    except Exception as e:
        print(f"Error getting intent statistics: {e}")
        return jsonify({'error': 'Error getting intent statistics'}), 500


@chatbot_bp.route('/admin/recent-intents')
def get_recent_intents():
    try:
        intents = UserIntent.get_recent_intents(limit=50)
        intent_list = [{
            'id': intent.id,
            'user_message': intent.user_message,
            'predicted_intent': intent.predicted_intent,
            'confidence': intent.confidence,
            'timestamp': intent.timestamp.isoformat(),
            'session_id': intent.session_id
        } for intent in intents]

        return jsonify(intent_list)
    except Exception as e:
        print(f"Error getting recent intents: {e}")
        return jsonify({'error': 'Error getting recent intents'}), 500