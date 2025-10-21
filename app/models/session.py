from datetime import datetime
from app import db

class Session(db.Model):
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')
    time_spent_s = db.Column(db.Integer, default=0)
    initial_response = db.Column(db.Text)
    
    user = db.relationship('User', back_populates='sessions')
    responses = db.relationship('Response', back_populates='session', lazy='dynamic')
    snapshots = db.relationship('ProficiencySnapshot', back_populates='session', lazy='dynamic')
    recommendations = db.relationship('Recommendation', back_populates='session', lazy='dynamic')
    
    def __repr__(self):
        return f'<Session {self.id} - {self.status}>'
