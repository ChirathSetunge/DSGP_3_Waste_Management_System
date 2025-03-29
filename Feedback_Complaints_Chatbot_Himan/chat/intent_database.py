from shared import db
from datetime import datetime


class UserIntent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_message = db.Column(db.Text, nullable=False)
    predicted_intent = db.Column(db.String(100), nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    session_id = db.Column(db.String(128), nullable=True)

    def __repr__(self):
        return f"<UserIntent {self.id}: {self.predicted_intent}>"

    @classmethod
    def get_intent_counts(cls, days=30):
        from sqlalchemy import func
        import datetime

        cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=days)

        intent_counts = db.session.query(
            cls.predicted_intent,
            func.count(cls.id).label('count')
        ).filter(
            cls.timestamp >= cutoff_date
        ).group_by(
            cls.predicted_intent
        ).all()

        counts = {intent: count for intent, count in intent_counts}
        total = sum(counts.values()) if counts else 0

        percentages = {}
        if total > 0:
            percentages = {intent: (count / total) * 100 for intent, count in counts.items()}

        return {
            'counts': counts,
            'percentages': percentages,
            'total_analyzed': total
        }

    @classmethod
    def get_recent_intents(cls, limit=50):
        return cls.query.order_by(cls.timestamp.desc()).limit(limit).all()
